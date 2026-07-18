"""Shared Markdown-to-PDF conversion engine."""

from __future__ import annotations

import hashlib
import html as html_lib
import io
import os
import re
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union
import markdown as md_lib

from .engine.contracts import (
    BatchPlan,
    CHROMIUM_REVISION,
    CHROMIUM_VERSION,
    ConversionError,
    DEFAULT_PROFILE_VERSION,
    DEFAULT_THEME_ID,
    HeaderFooterConfig,
    MARKDOWN_EXTENSIONS,
    MARGIN_NO_HEADER_FOOTER,
    MARGIN_WITH_HEADER_FOOTER,
    MAX_MARKDOWN_BYTES,
    MAX_RESOURCE_BYTES,
    MAX_RESOURCE_COUNT,
    MAX_TOTAL_RESOURCE_BYTES,
    PLAYWRIGHT_VERSION,
    PROFILE_SCHEMA,
    RENDER_TIMEOUT_MS,
    RenderDocument,
    RenderProfile,
    ThemeInfo,
    configure_resource_hashes as _configure_resource_hashes,
)
from .engine import themes as _themes
from .engine import resources as _resources

_PathInput = Union[str, os.PathLike]


def resource_path(relative: str) -> Path:
    """Resolve a frozen runtime resource from source, wheel, or PyInstaller."""
    return _resources.resource_path(relative, __file__)


DEFAULT_CSS_PATH = resource_path("style.css")
ICONS_DIR = resource_path("icons")
FONTS_DIR = resource_path("fonts")
BROWSERS_DIR = resource_path("browsers")
DEFAULT_THEME_ROOT = Path.home() / ".libremark-pdf" / "themes"

_resources.configure_resource_locations(DEFAULT_CSS_PATH, ICONS_DIR, FONTS_DIR, BROWSERS_DIR)
_resources.prefer_bundled_browser()
renderer_identity = _resources.renderer_identity
_FONT_FILES = _resources._FONT_FILES
_sha256_file = _resources._sha256_file
_renderer_resource_hashes = _resources._renderer_resource_hashes
_icon_data_uri = _resources._icon_data_uri
_font_face_css = _resources._font_face_css
_preview_template_font_css = _resources._preview_template_font_css
substitute_emoji_icons = _resources.substitute_emoji_icons
_is_within = _resources._is_within
_validate_image_bytes = _resources._validate_image_bytes
embed_local_resources = _resources.embed_local_resources
_css_has_forbidden_resources = _resources._css_has_forbidden_resources

_configure_resource_hashes(_renderer_resource_hashes)


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


def _build_preview_template(
    left: str,
    center: str,
    right: str,
    render_date: Optional[str],
    font_text: str,
) -> str:
    """Build a visually equivalent template without unrelated font payloads."""
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


def error_code(exc: BaseException) -> str:
    """Extract the stable leading code exposed by core diagnostics."""
    match = re.match(r"^([A-Z][A-Z0-9_]+):", str(exc))
    return match.group(1) if match else "INTERNAL_ERROR"


_themes.configure_theme_dependencies(
    resource_path,
    DEFAULT_CSS_PATH,
    DEFAULT_THEME_ROOT,
    _sha256_file,
    _is_within,
    _validate_image_bytes,
    _css_has_forbidden_resources,
)
THEME_MANIFEST_SCHEMA = _themes.THEME_MANIFEST_SCHEMA
THEME_MANIFEST_NAME = _themes.THEME_MANIFEST_NAME
_default_theme_info = _themes._default_theme_info
_manifest_relative_path = _themes._manifest_relative_path
_theme_file = _themes._theme_file
_theme_root = _themes._theme_root
_theme_error = _themes._theme_error
validate_theme_package = _themes.validate_theme_package
list_themes = _themes.list_themes
show_theme = _themes.show_theme
install_theme = _themes.install_theme
remove_theme = _themes.remove_theme
resolve_theme_css = _themes.resolve_theme_css


def _read_css(css_path: Optional[_PathInput]) -> str:
    path = Path(css_path) if css_path else DEFAULT_CSS_PATH
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
    css_path: Optional[_PathInput],
    render_date: Optional[str],
    trusted_html: bool,
    header_footer: HeaderFooterConfig,
    theme: Optional[str],
    theme_root: Optional[_PathInput],
) -> tuple:
    if css_path is not None and theme is not None:
        raise ConversionError("INVALID_OPTIONS: --css and --theme cannot be used together")
    theme_info = None
    if theme is not None:
        theme_info = resolve_theme_css(theme, theme_root)
        css_path = theme_info.css_path
    css_text = _read_css(css_path)
    if theme_info is not None and theme_info.identifier != "default":
        profile_theme = theme_info.reference
    elif css_path is not None and theme_info is None:
        profile_theme = "custom-css"
    else:
        # Keep the already approved G2 profile identity byte-for-byte. The
        # public default@1 theme is an exact alias of this internal value.
        profile_theme = "bundled-default"
    profile = RenderProfile(
        resolve_render_date(render_date),
        raw_html_policy="trusted-static" if trusted_html else "safe",
        theme_name=profile_theme,
        theme_hash=hashlib.sha256(css_text.encode("utf-8")).hexdigest(),
        header_footer=(
            header_footer.top_left,
            header_footer.top_center,
            header_footer.top_right,
            header_footer.bottom_left,
            header_footer.bottom_center,
            header_footer.bottom_right,
        ),
    )
    return css_text, profile


