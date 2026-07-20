"""Tk desktop lifecycle and main-thread queue dispatch."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional

from ... import core, i18n
from ..services import DEFAULT_DESKTOP_SERVICES, DesktopServices
from .conversion import TkConversionMixin
from .dialogs import DEFAULT_TK_DIALOGS, TkDialogs
from .inputs import TkInputMixin
from .layout import HAS_DND, TkLayoutMixin, TkinterDnD
from .preview import TkPreviewMixin
from .styles import install_ui_styles, status_label_style


_HAS_DND = HAS_DND


class LibreMarkPdfApp(
    TkLayoutMixin,
    TkInputMixin,
    TkPreviewMixin,
    TkConversionMixin,
):
    """Coordinate Tk widgets while toolkit-neutral services do background work."""

    def __init__(
        self,
        root: tk.Misc,
        services: DesktopServices = DEFAULT_DESKTOP_SERVICES,
        dialogs: TkDialogs = DEFAULT_TK_DIALOGS,
    ) -> None:
        self.root = root
        self.services = services
        self.dialogs = dialogs
        self.lang = i18n.load_language()
        self.files = []  # type: list[Path]
        self.css_path = None  # type: Optional[str]
        self.output_dir = None  # type: Optional[str]
        self.operation = "idle"
        self._status_key = "status_ready"
        self._status_kwargs = {}  # type: dict
        self._close_requested = False
        self._preview_generation = 0
        self._preview_after = None
        self._preview_running = False
        self._preview_last_submitted = None  # type: Optional[int]
        self._poll_after = None
        self._cancel_event = threading.Event()
        self._result_queue = queue.Queue()  # type: queue.Queue
        self._preview_requests = queue.Queue()  # type: queue.Queue
        self._preview_thread = threading.Thread(
            target=self.services.run_preview_worker,
            args=(self._preview_requests, self._result_queue),
            daemon=True,
        )
        self._preview_thread.start()
        self._preview_png = None  # type: Optional[bytes]
        self.preview_photo = None
        self.zoom_percent = tk.IntVar(value=100)
        self.advanced_open = tk.BooleanVar(value=False)
        self.trusted_html_var = tk.BooleanVar(value=False)
        self.render_date_var = tk.StringVar()
        self.theme_var = tk.StringVar(value=core.DEFAULT_THEME_ID)
        self.progress_var = tk.IntVar(value=0)
        self.hf_vars = {
            "header_left": tk.StringVar(),
            "header_center": tk.StringVar(),
            "header_right": tk.StringVar(),
            "footer_left": tk.StringVar(),
            "footer_center": tk.StringVar(value="Page {page} / {total}"),
            "footer_right": tk.StringVar(),
        }
        self._operation_controls = []  # type: list
        self._theme_buttons = []  # type: list
        self._automation_widgets = {}  # type: dict[str, tk.Misc]

        self.ui_styles = install_ui_styles(self.root)
        self._build_ui()
        self._bind_accessibility()
        self._retranslate()
        for variable in list(self.hf_vars.values()) + [
            self.render_date_var, self.trusted_html_var
        ]:
            variable.trace_add("write", self._on_preview_input_changed)
        self.root.protocol("WM_DELETE_WINDOW", self._request_close)
        self.browse_button.focus_set()

    def _set_lang(self, lang: str) -> None:
        self.lang = lang
        i18n.save_language(lang)
        self._retranslate()

    def _t(self, key: str, **kwargs) -> str:
        return i18n.t(key, self.lang, **kwargs)

    def automation_widget(self, action: str) -> tk.Misc:
        """Return the semantic control used by stable UI automation."""
        try:
            return self._automation_widgets[action]
        except KeyError:
            raise ValueError("Unknown desktop automation action: {0}".format(action))

    def _set_status(self, key: str, **kwargs) -> None:
        self._status_key = key
        self._status_kwargs = kwargs
        self.status_label.config(
            text=self._t(key, **kwargs),
            style=status_label_style(key),
        )

    def _retranslate(self) -> None:
        self.root.title(self._t("app_title"))
        self.title_label.config(text=self._t("app_title"))
        self.source_group.config(text=self._t("source_files_label"))
        self._drop_zone_text = self._t("drop_hint")
        self._redraw_drop_zone()
        self.browse_button.config(text=self._t("browse_files"))
        self.clear_files_button.config(text=self._t("clear_files"))
        self.theme_group.config(text=self._t("themes_label"))
        self.css_label.config(text=self._t("custom_css_label"))
        self.css_button.config(text=self._t("change"))
        self.css_reset_button.config(text=self._t("use_theme"))
        self.advanced_group.config(text=self._t("advanced_header_footer"))
        self.advanced_toggle.config(
            text=("\u25be " if self.advanced_open.get() else "\u25b8 ")
            + self._t("advanced_toggle")
        )
        self.tokens_hint_label.config(text=self._t("tokens_hint"))
        self.header_group_label.config(text=self._t("header_label"))
        self.footer_group_label.config(text=self._t("footer_label"))
        self.render_date_label.config(text=self._t("render_date_label"))
        self.trusted_html_check.config(text=self._t("trusted_html_label"))
        self.preview_group.config(text=self._t("preview_label"))
        self.refresh_preview_button.config(text=self._t("refresh_preview"))
        self.output_group.config(text=self._t("output_label"))
        self.output_button.config(text=self._t("choose_folder"))
        self.output_reset_button.config(text=self._t("use_source_folder"))
        self.cancel_button.config(text=self._t("cancel_button"))
        self._refresh_generate_button()
        self._refresh_css_entry()
        self._refresh_output_entry()
        self._render_theme_cards()
        self._render_file_list()
        self.zoom_label.config(text="{0}%".format(self.zoom_percent.get()))
        self.status_label.config(
            text=self._t(self._status_key, **self._status_kwargs),
            style=status_label_style(self._status_key),
        )

    def _schedule_queue_poll(self) -> None:
        if self._poll_after is None:
            self._poll_after = self.root.after(75, self._poll_queue)

    def _poll_queue(self) -> None:
        self._poll_after = None
        while True:
            try:
                message = self._result_queue.get_nowait()
            except queue.Empty:
                break
            kind = message[0]
            if kind in ("preview_ok", "preview_error"):
                generation = message[1]
                is_latest_request = generation == self._preview_last_submitted
                if is_latest_request:
                    self._preview_running = False
                if generation == self._preview_generation:
                    if kind == "preview_ok":
                        self._apply_preview_image(message[2])
                        self._set_status("status_ready")
                    else:
                        self._set_status("status_preview_error", error=message[2])
                if is_latest_request:
                    self._refresh_generate_button()
            elif kind == "progress":
                _kind, index, total, _result = message
                self.progress_var.set(index)
                self._set_status(
                    "status_generating_progress", current=index, total=total
                )
            elif kind == "generate_done":
                if not self._close_requested:
                    self._handle_generate_done(message[1])
                self._finish_operation()
            elif kind == "generate_failed":
                if not self._close_requested:
                    self._set_status("status_generation_error", error=message[1])
                    self.dialogs.show_error(self._t("error_title"), message[1])
                self._finish_operation()
        if self.operation != "idle" or self._preview_running:
            self._schedule_queue_poll()

    def _request_close(self) -> None:
        requests = getattr(self, "_preview_requests", None)
        if requests is not None:
            requests.put(None)
        if self.operation == "idle":
            self._close_requested = True
            self._invalidate_preview()
            if self._poll_after is not None:
                self.root.after_cancel(self._poll_after)
                self._poll_after = None
            self.root.destroy()
            return
        self._close_requested = True
        self._preview_generation += 1
        if self.operation == "generate":
            self._cancel_event.set()
        self._set_status("status_closing")


def launch(services: DesktopServices = DEFAULT_DESKTOP_SERVICES) -> None:
    """Create the best available Tk root and run the desktop event loop."""
    root = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    LibreMarkPdfApp(root, services=services)
    root.mainloop()
