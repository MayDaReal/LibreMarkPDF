"""PDFium rasterization and reusable Chromium preview sessions."""

from __future__ import annotations

import hashlib
import io
import tempfile
from pathlib import Path
from typing import Dict, NamedTuple, Optional, Tuple, Union

from . import chromium, document
from .contracts import ConversionError, HeaderFooterConfig, RENDER_TIMEOUT_MS

_PathInput = Union[str, Path]


class PreviewPage(NamedTuple):
    """A rasterized page from the current Chromium-rendered preview PDF."""

    page: int
    total: int
    png: bytes


def rasterize_pdf_page(pdf_path: Path, page_number: int, dpi: int) -> PreviewPage:
    """Rasterize one 1-based page from a core-rendered preview PDF."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ConversionError(
            "The 'pypdfium2' package is not installed. Run: pip install pypdfium2"
        ) from exc
    pdf = pdfium.PdfDocument(str(pdf_path))
    page = None
    bitmap = None
    try:
        total = len(pdf)
        if page_number < 1 or page_number > total:
            raise ConversionError(
                "PREVIEW_PAGE_OUT_OF_RANGE: page {0} of {1}".format(
                    page_number, total
                )
            )
        page = pdf[page_number - 1]
        bitmap = page.render(scale=dpi / 72)
        pil_image = bitmap.to_pil()
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return PreviewPage(page_number, total, buffer.getvalue())
    finally:
        if bitmap is not None and hasattr(bitmap, "close"):
            bitmap.close()
        if page is not None and hasattr(page, "close"):
            page.close()
        pdf.close()


def first_page_png(pdf_path: Path, dpi: int) -> bytes:
    """Rasterize the first page of a core-rendered PDF."""
    return rasterize_pdf_page(pdf_path, 1, dpi).png


class PreviewSession:
    """Reuse one network-denied Chromium page for related desktop previews."""

    def __init__(self) -> None:
        self._renderer = None  # type: Optional[chromium.BrowserRenderer]
        self._context = None
        self._page = None
        self._loaded_html_hash = None  # type: Optional[bytes]
        self._preview_directory = None  # type: Optional[tempfile.TemporaryDirectory]
        self._preview_pdf_path = None  # type: Optional[Path]
        self._page_count = 0
        self._page_cache = {}  # type: Dict[Tuple[int, int], bytes]

    def __enter__(self) -> "PreviewSession":
        renderer = chromium.BrowserRenderer()
        self._renderer = renderer.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            self._clear_preview_document()
        finally:
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

    def _clear_preview_document(self) -> None:
        directory = self._preview_directory
        self._preview_directory = None
        self._preview_pdf_path = None
        self._page_count = 0
        self._page_cache = {}
        if directory is not None:
            directory.cleanup()

    def render_document(
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
    ) -> PreviewPage:
        """Render one preview PDF and return its first rasterized page."""
        if self._renderer is None:
            raise ConversionError("BROWSER_UNAVAILABLE: preview session is not active")
        hf = header_footer if header_footer is not None else HeaderFooterConfig()
        rendered_document = document.prepare_render_document(
            markdown_text,
            css_path=css_path,
            header_footer=hf,
            render_date=render_date,
            trusted_html=trusted_html,
            resource_root=resource_root,
            theme=theme,
            theme_root=theme_root,
            _include_profile_fingerprint=False,
        )
        html_hash = hashlib.sha256(rendered_document.full_html.encode("utf-8")).digest()
        if self._page is None:
            self._context, self._page = self._renderer._open_page()
        self._renderer.last_observed_requests = []
        if html_hash != self._loaded_html_hash:
            self._page.set_content(
                rendered_document.full_html, wait_until="load", timeout=RENDER_TIMEOUT_MS
            )
            self._loaded_html_hash = html_hash
        template_text = " ".join((
            hf.top_left, hf.top_center, hf.top_right, hf.bottom_left,
            hf.bottom_center, hf.bottom_right, rendered_document.render_date,
        ))
        if "{title}" in template_text or "{titre}" in template_text:
            template_text += " " + rendered_document.title

        candidate_directory = tempfile.TemporaryDirectory(prefix="libremark-preview-")
        pdf_path = Path(candidate_directory.name) / "preview.pdf"
        try:
            try:
                self._renderer._render_loaded_page(
                    self._page, pdf_path, hf, rendered_document.render_date,
                    preview_font_text=template_text,
                )
            except ConversionError:
                self._loaded_html_hash = None
                raise
            first_page = rasterize_pdf_page(pdf_path, 1, dpi)
        except Exception:
            candidate_directory.cleanup()
            raise

        self._clear_preview_document()
        self._preview_directory = candidate_directory
        self._preview_pdf_path = pdf_path
        self._page_count = first_page.total
        self._page_cache[(1, dpi)] = first_page.png
        return first_page

    def render_page(self, page_number: int, dpi: int = 110) -> PreviewPage:
        """Rasterize a page from the current preview PDF without Chromium."""
        if self._preview_pdf_path is None or self._page_count < 1:
            raise ConversionError("PREVIEW_UNAVAILABLE: no preview document is active")
        if page_number < 1 or page_number > self._page_count:
            raise ConversionError(
                "PREVIEW_PAGE_OUT_OF_RANGE: page {0} of {1}".format(
                    page_number, self._page_count
                )
            )
        cache_key = (page_number, dpi)
        png = self._page_cache.get(cache_key)
        if png is None:
            rendered = rasterize_pdf_page(
                self._preview_pdf_path, page_number, dpi
            )
            png = rendered.png
            self._page_cache[cache_key] = png
        return PreviewPage(page_number, self._page_count, png)

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
        """Render the first page while retaining the preview PDF for navigation."""
        return self.render_document(
            markdown_text,
            css_path=css_path,
            header_footer=header_footer,
            dpi=dpi,
            render_date=render_date,
            trusted_html=trusted_html,
            resource_root=resource_root,
            theme=theme,
            theme_root=theme_root,
        ).png


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
            markdown_text, css_path=css_path, header_footer=header_footer, dpi=dpi,
            render_date=render_date, trusted_html=trusted_html,
            resource_root=resource_root, theme=theme, theme_root=theme_root,
        )