def render_profile_for_options(
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
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


class _BrowserRenderer:
    """One locked browser process with an isolated context per document."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self.last_observed_requests = []

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
                args=["--disable-font-subpixel-positioning"],
                timeout=RENDER_TIMEOUT_MS,
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

    def _open_page(self):
        """Create one isolated, network-denied page owned by this renderer."""
        if self._browser is None:
            raise ConversionError("BROWSER_UNAVAILABLE: browser session is not active")
        context = self._browser.new_context(
            locale="en-US", timezone_id="UTC", color_scheme="light",
            java_script_enabled=False, service_workers="block",
        )
        page = context.new_page()

        def abort_request(route):
            # Data URIs are validated and embedded by the core; every other
            # request is retained as evidence then denied.
            if route.request.url.startswith("data:"):
                route.continue_()
                return
            self.last_observed_requests.append(route.request.url)
            route.abort()

        page.route("**/*", abort_request)
        return context, page

    def _render_loaded_page(
        self,
        page,
        output_path: Path,
        header_footer: HeaderFooterConfig,
        render_date: Optional[str],
        preview_font_text: Optional[str] = None,
    ) -> None:
        """Print an already loaded page through the locked PDF settings."""
        display_hf = not header_footer.is_empty()
        margin = MARGIN_WITH_HEADER_FOOTER if display_hf else MARGIN_NO_HEADER_FOOTER
        if preview_font_text is None:
            header_template = (
                build_header_template(header_footer, render_date)
                if display_hf else "<div></div>"
            )
            footer_template = (
                build_footer_template(header_footer, render_date)
                if display_hf else "<div></div>"
            )
        else:
            header_template = _build_preview_template(
                header_footer.top_left,
                header_footer.top_center,
                header_footer.top_right,
                render_date,
                preview_font_text,
            )
            footer_template = _build_preview_template(
                header_footer.bottom_left,
                header_footer.bottom_center,
                header_footer.bottom_right,
                render_date,
                preview_font_text,
            )
        page.emulate_media(media="print")
        page.pdf(
            path=str(output_path),
            format="A4",
            margin=margin,
            display_header_footer=display_hf,
            header_template=header_template,
            footer_template=footer_template,
            print_background=True,
            tagged=True,
            outline=True,
        )
        if self.last_observed_requests:
            raise ConversionError("NETWORK_BLOCKED: renderer attempted a network request")

    def render(
        self,
        full_html: str,
        output_path: Path,
        header_footer: HeaderFooterConfig,
        render_date: Optional[str],
    ) -> None:
        if self._browser is None:
            raise ConversionError("BROWSER_UNAVAILABLE: browser session is not active")
        context = None
        try:
            self.last_observed_requests = []
            context, page = self._open_page()
            page.set_content(full_html, wait_until="load", timeout=RENDER_TIMEOUT_MS)
            self._render_loaded_page(
                page, output_path, header_footer, render_date
            )
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
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".pdf", prefix=".libremark-", dir=output_path.parent,
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
        except OSError as exc:
            raise ConversionError(
                "OUTPUT_UNAVAILABLE: cannot create temporary output in: {0}".format(output_path.parent)
            ) from exc
        if renderer is None:
            _render_pdf(full_html, temp_path, header_footer, render_date)
        else:
            renderer.render(full_html, temp_path, header_footer, render_date)
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise ConversionError("INVALID_OUTPUT: renderer did not create a PDF")
        try:
            os.replace(str(temp_path), str(output_path))
        except OSError as exc:
            raise ConversionError(
                "OUTPUT_REPLACE_FAILED: cannot publish output: {0}".format(output_path)
            ) from exc
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
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    _include_profile_fingerprint: bool = True,
) -> RenderDocument:
    """Resolve deterministic HTML and profile inputs without launching Chromium."""
    _validate_markdown_text(markdown_text)
    hf = header_footer if header_footer is not None else HeaderFooterConfig()
    css_text, profile = _resolve_style_profile(
        css_path, render_date, trusted_html, hf, theme, theme_root
    )
    resolved_date = profile.render_date
    body_html = markdown_to_html(markdown_text, trusted_html=trusted_html)
    body_html = embed_local_resources(body_html, resource_root or Path.cwd())
    title = extract_title(body_html)
    return RenderDocument(
        build_full_html(
            body_html,
            title,
            css_text,
            profile.fingerprint if _include_profile_fingerprint else None,
        ),
        profile,
        resolved_date,
        title,
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
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    _renderer: Optional[_BrowserRenderer] = None,
) -> Path:
    """Convert Markdown text to a PDF and return its output path."""
    output_path = Path(output_path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConversionError(
            "OUTPUT_UNAVAILABLE: cannot create destination directory: {0}".format(output_path.parent)
        ) from exc
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
        theme=theme,
        theme_root=theme_root,
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
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    _renderer: Optional[_BrowserRenderer] = None,
) -> Path:
    """Convert one Markdown file, defaulting to a sibling `.pdf` output."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise ConversionError(f"INPUT_NOT_FOUND: input file not found: {input_path}")

    try:
        if input_path.stat().st_size > MAX_MARKDOWN_BYTES:
            raise ConversionError("INPUT_TOO_LARGE: Markdown exceeds configured size limit")
    except OSError as exc:
        raise ConversionError(f"INPUT_UNREADABLE: cannot inspect input: {input_path}") from exc

    try:
        markdown_text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConversionError("INVALID_UTF8: Markdown input must be UTF-8") from exc
    except OSError as exc:
        raise ConversionError(f"INPUT_UNREADABLE: cannot read input: {input_path}") from exc
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
        resource_root=input_path.resolve().parent, theme=theme,
        theme_root=theme_root, _renderer=_renderer,
    )


