"""Locked Chromium rendering and atomic PDF publication for the private engine."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Optional

from . import document
from .contracts import (
    CHROMIUM_VERSION,
    ConversionError,
    HeaderFooterConfig,
    MARGIN_NO_HEADER_FOOTER,
    MARGIN_WITH_HEADER_FOOTER,
    RENDER_TIMEOUT_MS,
)


class BrowserRenderer:
    """One locked browser process with an isolated context per document."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self.last_observed_requests = []

    def __enter__(self) -> "BrowserRenderer":
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
        actual_version = self._browser.version
        if actual_version != CHROMIUM_VERSION:
            self.__exit__(None, None, None)
            raise ConversionError(
                f"BROWSER_MISMATCH: expected Chromium {CHROMIUM_VERSION}, "
                f"launched {actual_version}."
            )
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
                document.build_header_template(header_footer, render_date)
                if display_hf else "<div></div>"
            )
            footer_template = (
                document.build_footer_template(header_footer, render_date)
                if display_hf else "<div></div>"
            )
        else:
            header_template = document._build_preview_template(
                header_footer.top_left, header_footer.top_center,
                header_footer.top_right, render_date, preview_font_text,
            )
            footer_template = document._build_preview_template(
                header_footer.bottom_left, header_footer.bottom_center,
                header_footer.bottom_right, render_date, preview_font_text,
            )
        page.emulate_media(media="print")
        page.pdf(
            path=str(output_path), format="A4", margin=margin,
            display_header_footer=display_hf, header_template=header_template,
            footer_template=footer_template, print_background=True, tagged=True,
            outline=True,
        )
        if self.last_observed_requests:
            raise ConversionError("NETWORK_BLOCKED: renderer attempted a network request")

    def render(
        self, full_html: str, output_path: Path, header_footer: HeaderFooterConfig,
        render_date: Optional[str],
    ) -> None:
        if self._browser is None:
            raise ConversionError("BROWSER_UNAVAILABLE: browser session is not active")
        context = None
        try:
            self.last_observed_requests = []
            context, page = self._open_page()
            page.set_content(full_html, wait_until="load", timeout=RENDER_TIMEOUT_MS)
            self._render_loaded_page(page, output_path, header_footer, render_date)
        except ConversionError:
            raise
        except Exception as exc:
            raise ConversionError("RENDER_FAILED: {0}".format(exc)) from exc
        finally:
            if context is not None:
                context.close()


def render_pdf(
    full_html: str, output_path: Path, header_footer: HeaderFooterConfig,
    render_date: Optional[str] = None,
) -> None:
    """Render one document through a short-lived browser session."""
    with BrowserRenderer() as renderer:
        renderer.render(full_html, output_path, header_footer, render_date)


def _create_temporary_output(output_path: Path) -> Path:
    """Create one sibling output without tempfile's unbounded Windows retry."""
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    for _attempt in range(16):
        candidate = output_path.parent / (
            ".libremark-{0}.pdf".format(uuid.uuid4().hex)
        )
        try:
            descriptor = os.open(str(candidate), flags, 0o600)
        except FileExistsError:
            continue
        except OSError as exc:
            raise ConversionError(
                "OUTPUT_UNAVAILABLE: cannot create temporary output in: {0}".format(
                    output_path.parent
                )
            ) from exc
        os.close(descriptor)
        return candidate
    raise ConversionError(
        "OUTPUT_UNAVAILABLE: cannot reserve a temporary output in: {0}".format(
            output_path.parent
        )
    )


def atomic_render_pdf(
    full_html: str, output_path: Path, header_footer: HeaderFooterConfig,
    render_date: Optional[str], renderer: Optional[BrowserRenderer] = None,
    cancel_event: Optional[Any] = None,
) -> None:
    """Render into a sibling temporary file, then atomically publish it."""
    temp_path = None
    try:
        if cancel_event is not None and cancel_event.is_set():
            raise ConversionError("CANCELLED: conversion cancelled before rendering")
        temp_path = _create_temporary_output(output_path)
        if renderer is None:
            render_pdf(full_html, temp_path, header_footer, render_date)
        else:
            renderer.render(full_html, temp_path, header_footer, render_date)
        stage_callback = getattr(renderer, "stage_callback", None)
        if stage_callback is not None:
            stage_callback("finalizing")
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise ConversionError("INVALID_OUTPUT: renderer did not create a PDF")
        # Chromium calls are synchronous. This is the first safe interruption
        # point after printing and, critically, precedes atomic publication.
        if cancel_event is not None and cancel_event.is_set():
            raise ConversionError("CANCELLED: conversion cancelled before publication")
        if stage_callback is not None:
            stage_callback("publishing")
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
