"""Shared Markdown-to-PDF conversion engine."""

from __future__ import annotations

import base64
import io
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional, Sequence, Union

import markdown as md_lib

_PathInput = Union[str, os.PathLike]


def resource_path(relative: str) -> Path:
    """Resolve a runtime resource from source or a PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative


DEFAULT_CSS_PATH = resource_path("style.css")
ICONS_DIR = resource_path("icons")
BROWSERS_DIR = resource_path("browsers")

# A frozen artifact must prefer its bundled browser over the user's cache.
if BROWSERS_DIR.exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSERS_DIR))

# Embedded PNGs avoid dependence on platform emoji fonts for these status
# symbols. Cross-platform page equivalence is validated separately.
_EMOJI_FILES = {
    "\u2705": "icons_check.png",
    "\u26A0\uFE0F": "icons_warning.png",
    "\u26A0": "icons_warning.png",
    "\U0001F7E0": "icons_orange.png",
    "\U0001F501": "icons_repeat.png",
    "\u26D4": "icons_no_entry.png",
}

_icon_cache: dict[str, str] = {}


def _icon_data_uri(filename: str) -> str:
    if filename not in _icon_cache:
        path = ICONS_DIR / filename
        data = path.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        _icon_cache[filename] = f"data:image/png;base64,{encoded}"
    return _icon_cache[filename]


def substitute_emoji_icons(html: str) -> str:
    """Replace supported status emoji with embedded PNG images."""
    for ch, filename in _EMOJI_FILES.items():
        if ch in html:
            uri = _icon_data_uri(filename)
            html = html.replace(ch, f'<img class="emoji" src="{uri}" alt="">')
    return html


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown text to the HTML fragment used by the renderer."""
    html = md_lib.markdown(markdown_text, extensions=["extra", "sane_lists"])
    return substitute_emoji_icons(html)


def extract_title(html: str, default: str = "Document") -> str:
    """Return plain text from the first level-one heading."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if not m:
        return default
    text = re.sub(r"<[^>]+>", "", m.group(1))
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or default


@dataclass
class HeaderFooterConfig:
    """Text templates for the three header and three footer positions."""

    top_left: str = ""
    top_center: str = ""
    top_right: str = ""
    bottom_left: str = ""
    bottom_center: str = "Page {page} / {total}"
    bottom_right: str = ""

    def is_empty(self) -> bool:
        return not any(
            (
                self.top_left,
                self.top_center,
                self.top_right,
                self.bottom_left,
                self.bottom_center,
                self.bottom_right,
            )
        )

    @classmethod
    def none(cls) -> "HeaderFooterConfig":
        """Return a configuration that disables headers and footers."""
        return cls(
            top_left="",
            top_center="",
            top_right="",
            bottom_left="",
            bottom_center="",
            bottom_right="",
        )


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_TOKEN_RE = re.compile(r"(\{titre\}|\{title\}|\{date\}|\{page\}|\{total\})")


def _today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def _token_template_to_html(template: str) -> str:
    """Translate user tokens into a Chromium header/footer fragment.

    Chromium fills page, total-page, and title spans. The date is inserted by
    the application so its format does not depend on the browser locale.
    """
    if not template:
        return ""
    template = re.sub(r"\s+", " ", template).strip()
    parts = _TOKEN_RE.split(template)
    out = []
    for part in parts:
        if part in ("{titre}", "{title}"):
            out.append('<span class="title"></span>')
        elif part == "{date}":
            out.append(_html_escape(_today_str()))
        elif part == "{page}":
            out.append('<span class="pageNumber"></span>')
        elif part == "{total}":
            out.append('<span class="totalPages"></span>')
        elif part:
            out.append(_html_escape(part))
    return "".join(out)


_TEMPLATE_CONTAINER_STYLE = (
    "font-size:8px; color:#59636e; width:100%; "
    "padding:0 18mm; margin:0; box-sizing:border-box; "
    "font-family: Helvetica, Arial, sans-serif; "
    "display:flex; justify-content:space-between; align-items:center;"
)


def _build_template(left: str, center: str, right: str) -> str:
    return (
        f'<div style="{_TEMPLATE_CONTAINER_STYLE}">'
        f"<span>{_token_template_to_html(left)}</span>"
        f"<span>{_token_template_to_html(center)}</span>"
        f"<span>{_token_template_to_html(right)}</span>"
        f"</div>"
    )


def build_header_template(cfg: HeaderFooterConfig) -> str:
    """Build the Chromium header template for a configuration."""
    return _build_template(cfg.top_left, cfg.top_center, cfg.top_right)


def build_footer_template(cfg: HeaderFooterConfig) -> str:
    """Build the Chromium footer template for a configuration."""
    return _build_template(cfg.bottom_left, cfg.bottom_center, cfg.bottom_right)


def build_full_html(body_html: str, title: str, css_text: str) -> str:
    """Wrap rendered Markdown and CSS in a complete HTML document."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{_html_escape(title)}</title>
