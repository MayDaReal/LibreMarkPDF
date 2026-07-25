"""Preview interaction for the Tk desktop adapter."""

from __future__ import annotations

import io
from typing import Optional

from PIL import Image, ImageTk

from ... import core
from ..contracts import PreviewDocumentRequest, PreviewPageRequest


PREVIEW_DPI = 90
PREVIEW_DEBOUNCE_MS = 450
ZOOM_LEVELS = (50, 75, 100, 125, 150, 200)
CANVAS_MARGIN = 12
CONTROL_MASK = 0x0004


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
            self._preview_page = 1
            self._preview_total_pages = 0
            self._preview_pages = {}
            self._preview_page_pending = None
            self._preview_failed_page = None
            self._set_preview_state("empty")
            self._set_status("status_ready")
        elif getattr(self, "_preview_state", None) == "loading":
            self._set_preview_state(
                "ready" if getattr(self, "_preview_png", None) else "unavailable"
            )

    def _schedule_preview(self) -> None:
        if self.operation != "idle" or not hasattr(self, "refresh_preview_button"):
            return
        if not self.files:
            self._set_preview_state("empty")
            return
        self._preview_generation += 1
        generation = self._preview_generation
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
        self._preview_page_pending = None
        self._preview_failed_page = None
        self._set_preview_state("loading")
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
        if not self.files:
            self._set_preview_state("empty")
            return
        self._preview_page_pending = None
        self._preview_failed_page = None
        self._set_preview_state("loading")
        self._start_preview(self._preview_generation)

    def _start_preview(self, generation: int) -> None:
        self._preview_after = None
        if generation != self._preview_generation or self.operation != "idle":
            return
        source_path = (
            self.active_file
            if getattr(self, "active_file", None) in self.files
            else (self.files[0] if self.files else None)
        )
        if source_path is None:
            self._set_preview_state("empty")
            return
        options = self._preview_render_options()
        try:
            profile = core.render_profile_for_options(**options)
        except Exception as exc:
            self._set_preview_error(str(exc))
            self._set_status("status_preview_error", error=str(exc))
            return
        options["render_date"] = profile.render_date
        options["resource_root"] = source_path.resolve().parent
        options["dpi"] = PREVIEW_DPI
        self._preview_running = True
        self._preview_last_submitted = generation
        self._preview_active_request = ("document", generation, 1)
        self._refresh_generate_button()
        self._set_preview_state("loading")
        self._set_status("status_rendering_preview")
        self._preview_requests.put(
            PreviewDocumentRequest(generation, source_path, None, options)
        )
        self._schedule_queue_poll()

    def _apply_preview_document(
        self, page: int, total: int, png_bytes: bytes
    ) -> None:
        self._preview_page = page
        self._preview_total_pages = total
        self._preview_pages = {page: png_bytes}
        self._preview_page_pending = None
        self._preview_failed_page = None
        self._apply_preview_image(png_bytes)

    def _apply_preview_page(
        self, page: int, total: int, png_bytes: bytes
    ) -> None:
        self._preview_pages[page] = png_bytes
        self._preview_page = page
        self._preview_total_pages = total
        self._preview_page_pending = None
        self._preview_failed_page = None
        self._apply_preview_image(png_bytes)

    def _apply_preview_image(self, png_bytes: bytes) -> None:
        self._preview_png = png_bytes
        self._preview_error = None
        self._preview_state = "ready"
        self._redraw_preview()
        self._refresh_preview_ui()

    def _redraw_preview(self) -> None:
        if getattr(self, "_preview_png", None) is None:
            self._draw_preview_state()
            return
        with Image.open(io.BytesIO(self._preview_png)) as source:
            image = source.convert("RGB")
        scale = self.zoom_percent.get() / 100.0
        size = (
            max(1, int(image.width * scale)),
            max(1, int(image.height * scale)),
        )
        image = image.resize(size, Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            CANVAS_MARGIN,
            CANVAS_MARGIN,
            image=self.preview_photo,
            anchor="nw",
        )
        self.preview_canvas.configure(
            scrollregion=(
                0,
                0,
                image.width + (2 * CANVAS_MARGIN),
                image.height + (2 * CANVAS_MARGIN),
            )
        )
        self._update_zoom_controls()
        self.root.after_idle(self._update_preview_scrollbars)

    def _set_preview_state(
        self, state: str, error: Optional[str] = None
    ) -> None:
        self._preview_state = state
        self._preview_error = error
        self._refresh_preview_ui()
        if getattr(self, "_preview_png", None) is None:
            self._draw_preview_state()

    def _set_preview_error(self, error: str) -> None:
        self._preview_failed_page = None
        self._set_preview_state("error", error)

    def _set_preview_page_error(self, page: int, error: str) -> None:
        self._preview_failed_page = page
        self._set_preview_state("page_error", error)

    def _refresh_preview_ui(self) -> None:
        if not hasattr(self, "active_preview_label"):
            return
        active = (
            self.active_file
            if getattr(self, "active_file", None) in self.files
            else None
        )
        self.active_preview_label.config(
            text=active.name if active is not None else self._t("preview_heading")
        )
        state = getattr(self, "_preview_state", "empty")
        if state == "empty":
            message = self._t("preview_empty")
        elif state == "loading":
            message = self._t("preview_loading")
        elif state in ("error", "page_error"):
            message = "{0}: {1} {2}".format(
                self._t("preview_unavailable"),
                self._preview_error or "",
                self._t("preview_conversion_possible"),
            ).strip()
        elif state == "unavailable":
            message = "{0}. {1}".format(
                self._t("preview_unavailable"),
                self._t("preview_conversion_possible"),
            )
        else:
            message = ""
        self.preview_message_label.config(text=message)
        if state == "ready":
            self.preview_message_frame.pack_forget()
        else:
            self.preview_message_frame.pack(
                fill="x",
                pady=(8, 0),
                before=self.preview_canvas.master,
            )
        if state in ("error", "page_error", "unavailable"):
            self.preview_retry_button.pack(side="right", padx=(8, 0))
        else:
            self.preview_retry_button.pack_forget()
        if state in ("error", "page_error"):
            self.preview_copy_button.pack(side="right", padx=(8, 0))
        else:
            self.preview_copy_button.pack_forget()
        self._update_zoom_controls()
        self._update_page_controls()

    def _update_preview_translations(self) -> None:
        controls = (
            (self.refresh_preview_button, "refresh_preview_a11y"),
            (self.previous_page_button, "previous_page_a11y"),
            (self.next_page_button, "next_page_a11y"),
            (self.zoom_out_button, "zoom_out_a11y"),
            (self.zoom_in_button, "zoom_in_a11y"),
        )
        for button, key in controls:
            accessible_name = self._t(key)
            button.accessible_name = accessible_name
            button.tooltip.text = accessible_name
        self.preview_retry_button.config(text=self._t("preview_retry"))
        self.preview_copy_button.config(text=self._t("copy_details"))
        self._update_page_controls()

    def _draw_preview_state(self) -> None:
        if not hasattr(self, "preview_canvas") or self._preview_png is not None:
            return
        canvas = self.preview_canvas
        canvas.delete("all")
        width = max(240, canvas.winfo_width())
        height = max(180, canvas.winfo_height())
        page_width = min(150, width // 3)
        page_height = min(190, height // 2)
        left = (width - page_width) // 2
        top = max(18, (height - page_height) // 2 - 24)
        canvas.create_rectangle(
            left,
            top,
            left + page_width,
            top + page_height,
            outline=self.ui_styles.drop_border,
            width=2,
        )
        for offset in (34, 54, 74):
            canvas.create_line(
                left + 24,
                top + offset,
                left + page_width - 24,
                top + offset,
                fill=self.ui_styles.drop_border,
            )
        text_key = {
            "empty": "preview_empty",
            "loading": "preview_loading",
            "error": "preview_unavailable",
            "page_error": "preview_unavailable",
            "unavailable": "preview_unavailable",
        }.get(self._preview_state, "preview_empty")
        canvas.create_text(
            width // 2,
            min(height - 22, top + page_height + 22),
            text=self._t(text_key),
            fill=self.ui_styles.drop_border,
            width=max(180, width - 32),
            justify="center",
        )
        canvas.configure(scrollregion=(0, 0, width, height))
        self.root.after_idle(self._update_preview_scrollbars)

    def _change_zoom(self, direction: int, anchor=None) -> str:
        if getattr(self, "operation", "idle") != "idle":
            return "break"
        current = self.zoom_percent.get()
        index = min(
            range(len(ZOOM_LEVELS)),
            key=lambda item: abs(ZOOM_LEVELS[item] - current),
        )
        index = max(0, min(len(ZOOM_LEVELS) - 1, index + direction))
        self._set_zoom(ZOOM_LEVELS[index], anchor)
        return "break"

    def _reset_zoom(self) -> str:
        if getattr(self, "operation", "idle") == "idle":
            self._set_zoom(100)
        return "break"

    def _set_zoom(self, percent: int, anchor=None) -> None:
        old_percent = self.zoom_percent.get()
        source_point = None
        if anchor is not None and self._preview_png is not None:
            source_point = (
                (self.preview_canvas.canvasx(anchor[0]) - CANVAS_MARGIN)
                / (old_percent / 100.0),
                (self.preview_canvas.canvasy(anchor[1]) - CANVAS_MARGIN)
                / (old_percent / 100.0),
            )
        self.zoom_percent.set(percent)
        self._redraw_preview()
        if source_point is not None:
            region = self.preview_canvas.cget("scrollregion").split()
            if len(region) == 4:
                width = max(1.0, float(region[2]) - float(region[0]))
                height = max(1.0, float(region[3]) - float(region[1]))
                scale = percent / 100.0
                target_x = CANVAS_MARGIN + source_point[0] * scale - anchor[0]
                target_y = CANVAS_MARGIN + source_point[1] * scale - anchor[1]
                self.preview_canvas.xview_moveto(max(0.0, target_x / width))
                self.preview_canvas.yview_moveto(max(0.0, target_y / height))
        self._update_zoom_controls()

    def _update_zoom_controls(self) -> None:
        if not hasattr(self, "zoom_label"):
            return
        percent = self.zoom_percent.get()
        self.zoom_label.config(text=self._t("zoom_value", percent=percent))
        interactive = self.operation == "idle"
        self.zoom_out_button.config(
            state="normal" if interactive and percent > ZOOM_LEVELS[0] else "disabled"
        )
        self.zoom_in_button.config(
            state="normal" if interactive and percent < ZOOM_LEVELS[-1] else "disabled"
        )

    def _update_page_controls(self) -> None:
        if not hasattr(self, "preview_page_label"):
            return
        current = getattr(self, "_preview_page", 1)
        total = getattr(self, "_preview_total_pages", 0)
        self.preview_page_label.config(
            text=(
                self._t("preview_page", current=current, total=total)
                if total > 0
                else ""
            )
        )
        interactive = (
            self.operation == "idle"
            and getattr(self, "_preview_state", "empty") in ("ready", "page_error")
            and getattr(self, "_preview_page_pending", None) is None
        )
        self.previous_page_button.config(
            state="normal" if interactive and current > 1 else "disabled"
        )
        self.next_page_button.config(
            state="normal" if interactive and current < total else "disabled"
        )

    def _change_preview_page(self, direction: int) -> str:
        if getattr(self, "operation", "idle") != "idle":
            return "break"
        current = getattr(self, "_preview_page", 1)
        total = getattr(self, "_preview_total_pages", 0)
        target = current + direction
        if target < 1 or target > total:
            return "break"
        self._request_preview_page(target)
        return "break"

    def _request_preview_page(self, page: int) -> None:
        cached = getattr(self, "_preview_pages", {}).get(page)
        if cached is not None:
            self._apply_preview_page(page, self._preview_total_pages, cached)
            return
        generation = self._preview_generation
        self._preview_page_pending = page
        self._preview_failed_page = None
        self._preview_running = True
        self._preview_active_request = ("page", generation, page)
        self._set_preview_state("loading")
        self._set_status("status_rendering_preview")
        self._preview_requests.put(
            PreviewPageRequest(generation, page, PREVIEW_DPI)
        )
        self._schedule_queue_poll()

    def _retry_preview(self) -> None:
        failed_page = getattr(self, "_preview_failed_page", None)
        if failed_page is not None:
            self._request_preview_page(failed_page)
        else:
            self._refresh_preview()

    def _focus_preview(self, _event=None) -> None:
        self.preview_canvas.focus_set()

    def _on_preview_mousewheel(self, event) -> str:
        self.preview_canvas.focus_set()
        upward = getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4
        if getattr(event, "state", 0) & CONTROL_MASK:
            self._change_zoom(1 if upward else -1, (event.x, event.y))
        else:
            self.preview_canvas.yview_scroll(-1 if upward else 1, "units")
        return "break"

    def _start_preview_pan(self, event) -> str:
        self.preview_canvas.focus_set()
        self.preview_canvas.scan_mark(event.x, event.y)
        return "break"

    def _drag_preview_pan(self, event) -> str:
        self.preview_canvas.scan_dragto(event.x, event.y, gain=1)
        return "break"

    def _on_preview_canvas_configure(self, _event=None) -> None:
        if self._preview_png is None:
            self._draw_preview_state()
        else:
            self._update_preview_scrollbars()

    def _update_preview_scrollbars(self) -> None:
        if not hasattr(self, "preview_vertical"):
            return
        bounds = self.preview_canvas.bbox("all")
        if bounds is None:
            needs_horizontal = needs_vertical = False
        else:
            needs_horizontal = bounds[2] - bounds[0] > self.preview_canvas.winfo_width()
            needs_vertical = bounds[3] - bounds[1] > self.preview_canvas.winfo_height()
        if needs_vertical:
            self.preview_vertical.grid(row=0, column=1, sticky="ns")
        else:
            self.preview_vertical.grid_remove()
        if needs_horizontal:
            self.preview_horizontal.grid(row=1, column=0, sticky="ew")
        else:
            self.preview_horizontal.grid_remove()

    def _copy_preview_details(self) -> None:
        if not self._preview_error:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self._preview_error)
