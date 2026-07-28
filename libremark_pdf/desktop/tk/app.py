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
        self._file_feedback_after = None
        self._file_conversion_states = {}  # type: dict[Path, Optional[str]]
        self.css_path = None  # type: Optional[str]
        self.output_dir = None  # type: Optional[str]
        self.operation = "idle"
        self._action_state = "idle"
        self._action_progress_current = 0
        self._action_progress_total = 0
        self._action_active_name = ""
        self._action_item_index = 1
        self._action_stage = "preparing"
        self._decision_plans = []
        self._decision_has_collisions = False
        self._decision_has_existing = False
        self._expected_kept_outputs = {}  # type: dict[Path, Path]
        self._conversion_options_summary = ""
        self._status_key = "status_ready"
        self._status_kwargs = {}  # type: dict
        self._close_requested = False
        self._close_dialog_open = False
        self._conversion_results = []  # type: list
        self._global_conversion_error = None  # type: Optional[str]
        self._active_compact_tab = "files"
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
        self._preview_source_path = None  # type: Optional[Path]
        self._preview_fit_mode = None  # type: Optional[str]
        self._preview_image_origin = (16.0, 16.0)
        self._poll_after = None
        self._cancel_event = threading.Event()
        self._cancel_current_event = threading.Event()
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
        # The unified settings dialog edits a temporary draft. Authoritative
        # render state changes only when the user selects Apply.
        self._settings_draft_css_path = self.css_path
        self._settings_draft_output_dir = self.output_dir
        self._settings_draft_style_mode_var = tk.StringVar(value="theme")
        self._settings_draft_theme_var = tk.StringVar(
            value=core.DEFAULT_THEME_ID
        )
        self._settings_draft_hf_vars = {
            key: tk.StringVar(value=variable.get())
            for key, variable in self.hf_vars.items()
        }
        self._settings_draft_render_date_var = tk.StringVar()
        self._settings_draft_trusted_html_var = tk.BooleanVar(value=False)
        self._style_theme_display_var = tk.StringVar()
        self._style_css_display_var = tk.StringVar()
        self._style_error_var = tk.StringVar()
        self._style_editor_open = False
        self._style_editor_preview_snapshot = None
        self._destination_mode_var = tk.StringVar(value="source")
        self._destination_path_var = tk.StringVar()
        self._destination_error_var = tk.StringVar()
        self._destination_editor_open = False
        self._header_footer_editor_open = False
        self._header_footer_editor_preview_snapshot = None
        self._advanced_error_var = tk.StringVar()
        self._advanced_editor_open = False
        self._advanced_editor_preview_snapshot = None
        self._operation_controls = []  # type: list
        self._theme_buttons = []  # type: list
        self._automation_widgets = {}  # type: dict[str, tk.Misc]

        self.ui_styles = install_ui_styles(self.root)
        self._build_ui()
        for variable in self._settings_draft_hf_vars.values():
            variable.trace_add("write", self._on_header_footer_draft_changed)
        self._settings_draft_render_date_var.trace_add(
            "write", self._on_advanced_date_changed
        )
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

    def _file_panel_labels(self) -> dict:
        keys = (
            "files_heading",
            "file_count_one",
            "file_count_many",
            "add_files",
            "drop_or_browse",
            "browse_without_dnd",
            "drop_active",
            "unsupported_drop",
            "active_preview_badge",
            "file_menu_a11y",
            "reveal_source",
            "copy_path",
            "remove_from_batch",
            "all_remove_action",
            "conversion_pending",
            "conversion_running",
            "conversion_ok",
            "conversion_error",
            "conversion_kept",
            "conversion_cancelled",
        )
        return {key: self._t(key) for key in keys}

    def _compact_tab_labels(self) -> dict:
        return {
            "files": self._t("compact_tab_files"),
            "preview": self._t("compact_tab_preview"),
            "settings": self._t("compact_tab_settings"),
            "results": self._t("compact_tab_results"),
        }

    def _preview_labels(self) -> dict:
        keys = (
            "preview_heading",
            "refresh_preview_a11y",
            "previous_page_a11y",
            "next_page_a11y",
            "zoom_out_a11y",
            "zoom_in_a11y",
            "fit_page",
            "fit_width",
            "preview_more_a11y",
            "preview_canvas_a11y",
            "preview_empty",
            "add_files",
            "preview_retry",
            "copy_details",
            "report_issue_action",
        )
        return {key: self._t(key) for key in keys}

    def _results_labels(self) -> dict:
        keys = (
            "results_heading",
            "results_empty",
            "result_file_heading",
            "result_status_heading",
            "result_output_heading",
            "result_actions_heading",
            "result_status_ok",
            "result_status_error",
            "result_status_kept",
            "result_status_cancelled",
            "result_output_value",
            "result_kept_summary",
            "result_cancelled_summary",
            "result_error_code",
            "show_details",
            "hide_details",
            "expand_results",
            "collapse_results",
            "clear_results",
            "batch_error",
            "open_pdf",
            "open_folder",
            "copy_details",
            "report_issue_action",
        )
        return {key: self._t(key) for key in keys}

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
        feedback_after = getattr(self, "_file_feedback_after", None)
        if feedback_after is not None and key not in (
            "files_add_summary",
            "files_added_one",
            "files_added_many",
        ):
            self.root.after_cancel(feedback_after)
            self._file_feedback_after = None
        self._status_key = key
        self._status_kwargs = kwargs
        self.status_label.config(
            text=self._translated_status(key, kwargs),
            style=status_label_style(key),
        )
        self._project_action_bar()

    def _set_action_state(
        self,
        state: str,
        *,
        progress_current: int = 0,
        progress_total: int = 0,
        active_name: str = "",
    ) -> None:
        """Store and project the visual state owned by the action bar."""
        self._action_state = state
        self._action_progress_current = progress_current
        self._action_progress_total = progress_total
        self._action_active_name = active_name
        self._project_action_bar()

    def _project_action_bar(self) -> None:
        action_bar = getattr(self, "action_bar", None)
        if action_bar is None:
            return
        count = len(self.files)
        state = getattr(self, "_action_state", "idle")
        generate_text = self._tp("generate_one", "generate_many", count)
        disabled_reason = ""
        if state == "idle" and not self.files:
            disabled_reason = self._t("action_blocked_no_files")
        elif state == "validating":
            disabled_reason = self._t("action_blocked_validating")
        progress_total = getattr(self, "_action_progress_total", 0)
        progress_current = getattr(self, "_action_progress_current", 0)
        progress_percent = (
            int(progress_current * 100 / progress_total)
            if progress_total else 0
        )
        progress_text = (
            self._t(
                "action_progress_completed",
                current=progress_current,
                total=progress_total,
                percent=progress_percent,
            )
            if state in ("running", "cancel_requested")
            else ""
        )
        running = state in ("running", "cancel_requested")
        batch_text = (
            self._tp(
                "action_running_one", "action_running_many", count,
                destination=self._destination_summary(),
            )
            if running else ""
        )
        if state == "running":
            active_text = self._t(
                "action_active_stage",
                current=min(
                    getattr(self, "_action_item_index", progress_current + 1),
                    progress_total,
                ),
                total=progress_total,
                name=getattr(self, "_action_active_name", ""),
                stage=self._t(
                    "conversion_stage_{0}".format(
                        getattr(self, "_action_stage", "preparing")
                    )
                ),
            )
        elif state == "cancel_requested":
            active_text = self._translated_status(
                self._status_key, self._status_kwargs
            )
        else:
            active_text = ""
        decision_plans = getattr(self, "_decision_plans", [])
        collision_count = sum(
            plan.error_code != "OUTPUT_EXISTS" for plan in decision_plans
        )
        existing_count = sum(
            plan.error_code == "OUTPUT_EXISTS" for plan in decision_plans
        )
        decision_summary = " · ".join(
            part for part in (
                self._tp(
                    "decision_existing_one", "decision_existing_many",
                    existing_count,
                ) if existing_count else "",
                self._tp(
                    "decision_conflict_one", "decision_conflict_many",
                    collision_count,
                ) if collision_count else "",
            ) if part
        )
        issue_keys = {
            "DUPLICATE_OUTPUT": "decision_issue_duplicate",
            "INPUT_OUTPUT_COLLISION": "decision_issue_same_path",
            "INPUT_NOT_FOUND": "decision_issue_missing_input",
            "OUTPUT_EXISTS": "decision_issue_existing",
        }
        decision_rows = tuple(
            (
                str(plan.input_path),
                str(plan.output_path),
                self._t(issue_keys.get(plan.error_code, "decision_issue_other")),
                plan.error_code == "OUTPUT_EXISTS",
            )
            for plan in decision_plans
        )
        action_bar.set_state(
            state,
            status_text=self._translated_status(
                self._status_key, self._status_kwargs
            ),
            generate_text=generate_text,
            generate_enabled=(
                bool(self.files)
                and self.operation == "idle"
                and state not in ("validating", "running", "cancel_requested")
            ),
            disabled_reason=disabled_reason,
            progress_current=progress_current,
            progress_total=progress_total,
            progress_text=progress_text,
            cancel_text=self._t("stop_after_current"),
            cancel_enabled=(
                state == "running" and not self._cancel_event.is_set()
            ),
            cancel_now_text=self._t("cancel_now"),
            cancel_now_enabled=(
                state in ("running", "cancel_requested")
                and not self._cancel_current_event.is_set()
            ),
            batch_text=batch_text,
            active_text=active_text,
            options_text=self._t("applied_options"),
            options_summary=getattr(self, "_conversion_options_summary", ""),
            decision_title=self._t("decision_required_title"),
            decision_message=decision_summary,
            decision_rows=decision_rows,
            decision_has_existing=self._decision_has_existing,
            decision_instruction=self._t(
                "decision_replace_instruction"
                if existing_count else "decision_blocked_instruction"
            ),
            decision_source_heading=self._t("decision_source_heading"),
            decision_destination_heading=self._t(
                "decision_destination_heading"
            ),
            decision_issue_heading=self._t("decision_issue_heading"),
            decision_replace_heading=self._t("decision_replace_heading"),
            decision_blocked_text=self._t("decision_blocked"),
            decision_replace_help=self._t("decision_replace_help"),
            decision_blocked_help=self._t("decision_blocked_help"),
            decision_replaced_one=self._t("decision_replaced_one"),
            decision_replaced_many=self._t("decision_replaced_many"),
            decision_kept_one=self._t("decision_kept_one"),
            decision_kept_many=self._t("decision_kept_many"),
            continue_text=self._t("continue_generation"),
            back_text=self._t("back_action"),
        )
        action_bar.status_label.configure(
            style=status_label_style(self._status_key)
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
                    kwargs["ok"], kwargs["failed"], kwargs["cancelled"],
                    kwargs.get("kept", 0),
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
        values = [
            ("technical_app_version", __version__),
            ("technical_render_profile", core.DEFAULT_PROFILE_VERSION),
            ("technical_playwright", core.PLAYWRIGHT_VERSION),
            ("technical_chromium", core.CHROMIUM_VERSION),
            ("technical_chromium_revision", core.CHROMIUM_REVISION),
            ("technical_python", platform.python_version()),
            ("technical_system", system or sys.platform),
            ("technical_architecture", platform.machine() or "unknown"),
        ]
        execution_mode = self._execution_mode()
        if execution_mode is not None:
            values.append(("technical_execution_mode", execution_mode))
        return "\n".join(
            "{0}: {1}".format(self._t(label_key), value)
            for label_key, value in values
        )

    def _execution_mode(self) -> Optional[str]:
        """Return source/artifact mode only when the runtime proves it."""
        if getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None):
            return self._t("execution_mode_artifact")
        source_root = Path(__file__).resolve().parents[3]
        if (source_root / "pyproject.toml").is_file():
            return self._t("execution_mode_source")
        return None

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
            self._t("about_local_conversion"),
            self._t("about_no_network"),
        )

    def _show_problem_report(
        self,
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        path_aliases = {}
        source_folder_index = 0
        for index, source_path in enumerate(self.files, start=1):
            source = Path(source_path)
            path_aliases[source] = "<source-{0}{1}>".format(
                index, source.suffix.lower()
            )
            if (
                str(source.parent) not in ("", ".")
                and source.parent not in path_aliases
            ):
                source_folder_index += 1
                suffix = "" if source_folder_index == 1 else "-{0}".format(
                    source_folder_index
                )
                path_aliases[source.parent] = "<source-folder{0}>".format(suffix)
        if getattr(self, "output_dir", None):
            path_aliases[Path(self.output_dir)] = "<output-folder>"
        if getattr(self, "css_path", None):
            path_aliases[Path(self.css_path)] = "<custom-css>"
        private_paths = tuple(path_aliases)

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
                    path_aliases=path_aliases,
                )
            return self.reporting.build_report(
                language=self.lang,
                summary=summary,
                steps=steps,
                expected=expected,
                error_code=error_code,
                error_context=error_message,
                diagnostics=diagnostics,
                private_paths=private_paths,
                path_aliases=path_aliases,
            )

        keys = (
            "report_title",
            "report_intro",
            "report_summary",
            "report_summary_placeholder",
            "report_summary_required",
            "report_steps",
            "report_expected",
            "report_error_code",
            "report_error_context",
            "include_diagnostics",
            "diagnostics_consent",
            "report_local_help",
            "preview_report",
            "report_preview",
            "report_preview_help",
            "report_preview_expand",
            "report_preview_collapse",
            "report_preview_edited",
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
            sanitize_report=lambda text: self.reporting.sanitize_report(
                text, private_paths, path_aliases
            ),
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
            "language_menu",
            "compact_menu_a11y",
            "version_information",
        )
        self.app_header.retranslate(
            {key: self._t(key) for key in header_keys},
            version=__version__,
            language=self.lang,
        )
        self._update_language_accessibility()
        self.compact_tabs.retranslate(self._compact_tab_labels())
        self._drop_zone_text = self._t(drop_zone_text_key(HAS_DND))
        self.files_panel.retranslate(self._file_panel_labels())
        self.theme_mode_radio.config(text=self._t("local_theme"))
        self.css_mode_radio.config(text=self._t("custom_css"))
        self.css_label.config(text=self._t("custom_css_label"))
        self.css_button.config(text=self._t("choose_css"))
        self.css_reset_button.config(text=self._t("return_to_theme"))
        self._refresh_style_editors()
        self._refresh_destination_editors()
        self._refresh_header_footer_editors()
        self._refresh_advanced_editors()
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
        settings_labels = self._settings_summary_labels()
        self._settings_dialog["window"].title(
            self._t("settings_dialog_title")
        )
        self._settings_dialog["title"].configure(
            text=self._t("settings_dialog_title")
        )
        self._settings_dialog["description"].configure(
            text=self._t("settings_dialog_description")
        )
        for name, title in self._settings_dialog["section_titles"].items():
            title.configure(text=settings_labels[name])
        self._settings_dialog["apply"].config(text=self._t("apply_settings"))
        self._settings_dialog["cancel"].config(text=self._t("cancel_settings"))
        self.preview_group.retranslate(self._preview_labels())
        self._update_preview_translations()
        self.output_button.config(text=self._t("change_destination"))
        self.output_reset_button.config(text=self._t("reset_destination"))
        self.cancel_button.config(text=self._t("stop_after_current"))
        self.results_view.retranslate(self._results_labels())
        self._refresh_generate_button(preserve_action_state=True)
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
        self._project_action_bar()
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
            elif kind == "conversion_stage":
                _kind, index, total, input_path, stage = message
                if not self._close_requested:
                    self._handle_conversion_stage(
                        index, total, input_path, stage
                    )
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
            if getattr(self, "_file_feedback_after", None) is not None:
                self.root.after_cancel(self._file_feedback_after)
                self._file_feedback_after = None
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
