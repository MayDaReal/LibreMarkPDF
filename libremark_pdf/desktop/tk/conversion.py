"""Batch conversion interaction for the Tk desktop adapter."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from typing import Optional

from ... import core


class TkConversionMixin:
    """Manage conversion preflight, progress, cancellation, and results."""

    def _refresh_generate_button(self, preserve_action_state: bool = False) -> None:
        count = len(self.files)
        self.generate_button.config(
            text=self._tp("generate_one", "generate_many", count),
            state=(
                "normal"
                if self.files
                and self.operation == "idle"
                else "disabled"
            ),
        )
        if hasattr(self, "_action_state") and self.operation == "idle":
            terminal = self._action_state in ("complete", "failed")
            if not (preserve_action_state and terminal):
                self._action_state = "ready" if self.files else "idle"
            self._project_action_bar()

    def _preflight_decisions(self) -> tuple:
        plans = core.plan_batch_outputs(self.files, self.output_dir, overwrite=False)
        collisions = [
            plan for plan in plans
            if plan.error and not plan.error.startswith("OUTPUT_EXISTS:")
        ]
        existing = [plan for plan in plans if plan.error_code == "OUTPUT_EXISTS"]
        return plans, collisions, existing

    def _on_generate_clicked(self) -> None:
        if self.operation != "idle":
            return
        if not self.files:
            self.dialogs.show_error(
                self._t("error_title"), self._t("error_no_files")
            )
            return
        self._begin_operation("validate")
        self._set_action_state(
            "validating",
            progress_total=len(self.files),
            active_name=self.files[0].name,
        )
        self._set_status("status_validating")
        self.root.update_idletasks()
        try:
            plans, collisions, existing = self._preflight_decisions()
        except Exception as exc:
            self._finish_operation()
            self._set_action_state("failed")
            self._set_status("status_generation_error", error=str(exc))
            return
        if collisions or existing:
            self._decision_plans = existing + collisions
            self._decision_has_collisions = bool(collisions)
            self._decision_has_existing = bool(existing)
            if hasattr(self, "action_bar"):
                self.action_bar.clear_decision_choices()
            self._begin_operation("decision")
            self._set_action_state("decision_required")
            return
        self._expected_kept_outputs = {}
        self._start_generation(False)

    def _continue_generation_decision(self) -> None:
        if self.operation != "decision":
            return
        overwrite_targets = self.action_bar.selected_overwrite_targets()
        selected = {Path(str(path)) for path in overwrite_targets}
        self._expected_kept_outputs = {
            plan.input_path: plan.output_path
            for plan in getattr(self, "_decision_plans", [])
            if plan.error_code == "OUTPUT_EXISTS"
            and plan.output_path not in selected
        }
        self._start_generation(False, overwrite_targets=overwrite_targets)

    def _cancel_generation_decision(self) -> None:
        if self.operation != "decision":
            return
        self._decision_plans = []
        self._decision_has_collisions = False
        self._decision_has_existing = False
        self._expected_kept_outputs = {}
        if hasattr(self, "action_bar"):
            self.action_bar.clear_decision_choices()
        self._finish_operation()
        self._set_action_state("ready")
        self._set_status("status_cancelled")

    def _applied_options_summary(self) -> str:
        summaries = self._settings_summaries()
        header_footer = self._current_header_footer()
        slots = (
            ("header_left_summary", header_footer.top_left),
            ("header_center_summary", header_footer.top_center),
            ("header_right_summary", header_footer.top_right),
            ("footer_left_summary", header_footer.bottom_left),
            ("footer_center_summary", header_footer.bottom_center),
            ("footer_right_summary", header_footer.bottom_right),
        )
        return "\n".join((
            "{0}: {1}".format(self._t("style_heading"), summaries["style"]),
            "{0}: {1}".format(
                self._t("destination_heading"), self._destination_summary()
            ),
            *(self._t(key, value=value or "—") for key, value in slots),
            "{0}: {1}".format(
                self._t("advanced_options_heading"), summaries["other"]
            ),
        ))

    def _start_generation(
        self, overwrite: bool, overwrite_targets: tuple = ()
    ) -> None:
        self._invalidate_preview()
        options = self._render_options()
        try:
            profile = core.render_profile_for_options(**options)
        except Exception as exc:
            self._finish_operation()
            self._set_action_state("failed")
            self._set_status("status_generation_error", error=str(exc))
            return
        options["render_date"] = profile.render_date
        options["output_dir"] = self.output_dir
        options["overwrite"] = overwrite
        options["overwrite_targets"] = overwrite_targets
        self._conversion_options_summary = self._applied_options_summary()
        self._action_item_index = 1
        self._action_stage = "preparing"
        files = list(self.files)
        self._cancel_event = threading.Event()
        self._cancel_current_event = threading.Event()
        self.progress.configure(maximum=max(1, len(files)))
        self.progress_var.set(0)
        self._clear_results()
        self._begin_operation("generate")
        self._set_action_state(
            "running",
            progress_current=0,
            progress_total=len(files),
            active_name=files[0].name,
        )
        self._set_status(
            "status_generating_file",
            current=1,
            total=len(files),
            name=files[0].name,
        )
        threading.Thread(
            target=self.services.run_conversion_job,
            args=(
                self._result_queue,
                files,
                options,
                self._cancel_event,
                self._cancel_current_event,
            ),
            daemon=True,
        ).start()
        self._schedule_queue_poll()

    def _cancel_conversion(self) -> None:
        if self.operation == "generate" and not self._cancel_event.is_set():
            self._cancel_event.set()
            self.cancel_button.config(state="disabled")
            self._set_action_state(
                "cancel_requested",
                progress_current=self._action_progress_current,
                progress_total=self._action_progress_total,
                active_name=self._action_active_name,
            )
            self._set_status(
                "status_cancelling_file",
                name=self._action_active_name,
            )

    def _cancel_conversion_now(self) -> None:
        if (
            self.operation == "generate"
            and not self._cancel_current_event.is_set()
        ):
            self._cancel_current_event.set()
            self.cancel_now_button.config(state="disabled")
            self._set_action_state(
                "cancel_requested",
                progress_current=self._action_progress_current,
                progress_total=self._action_progress_total,
                active_name=self._action_active_name,
            )
            self._set_status("status_cancelling_now")

    def _begin_operation(self, operation: str) -> None:
        self.operation = operation
        results_view = getattr(self, "results_view", None)
        if results_view is not None:
            results_view.set_conversion_active(True)
        for widget in self._operation_controls:
            try:
                widget.config(state="disabled")
            except tk.TclError:
                pass
        for card in self._theme_buttons:
            card.config(state="disabled")
        self.generate_button.config(state="disabled")
        self.cancel_button.config(
            state="normal" if operation == "generate" else "disabled"
        )
        files_panel = getattr(self, "files_panel", None)
        if files_panel is not None:
            files_panel.set_interaction_enabled(
                mutation_enabled=False,
                selection_enabled=operation in ("decision", "generate"),
                reason=self._t("file_mutation_disabled"),
            )
        settings_panel = getattr(self, "settings_panel", None)
        if settings_panel is not None:
            settings_panel.set_enabled(False)
        if operation == "generate":
            self._file_conversion_states = {
                path: "pending" for path in self.files
            }
            if self.files:
                self._file_conversion_states[self.files[0]] = "running"
            self._refresh_file_conversion_states()

    def _finish_operation(self) -> None:
        self.operation = "idle"
        if self._close_requested:
            self.root.destroy()
            return
        for widget in self._operation_controls:
            try:
                widget.config(state="normal")
            except tk.TclError:
                pass
        self.css_entry.config(state="readonly")
        self.output_entry.config(state="readonly")
        self.cancel_button.config(state="disabled")
        cancel_now_button = getattr(self, "cancel_now_button", None)
        if cancel_now_button is not None:
            cancel_now_button.config(state="disabled")
        self._render_theme_cards()
        files_panel = getattr(self, "files_panel", None)
        if files_panel is not None:
            files_panel.set_interaction_enabled(
                mutation_enabled=True,
                selection_enabled=True,
            )
        settings_panel = getattr(self, "settings_panel", None)
        if settings_panel is not None:
            settings_panel.set_enabled(True)
        self._update_zoom_controls()
        self._update_page_controls()
        results_view = getattr(self, "results_view", None)
        if results_view is not None:
            results_view.set_conversion_active(False)
        self._refresh_generate_button(preserve_action_state=True)

    def _handle_generate_done(self, results: list) -> None:
        results = [self._project_expected_kept_result(item) for item in results]
        ok = [item for item in results if item["status"] == "ok"]
        failed = [item for item in results if item["status"] == "error"]
        kept = [item for item in results if item["status"] == "kept"]
        cancelled = [item for item in results if item["status"] == "cancelled"]
        self._render_results(results)
        self._file_conversion_states = {
            Path(item["input"]): item["status"] for item in results
        }
        self._refresh_file_conversion_states()
        self._set_status(
            "status_done_summary",
            ok=len(ok),
            failed=len(failed),
            kept=len(kept),
            cancelled=len(cancelled),
        )
        self._set_action_state("complete")
        if failed:
            self._reveal_terminal_results(str(failed[0]["input"]))

    def _handle_conversion_progress(
        self, index: int, total: int, result: dict
    ) -> None:
        result = self._project_expected_kept_result(result)
        self.progress_var.set(index)
        self._conversion_results.append(result)
        if not hasattr(self, "_file_conversion_states"):
            self._file_conversion_states = {}
        self._file_conversion_states[Path(result["input"])] = result["status"]
        files = getattr(self, "files", [])
        cancel_current_event = getattr(self, "_cancel_current_event", None)
        cancellation_requested = self._cancel_event.is_set() or (
            cancel_current_event is not None and cancel_current_event.is_set()
        )
        if index < len(files) and not cancellation_requested:
            self._file_conversion_states[files[index]] = "running"
        self._refresh_file_conversion_states()
        self._render_results(self._conversion_results)
        files = getattr(self, "files", [])
        if cancellation_requested:
            active_name = (
                getattr(self, "_action_active_name", "")
                or Path(result["input"]).name
            )
            self._set_action_state(
                "cancel_requested",
                progress_current=index,
                progress_total=total,
                active_name=active_name,
            )
            self._set_status("status_cancelling_file", name=active_name)
        else:
            active_name = (
                files[index].name
                if index < len(files)
                else Path(result["input"]).name
            )
            item = min(index + 1, total)
            self._action_item_index = item
            self._set_action_state(
                "running",
                progress_current=index,
                progress_total=total,
                active_name=active_name,
            )
            self._set_status(
                "status_generating_file",
                current=item,
                total=total,
                name=active_name,
            )

    def _project_expected_kept_result(self, result: dict) -> dict:
        """Classify only an explicitly declined replacement as kept."""
        if (
            result.get("status") != "error"
            or result.get("error_code") != "OUTPUT_EXISTS"
        ):
            return result
        source = Path(str(result.get("input") or ""))
        output = getattr(self, "_expected_kept_outputs", {}).get(source)
        if output is None:
            return result
        projected = dict(result)
        projected.update({
            "output": str(output),
            "status": "kept",
            "error": None,
            "error_code": None,
            "kept_reason": "OUTPUT_EXISTS",
        })
        return projected

    def _handle_conversion_stage(
        self, index: int, total: int, input_path: Path, stage: str
    ) -> None:
        if self.operation != "generate":
            return
        self._action_item_index = index
        self._action_stage = stage
        self._set_action_state(
            "cancel_requested"
            if self._cancel_event.is_set() or self._cancel_current_event.is_set()
            else "running",
            progress_current=len(getattr(self, "_conversion_results", [])),
            progress_total=total,
            active_name=input_path.name,
        )
        if not self._cancel_event.is_set() and not self._cancel_current_event.is_set():
            self._set_status(
                "status_generating_file",
                current=index,
                total=total,
                name=input_path.name,
            )

    def _handle_generate_failed(self, error: str) -> None:
        self._global_conversion_error = error
        self._file_conversion_states = {
            path: (
                "error" if status == "running" else "cancelled"
                if status == "pending" else status
            )
            for path, status in getattr(
                self, "_file_conversion_states", {}
            ).items()
        }
        self._refresh_file_conversion_states()
        self._render_results(
            self._conversion_results,
            global_error=error,
        )
        self._set_status("status_generation_error", error=error)
        self._set_action_state("failed")
        self._reveal_terminal_results()

    def _refresh_file_conversion_states(self) -> None:
        files_panel = getattr(self, "files_panel", None)
        if files_panel is not None:
            files_panel.set_conversion_states(
                getattr(self, "_file_conversion_states", {})
            )

    def _clear_results(self) -> None:
        self._conversion_results = []
        self._global_conversion_error = None
        results_view = getattr(self, "results_view", None)
        if results_view is not None:
            results_view.set_results([], "")

    def _clear_results_from_ui(self) -> None:
        """Clear result UI only while idle and leave produced PDFs untouched."""
        if self.operation != "idle":
            return
        self._clear_results()
        self._file_conversion_states = {}
        self._refresh_file_conversion_states()
        self._set_status("status_ready")
        self._set_action_state("ready" if self.files else "idle")

    def _refresh_results_projection(self) -> None:
        """Rebuild the responsive projection from authoritative app state."""
        self._render_results(
            getattr(self, "_conversion_results", []),
            global_error=getattr(self, "_global_conversion_error", None),
        )

    def _render_results(
        self,
        results: list,
        global_error: Optional[str] = None,
    ) -> None:
        self._conversion_results = list(results)
        self._global_conversion_error = global_error
        ok = sum(item["status"] == "ok" for item in results)
        failed = sum(item["status"] == "error" for item in results)
        kept = sum(item["status"] == "kept" for item in results)
        cancelled = sum(item["status"] == "cancelled" for item in results)
        summary = (
            self._format_result_summary(ok, failed, cancelled, kept)
            if results else ""
        )
        self.results_view.set_results(
            results,
            summary,
            global_error=global_error,
        )

    def _format_result_summary(
        self, ok: int, failed: int, cancelled: int, kept: int = 0
    ) -> str:
        return " · ".join((
            self._tp(
                "summary_succeeded_one", "summary_succeeded_many", ok
            ),
            self._tp("summary_failed_one", "summary_failed_many", failed),
            self._tp("summary_kept_one", "summary_kept_many", kept),
            self._tp(
                "summary_cancelled_one", "summary_cancelled_many", cancelled
            ),
        ))

    def _reveal_terminal_results(
        self, source_id: Optional[str] = None
    ) -> None:
        """Reveal and focus results only for a terminal batch failure."""
        if self._layout_mode == "compact":
            self._select_compact_tab("results")
        else:
            self.results_view.set_collapsed(False)
        if source_id is not None:
            self.results_view.focus_result(source_id)
        else:
            self.results_view.focus_results()

    def _copy_result_details(self, result: dict) -> None:
        details = "{0}: [{1}] {2}".format(
            result["input"],
            result.get("error_code") or "UNKNOWN",
            result.get("error") or "",
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(details)
        self._set_status("status_details_copied")

    def _open_result(self, path: Path) -> None:
        try:
            self.services.open_path(path)
        except Exception as exc:
            self.dialogs.show_error(
                self._t("error_title"),
                self._t("open_error", error=str(exc)),
            )
