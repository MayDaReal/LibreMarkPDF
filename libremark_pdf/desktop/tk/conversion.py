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
                and not self._preview_running
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
                self._t("collision_title"),
                self._t("collision_continue", details=details),
            ):
                return None
        existing = [plan for plan in plans if plan.error_code == "OUTPUT_EXISTS"]
        if not existing:
            return False
        return self.dialogs.ask_overwrite(
            self._t("overwrite_title"),
            self._t("overwrite_question", count=len(existing)),
        )

    def _on_generate_clicked(self) -> None:
        if self.operation != "idle" or self._preview_running:
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
        self._refresh_generate_button()

    def _handle_generate_done(self, results: list) -> None:
        ok = [item for item in results if item["status"] == "ok"]
        failed = [item for item in results if item["status"] == "error"]
        cancelled = [item for item in results if item["status"] == "cancelled"]
        self._render_results(ok)
        self._set_status(
            "status_done_summary",
            ok=len(ok),
            failed=len(failed),
            cancelled=len(cancelled),
        )
        if failed:
            details = "\n".join(
                "{0}: [{1}] {2}".format(
                    item["input"], item["error_code"], item["error"]
                )
                for item in failed
            )
            self.dialogs.show_error(self._t("error_title"), details)

    def _clear_results(self) -> None:
        for child in self.results_frame.winfo_children():
            child.destroy()

    def _render_results(self, successful: list) -> None:
        self._clear_results()
        for result in successful:
            output = Path(result["output"])
            row = ttk.Frame(self.results_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=str(output), anchor="w").pack(
                side="left", fill="x", expand=True
            )
            ttk.Button(
                row,
                text=self._t("open_pdf"),
                command=lambda path=output: self._open_result(path),
            ).pack(side="right")
            ttk.Button(
                row,
                text=self._t("open_folder"),
                command=lambda path=output.parent: self._open_result(path),
            ).pack(side="right", padx=4)

    def _open_result(self, path: Path) -> None:
        try:
            self.services.open_path(path)
        except Exception as exc:
            self.dialogs.show_error(
                self._t("error_title"),
                self._t("open_error", error=str(exc)),
            )
