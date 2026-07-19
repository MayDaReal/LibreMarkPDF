"""Shared Markdown-to-PDF conversion engine."""

from __future__ import annotations

import re
from pathlib import Path

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
from .engine import jobs as _jobs
from .engine import preview as _preview

def resource_path(relative: str) -> Path:
    """Resolve a frozen runtime resource from source, wheel, or PyInstaller."""
    return _resources.resource_path(relative, __file__)


DEFAULT_CSS_PATH = resource_path("style.css")
ICONS_DIR = resource_path("icons")
FONTS_DIR = resource_path("fonts")
BROWSERS_DIR = _resources.browser_resource_path(__file__)
DEFAULT_THEME_ROOT = Path.home() / ".libremark-pdf" / "themes"

_resources.configure_resource_locations(DEFAULT_CSS_PATH, ICONS_DIR, FONTS_DIR, BROWSERS_DIR)
_resources.prefer_bundled_browser()
renderer_identity = _resources.renderer_identity
_FONT_FILES = _resources._FONT_FILES
substitute_emoji_icons = _resources.substitute_emoji_icons
embed_local_resources = _resources.embed_local_resources

_configure_resource_hashes(_resources._renderer_resource_hashes)


def error_code(exc: BaseException) -> str:
    """Extract the stable leading code exposed by core diagnostics."""
    match = re.match(r"^([A-Z][A-Z0-9_]+):", str(exc))
    return match.group(1) if match else "INTERNAL_ERROR"


_themes.configure_theme_dependencies(
    resource_path,
    DEFAULT_CSS_PATH,
    DEFAULT_THEME_ROOT,
    _resources._sha256_file,
    _resources._is_within,
    _resources._validate_image_bytes,
    _resources._css_has_forbidden_resources,
)
THEME_MANIFEST_SCHEMA = _themes.THEME_MANIFEST_SCHEMA
THEME_MANIFEST_NAME = _themes.THEME_MANIFEST_NAME
validate_theme_package = _themes.validate_theme_package
list_themes = _themes.list_themes
show_theme = _themes.show_theme
install_theme = _themes.install_theme
remove_theme = _themes.remove_theme
resolve_theme_css = _themes.resolve_theme_css

_document.configure_document_dependencies(
    DEFAULT_CSS_PATH,
    _resources._font_face_css,
    _resources._preview_template_font_css,
    substitute_emoji_icons,
    embed_local_resources,
    _resources._css_has_forbidden_resources,
    resolve_theme_css,
)
markdown_to_html = _document.markdown_to_html
extract_title = _document.extract_title
resolve_render_date = _document.resolve_render_date
build_header_template = _document.build_header_template
build_footer_template = _document.build_footer_template
build_full_html = _document.build_full_html
render_profile_for_options = _document.render_profile_for_options
prepare_render_document = _document.prepare_render_document


_jobs.configure_job_dependencies(error_code)
convert_markdown_text_to_pdf = _jobs.convert_markdown_text_to_pdf
convert_markdown_to_pdf = _jobs.convert_markdown_to_pdf
plan_batch_outputs = _jobs.plan_batch_outputs
convert_batch = _jobs.convert_batch


PreviewSession = _preview.PreviewSession
render_preview_png = _preview.render_preview_png