def plan_batch_outputs(
    input_paths: Sequence[_PathInput],
    output_dir: Optional[_PathInput] = None,
    overwrite: bool = False,
) -> list:
    """Preflight batch paths without launching a browser or writing output."""
    provisional = []
    duplicate_targets = set()
    seen_targets = set()
    for raw_path in input_paths:
        input_path = Path(raw_path)
        target = (
            Path(output_dir) / (input_path.stem + ".pdf")
            if output_dir else input_path.with_suffix(".pdf")
        )
        try:
            key = str(target.resolve())
        except OSError:
            key = str(target.absolute())
        if key in seen_targets:
            duplicate_targets.add(key)
        seen_targets.add(key)
        provisional.append((input_path, target, key))

    plans = []
    for input_path, target, key in provisional:
        message = None
        if key in duplicate_targets:
            message = "DUPLICATE_OUTPUT: batch contains duplicate destinations"
        elif not input_path.exists():
            message = "INPUT_NOT_FOUND: input file not found: {0}".format(input_path)
        else:
            try:
                same_path = input_path.resolve() == target.resolve()
            except OSError:
                same_path = input_path.absolute() == target.absolute()
            if same_path:
                message = "INPUT_OUTPUT_COLLISION: input and output paths are identical"
            elif target.exists() and not overwrite:
                message = "OUTPUT_EXISTS: refusing to overwrite: {0}".format(target)
        plans.append(BatchPlan(input_path, target, message))
    return plans


def convert_batch(
    input_paths: Sequence[_PathInput],
    output_dir: Optional[_PathInput] = None,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    overwrite: bool = False,
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
    cancel_event: Optional[Any] = None,
    progress_callback: Optional[Callable[[int, int, dict], None]] = None,
) -> list[dict[str, Optional[str]]]:
    """Convert every input independently and return one result per input."""
    try:
        resolved_date = resolve_render_date(render_date)
        date_error = None
    except ConversionError as exc:
        resolved_date = render_date
        date_error = str(exc)
    planned = plan_batch_outputs(input_paths, output_dir, overwrite)

    renderer = None
    renderer_manager = None
    renderer_error = None
    initially_cancelled = cancel_event is not None and cancel_event.is_set()
    if (
        not initially_cancelled
        and any(plan.error is None and date_error is None for plan in planned)
    ):
        try:
            renderer_manager = _BrowserRenderer()
            renderer = renderer_manager.__enter__()
        except Exception as exc:
            renderer_error = exc

    results = []
    try:
        for index, plan in enumerate(planned, start=1):
            input_path = plan.input_path
            target = plan.output_path
            try:
                if cancel_event is not None and cancel_event.is_set():
                    result = {
                        "input": str(input_path),
                        "output": None,
                        "status": "cancelled",
                        "error": "CANCELLED: conversion cancelled before this item",
                        "error_code": "CANCELLED",
                    }
                    results.append(result)
                    if progress_callback is not None:
                        try:
                            progress_callback(index, len(planned), result)
                        except Exception:
                            pass
                    continue
                if date_error is not None:
                    raise ConversionError(date_error)
                if plan.error is not None:
                    raise ConversionError(plan.error)
                if renderer_error is not None:
                    raise renderer_error
                result_path = convert_markdown_to_pdf(
                    input_path, target, css_path=css_path, header_footer=header_footer,
                    render_date=resolved_date, trusted_html=trusted_html, overwrite=overwrite,
                    theme=theme, theme_root=theme_root, _renderer=renderer,
                )
                result = {
                    "input": str(input_path),
                    "output": str(result_path),
                    "status": "ok",
                    "error": None,
                    "error_code": None,
                }
                results.append(result)
            except Exception as exc:
                # A failed item must not abort the remaining batch.
                result = {
                    "input": str(input_path),
                    "output": None,
                    "status": "error",
                    "error": str(exc),
                    "error_code": error_code(exc),
                }
                results.append(result)
            if progress_callback is not None:
                try:
                    progress_callback(index, len(planned), result)
                except Exception:
                    # Presentation callbacks cannot change conversion results.
                    pass
    finally:
        if renderer_manager is not None and renderer is not None:
            renderer_manager.__exit__(None, None, None)
    return results


