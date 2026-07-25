"""Tk desktop lifecycle and main-thread queue dispatch."""

from __future__ import annotations

import queue
import platform
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional

from ... import __version__, core, i18n
from ..reporting import DEFAULT_REPORTING_SERVICE, ReportingService
from ..services import DEFAULT_DESKTOP_SERVICES, DesktopServices
from .conversion import TkConversionMixin
from .dialogs import DEFAULT_TK_DIALOGS, TkDialogs
from .inputs import TkInputMixin
from .layout import HAS_DND, TkLayoutMixin, TkinterDnD, drop_zone_text_key
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
        reporting: ReportingService = DEFAULT_REPORTING_SERVICE,
    ) -> None:
        self.root = root
        self.services = services
        self.dialogs = dialogs
        self.reporting = reporting
        self.lang = i18n.load_language()
        self.files = []  # type: list[Path]
        self.active_file = None  # type: Optional[Path]
        self._drop_zone_state = "empty"
        self._file_operation_controls = []  # type: list
        self.css_path = None  # type: Optional[str]
        self.output_dir = None  # type: Optional[str]
        self.operation = "idle"
        self._status_key = "status_ready"
        self._status_kwargs = {}  # type: dict
        self._close_requested = False
        self._close_dialog_open = False
        self._conversion_results = []  # type: list
        self._global_conversion_error = None  # type: Optional[str]
        self._preview_generation = 0
        self._preview_after = None
        self._preview_running = False
        self._preview_last_submitted = None  # type: Optional[int]
        self._preview_state = "empty"
        self._preview_error = None  # type: Optional[str]
        self._preview_page = 1
        self._preview_total_pages = 0
        self._preview_pages = {}  # type: dict[int, bytes]
        self._preview_page_pending = None
        self._preview_failed_page = None  # type: Optional[int]
        self._preview_active_request = None
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
        self.active_file_var = tk.StringVar()
        self.accordion_open = {
            "style": tk.BooleanVar(value=True),
            "destination": tk.BooleanVar(value=False),
            "header_footer": tk.BooleanVar(value=False),
            "other": tk.BooleanVar(value=False),
        }
        self.style_mode_var = tk.StringVar(value="theme")
        self._trusted_html_confirmed = False
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
            variable.trace_add("write", self._on_render_setting_changed)
        self.root.protocol("WM_DELETE_WINDOW", self._request_close)
        self.root.bind(
            "<<CustomTitlebarClose>>",
            lambda _event: self._request_close(),
            add="+",
        )
        self.browse_button.focus_set()

    def _set_lang(self, lang: str) -> None:
        self.lang = lang
        i18n.save_language(lang)
        self._retranslate()

    def _t(self, key: str, **kwargs) -> str:
        return i18n.t(key, self.lang, **kwargs)

    def _tp(
        self,
        one_key: str,
        many_key: str,
        count: int,
        **kwargs
    ) -> str:
        values = dict(kwargs)
        values["count"] = count
        return self._t(
            i18n.plural_key(one_key, many_key, count),
            **values
        )

    def automation_widget(self, action: str) -> object:
        """Return the semantic control used by stable UI automation."""
        try:
            return self._automation_widgets[action]
        except KeyError:
            raise ValueError("Unknown desktop automation action: {0}".format(action))

    def _set_status(self, key: str, **kwargs) -> None:
        self._status_key = key
        self._status_kwargs = kwargs
        self.status_label.config(
            text=self._translated_status(key, kwargs),
            style=status_label_style(key),
        )

    def _translated_status(self, key: str, kwargs: dict) -> str:
        if key == "status_ready" and self.files:
            return self._tp(
                "action_ready_one",
                "action_ready_many",
                len(self.files),
                destination=self._destination_summary(),
            )
        if key == "status_done_summary":
            return self._t(
                key,
                summary=self._format_result_summary(
                    kwargs["ok"], kwargs["failed"], kwargs["cancelled"]
                ),
            )
        if key == "files_add_summary":
            return self._t(
                key,
                summary=self._format_files_add_summary(
                    kwargs["added"],
                    kwargs["duplicates"],
                    kwargs["unsupported"],
                ),
            )
        return self._t(key, **kwargs)

    def _update_language_accessibility(self) -> None:
        for button, key in (
            (self.btn_en, "language_english_a11y"),
            (self.btn_fr, "language_french_a11y"),
        ):
            button.accessible_name = self._t(key)

    def _show_user_manual(self) -> None:
        manual_name = "MANUEL_FR.md" if self.lang == "fr" else "MANUAL_EN.md"
        manual_path = core.resource_path("docs/{0}".format(manual_name))
        try:
            self.services.open_path(manual_path)
        except Exception as exc:
            self.dialogs.show_error(
                self._t("error_title"),
                self._t("manual_open_error", error=str(exc)),
            )

    def _technical_information(self) -> str:
        system = " ".join(
            part for part in (platform.system(), platform.release()) if part
        )
        values = (
            ("technical_app_version", __version__),
            ("technical_render_profile", core.DEFAULT_PROFILE_VERSION),
            ("technical_playwright", core.PLAYWRIGHT_VERSION),
            ("technical_chromium", core.CHROMIUM_VERSION),
            ("technical_chromium_revision", core.CHROMIUM_REVISION),
            ("technical_python", platform.python_version()),
            ("technical_system", system or sys.platform),
            ("technical_architecture", platform.machine() or "unknown"),
        )
        return "\n".join(
            "{0}: {1}".format(self._t(label_key), value)
            for label_key, value in values
        )

    def _show_about(self) -> None:
        self.dialogs.show_about(
            self.root,
            self._t("about_action"),
            self._t("about_version", version=__version__),
            self._t("technical_information"),
            self._technical_information(),
            self._t("copy_technical_information"),
            self._t("technical_information_copied"),
            self._t("close_action"),
        )

    def _show_problem_report(
        self,
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        private_paths = tuple(self.files)

        def build_report(
            summary: str,
            steps: str,
            expected: str,
            include_diagnostics: bool,
        ) -> str:
            diagnostics = None
            if include_diagnostics:
                diagnostics = self.reporting.diagnostic_payload(
                    language=self.lang,
                    theme=self.theme_var.get(),
                    file_count=len(self.files),
                    has_drag_and_drop=HAS_DND,
                    error_code=error_code,
                    error_message=error_message,
                    private_paths=private_paths,
                )
            return self.reporting.build_report(
                language=self.lang,
                summary=summary,
                steps=steps,
                expected=expected,
                error_code=error_code,
                diagnostics=diagnostics,
            )

        keys = (
            "report_title",
            "report_summary",
            "report_summary_required",
            "report_steps",
            "report_expected",
            "report_error_code",
            "include_diagnostics",
            "diagnostics_consent",
            "report_local_help",
            "preview_report",
            "report_preview",
            "copy_report",
            "save_report",
            "open_support_channel",
            "support_not_configured",
            "report_copied",
            "report_saved",
            "report_copy_error",
            "report_save_error",
            "support_open_error",
            "report_text_filter",
            "report_save_title",
            "close_action",
        )
        self.dialogs.show_problem_report(
            self.root,
            labels={key: self._t(key) for key in keys},
            error_code=error_code,
            build_report=build_report,
            save_report=self.reporting.save_report,
            has_support_channel=self.reporting.has_support_channel,
            open_support_page=self.reporting.open_support_page,
        )

    def _retranslate(self) -> None:
        self.root.title(self._t("app_title"))
        header_keys = (
            "app_title",
            "app_version_compact",
            "help_menu",
            "keyboard_shortcuts_action",
            "manual_action",
            "report_issue_action",
            "about_action",
        )
        self.app_header.retranslate(
            {key: self._t(key) for key in header_keys},
            version=__version__,
            language=self.lang,
        )
        self._update_language_accessibility()
        self.source_group.config(text=self._t("files_heading"))
        self._drop_zone_text = self._t(drop_zone_text_key(HAS_DND))
        self._redraw_drop_zone()
        self.browse_button.config(text=self._t("add_files"))
        self.clear_files_button.config(text=self._t("clear_files"))
        self.theme_mode_radio.config(text=self._t("local_theme"))
        self.css_mode_radio.config(text=self._t("custom_css"))
        self.css_label.config(text=self._t("custom_css_label"))
        self.css_button.config(text=self._t("choose_css"))
        self.css_reset_button.config(text=self._t("return_to_theme"))
        self.tokens_hint_label.config(text=self._t("tokens_help"))
        self.header_group_label.config(text=self._t("header_label"))
        self.footer_group_label.config(text=self._t("footer_label"))
        for position_key, labels in self.hf_position_labels.items():
            for label in labels:
                label.config(text=self._t(position_key))
        self.reset_header_footer_button.config(
            text=self._t("reset_header_footer")
        )
        self.render_date_label.config(text=self._t("render_date"))
        self.trusted_html_check.config(text=self._t("trusted_html"))
        self.trusted_html_help_label.config(text=self._t("trusted_html_help"))
        self.preview_group.config(text=self._t("preview_heading"))
        self._update_preview_translations()
        self.output_button.config(text=self._t("change_destination"))
        self.output_reset_button.config(text=self._t("reset_destination"))
        self.cancel_button.config(text=self._t("cancel_button"))
        self.results_frame.config(text=self._t("results_heading"))
        self._refresh_generate_button()
        self._refresh_css_entry()
        self._refresh_output_entry()
        self._render_theme_cards()
        self._render_file_list()
        self._refresh_accordion_headers()
        self._refresh_preview_ui()
        self.status_label.config(
            text=self._translated_status(self._status_key, self._status_kwargs),
            style=status_label_style(self._status_key),
        )
        if self._conversion_results or self._global_conversion_error:
            self._render_results(
                self._conversion_results,
                global_error=self._global_conversion_error,
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
            if kind == "preview_document_ok":
                generation = message[1]
                is_latest_request = self._preview_active_request == (
                    "document", generation, 1
                )
                if is_latest_request:
                    self._preview_running = False
                if generation == self._preview_generation:
                    self._apply_preview_document(
                        message[2], message[3], message[4]
                    )
                    self._set_status("status_ready")
                if is_latest_request:
                    self._refresh_generate_button()
            elif kind in ("preview_page_ok", "preview_page_error"):
                generation = message[1]
                page = message[2]
                request = ("page", generation, page)
                is_latest_request = self._preview_active_request == request
                if is_latest_request:
                    self._preview_running = False
                    self._preview_page_pending = None
                if generation == self._preview_generation and is_latest_request:
                    if kind == "preview_page_ok":
                        self._apply_preview_page(page, message[3], message[4])
                        self._set_status("status_ready")
                    else:
                        self._set_preview_page_error(page, message[3])
                        self._set_status("status_preview_error", error=message[3])
                if is_latest_request:
                    self._refresh_generate_button()
            elif kind in ("preview_ok", "preview_error"):
                generation = message[1]
                active_request = getattr(self, "_preview_active_request", None)
                is_latest_request = (
                    active_request == ("document", generation, 1)
                    if active_request is not None
                    else generation == self._preview_last_submitted
                )
                if is_latest_request:
                    self._preview_running = False
                if generation == self._preview_generation:
                    if kind == "preview_ok":
                        self._apply_preview_image(message[2])
                        self._set_status("status_ready")
                    else:
                        self._set_preview_error(message[2])
                        self._set_status("status_preview_error", error=message[2])
                if is_latest_request:
                    self._refresh_generate_button()
            elif kind == "progress":
                _kind, index, total, result = message
                if not self._close_requested:
                    self._handle_conversion_progress(index, total, result)
            elif kind == "generate_done":
                if not self._close_requested:
                    self._handle_generate_done(message[1])
                self._finish_operation()
            elif kind == "generate_failed":
                if not self._close_requested:
                    self._handle_generate_failed(message[1])
                self._finish_operation()
        if self.operation != "idle" or self._preview_running:
            self._schedule_queue_poll()

    def _request_close(self) -> None:
        if self._close_requested or getattr(self, "_close_dialog_open", False):
            return
        if self.operation == "idle":
            self._close_requested = True
            responsive = getattr(self, "_responsive_controller", None)
            if responsive is not None:
                responsive.cancel()
            requests = getattr(self, "_preview_requests", None)
            if requests is not None:
                requests.put(None)
            self._invalidate_preview()
            if self._poll_after is not None:
                self.root.after_cancel(self._poll_after)
                self._poll_after = None
            self.root.destroy()
            return
        if self.operation == "generate":
            self._close_dialog_open = True
            try:
                choice = self.dialogs.ask_close_during_conversion(
                    self.root,
                    self._t("close_conversion_title"),
                    self._t("close_conversion_question"),
                    self._t("continue_conversion"),
                    self._t("cancel_conversion_and_close"),
                )
            finally:
                self._close_dialog_open = False
            if choice != "cancel_close":
                self.status_label.focus_set()
                return
            if self.operation == "idle":
                self._request_close()
                return
        self._close_requested = True
        responsive = getattr(self, "_responsive_controller", None)
        if responsive is not None:
            responsive.cancel()
        requests = getattr(self, "_preview_requests", None)
        if requests is not None:
            requests.put(None)
        self._preview_generation += 1
        if self.operation == "generate":
            if not self._cancel_event.is_set():
                self._cancel_event.set()
            self.cancel_button.config(state="disabled")
        self._set_status("status_closing")


def launch(services: DesktopServices = DEFAULT_DESKTOP_SERVICES) -> None:
    """Create the best available Tk root and run the desktop event loop."""
    root = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    LibreMarkPdfApp(root, services=services)
    root.mainloop()
