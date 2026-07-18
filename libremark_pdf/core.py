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
