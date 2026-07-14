"""Shared Markdown-to-PDF conversion engine."""

from __future__ import annotations

import base64
import hashlib
import html as html_lib
import io
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, Sequence, Union
from urllib.parse import unquote, urlparse

import markdown as md_lib

_PathInput = Union[str, os.PathLike]

PROFILE_SCHEMA = 1
MARKDOWN_EXTENSIONS = ("extra", "sane_lists")
MAX_RESOURCE_BYTES = 5 * 1024 * 1024
MAX_RESOURCE_COUNT = 32
MAX_TOTAL_RESOURCE_BYTES = 20 * 1024 * 1024
RENDER_TIMEOUT_MS = 30_000
_ALLOWED_RESOURCE_MIME = {
    ".gif": "image/gif", ".jpeg": "image/jpeg", ".jpg": "image/jpeg",
    ".png": "image/png", ".svg": "image/svg+xml",
}


@dataclass(frozen=True)
class RenderProfile:
    """Versioned, canonical rendering inputs used by the shared core."""

    render_date: str
    raw_html_policy: str = "safe"
    network_policy: str = "deny-all"
    profile_version: str = "default@1"
    theme_name: str = "bundled-default"
    theme_hash: Optional[str] = None
    header_footer: tuple = ()

    def canonical_json(self) -> str:
        payload = {
            "chrome_revision": "1223",
            "color_scheme": "light",
            "locale": "en-US",
            "markdown_extensions": list(MARKDOWN_EXTENSIONS),
            "markdown_version": md_lib.__version__,
            "margins": {"header_footer": MARGIN_WITH_HEADER_FOOTER,
                        "none": MARGIN_NO_HEADER_FOOTER},
            "network_policy": self.network_policy,
            "page": {"background": True, "format": "A4", "media": "print", "scale": 1},
            "playwright_version": "1.60.0",
            "profile_schema": PROFILE_SCHEMA,
            "profile_version": self.profile_version,
            "raw_html_policy": self.raw_html_policy,
            "renderer_flags": ["--disable-font-subpixel-positioning"],
            "header_footer": list(self.header_footer),
            "resource_hashes": _renderer_resource_hashes(self.theme_hash),
            "resource_limits": {
                "count": MAX_RESOURCE_COUNT,
                "bytes_per_resource": MAX_RESOURCE_BYTES,
                "total_bytes": MAX_TOTAL_RESOURCE_BYTES,
            },
            "render_date": self.render_date,
            "timeouts_ms": {"render": RENDER_TIMEOUT_MS},
            "theme": {"name": self.theme_name, "version": self.theme_hash},
            "timezone": "UTC",
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def resource_path(relative: str) -> Path:
    """Resolve a frozen runtime resource from source, wheel, or PyInstaller."""
    frozen_base = getattr(sys, "_MEIPASS", None)
    if frozen_base:
        return Path(frozen_base) / relative

    source_base = Path(__file__).resolve().parent.parent
    source_candidate = source_base / relative
    if source_candidate.exists():
        return source_candidate

    # setuptools installs declared data_files under the interpreter prefix,
    # outside site-packages. This keeps root-level runtime resources compatible
    # with the existing frozen-artifact layout.
    wheel_candidate = Path(sys.prefix) / "libremark_pdf" / relative
    if wheel_candidate.exists():
        return wheel_candidate
    return source_candidate


DEFAULT_CSS_PATH = resource_path("style.css")
ICONS_DIR = resource_path("icons")
FONTS_DIR = resource_path("fonts")
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
_font_css_cache: Optional[str] = None

_FONT_FILES = (
    ("NotoSans-Regular.ttf", "G1 Noto Sans", "400"),
    ("NotoSans-SemiBold.ttf", "G1 Noto Sans", "600"),
    ("NotoSansMono-Regular.ttf", "G1 Noto Sans Mono", "400"),
    ("NotoSansArabic-Regular.ttf", "G1 Noto Sans Arabic", "400"),
    ("NotoSansCJKsc-Regular.otf", "G1 Noto Sans CJK SC", "400"),
    ("NotoSansSymbols2-Regular.ttf", "G1 Noto Sans Symbols 2", "400"),
    ("NotoEmoji.ttf", "G1 Noto Emoji", "400"),
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _renderer_resource_hashes(theme_hash: Optional[str] = None) -> dict:
    """Return stable hashes of every local resource that changes rendering."""
    icon_hashes = {}
    if ICONS_DIR.is_dir():
        for path in sorted(ICONS_DIR.glob("*.png")):
            icon_hashes[path.name] = _sha256_file(path)
    font_hashes = {}
    for filename, _family, _weight in _FONT_FILES:
        path = FONTS_DIR / filename
        font_hashes[filename] = _sha256_file(path) if path.is_file() else "missing"
    return {
        "css": theme_hash or _sha256_file(DEFAULT_CSS_PATH),
        "fonts": font_hashes,
        "icons": icon_hashes,
    }


def _icon_data_uri(filename: str) -> str:
    if filename not in _icon_cache:
        path = ICONS_DIR / filename
        data = path.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        _icon_cache[filename] = f"data:image/png;base64,{encoded}"
    return _icon_cache[filename]


def _font_face_css() -> str:
    """Embed the seven exact static G1 font files in renderer input."""
    global _font_css_cache
    if _font_css_cache is None:
        rules = []
        for filename, family, weight in _FONT_FILES:
            path = FONTS_DIR / filename
            if not path.is_file():
                raise ConversionError("FONT_NOT_FOUND: bundled font is missing: " + filename)
            mime = "font/otf" if path.suffix == ".otf" else "font/ttf"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            rules.append(
                "@font-face{font-family:'%s';src:url(data:%s;base64,%s);"
                "font-style:normal;font-weight:%s;font-display:block;}"
                % (family, mime, encoded, weight)
            )
        _font_css_cache = "\n".join(rules)
    return _font_css_cache


def substitute_emoji_icons(html: str) -> str:
    """Replace supported status emoji with embedded PNG images."""
    # Markdown examples in code/pre blocks must remain literal. Attributes and
    # alternative text are part of tags, so splitting also keeps them intact.
    for ch, filename in _EMOJI_FILES.items():
        if ch in html:
            uri = _icon_data_uri(filename)
            parts = re.split(r"(<[^>]+>)", html)
            protected_depth = 0
            out = []
            for part in parts:
                if part.startswith("<"):
                    if re.match(r"<\s*/\s*(code|pre)\b", part, re.I):
                        protected_depth = max(0, protected_depth - 1)
                    out.append(part)
                    if re.match(r"<\s*(code|pre)\b[^>]*>", part, re.I):
                        protected_depth += 1
                elif protected_depth:
                    out.append(part)
                else:
                    out.append(part.replace(ch, f'<img class="emoji" src="{uri}" alt="">'))
            html = "".join(out)
    return html


def markdown_to_html(markdown_text: str, trusted_html: bool = False) -> str:
    """Convert Markdown text to the HTML fragment used by the renderer."""
    if not trusted_html:
        markdown_text = re.sub(r"<[^>]*>", lambda m: html_lib.escape(m.group(0)), markdown_text)
    rendered = md_lib.markdown(markdown_text, extensions=list(MARKDOWN_EXTENSIONS))
    if trusted_html and re.search(
        r"(?is)<\s*(script|iframe|frame|object|embed|link|base)\b|\bon\w+\s*=",
        rendered,
    ):
        raise ConversionError("FORBIDDEN_HTML: active HTML is not allowed")
    if trusted_html and re.search(
        r"(?is)<meta\b[^>]*http-equiv\s*=\s*['\"]?refresh|"
        r"\b(?:srcset|poster|background|data|formaction)\s*=|"
        r"\bsrc\s*=\s*['\"]?\s*(?:https?:|//|file:)",
        rendered,
    ):
        raise ConversionError("FORBIDDEN_HTML_URL: network and file URLs are not allowed")
    if trusted_html:
        for style in re.findall(r"(?is)<style\b[^>]*>(.*?)</style\s*>", rendered):
            if _css_has_forbidden_resources(style):
                raise ConversionError("FORBIDDEN_CSS_URL: CSS resources are not allowed")
        for style in re.findall(r"(?is)\bstyle\s*=\s*(['\"])(.*?)\1", rendered):
            if _css_has_forbidden_resources(style[1]):
                raise ConversionError("FORBIDDEN_CSS_URL: CSS resources are not allowed")
    return substitute_emoji_icons(rendered)


def _resource_error(message: str) -> ConversionError:
    return ConversionError("FORBIDDEN_RESOURCE: " + message)


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def _validate_image_bytes(data: bytes, suffix: str) -> None:
    """Validate bytes against the narrow image types accepted by safe mode."""
    if not data or len(data) > MAX_RESOURCE_BYTES:
        raise _resource_error("image is empty or exceeds configured size limit")
    if suffix == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise _resource_error("PNG signature does not match its extension")
    if suffix in (".jpg", ".jpeg") and not data.startswith(b"\xff\xd8\xff"):
        raise _resource_error("JPEG signature does not match its extension")
    if suffix == ".gif" and not data.startswith((b"GIF87a", b"GIF89a")):
        raise _resource_error("GIF signature does not match its extension")
    if suffix == ".svg":
        if not re.search(rb"(?is)<\s*svg\b", data):
            raise _resource_error("SVG signature does not match its extension")
        if re.search(
            rb"(?is)<\s*(script|iframe|object|embed|foreignObject)\b|\bon\w+\s*=|"
            rb"(?:https?:|//|file:)|@import|url\s*\(",
            data,
        ):
            raise _resource_error("SVG contains active or network-capable content")


def _validated_image_data_uri(value: str, resource_root: Path) -> tuple[str, int]:
    """Validate an image and return a renderer-safe data URI."""
    if value.startswith("data:"):
        match = re.match(r"^data:([^;,]+);base64,([A-Za-z0-9+/=]+)$", value, re.I)
        if not match or match.group(1).lower() not in _ALLOWED_RESOURCE_MIME.values():
            raise _resource_error("unsupported or malformed data URI")
        try:
            data = base64.b64decode(match.group(2), validate=True)
        except ValueError as exc:
            raise _resource_error("malformed data URI") from exc
        suffix = next(
            suffix for suffix, mime in _ALLOWED_RESOURCE_MIME.items()
            if mime == match.group(1).lower()
        )
        _validate_image_bytes(data, suffix)
        return value, len(data)

    parsed = urlparse(value)
    if parsed.scheme or value.startswith("//") or parsed.query or parsed.fragment:
        raise _resource_error("only relative local image paths are allowed")
    candidate = (resource_root / unquote(value)).resolve()
    if not _is_within(candidate, resource_root) or not candidate.is_file():
        raise _resource_error("image is missing or escapes the source directory")
    suffix = candidate.suffix.lower()
    mime = _ALLOWED_RESOURCE_MIME.get(suffix)
    if mime is None:
        raise _resource_error("unsupported image type")
    data = candidate.read_bytes()
    _validate_image_bytes(data, suffix)
    return "data:{0};base64,{1}".format(mime, base64.b64encode(data).decode("ascii")), len(data)


def embed_local_resources(html: str, resource_root: _PathInput) -> str:
    """Embed approved local image references before Chromium receives HTML."""
    root = Path(resource_root).resolve()
    if not root.is_dir():
        raise _resource_error("source directory is unavailable")
    count = 0
    total_bytes = 0

    def replace(match: re.Match) -> str:
        nonlocal count, total_bytes
        count += 1
        if count > MAX_RESOURCE_COUNT:
            raise _resource_error("image count exceeds configured limit")
        quote, value = match.group(1), html_lib.unescape(match.group(2))
        uri, resource_bytes = _validated_image_data_uri(value, root)
        total_bytes += resource_bytes
        if total_bytes > MAX_TOTAL_RESOURCE_BYTES:
            raise _resource_error("total image size exceeds configured limit")
        return "src={0}{1}{0}".format(quote, uri)

    return re.sub(r"\bsrc\s*=\s*(['\"])(.*?)\1", replace, html, flags=re.I | re.S)


def extract_title(html: str, default: str = "Document") -> str:
    """Return plain text from the first level-one heading."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if not m:
        return default
    text = html_lib.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
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
    return datetime.now(timezone.utc).date().isoformat()


def _token_template_to_html(template: str, render_date: Optional[str] = None) -> str:
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
            out.append(_html_escape(render_date or _today_str()))
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
    "font-family:'G1 Noto Sans', 'G1 Noto Sans Arabic', 'G1 Noto Sans CJK SC', sans-serif; "
    "display:grid; grid-template-columns:1fr auto 1fr; align-items:center;"
)


def _build_template(left: str, center: str, right: str, render_date: Optional[str] = None) -> str:
    return (
        f'<div style="{_TEMPLATE_CONTAINER_STYLE}">'
        f'<span style="text-align:left">{_token_template_to_html(left, render_date)}</span>'
        f'<span style="text-align:center">{_token_template_to_html(center, render_date)}</span>'
        f'<span style="text-align:right">{_token_template_to_html(right, render_date)}</span>'
        f"</div>"
    )


def build_header_template(cfg: HeaderFooterConfig, render_date: Optional[str] = None) -> str:
    """Build the Chromium header template for a configuration."""
    return "<style>%s</style>%s" % (
        _font_face_css(), _build_template(cfg.top_left, cfg.top_center, cfg.top_right, render_date)
    )


def build_footer_template(cfg: HeaderFooterConfig, render_date: Optional[str] = None) -> str:
    """Build the Chromium footer template for a configuration."""
    return "<style>%s</style>%s" % (
        _font_face_css(), _build_template(cfg.bottom_left, cfg.bottom_center, cfg.bottom_right, render_date)
    )


def build_full_html(
    body_html: str, title: str, css_text: str, profile_fingerprint: Optional[str] = None
) -> str:
    """Wrap rendered Markdown and CSS in a complete HTML document."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="libremark-render-profile" content="{_html_escape(profile_fingerprint or '')}">
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


@dataclass(frozen=True)
class RenderDocument:
    """Fully resolved deterministic document passed to the locked renderer."""

    full_html: str
    profile: RenderProfile
    render_date: str


def error_code(exc: BaseException) -> str:
    """Extract the stable leading code exposed by core diagnostics."""
    match = re.match(r"^([A-Z][A-Z0-9_]+):", str(exc))
    return match.group(1) if match else "INTERNAL_ERROR"


def _css_has_forbidden_resources(css: str) -> bool:
    """CSS URLs would bypass the image embedding boundary, so reject them."""
    return bool(re.search(r"(?is)@import\b|url\s*\(", css))


def _read_css(css_path: Optional[_PathInput]) -> str:
    path = Path(css_path) if css_path else DEFAULT_CSS_PATH
    if not path.exists():
        raise ConversionError(f"CSS_NOT_FOUND: CSS file not found: {path}")
    css = path.read_text(encoding="utf-8")
    if _css_has_forbidden_resources(css):
        raise ConversionError("FORBIDDEN_CSS_URL: CSS resources are not allowed")
    return _font_face_css() + "\n" + css


class _BrowserRenderer:
    """One locked browser process with an isolated context per document."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None

    def __enter__(self) -> "_BrowserRenderer":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ConversionError(
                "The 'playwright' package is not installed. Run: pip install playwright"
            ) from exc
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(
                args=["--disable-font-subpixel-positioning"]
            )
        except Exception as exc:
            self._playwright.stop()
            self._playwright = None
            raise ConversionError(
                "BROWSER_UNAVAILABLE: could not launch the headless browser. Run "
                "'python -m playwright install chromium' once, then retry."
            ) from exc
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
        finally:
            if self._playwright is not None:
                self._playwright.stop()
            self._browser = None
            self._playwright = None

    def render(
        self,
        full_html: str,
        output_path: Path,
        header_footer: HeaderFooterConfig,
        render_date: Optional[str],
    ) -> None:
        if self._browser is None:
            raise ConversionError("BROWSER_UNAVAILABLE: browser session is not active")
        display_hf = not header_footer.is_empty()
        margin = MARGIN_WITH_HEADER_FOOTER if display_hf else MARGIN_NO_HEADER_FOOTER
        context = None
        try:
            context = self._browser.new_context(
                locale="en-US", timezone_id="UTC", color_scheme="light",
                java_script_enabled=False, service_workers="block",
            )
            page = context.new_page()
            observed_requests = []

            def abort_request(route):
                # Data URIs are validated and embedded by the core; every other
                # request is retained as evidence then denied.
                if route.request.url.startswith("data:"):
                    route.continue_()
                    return
                observed_requests.append(route.request.url)
                route.abort()

            page.route("**/*", abort_request)
            page.set_content(full_html, wait_until="load", timeout=RENDER_TIMEOUT_MS)
            page.emulate_media(media="print")
            page.pdf(
                path=str(output_path),
                format="A4",
                margin=margin,
                display_header_footer=display_hf,
                header_template=(
                    build_header_template(header_footer, render_date)
                    if display_hf else "<div></div>"
                ),
                footer_template=(
                    build_footer_template(header_footer, render_date)
                    if display_hf else "<div></div>"
                ),
                print_background=True,
                tagged=True,
                outline=True,
            )
            if observed_requests:
                raise ConversionError("NETWORK_BLOCKED: renderer attempted a network request")
        except ConversionError:
            raise
        except Exception as exc:
            raise ConversionError("RENDER_FAILED: {0}".format(exc)) from exc
        finally:
            if context is not None:
                context.close()


def _render_pdf(
    full_html: str,
    output_path: Path,
    header_footer: HeaderFooterConfig,
    render_date: Optional[str] = None,
) -> None:
    """Render one document through a short-lived browser session."""
    with _BrowserRenderer() as renderer:
        renderer.render(full_html, output_path, header_footer, render_date)


def _atomic_render_pdf(
    full_html: str,
    output_path: Path,
    header_footer: HeaderFooterConfig,
    render_date: Optional[str],
    renderer: Optional[_BrowserRenderer] = None,
) -> None:
    """Render into a sibling temporary file, then atomically publish it."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", prefix=".libremark-", dir=output_path.parent,
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
        if renderer is None:
            _render_pdf(full_html, temp_path, header_footer, render_date)
        else:
            renderer.render(full_html, temp_path, header_footer, render_date)
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise ConversionError("INVALID_OUTPUT: renderer did not create a PDF")
        os.replace(str(temp_path), str(output_path))
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def prepare_render_document(
    markdown_text: str,
    css_path: Optional[_PathInput] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    resource_root: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
) -> RenderDocument:
    """Resolve deterministic HTML and profile inputs without launching Chromium."""
    if render_date is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", render_date):
            raise ConversionError("INVALID_DATE: use YYYY-MM-DD")
        try:
            date.fromisoformat(render_date)
        except ValueError as exc:
            raise ConversionError("INVALID_DATE: use YYYY-MM-DD") from exc
    resolved_date = render_date or _today_str()
    css_text = _read_css(css_path)
    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    profile = RenderProfile(
        resolved_date,
        raw_html_policy="trusted-static" if trusted_html else "safe",
        theme_name="custom-css" if css_path else "bundled-default",
        theme_hash=hashlib.sha256(css_text.encode("utf-8")).hexdigest(),
        header_footer=(
            hf.top_left, hf.top_center, hf.top_right,
            hf.bottom_left, hf.bottom_center, hf.bottom_right,
        ),
    )
    body_html = markdown_to_html(markdown_text, trusted_html=trusted_html)
    body_html = embed_local_resources(body_html, resource_root or Path.cwd())
    title = extract_title(body_html)
    return RenderDocument(
        build_full_html(body_html, title, css_text, profile.fingerprint),
        profile,
        resolved_date,
    )


def convert_markdown_text_to_pdf(
    markdown_text: str,
    output_path: _PathInput,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
    resource_root: Optional[_PathInput] = None,
    _renderer: Optional[_BrowserRenderer] = None,
) -> Path:
    """Convert Markdown text to a PDF and return its output path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not overwrite:
        raise ConversionError(f"OUTPUT_EXISTS: refusing to overwrite: {output_path}")

    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    document = prepare_render_document(
        markdown_text,
        css_path=css_path,
        render_date=render_date,
        trusted_html=trusted_html,
        resource_root=resource_root,
        header_footer=hf,
    )

    _atomic_render_pdf(
        document.full_html,
        output_path,
        hf,
        document.render_date,
        renderer=_renderer,
    )
    return output_path


def convert_markdown_to_pdf(
    input_path: _PathInput,
    output_path: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
    _renderer: Optional[_BrowserRenderer] = None,
) -> Path:
    """Convert one Markdown file, defaulting to a sibling `.pdf` output."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise ConversionError(f"INPUT_NOT_FOUND: input file not found: {input_path}")

    try:
        markdown_text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConversionError("INVALID_UTF8: Markdown input must be UTF-8") from exc
    resolved_output = Path(output_path) if output_path else input_path.with_suffix(".pdf")
    try:
        same_path = input_path.resolve() == resolved_output.resolve()
    except OSError:
        same_path = input_path.absolute() == resolved_output.absolute()
    if same_path:
        raise ConversionError("INPUT_OUTPUT_COLLISION: input and output paths are identical")
    return convert_markdown_text_to_pdf(
        markdown_text, resolved_output, css_path=css_path, header_footer=header_footer,
        render_date=render_date, trusted_html=trusted_html, overwrite=overwrite,
        resource_root=input_path.resolve().parent, _renderer=_renderer,
    )


def convert_batch(
    input_paths: Sequence[_PathInput],
    output_dir: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
) -> list[dict[str, Optional[str]]]:
    """Convert every input independently and return one result per input."""
    planned = []
    duplicate_targets = set()
    seen_targets = set()
    for raw_path in input_paths:
        input_path = Path(raw_path)
        target = Path(output_dir) / (input_path.stem + ".pdf") if output_dir else input_path.with_suffix(".pdf")
        try:
            key = str(target.resolve())
        except OSError:
            key = str(target.absolute())
        if key in seen_targets:
            duplicate_targets.add(key)
        seen_targets.add(key)
        planned.append((input_path, target, key))

    plan_errors = {}
    for input_path, target, key in planned:
        if key in duplicate_targets:
            plan_errors[key] = "DUPLICATE_OUTPUT: batch contains duplicate destinations"
            continue
        try:
            same_path = input_path.resolve() == target.resolve()
        except OSError:
            same_path = input_path.absolute() == target.absolute()
        if same_path:
            plan_errors[key] = "INPUT_OUTPUT_COLLISION: input and output paths are identical"
        elif target.exists() and not overwrite:
            plan_errors[key] = "OUTPUT_EXISTS: refusing to overwrite: {0}".format(target)

    renderer = None
    renderer_manager = None
    renderer_error = None
    if any(key not in plan_errors for _input_path, _target, key in planned):
        try:
            renderer_manager = _BrowserRenderer()
            renderer = renderer_manager.__enter__()
        except Exception as exc:
            renderer_error = exc

    results = []
    try:
        for input_path, target, key in planned:
            try:
                if key in plan_errors:
                    raise ConversionError(plan_errors[key])
                if renderer_error is not None:
                    raise renderer_error
                result_path = convert_markdown_to_pdf(
                    input_path, target, css_path=css_path, header_footer=header_footer,
                    render_date=render_date, trusted_html=trusted_html, overwrite=overwrite,
                    _renderer=renderer,
                )
                results.append(
                    {
                        "input": str(input_path),
                        "output": str(result_path),
                        "status": "ok",
                        "error": None,
                        "error_code": None,
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
                        "error_code": error_code(exc),
                    }
                )
    finally:
        if renderer_manager is not None and renderer is not None:
            renderer_manager.__exit__(None, None, None)
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
