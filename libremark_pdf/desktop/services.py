"""Toolkit-independent preview, conversion, and native-path services."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

from .. import core
from .contracts import (
    ConversionProgressEvent,
    ConversionStageEvent,
    ConversionTerminalEvent,
    PreviewDocumentEvent,
    PreviewDocumentRequest,
    PreviewEvent,
    PreviewPageErrorEvent,
    PreviewPageEvent,
    PreviewPageRequest,
    PreviewRequest,
)


def open_path(path: Path) -> None:
    """Open a successful output or directory through the native shell."""
    resolved = str(path)
    if os.name == "nt":
        os.startfile(resolved)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", resolved])
    else:
        subprocess.Popen(["xdg-open", resolved])


def run_preview_worker(
    request_queue: "queue.Queue",
    result_queue: "queue.Queue",
) -> None:
    """Own one preview session and render only the latest queued request."""
    session = None  # type: Optional[core.PreviewSession]
    try:
        while True:
            item = request_queue.get()
            if item is None:
                return
            # Changes can arrive while Chromium is busy. Intermediate previews
            # have no value, so retain only the newest complete request.
            while True:
                try:
                    newer = request_queue.get_nowait()
                except queue.Empty:
                    break
                if newer is None:
                    return
                item = newer
            if isinstance(item, PreviewPageRequest):
                try:
                    if session is None:
                        raise core.ConversionError(
                            "PREVIEW_UNAVAILABLE: no preview document is active"
                        )
                    page = session.render_page(item.page, dpi=item.dpi)
                    result_queue.put(PreviewPageEvent(
                        "preview_page_ok",
                        item.generation,
                        page.page,
                        page.total,
                        page.png,
                    ))
                except Exception as exc:
                    result_queue.put(PreviewPageErrorEvent(
                        "preview_page_error",
                        item.generation,
                        item.page,
                        str(exc),
                    ))
                continue
            multipage = isinstance(item, PreviewDocumentRequest)
            request = (
                item if multipage else PreviewRequest.from_queue_item(item)
            )
            try:
                markdown_text = request.markdown_text
                if request.source_path is not None:
                    markdown_text = request.source_path.read_text(encoding="utf-8")
                if session is None:
                    candidate = core.PreviewSession()
                    candidate.__enter__()
                    session = candidate
                if multipage:
                    page = session.render_document(
                        markdown_text or "", **request.options
                    )
                    result_queue.put(PreviewDocumentEvent(
                        "preview_document_ok",
                        request.generation,
                        page.page,
                        page.total,
                        page.png,
                    ))
                else:
                    png = session.render_png(markdown_text or "", **request.options)
                    result_queue.put(PreviewEvent("preview_ok", request.generation, png))
            except Exception as exc:
                result_queue.put(
                    PreviewEvent("preview_error", request.generation, str(exc))
                )
    finally:
        if session is not None:
            session.__exit__(None, None, None)


def run_conversion_job(
    result_queue: "queue.Queue",
    files: list,
    options: dict,
    cancel_event: threading.Event,
    cancel_current_event: Optional[threading.Event] = None,
) -> None:
    """Run a batch conversion and publish progress through a neutral queue."""

    def progress(index: int, total: int, result: dict) -> None:
        result_queue.put(ConversionProgressEvent("progress", index, total, result))

    def stage(index: int, total: int, input_path: Path, name: str) -> None:
        result_queue.put(
            ConversionStageEvent("conversion_stage", index, total, input_path, name)
        )

    try:
        results = core.convert_batch(
            files,
            cancel_event=cancel_event,
            cancel_current_event=cancel_current_event,
            progress_callback=progress,
            stage_callback=stage,
            **options
        )
        result_queue.put(ConversionTerminalEvent("generate_done", results))
    except Exception as exc:
        result_queue.put(ConversionTerminalEvent("generate_failed", str(exc)))


class DesktopServices:
    """Dependency boundary used by desktop adapters and UI experiments."""

    def open_path(self, path: Path) -> None:
        open_path(path)

    def run_preview_worker(
        self,
        request_queue: "queue.Queue",
        result_queue: "queue.Queue",
    ) -> None:
        run_preview_worker(request_queue, result_queue)

    def run_conversion_job(
        self,
        result_queue: "queue.Queue",
        files: list,
        options: dict,
        cancel_event: threading.Event,
        cancel_current_event: Optional[threading.Event] = None,
    ) -> None:
        run_conversion_job(
            result_queue, files, options, cancel_event, cancel_current_event
        )


DEFAULT_DESKTOP_SERVICES = DesktopServices()