<style>{css_text}</style>
</head>
<body>
<article class="markdown-body">
{body_html}
</article>
</body>
</html>
"""


MARGIN_NO_HEADER_FOOTER = {
    "top": "18mm",
    "bottom": "18mm",
    "left": "16mm",
    "right": "16mm",
}
MARGIN_WITH_HEADER_FOOTER = {
    "top": "22mm",
    "bottom": "20mm",
    "left": "16mm",
    "right": "16mm",
}


class ConversionError(Exception):
    """Conversion failure with an actionable message safe for front ends."""


def _read_css(css_path: Optional[_PathInput]) -> str:
    path = Path(css_path) if css_path else DEFAULT_CSS_PATH
    if not path.exists():
        raise ConversionError(f"CSS file not found: {path}")
    return path.read_text(encoding="utf-8")


def _render_pdf(
    full_html: str,
    output_path: Path,
    header_footer: HeaderFooterConfig,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ConversionError(
            "The 'playwright' package is not installed. Run: pip install playwright"
        ) from exc

    display_hf = not header_footer.is_empty()
    margin = MARGIN_WITH_HEADER_FOOTER if display_hf else MARGIN_NO_HEADER_FOOTER

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:
            # Browser backends expose several exception types; normalize this
            # user-facing boundary while preserving the original cause.
            raise ConversionError(
                "Could not launch the headless browser. Run "
                "'python -m playwright install chromium' once, then retry."
            ) from exc
        try:
            page = browser.new_page()
            page.set_content(full_html, wait_until="load")
            page.pdf(
                path=str(output_path),
                format="A4",
                margin=margin,
                display_header_footer=display_hf,
                header_template=(
                    build_header_template(header_footer)
                    if display_hf
                    else "<div></div>"
                ),
                footer_template=(
                    build_footer_template(header_footer)
                    if display_hf
                    else "<div></div>"
                ),
                print_background=True,
            )
        finally:
            browser.close()


def convert_markdown_text_to_pdf(
    markdown_text: str,
    output_path: _PathInput,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
) -> Path:
    """Convert Markdown text to a PDF and return its output path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    css_text = _read_css(css_path)
    body_html = markdown_to_html(markdown_text)
    title = extract_title(body_html)
    full_html = build_full_html(body_html, title, css_text)

    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    _render_pdf(full_html, output_path, hf)
    return output_path


def convert_markdown_to_pdf(
    input_path: _PathInput,
    output_path: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
) -> Path:
    """Convert one Markdown file, defaulting to a sibling `.pdf` output."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise ConversionError(f"Input file not found: {input_path}")

    markdown_text = input_path.read_text(encoding="utf-8")
    resolved_output = Path(output_path) if output_path else input_path.with_suffix(".pdf")
    return convert_markdown_text_to_pdf(
        markdown_text, resolved_output, css_path=css_path, header_footer=header_footer
    )


def convert_batch(
    input_paths: Sequence[_PathInput],
    output_dir: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
) -> list[dict[str, Optional[str]]]:
    """Convert every input independently and return one result per input."""
    results = []
    for raw_path in input_paths:
        input_path = Path(raw_path)
        target = (
            Path(output_dir) / (input_path.stem + ".pdf")
            if output_dir
            else input_path.with_suffix(".pdf")
        )
        try:
            result_path = convert_markdown_to_pdf(
                input_path, target, css_path=css_path, header_footer=header_footer
            )
            results.append(
                {
                    "input": str(input_path),
                    "output": str(result_path),
                    "status": "ok",
                    "error": None,
                }
            )
        except Exception as exc:
            # A failed item must not abort the remaining batch.
            results.append(
                {
                    "input": str(input_path),
                    "output": None,
                    "status": "error",
                    "error": str(exc),
                }
            )
    return results


def render_preview_png(
    markdown_text: str,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    dpi: int = 110,
) -> bytes:
    """Render the first PDF page as PNG bytes for the desktop preview."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ConversionError(
            "The 'pypdfium2' package is not installed. Run: pip install pypdfium2"
        ) from exc

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "preview.pdf"
        convert_markdown_text_to_pdf(
            markdown_text, pdf_path, css_path=css_path, header_footer=header_footer
        )
        pdf = pdfium.PdfDocument(str(pdf_path))
        try:
            page = pdf[0]
            bitmap = page.render(scale=dpi / 72)
            pil_image = bitmap.to_pil()
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            return buffer.getvalue()
        finally:
            pdf.close()
