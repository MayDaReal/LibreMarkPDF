"""Toolkit-independent services shared by desktop front ends."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

from . import core


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
            request = request_queue.get()
            if request is None:
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
                request = newer
            generation, source_path, markdown_text, options = request
            try:
                if source_path is not None:
                    markdown_text = source_path.read_text(encoding="utf-8")
                if session is None:
                    candidate = core.PreviewSession()
                    candidate.__enter__()
                    session = candidate
                png = session.render_png(markdown_text or "", **options)
                result_queue.put(("preview_ok", generation, png))
            except Exception as exc:
                result_queue.put(("preview_error", generation, str(exc)))
    finally:
        if session is not None:
            session.__exit__(None, None, None)


def run_conversion_job(
    result_queue: "queue.Queue",
    files: list,
    options: dict,
    cancel_event: threading.Event,
) -> None:
    """Run a batch conversion and publish progress through a neutral queue."""

    def progress(index: int, total: int, result: dict) -> None:
        result_queue.put(("progress", index, total, result))

    try:
        results = core.convert_batch(
            files,
            cancel_event=cancel_event,
            progress_callback=progress,
            **options
        )
        result_queue.put(("generate_done", results))
    except Exception as exc:
        result_queue.put(("generate_failed", str(exc)))


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
    ) -> None:
        run_conversion_job(result_queue, files, options, cancel_event)


DEFAULT_DESKTOP_SERVICES = DesktopServices()
