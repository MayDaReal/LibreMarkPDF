"""Deterministic Markdown document preparation for the private engine."""

from __future__ import annotations

import hashlib
import html as html_lib
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Union

import markdown as md_lib

from .contracts import (
    ConversionError,
    HeaderFooterConfig,
    MARKDOWN_EXTENSIONS,
    MAX_MARKDOWN_BYTES,
    RenderDocument,
    RenderProfile,
)

_PathInput = Union[str, os.PathLike]

_default_css_path = None  # type: Optional[Path]
_font_face_css = None  # type: Optional[Callable[[], str]]
_preview_template_font_css = None  # type: Optional[Callable[[str], str]]
_substitute_emoji_icons = None  # type: Optional[Callable[[str], str]]
_embed_local_resources = None  # type: Optional[Callable[[str, Path], str]]
_css_has_forbidden_resources = None  # type: Optional[Callable[[str], bool]]
_resolve_theme_css = None  # type: Optional[Callable]


def configure_document_dependencies(
    default_css_path: Path,
    font_face_css: Callable[[], str],
    preview_template_font_css: Callable[[str], str],
    substitute_emoji_icons: Callable[[str], str],
    embed_local_resources: Callable[[str, Path], str],
    css_has_forbidden_resources: Callable[[str], bool],
    resolve_theme_css: Callable,
) -> None:
    """Bind resource and theme services without importing the public façade."""
    global _default_css_path, _font_face_css, _preview_template_font_css
    global _substitute_emoji_icons, _embed_local_resources
    global _css_has_forbidden_resources, _resolve_theme_css
    _default_css_path = default_css_path
    _font_face_css = font_face_css
    _preview_template_font_css = preview_template_font_css
    _substitute_emoji_icons = substitute_emoji_icons
    _embed_local_resources = embed_local_resources
    _css_has_forbidden_resources = css_has_forbidden_resources
    _resolve_theme_css = resolve_theme_css


def _configured() -> None:
    if any(value is None for value in (
        _default_css_path, _font_face_css, _preview_template_font_css,
        _substitute_emoji_icons, _embed_local_resources,
        _css_has_forbidden_resources, _resolve_theme_css,
    )):
        raise RuntimeError("document dependencies are not configured")


def markdown_to_html(markdown_text: str, trusted_html: bool = False) -> str:
    """Convert Markdown text to the HTML fragment used by the renderer."""
    _configured()
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
    return _substitute_emoji_icons(rendered)


