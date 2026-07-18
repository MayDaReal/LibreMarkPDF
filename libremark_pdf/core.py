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
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

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
from .engine import document as _document
from .engine import chromium as _chromium
from .engine import jobs as _jobs

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

_document.configure_document_dependencies(
    DEFAULT_CSS_PATH,
    _font_face_css,
    _preview_template_font_css,
    substitute_emoji_icons,
    embed_local_resources,
    _css_has_forbidden_resources,
    resolve_theme_css,
)
markdown_to_html = _document.markdown_to_html
extract_title = _document.extract_title
resolve_render_date = _document.resolve_render_date
build_header_template = _document.build_header_template
build_footer_template = _document.build_footer_template
_build_preview_template = _document._build_preview_template
build_full_html = _document.build_full_html
_read_css = _document._read_css
_resolve_style_profile = _document._resolve_style_profile
render_profile_for_options = _document.render_profile_for_options
_validate_markdown_text = _document._validate_markdown_text
prepare_render_document = _document.prepare_render_document


_BrowserRenderer = _chromium.BrowserRenderer
_render_pdf = _chromium.render_pdf
_atomic_render_pdf = _chromium.atomic_render_pdf

_jobs.configure_job_dependencies(error_code)
convert_markdown_text_to_pdf = _jobs.convert_markdown_text_to_pdf
convert_markdown_to_pdf = _jobs.convert_markdown_to_pdf
plan_batch_outputs = _jobs.plan_batch_outputs
convert_batch = _jobs.convert_batch


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
