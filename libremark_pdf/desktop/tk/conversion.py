"""Batch conversion interaction for the Tk desktop adapter."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional

from ... import core


class TkConversionMixin:
    """Manage conversion preflight, progress, cancellation, and results."""

    def _refresh_generate_button(self) -> None:
        self.generate_button.config(
            text=self._t("generate_button", count=len(self.files)),
            state=(
                "normal"
                if self.files
                and self.operation == "idle"
                else "disabled"
            ),
        )

    def _overwrite_choice(self) -> Optional[bool]:
        plans = core.plan_batch_outputs(self.files, self.output_dir, overwrite=False)
        collisions = [
            plan for plan in plans
            if plan.error and not plan.error.startswith("OUTPUT_EXISTS:")
        ]
        if collisions:
            details = "\n".join(
                "{0}: {1}".format(plan.input_path.name, plan.error)
                for plan in collisions
            )
            if not self.dialogs.ask_collision_continue(
                self.root,
                self._t("collision_title"),
                self._t("collision_continue", details=details),
                self._t("continue_with_others"),
                self._t("cancel_button_short"),
            ):
                return None
        existing = [plan for plan in plans if plan.error_code == "OUTPUT_EXISTS"]
        if not existing:
            return False
        return self.dialogs.ask_overwrite(
            self.root,
            self._t("overwrite_title"),
            self._t("overwrite_question", count=len(existing)),
            self._t("replace_after_success"),
            self._t("keep_and_report"),
            self._t("cancel_button_short"),
        )

    def _on_generate_clicked(self) -> None:
        if self.operation != "idle":
            return
        if not self.files:
            self.dialogs.show_error(
                self._t("error_title"), self._t("error_no_files")
            )
            return
        overwrite = self._overwrite_choice()
        if overwrite is None:
            self._set_status("status_cancelled")
            return
        self._invalidate_preview()
        options = self._render_options()
        try:
            profile = core.render_profile_for_options(**options)
        except Exception as exc:
            self.dialogs.show_error(self._t("error_title"), str(exc))
            self._set_status("status_generation_error", error=str(exc))
            return
        options["render_date"] = profile.render_date
        options["output_dir"] = self.output_dir
        options["overwrite"] = overwrite
        files = list(self.files)
        self._cancel_event = threading.Event()
        self.progress.configure(maximum=max(1, len(files)))
        self.progress_var.set(0)
        self._clear_results()
        self._begin_operation("generate")
        self._set_status("status_generating_progress", current=0, total=len(files))
        threading.Thread(
            target=self.services.run_conversion_job,
            args=(self._result_queue, files, options, self._cancel_event),
            daemon=True,
        ).start()
        self._schedule_queue_poll()

    def _cancel_conversion(self) -> None:
        if self.operation == "generate" and not self._cancel_event.is_set():
            self._cancel_event.set()
            self.cancel_button.config(state="disabled")
            self._set_status("status_cancelling")

    def _begin_operation(self, operation: str) -> None:
        self.operation = operation
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
        self._render_theme_cards()
        self._update_zoom_controls()
        self._update_page_controls()
        self._refresh_generate_button()

    def _handle_generate_done(self, results: list) -> None:
        ok = [item for item in results if item["status"] == "ok"]
        failed = [item for item in results if item["status"] == "error"]
        cancelled = [item for item in results if item["status"] == "cancelled"]
        self._render_results(results)
        self._set_status(
            "status_done_summary",
            ok=len(ok),
            failed=len(failed),
            cancelled=len(cancelled),
        )
        self.results_summary_label.focus_set()

    def _handle_conversion_progress(
        self, index: int, total: int, result: dict
    ) -> None:
        self.progress_var.set(index)
        self._conversion_results.append(result)
        self._render_results(self._conversion_results)
        if self._cancel_event.is_set():
            self._set_status("status_cancelling")
        else:
            self._set_status(
                "status_generating_file",
                current=index,
                total=total,
                name=Path(result["input"]).name,
            )

    def _handle_generate_failed(self, error: str) -> None:
        self._global_conversion_error = error
        self._render_results(
            self._conversion_results,
            global_error=error,
        )
        self._set_status("status_generation_error", error=error)
        self.results_summary_label.focus_set()

    def _clear_results(self) -> None:
        self._conversion_results = []
        self._global_conversion_error = None
        self.results_summary_label.config(text="")
        self.results_error_label.pack_forget()
        for child in self.result_rows_frame.winfo_children():
            child.destroy()

    def _render_results(
        self,
        results: list,
        global_error: Optional[str] = None,
    ) -> None:
        self._conversion_results = list(results)
        self._global_conversion_error = global_error
        for child in self.result_rows_frame.winfo_children():
            child.destroy()
        ok = sum(item["status"] == "ok" for item in results)
        failed = sum(item["status"] == "error" for item in results)
        cancelled = sum(item["status"] == "cancelled" for item in results)
        if results:
            self.results_summary_label.config(text=self._t(
                "results_count_summary",
                ok=ok,
                failed=failed,
                cancelled=cancelled,
            ))
        else:
            self.results_summary_label.config(text="")
        if global_error:
            self.results_error_label.config(
                text="{0}: {1}".format(self._t("batch_error"), global_error)
            )
            self.results_error_label.pack(fill="x", pady=(4, 0))
        else:
            self.results_error_label.pack_forget()
        for result in results:
            self._render_result_row(result)

    def _render_result_row(self, result: dict) -> None:
        source = Path(result["input"])
        row = ttk.LabelFrame(
            self.result_rows_frame,
            text=source.name,
            padding=6,
        )
        row.pack(fill="x", pady=2)
        status = result["status"]
        status_text = {
            "ok": "✓ {0}".format(self._t("result_status_ok")),
            "error": "! {0}".format(self._t("result_status_error")),
            "cancelled": "– {0}".format(self._t("result_status_cancelled")),
        }[status]
        ttk.Label(row, text=status_text, anchor="w").pack(fill="x")
        if status == "ok":
            output = Path(result["output"])
            ttk.Label(row, text=str(output), anchor="w").pack(fill="x")
            actions = ttk.Frame(row)
            actions.pack(fill="x", pady=(4, 0))
            ttk.Button(
                actions,
                text=self._t("open_pdf"),
                command=lambda path=output: self._open_result(path),
            ).pack(side="right")
            ttk.Button(
                actions,
                text=self._t("open_folder"),
                command=lambda path=output.parent: self._open_result(path),
            ).pack(side="right", padx=4)
        elif status == "error":
            ttk.Label(
                row,
                text=str(result.get("error") or ""),
                anchor="w",
                wraplength=440,
            ).pack(fill="x")
            details = ttk.Frame(row)
            ttk.Label(
                details,
                text=self._t(
                    "result_error_code",
                    code=result.get("error_code") or "UNKNOWN",
                ),
                anchor="w",
            ).pack(fill="x")
            actions = ttk.Frame(row)
            actions.pack(fill="x", pady=(4, 0))
            toggle = ttk.Button(actions)

            def toggle_details() -> None:
                if details.winfo_manager():
                    details.pack_forget()
                    toggle.config(text=self._t("show_details"))
                else:
                    details.pack(fill="x", pady=(4, 0), before=actions)
                    toggle.config(text=self._t("hide_details"))

            toggle.config(
                text=self._t("show_details"),
                command=toggle_details,
            )
            toggle.pack(side="left")
            ttk.Button(
                actions,
                text=self._t("copy_details"),
                command=lambda item=result: self._copy_result_details(item),
            ).pack(side="left", padx=4)

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