def _first_page_png(pdf_path: Path, dpi: int) -> bytes:
    """Rasterize the first page of a core-rendered PDF."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ConversionError(
            "The 'pypdfium2' package is not installed. Run: pip install pypdfium2"
        ) from exc

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


class PreviewSession:
    """Reuse one network-denied Chromium page for related desktop previews."""

    def __init__(self) -> None:
        self._renderer = None  # type: Optional[_BrowserRenderer]
        self._context = None
        self._page = None
        self._loaded_html_hash = None  # type: Optional[bytes]

    def __enter__(self) -> "PreviewSession":
        renderer = _BrowserRenderer()
        self._renderer = renderer.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if self._context is not None:
                self._context.close()
        finally:
            if self._renderer is not None:
                self._renderer.__exit__(exc_type, exc_value, traceback)
            self._context = None
            self._page = None
            self._renderer = None
            self._loaded_html_hash = None

    def render_png(
        self,
        markdown_text: str,
        css_path: Optional[_PathInput] = None,
        header_footer: Optional[HeaderFooterConfig] = None,
        dpi: int = 110,
        render_date: Optional[str] = None,
        trusted_html: bool = False,
        resource_root: Optional[_PathInput] = None,
        theme: Optional[str] = None,
        theme_root: Optional[_PathInput] = None,
    ) -> bytes:
        """Render a preview, reloading its page only when visual content changes."""
        if self._renderer is None:
            raise ConversionError("BROWSER_UNAVAILABLE: preview session is not active")
        hf = header_footer if header_footer is not None else HeaderFooterConfig()
        document = prepare_render_document(
            markdown_text,
            css_path=css_path,
            header_footer=hf,
            render_date=render_date,
            trusted_html=trusted_html,
            resource_root=resource_root,
            theme=theme,
            theme_root=theme_root,
            # Header/footer values affect the PDF templates, not the page pixels.
            _include_profile_fingerprint=False,
        )
        html_hash = hashlib.sha256(document.full_html.encode("utf-8")).digest()
        if self._page is None:
            self._context, self._page = self._renderer._open_page()
        self._renderer.last_observed_requests = []
        if html_hash != self._loaded_html_hash:
            self._page.set_content(
                document.full_html, wait_until="load", timeout=RENDER_TIMEOUT_MS
            )
            self._loaded_html_hash = html_hash

        template_text = " ".join((
            hf.top_left,
            hf.top_center,
            hf.top_right,
            hf.bottom_left,
            hf.bottom_center,
            hf.bottom_right,
            document.render_date,
        ))
        if "{title}" in template_text or "{titre}" in template_text:
            template_text += " " + document.title
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "preview.pdf"
            try:
                self._renderer._render_loaded_page(
                    self._page,
                    pdf_path,
                    hf,
                    document.render_date,
                    preview_font_text=template_text,
                )
            except ConversionError:
                # A failed page is never retained as trusted reusable state.
                self._loaded_html_hash = None
                raise
            return _first_page_png(pdf_path, dpi)


def render_preview_png(
    markdown_text: str,
    css_path: Optional[_PathInput] = None,
    header_footer: Optional[HeaderFooterConfig] = None,
    dpi: int = 110,
    render_date: Optional[str] = None,
    trusted_html: bool = False,
    resource_root: Optional[_PathInput] = None,
    theme: Optional[str] = None,
    theme_root: Optional[_PathInput] = None,
) -> bytes:
    """Render the first PDF page as PNG bytes for the desktop preview."""
    with PreviewSession() as session:
        return session.render_png(
            markdown_text,
            css_path=css_path,
            header_footer=header_footer,
            dpi=dpi,
            render_date=render_date,
            trusted_html=trusted_html,
            resource_root=resource_root,
            theme=theme,
            theme_root=theme_root,
        )
