"""PDFium rasterization and reusable Chromium preview sessions."""

from __future__ import annotations

import hashlib
import io
import tempfile
from pathlib import Path
from typing import Optional, Union

from . import chromium, document
from .contracts import ConversionError, HeaderFooterConfig, RENDER_TIMEOUT_MS

_PathInput = Union[str, Path]


def first_page_png(pdf_path: Path, dpi: int) -> bytes:
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
        self._renderer = None  # type: Optional[chromium.BrowserRenderer]
        self._context = None
        self._page = None
        self._loaded_html_hash = None  # type: Optional[bytes]

    def __enter__(self) -> "PreviewSession":
        renderer = chromium.BrowserRenderer()
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
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "preview.pdf"
            try:
                self._renderer._render_loaded_page(
                    self._page, pdf_path, hf, rendered_document.render_date,
                    preview_font_text=template_text,
                )
            except ConversionError:
                self._loaded_html_hash = None
                raise
            return first_page_png(pdf_path, dpi)


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
