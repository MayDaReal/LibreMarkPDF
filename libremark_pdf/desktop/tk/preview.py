"""Preview interaction for the Tk desktop adapter."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageTk

from ... import core


PREVIEW_DPI = 90
PREVIEW_DEBOUNCE_MS = 450
ZOOM_LEVELS = (50, 75, 100, 125, 150, 200)

SAMPLE_MARKDOWN = """# {title}

{body}

| Status | Description |
|---|---|
| Done | Everything works |
| Pending | Waiting on review |
"""


class TkPreviewMixin:
    """Manage debounced preview requests and main-thread image updates."""

    def _on_preview_input_changed(self, *unused) -> None:
        self._schedule_preview()

    def _invalidate_preview(self, clear_image: bool = False) -> None:
        self._preview_generation += 1
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
            self._preview_after = None
        if clear_image:
            self._preview_png = None
            self.preview_photo = None
            self.preview_canvas.delete("all")
            self._set_status("status_ready")

    def _schedule_preview(self) -> None:
        if self.operation != "idle" or not hasattr(self, "refresh_preview_button"):
            return
        self._preview_generation += 1
        generation = self._preview_generation
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
        self._preview_after = self.root.after(
            PREVIEW_DEBOUNCE_MS, lambda: self._start_preview(generation)
        )

    def _refresh_preview(self) -> None:
        if self.operation != "idle":
            return
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
            self._preview_after = None
        self._preview_generation += 1
        self._start_preview(self._preview_generation)

    def _start_preview(self, generation: int) -> None:
        self._preview_after = None
        if generation != self._preview_generation or self.operation != "idle":
            return
        options = self._render_options()
        try:
            profile = core.render_profile_for_options(**options)
        except Exception as exc:
            self._set_status("status_preview_error", error=str(exc))
            return
        options["render_date"] = profile.render_date
        source_path = self.files[0] if self.files else None
        markdown_text = None
        if source_path is None:
            markdown_text = SAMPLE_MARKDOWN.format(
                title=self._t("sample_preview_title"),
                body=self._t("sample_preview_body"),
            )
            options["resource_root"] = Path.cwd()
        else:
            options["resource_root"] = source_path.resolve().parent
        options["dpi"] = PREVIEW_DPI
        self._preview_running = True
        self._preview_last_submitted = generation
        self._refresh_generate_button()
        self._set_status("status_rendering_preview")
        self._preview_requests.put(
            (generation, source_path, markdown_text, options)
        )
        self._schedule_queue_poll()

    def _apply_preview_image(self, png_bytes: bytes) -> None:
        self._preview_png = png_bytes
        self._redraw_preview()

    def _redraw_preview(self) -> None:
        if self._preview_png is None:
            return
        image = Image.open(io.BytesIO(self._preview_png)).convert("RGB")
        scale = self.zoom_percent.get() / 100.0
        size = (
            max(1, int(image.width * scale)),
            max(1, int(image.height * scale)),
        )
        image = image.resize(size, Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(12, 12, image=self.preview_photo, anchor="nw")
        self.preview_canvas.configure(
            scrollregion=(0, 0, image.width + 24, image.height + 24)
        )
        self.zoom_label.config(text="{0}%".format(self.zoom_percent.get()))

    def _change_zoom(self, direction: int) -> None:
        current = self.zoom_percent.get()
        index = min(
            range(len(ZOOM_LEVELS)),
            key=lambda item: abs(ZOOM_LEVELS[item] - current),
        )
        index = max(0, min(len(ZOOM_LEVELS) - 1, index + direction))
        self.zoom_percent.set(ZOOM_LEVELS[index])
        self._redraw_preview()
