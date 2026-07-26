"""Fixed modern action bar and non-modal conversion progress states."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from ..components import PrimaryButton, SecondaryButton, Tooltip
from ..theme import COLORS, SPACING, SystemFontResolver


ACTION_BAR_STATES = frozenset((
    "idle",
    "ready",
    "validating",
    "decision_required",
    "running",
    "cancel_requested",
    "complete",
    "failed",
))


class ShellStatusLabel(ctk.CTkLabel):
    """Accept legacy status updates while rendering modern semantic colors."""

    def configure(self, require_redraw=False, **kwargs):
        style = kwargs.pop("style", "")
        if "Error" in style:
            kwargs["text_color"] = COLORS["error"]
        elif "Success" in style:
            kwargs["text_color"] = COLORS["success"]
        elif style:
            kwargs["text_color"] = COLORS["text_secondary"]
        return super().configure(require_redraw=require_redraw, **kwargs)

    config = configure


class ActionBar(ctk.CTkFrame):
    """Project conversion state while keeping the ready action centered."""

    def __init__(
        self,
        master,
        fonts: SystemFontResolver,
        on_generate: Callable[[], None],
        on_cancel: Callable[[], None],
        progress_variable: tk.Variable,
        generate_icon,
        on_cancel_now: Optional[Callable[[], None]] = None,
        on_decision_continue: Optional[Callable[[], None]] = None,
        on_decision_back: Optional[Callable[[], None]] = None,
        on_scroll_outside: Optional[Callable[[tk.Event], None]] = None,
    ) -> None:
        super().__init__(
            master,
            corner_radius=0,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        for column in range(3):
            self.grid_columnconfigure(column, weight=1, uniform="action")

        self.status_label = ShellStatusLabel(
            self,
            text="",
            anchor="w",
            justify="left",
            font=fonts.font("secondary"),
            text_color=COLORS["text_secondary"],
        )
        tk.Frame.configure(self.status_label, takefocus=True)
        self.reason_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            justify="left",
            font=fonts.font("secondary"),
            text_color=COLORS["text_secondary"],
        )
        self.generate_button = PrimaryButton(
            self,
            text="",
            command=on_generate,
            width=280,
            font=fonts.font("label"),
            image=generate_icon,
            compound="left",
        )
        self.cancel_button = SecondaryButton(
            self,
            text="",
            command=on_cancel,
            width=190,
            font=fonts.font("body"),
        )
        self.cancel_now_button = SecondaryButton(
            self,
            text="",
            command=on_cancel_now or (lambda: None),
            width=170,
            font=fonts.font("body"),
        )
        self.batch_label = ctk.CTkLabel(
            self, text="", anchor="w", font=fonts.font("label"),
            text_color=COLORS["text"],
        )
        self.active_label = ctk.CTkLabel(
            self, text="", anchor="w", font=fonts.font("body"),
            text_color=COLORS["text_secondary"],
        )
        self.options_button = ctk.CTkLabel(
            self, text="", cursor="hand2", anchor="e",
            font=fonts.font("secondary"), text_color=COLORS["primary"],
        )
        tk.Frame.configure(self.options_button, takefocus=True)
        self.options_button.bind("<Button-1>", self._toggle_options_popover)
        self.options_button.bind("<Return>", self._toggle_options_popover)
        self.options_button.bind("<space>", self._toggle_options_popover)
        self.options_button.bind(
            "<Enter>",
            lambda _event: self.options_button.configure(
                text_color=COLORS["primary_hover"]
            ),
            add="+",
        )
        self.options_button.bind(
            "<Leave>",
            lambda _event: self.options_button.configure(
                text_color=COLORS["primary"]
            ),
            add="+",
        )
        self.options_tooltip = Tooltip(self.options_button, "")
        self._options_summary = ""
        self._options_popover = None  # type: Optional[tk.Toplevel]
        self.progress = ttk.Progressbar(
            self,
            variable=progress_variable,
            maximum=100,
            takefocus=True,
        )
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            anchor="e",
            font=fonts.font("label"),
            text_color=COLORS["text_secondary"],
        )
        self.decision_header_frame = ctk.CTkFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self.decision_back_button = SecondaryButton(
            self.decision_header_frame,
            text="",
            command=on_decision_back or (lambda: None),
            width=104,
            font=fonts.font("body"),
        )
        self.decision_title = ctk.CTkLabel(
            self.decision_header_frame, text="", anchor="w", font=fonts.font("label"),
            text_color=COLORS["text"],
        )
        self.decision_message = ctk.CTkLabel(
            self.decision_header_frame, text="", anchor="w", justify="left",
            font=fonts.font("secondary"), text_color=COLORS["text_secondary"],
        )
        self.decision_back_button.grid(row=0, column=0, sticky="w")
        self.decision_title.grid(row=0, column=1, sticky="w", padx=(12, 6))
        self.decision_message.grid(row=0, column=2, sticky="w")
        self.decision_header_frame.columnconfigure(3, weight=1)
        self.decision_instruction = ctk.CTkLabel(
            self, text="", anchor="w", justify="left",
            font=fonts.font("secondary"), text_color=COLORS["text_secondary"],
        )
        self.decision_table_frame = ttk.Frame(self)
        self.decision_table = ttk.Treeview(
            self.decision_table_frame,
            columns=("source", "destination", "issue", "replace"),
            show="headings",
            height=4,
            selectmode="browse",
            takefocus=True,
            style="Decision.Treeview",
        )
        table_style = ttk.Style(self)
        table_style.configure(
            "Decision.Treeview",
            background=COLORS["surface_subtle"],
            fieldbackground=COLORS["surface_subtle"],
            foreground=COLORS["text"],
            borderwidth=0,
            rowheight=25,
        )
        table_style.map(
            "Decision.Treeview",
            background=[("selected", COLORS["surface_selected"])],
            foreground=[("selected", COLORS["text"])],
        )
        self.decision_table.column("source", width=230, minwidth=100, stretch=True)
        self.decision_table.column(
            "destination", width=230, minwidth=100, stretch=True
        )
        self.decision_table.column("issue", width=170, minwidth=110, stretch=True)
        self.decision_table.column(
            "replace", width=118, minwidth=100, stretch=False, anchor="center"
        )
        self.decision_scrollbar = ttk.Scrollbar(
            self.decision_table_frame,
            orient="vertical",
            command=self.decision_table.yview,
        )
        self.decision_table.configure(yscrollcommand=self._set_decision_scrollbar)
        self.decision_table.grid(row=0, column=0, sticky="nsew")
        self.decision_table_frame.columnconfigure(0, weight=1)
        self.decision_table_frame.rowconfigure(0, weight=1)
        self._decision_row_details = {}  # type: dict[str, Tuple[str, str, str, str]]
        self._decision_replaceable = {}  # type: dict[str, str]
        self._decision_overwrite_targets = set()  # type: set[str]
        self._decision_replace_heading = ""
        self._decision_blocked_text = ""
        self._decision_replace_help = ""
        self._decision_blocked_help = ""
        self._decision_replaced_one = ""
        self._decision_replaced_many = ""
        self._decision_kept_one = ""
        self._decision_kept_many = ""
        self.decision_table_tooltip = Tooltip(self.decision_table, "")
        self.decision_table.bind(
            "<Motion>", self._update_decision_table_tooltip, add="+"
        )
        self.decision_table.bind("<Button-1>", self._on_decision_click, add="+")
        self.decision_table.bind("<space>", self._toggle_focused_decision, add="+")
        self.decision_table.bind("<Return>", self._toggle_focused_decision, add="+")
        self.decision_table.bind(
            "<Control-space>", self._toggle_all_decisions, add="+"
        )
        self._on_scroll_outside = on_scroll_outside
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.decision_table.bind(
                sequence, self._on_decision_mousewheel, add="+"
            )
        self.decision_continue_button = PrimaryButton(
            self, text="", command=on_decision_continue or (lambda: None), width=210,
            font=fonts.font("label"),
        )
        self.decision_selection_summary = ctk.CTkLabel(
            self, text="", anchor="w", font=fonts.font("secondary"),
            text_color=COLORS["text_secondary"],
        )
        self._progress_variable = progress_variable
        self._layout_mode = "large"
        self.state = "idle"
        self.progress_percent = 0
        self._show_generate = True
        self._show_cancel = False
        self._show_progress = False
        self._pulse_after = None  # type: Optional[str]
        self._pulse_step = 0
        self.set_state(
            "idle",
            status_text="",
            generate_text="",
            generate_enabled=False,
        )

    def set_state(
        self,
        state: str,
        *,
        status_text: str,
        generate_text: str,
        generate_enabled: bool,
        disabled_reason: str = "",
        progress_current: int = 0,
        progress_total: int = 0,
        progress_text: str = "",
        cancel_text: str = "",
        cancel_enabled: bool = False,
        cancel_now_text: str = "",
        cancel_now_enabled: bool = False,
        batch_text: str = "",
        active_text: str = "",
        options_text: str = "",
        options_summary: str = "",
        decision_title: str = "",
        decision_message: str = "",
        decision_rows: Sequence[Tuple[str, str, str, bool]] = (),
        decision_has_existing: bool = False,
        decision_instruction: str = "",
        decision_source_heading: str = "",
        decision_destination_heading: str = "",
        decision_issue_heading: str = "",
        decision_replace_heading: str = "",
        decision_blocked_text: str = "",
        decision_replace_help: str = "",
        decision_blocked_help: str = "",
        decision_replaced_one: str = "",
        decision_replaced_many: str = "",
        decision_kept_one: str = "",
        decision_kept_many: str = "",
        continue_text: str = "",
        back_text: str = "",
    ) -> None:
        """Render one canonical state without changing conversion semantics."""
        if state not in ACTION_BAR_STATES:
            raise ValueError("Unknown action-bar state: {0}".format(state))
        self._stop_progress_pulse()
        if state not in ("running", "cancel_requested"):
            self._hide_options_popover()
        self.progress.stop()
        self.state = state
        self._status_text = status_text
        self._disabled_reason = disabled_reason
        self.status_label.configure(text=status_text)
        self.status_label.accessible_name = " ".join(
            part for part in (status_text, disabled_reason) if part
        )
        self.reason_label.configure(text=disabled_reason)
        self.reason_label.accessible_name = disabled_reason
        self.generate_button.configure(
            text=generate_text,
            state="normal" if generate_enabled else "disabled",
        )
        self.cancel_button.configure(
            text=cancel_text,
            state="normal" if cancel_enabled else "disabled",
        )
        self.cancel_now_button.configure(
            text=cancel_now_text,
            state="normal" if cancel_now_enabled else "disabled",
        )
        self.batch_label.configure(text=batch_text)
        self.active_label.configure(text=active_text)
        self.options_button.configure(text=options_text)
        self.options_button.accessible_name = options_text
        self._options_summary = options_summary
        self.options_tooltip.update_text(options_summary)
        self.decision_title.configure(text=decision_title)
        self.decision_message.configure(text=decision_message)
        self.decision_instruction.configure(text=decision_instruction)
        self.decision_table.heading("source", text=decision_source_heading)
        self.decision_table.heading("destination", text=decision_destination_heading)
        self.decision_table.heading("issue", text=decision_issue_heading)
        self._decision_replace_heading = decision_replace_heading
        self._decision_blocked_text = decision_blocked_text
        self._decision_replace_help = decision_replace_help
        self._decision_blocked_help = decision_blocked_help
        self._decision_replaced_one = decision_replaced_one
        self._decision_replaced_many = decision_replaced_many
        self._decision_kept_one = decision_kept_one
        self._decision_kept_many = decision_kept_many
        self.decision_continue_button.configure(text=continue_text)
        self.decision_back_button.configure(text=back_text)
        self._decision_has_existing = decision_has_existing
        self._populate_decision_table(decision_rows)
        total = max(0, int(progress_total))
        current = max(0, min(int(progress_current), total)) if total else 0
        self.progress_percent = int(current * 100 / total) if total else 0
        self.progress_label.configure(text=progress_text)
        self.progress_label.accessible_name = progress_text
        self._show_generate = state in (
            "idle", "ready", "validating", "complete", "failed"
        )
        self._show_cancel = state in ("running", "cancel_requested")
        self._show_progress = state in (
            "validating", "running", "cancel_requested"
        )
        if state == "validating":
            self.progress.configure(mode="indeterminate", maximum=100)
            self._progress_variable.set(0)
            self.progress.start(12)
        else:
            self.progress.configure(mode="determinate", maximum=100)
            self._progress_variable.set(self.progress_percent)
            if state in ("running", "cancel_requested") and current < total:
                self._start_progress_pulse(total)
        self._layout_widgets()

    def _toggle_options_popover(self, _event=None) -> str:
        if self._options_popover is not None:
            self._hide_options_popover()
            return "break"
        if not self._options_summary:
            return "break"
        self.options_tooltip.hide()
        window = tk.Toplevel(self)
        window.overrideredirect(True)
        window.transient(self.winfo_toplevel())
        panel = tk.Label(
            window,
            text=self._options_summary,
            justify="left",
            anchor="nw",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=10,
        )
        panel.pack()
        window.update_idletasks()
        x = self.options_button.winfo_rootx() + self.options_button.winfo_width()
        x -= window.winfo_reqwidth()
        y = self.options_button.winfo_rooty() - window.winfo_reqheight() - 6
        window.geometry("+{0}+{1}".format(max(0, x), max(0, y)))
        window.bind("<Escape>", self._hide_options_popover)
        window.bind("<FocusOut>", self._hide_options_popover)
        self._options_popover = window
        window.focus_set()
        return "break"

    def _hide_options_popover(self, _event=None) -> None:
        if self._options_popover is not None:
            window = self._options_popover
            self._options_popover = None
            window.destroy()

    def _populate_decision_table(
        self, rows: Sequence[Tuple[str, str, str, bool]]
    ) -> None:
        destinations = {destination for _, destination, _, replaceable in rows if replaceable}
        self._decision_overwrite_targets.intersection_update(destinations)
        for item in self.decision_table.get_children():
            self.decision_table.delete(item)
        self._decision_row_details = {}
        self._decision_replaceable = {}
        for source, destination, issue, replaceable in rows:
            replace = destination in self._decision_overwrite_targets
            item = self.decision_table.insert(
                "",
                "end",
                values=(
                    self._short_path(source),
                    self._short_path(destination),
                    issue,
                    self._decision_mark(replace) if replaceable else self._decision_blocked_text,
                ),
            )
            action_help = (
                self._decision_replace_help if replaceable
                else self._decision_blocked_help
            )
            self._decision_row_details[item] = (
                source, destination, issue, action_help
            )
            if replaceable:
                self._decision_replaceable[item] = destination
        self.decision_table.configure(height=max(1, min(4, len(rows))))
        self._update_decision_selection()

    @staticmethod
    def _decision_mark(selected: bool) -> str:
        return "☑" if selected else "☐"

    def clear_decision_choices(self) -> None:
        """Restore the safe keep-existing default for a new preflight."""
        self._decision_overwrite_targets.clear()

    def selected_overwrite_targets(self) -> tuple:
        """Return the destinations explicitly approved for replacement."""
        return tuple(sorted(self._decision_overwrite_targets))

    def _toggle_decision_item(self, item: str) -> None:
        destination = self._decision_replaceable.get(item)
        if destination is None:
            return
        if destination in self._decision_overwrite_targets:
            self._decision_overwrite_targets.remove(destination)
        else:
            self._decision_overwrite_targets.add(destination)
        values = list(self.decision_table.item(item, "values"))
        values[3] = self._decision_mark(
            destination in self._decision_overwrite_targets
        )
        self.decision_table.item(item, values=values)
        self._update_decision_selection()

    def _on_decision_click(self, event) -> Optional[str]:
        if self.decision_table.identify_column(event.x) != "#4":
            return None
        item = self.decision_table.identify_row(event.y)
        if not item:
            return None
        self.decision_table.selection_set(item)
        self.decision_table.focus(item)
        self.decision_table.focus_set()
        self._toggle_decision_item(item)
        return "break"

    def _toggle_focused_decision(self, _event=None) -> str:
        item = self.decision_table.focus()
        if item:
            self._toggle_decision_item(item)
        return "break"

    def _toggle_all_decisions(self, _event=None) -> str:
        destinations = set(self._decision_replaceable.values())
        select_all = bool(destinations - self._decision_overwrite_targets)
        if select_all:
            self._decision_overwrite_targets.update(destinations)
        else:
            self._decision_overwrite_targets.difference_update(destinations)
        for item, destination in self._decision_replaceable.items():
            values = list(self.decision_table.item(item, "values"))
            values[3] = self._decision_mark(
                destination in self._decision_overwrite_targets
            )
            self.decision_table.item(item, values=values)
        self._update_decision_selection()
        return "break"

    def _update_decision_selection(self) -> None:
        destinations = set(self._decision_replaceable.values())
        selected = len(destinations & self._decision_overwrite_targets)
        if not destinations or selected == 0:
            heading_mark = "☐"
        elif selected == len(destinations):
            heading_mark = "☑"
        else:
            heading_mark = "◩"
        self.decision_table.heading(
            "replace",
            text="{0} {1}".format(heading_mark, self._decision_replace_heading),
            command=self._toggle_all_decisions,
        )
        kept = len(destinations) - selected
        replaced_template = (
            self._decision_replaced_one if selected == 1
            else self._decision_replaced_many
        )
        kept_template = (
            self._decision_kept_one if kept == 1 else self._decision_kept_many
        )
        parts = []
        if destinations:
            parts.extend((
                replaced_template.format(count=selected),
                kept_template.format(count=kept),
            ))
        self.decision_selection_summary.configure(text=" · ".join(parts))

    @staticmethod
    def _short_path(value: str) -> str:
        path = Path(value)
        parent = path.parent.name
        return "{0} / {1}".format(parent, path.name) if parent else path.name

    def _set_decision_scrollbar(self, first: str, last: str) -> None:
        self.decision_scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.decision_scrollbar.grid_remove()
        else:
            self.decision_scrollbar.grid(row=0, column=1, sticky="ns")

    def _update_decision_table_tooltip(self, event) -> None:
        item = self.decision_table.identify_row(event.y)
        column = self.decision_table.identify_column(event.x)
        details = self._decision_row_details.get(item)
        if details is None or column not in ("#1", "#2", "#3", "#4"):
            self.decision_table_tooltip.update_text("")
            return
        text = details[int(column[1:]) - 1]
        if text != self.decision_table_tooltip.text:
            self.decision_table_tooltip.update_text(text)
            self.decision_table_tooltip.schedule()

    def _on_decision_mousewheel(self, event) -> str:
        if self.focus_get() is self.decision_table:
            direction = -1 if getattr(event, "delta", 0) > 0 else 1
            if getattr(event, "num", 0) == 4:
                direction = -1
            elif getattr(event, "num", 0) == 5:
                direction = 1
            self.decision_table.yview_scroll(direction, "units")
        elif self._on_scroll_outside is not None:
            self._on_scroll_outside(event)
        return "break"

    def _start_progress_pulse(self, total: int) -> None:
        self._pulse_step = 0

        def advance() -> None:
            self._pulse_after = None
            if self.state not in ("running", "cancel_requested"):
                return
            segment = 100.0 / max(1, total)
            wave = (self._pulse_step % 12) / 11.0
            self._progress_variable.set(
                min(99.0, self.progress_percent + segment * (0.12 + wave * 0.55))
            )
            self._pulse_step += 1
            self._pulse_after = self.winfo_toplevel().after(110, advance)

        self._pulse_after = self.winfo_toplevel().after(110, advance)

    def _stop_progress_pulse(self) -> None:
        if self._pulse_after is not None:
            try:
                self.winfo_toplevel().after_cancel(self._pulse_after)
            except tk.TclError:
                pass
            self._pulse_after = None

    def set_conversion_active(self, active: bool) -> None:
        """Retain the legacy shell probe while callers migrate to states."""
        target = "running" if active else "ready"
        self.set_state(
            target,
            status_text=self.status_label.cget("text"),
            generate_text=self.generate_button.cget("text"),
            generate_enabled=not active,
            progress_current=0,
            progress_total=1,
            cancel_text=self.cancel_button.cget("text"),
            cancel_enabled=active,
        )

    def set_layout_mode(self, mode: str) -> None:
        """Project the same state into the compact or full-width layout."""
        if mode not in ("compact", "medium", "large"):
            raise ValueError("Unknown action-bar layout: {0}".format(mode))
        if mode == self._layout_mode:
            return
        self._layout_mode = mode
        self._layout_widgets()

    def _layout_widgets(self) -> None:
        for widget in (
            self.status_label,
            self.reason_label,
            self.generate_button,
            self.cancel_button,
            self.cancel_now_button,
            self.batch_label,
            self.active_label,
            self.options_button,
            self.progress,
            self.progress_label,
            self.decision_header_frame,
            self.decision_instruction,
            self.decision_table_frame,
            self.decision_continue_button,
            self.decision_selection_summary,
        ):
            widget.grid_forget()
        if self.state == "decision_required":
            self.decision_header_frame.grid(
                row=0, column=0, columnspan=3, sticky="ew",
                padx=SPACING["lg"], pady=(SPACING["sm"], 0),
            )
            self.decision_instruction.grid(
                row=1, column=0, columnspan=3, sticky="ew",
                padx=SPACING["lg"], pady=(SPACING["xs"], 0),
            )
            self.decision_table_frame.grid(
                row=2, column=0, columnspan=3, sticky="ew",
                padx=SPACING["lg"], pady=SPACING["xs"],
            )
            self.decision_selection_summary.grid(
                row=3, column=0, columnspan=2, sticky="w",
                padx=SPACING["lg"],
                pady=(0, SPACING["sm"]),
            )
            self.decision_continue_button.grid(
                row=3, column=2, sticky="e", padx=SPACING["lg"],
                pady=(0, SPACING["sm"]),
            )
            return
        if self.state in ("running", "cancel_requested"):
            self.batch_label.grid(
                row=0, column=0, columnspan=2, sticky="w",
                padx=(SPACING["lg"], SPACING["sm"]), pady=(SPACING["sm"], 0),
            )
            self.options_button.grid(
                row=0, column=2, sticky="e", padx=(SPACING["sm"], SPACING["lg"]),
                pady=(SPACING["sm"], 0),
            )
            self.active_label.grid(
                row=1, column=0, columnspan=2, sticky="w",
                padx=(SPACING["lg"], SPACING["sm"]), pady=SPACING["xs"],
            )
            self.progress_label.grid(
                row=1, column=2, sticky="e", padx=(0, SPACING["lg"]),
            )
            self.progress.grid(
                row=2, column=0, columnspan=3, sticky="ew",
                padx=SPACING["lg"], pady=(0, SPACING["sm"]),
            )
            self.cancel_button.grid(
                row=3, column=0, sticky="w", padx=SPACING["lg"],
                pady=(0, SPACING["sm"]),
            )
            self.cancel_now_button.grid(
                row=3, column=2, sticky="e", padx=SPACING["lg"],
                pady=(0, SPACING["sm"]),
            )
            return
        if self._layout_mode == "compact":
            self.status_label.configure(
                text=" ".join(
                    part
                    for part in (self._status_text, self._disabled_reason)
                    if part
                )
            )
            self.status_label.grid(
                row=0,
                column=0,
                columnspan=3,
                sticky="ew",
                padx=SPACING["md"],
                pady=(SPACING["xs"], 0),
            )
            row = 1
            action = self.generate_button if self._show_generate else self.cancel_button
            if self._show_generate or self._show_cancel:
                action.grid(
                    row=row,
                    column=0,
                    columnspan=3,
                    sticky="ew",
                    padx=SPACING["md"],
                    pady=SPACING["xs"],
                )
                row += 1
            if self._show_progress:
                self.progress.grid(
                    row=row,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    padx=(SPACING["md"], SPACING["sm"]),
                    pady=(0, SPACING["sm"]),
                )
                if self.state != "validating":
                    self.progress_label.grid(
                        row=row,
                        column=2,
                        sticky="e",
                        padx=(0, SPACING["md"]),
                        pady=(0, SPACING["sm"]),
                    )
            return

        self.status_label.configure(text=self._status_text)
        self.status_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(SPACING["lg"], SPACING["sm"]),
            pady=SPACING["sm"],
        )
        if self._show_generate:
            self.generate_button.configure(width=280)
            self.generate_button.grid(row=0, column=1, pady=SPACING["sm"])
        if self._show_cancel:
            self.cancel_button.grid(
                row=0,
                column=2,
                sticky="e",
                padx=(SPACING["sm"], SPACING["lg"]),
                pady=SPACING["sm"],
            )
        if self.reason_label.cget("text"):
            self.reason_label.grid(
                row=1,
                column=0,
                columnspan=3,
                sticky="ew",
                padx=SPACING["lg"],
                pady=(0, SPACING["xs"]),
            )
        if self._show_progress:
            progress_row = 2 if self.reason_label.cget("text") else 1
            self.progress.grid(
                row=progress_row,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=(SPACING["lg"], SPACING["sm"]),
                pady=(0, SPACING["sm"]),
            )
            if self.state != "validating":
                self.progress_label.grid(
                    row=progress_row,
                    column=2,
                    sticky="e",
                    padx=(0, SPACING["lg"]),
                    pady=(0, SPACING["sm"]),
                )

    def button_center_error(self) -> int:
        """Return the primary button's horizontal error from shell center."""
        self.update_idletasks()
        button_center = (
            self.generate_button.winfo_rootx()
            + self.generate_button.winfo_width() // 2
        )
        shell_center = self.winfo_rootx() + self.winfo_width() // 2
        return button_center - shell_center