def extract_title(html: str, default: str = "Document") -> str:
    """Return plain text from the first level-one heading."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if not m:
        return default
    text = html_lib.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or default


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_TOKEN_RE = re.compile(r"(\{titre\}|\{title\}|\{date\}|\{page\}|\{total\})")


def _today_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def resolve_render_date(render_date: Optional[str] = None) -> str:
    """Resolve and validate one calendar date for an entire conversion job."""
    if render_date is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", render_date):
            raise ConversionError("INVALID_DATE: use YYYY-MM-DD")
        try:
            date.fromisoformat(render_date)
        except ValueError as exc:
            raise ConversionError("INVALID_DATE: use YYYY-MM-DD") from exc
        return render_date
    return _today_str()


def _token_template_to_html(template: str, render_date: Optional[str] = None) -> str:
    """Translate user tokens into a Chromium header/footer fragment."""
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
    _configured()
    return "<style>%s</style>%s" % (
        _font_face_css(), _build_template(cfg.top_left, cfg.top_center, cfg.top_right, render_date)
    )


def build_footer_template(cfg: HeaderFooterConfig, render_date: Optional[str] = None) -> str:
    """Build the Chromium footer template for a configuration."""
    _configured()
    return "<style>%s</style>%s" % (
        _font_face_css(), _build_template(cfg.bottom_left, cfg.bottom_center, cfg.bottom_right, render_date)
    )


def _build_preview_template(
    left: str, center: str, right: str, render_date: Optional[str], font_text: str,
) -> str:
    """Build a visually equivalent template without unrelated font payloads."""
    _configured()
    if not any((left, center, right)):
        return "<div></div>"
    return "<style>%s</style>%s" % (
        _preview_template_font_css(font_text),
        _build_template(left, center, right, render_date),
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


def _read_css(css_path: Optional[_PathInput]) -> str:
    _configured()
    path = Path(css_path) if css_path else _default_css_path
    if not path.exists():
        raise ConversionError(f"CSS_NOT_FOUND: CSS file not found: {path}")
    try:
        css = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConversionError("INVALID_CSS: CSS must be UTF-8") from exc
    if "\x00" in css:
        raise ConversionError("INVALID_CSS: CSS contains a null byte")
    if _css_has_forbidden_resources(css):
        raise ConversionError("FORBIDDEN_CSS_URL: CSS resources are not allowed")
    return _font_face_css() + "\n" + css


def _resolve_style_profile(
    css_path: Optional[_PathInput], render_date: Optional[str], trusted_html: bool,
    header_footer: HeaderFooterConfig, theme: Optional[str], theme_root: Optional[_PathInput],
) -> tuple:
    if css_path is not None and theme is not None:
        raise ConversionError("INVALID_OPTIONS: --css and --theme cannot be used together")
    theme_info = None
    if theme is not None:
        theme_info = _resolve_theme_css(theme, theme_root)
        css_path = theme_info.css_path
    css_text = _read_css(css_path)
    if theme_info is not None and theme_info.identifier != "default":
        profile_theme = theme_info.reference
    elif css_path is not None and theme_info is None:
        profile_theme = "custom-css"
    else:
        profile_theme = "bundled-default"
    profile = RenderProfile(
        resolve_render_date(render_date),
        raw_html_policy="trusted-static" if trusted_html else "safe",
        theme_name=profile_theme,
        theme_hash=hashlib.sha256(css_text.encode("utf-8")).hexdigest(),
        header_footer=(
            header_footer.top_left, header_footer.top_center, header_footer.top_right,
            header_footer.bottom_left, header_footer.bottom_center, header_footer.bottom_right,
        ),
    )
    return css_text, profile


def render_profile_for_options(
    css_path: Optional[_PathInput] = None, header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None, trusted_html: bool = False,
    theme: Optional[str] = None, theme_root: Optional[_PathInput] = None,
) -> RenderProfile:
    """Resolve the exact profile used by conversion without launching Chromium."""
    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    _css_text, profile = _resolve_style_profile(
        css_path, render_date, trusted_html, hf, theme, theme_root
    )
    return profile


def _validate_markdown_text(markdown_text: str) -> None:
    """Reject non-UTF-8-compatible and unbounded in-memory input."""
    try:
        byte_count = len(markdown_text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ConversionError("INVALID_UTF8: Markdown input must be UTF-8") from exc
    if byte_count > MAX_MARKDOWN_BYTES:
        raise ConversionError("INPUT_TOO_LARGE: Markdown exceeds configured size limit")


def prepare_render_document(
    markdown_text: str, css_path: Optional[_PathInput] = None,
    render_date: Optional[str] = None, trusted_html: bool = False,
    resource_root: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None, theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None, _include_profile_fingerprint: bool = True,
) -> RenderDocument:
    """Resolve deterministic HTML and profile inputs without launching Chromium."""
    _configured()
    _validate_markdown_text(markdown_text)
    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    css_text, profile = _resolve_style_profile(
        css_path, render_date, trusted_html, hf, theme, theme_root
    )
    resolved_date = profile.render_date
    body_html = markdown_to_html(markdown_text, trusted_html=trusted_html)
    body_html = _embed_local_resources(body_html, resource_root or Path.cwd())
    title = extract_title(body_html)
    return RenderDocument(
        build_full_html(
            body_html, title, css_text,
            profile.fingerprint if _include_profile_fingerprint else None,
        ),
        profile, resolved_date, title,
    )
