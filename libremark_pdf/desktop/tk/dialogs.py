"""Injectable boundary for the existing native Tk dialogs."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from ..ctk.assets import product_logo
from ..ctk.components import (
    PrimaryButton,
    SecondaryButton,
    monitor_work_area,
)
from ..ctk.theme import COLORS, SPACING, SystemFontResolver


REPORT_COMPACT_BREAKPOINT = 820
REPORT_DEBOUNCE_MS = 200
REPORT_TEXT_LIMIT = 10000


def dialog_geometry(
    anchor_bounds: Tuple[int, int, int, int],
    requested_size: Tuple[int, int],
    work_area: Tuple[int, int, int, int],
    maximum_size: Tuple[int, int],
) -> Tuple[int, int, int, int]:
    """Return a parent-centred dialog rectangle clamped to one work area."""
    anchor_x, anchor_y, anchor_width, anchor_height = anchor_bounds
    requested_width, requested_height = requested_size
    work_x, work_y, work_width, work_height = work_area
    margin = SPACING["lg"]
    available_width = max(1, work_width - (2 * margin))
    available_height = max(1, work_height - (2 * margin))
    width = min(requested_width, maximum_size[0], available_width)
    height = min(requested_height, maximum_size[1], available_height)
    desired_x = anchor_x + (anchor_width - width) // 2
    desired_y = anchor_y + (anchor_height - height) // 2
    x = max(work_x, min(desired_x, work_x + work_width - width))
    y = max(work_y, min(desired_y, work_y + work_height - height))
    return int(width), int(height), int(x), int(y)


class GeneralDialog:
    """Reusable modal CTk shell with safe dismissal and focus restoration."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        dismiss: Callable[[], None],
        scrollable: bool = True,
    ) -> None:
        self.parent = parent
        self.owner = parent.winfo_toplevel()
        self.trigger = self.owner.focus_get()
        self._dismiss = dismiss
        self._closed = False
        self.initial_focus = None  # type: Optional[tk.Misc]
        self.fonts = SystemFontResolver(self.owner)
        self.window = ctk.CTkToplevel(self.owner)
        self.window.withdraw()
        self.window.title(title)
        self.window.transient(self.owner)
        self.window.resizable(True, True)
        self.window.configure(fg_color=COLORS["app_bg"])
        self.window.protocol("WM_DELETE_WINDOW", self.dismiss)
        self.window.bind("<Escape>", self.dismiss)

        self.shell = ctk.CTkFrame(
            self.window,
            fg_color=COLORS["app_bg"],
            corner_radius=0,
        )
        self.shell.pack(fill="both", expand=True)
        self.title_label = ctk.CTkLabel(
            self.shell,
            text=title,
            anchor="w",
            text_color=COLORS["text"],
            font=self.fonts.font("dialog_title"),
        )
        self.title_label.pack(
            fill="x",
            padx=SPACING["lg"],
            pady=(SPACING["lg"], SPACING["md"]),
        )
        content_type = ctk.CTkScrollableFrame if scrollable else ctk.CTkFrame
        self.content = content_type(
            self.shell, fg_color="transparent", corner_radius=0
        )
        self.content.pack(
            fill="both",
            expand=True,
            padx=SPACING["lg"],
        )
        self.actions = ctk.CTkFrame(
            self.shell,
            fg_color=COLORS["surface"],
            corner_radius=0,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.actions.pack(fill="x", side="bottom")

    def set_initial_focus(self, widget: tk.Misc) -> None:
        """Select the deterministic control focused after the dialog appears."""
        self.initial_focus = widget

    def _focus_initial(self) -> None:
        """Activate the modal before moving focus to its safe first control."""
        try:
            self.window.focus_force()
            self.window.after(100, self._focus_initial_control)
        except tk.TclError:
            pass

    def _focus_initial_control(self) -> None:
        if self.initial_focus is not None:
            self.initial_focus.focus_force()

    def dismiss(self, _event=None) -> str:
        """Apply the configured safe dismissal policy and close the window."""
        if not self._closed:
            self._dismiss()
            self.close()
        return "break"

    def close(self) -> None:
        """Destroy the modal exactly once."""
        if self._closed:
            return
        self._closed = True
        self.window.destroy()

    def _restore_owner_opacity(self) -> None:
        """Undo a partially completed CustomTkinter DPI transition."""
        try:
            if self.owner.winfo_exists():
                self.owner.attributes("-alpha", 1.0)
        except (AttributeError, tk.TclError):
            pass

    def show(
        self,
        preferred_size: Tuple[int, int],
        maximum_size: Tuple[int, int],
    ) -> None:
        """Place, show, wait for, and restore focus from the modal."""
        self.window.update_idletasks()
        requested_size = (
            max(self.window.winfo_reqwidth(), preferred_size[0]),
            max(self.window.winfo_reqheight(), preferred_size[1]),
        )
        owner_width = max(1, self.owner.winfo_width())
        owner_height = max(1, self.owner.winfo_height())
        responsive_maximum = (
            min(maximum_size[0], max(360, owner_width - (2 * SPACING["lg"]))),
            min(maximum_size[1], max(280, owner_height - (2 * SPACING["lg"]))),
        )
        width, height, x, y = dialog_geometry(
            (
                self.owner.winfo_rootx(),
                self.owner.winfo_rooty(),
                self.owner.winfo_width(),
                self.owner.winfo_height(),
            ),
            requested_size,
            monitor_work_area(self.owner),
            responsive_maximum,
        )
        self.window.geometry(
            "{0}x{1}+{2}+{3}".format(width, height, x, y)
        )
        self.window.minsize(min(360, width), min(280, height))
        self.window.deiconify()
        self.window.wait_visibility()
        self.window.lift(self.owner)
        self.window.grab_set()
        if self.initial_focus is not None:
            self.window.after_idle(self._focus_initial)
        try:
            self.window.wait_window()
        finally:
            self._restore_owner_opacity()
        trigger = self.trigger
        try:
            if trigger is not None and trigger.winfo_exists():
                self.owner.focus_force()
                self.owner.after(100, trigger.focus_force)
        except (AttributeError, tk.TclError):
            pass


def problem_report_mode(width: int) -> str:
    """Return the report layout selected for the available dialog width."""
    return "compact" if width < REPORT_COMPACT_BREAKPOINT else "large"


class ProblemReportDialog:
    """Responsive, local-only editor for one privacy-reviewed problem report."""

    def __init__(
        self,
        root: tk.Misc,
        *,
        labels: dict,
        error_code: str,
        build_report: Callable[[str, str, str, bool], str],
        sanitize_report: Callable[[str], str],
        save_report: Callable[[Path, str], None],
        has_support_channel: bool,
        open_support_page: Callable[[], None],
    ) -> None:
        self.root = root
        self.labels = labels
        self.error_code = error_code
        self.build_report = build_report
        self.sanitize_report = sanitize_report
        self.save_report = save_report
        self.has_support_channel = has_support_channel
        self.open_support_page = open_support_page
        self._after_id = None
        self._report_edited = False
        self._generated_report = ""
        self._mode = "large"
        self._preview_expanded = True
        self.dialog = GeneralDialog(
            root, labels["report_title"], self._dismiss, scrollable=True
        )
        self.include_diagnostics = tk.BooleanVar(value=False)
        self._build_widgets()

    def _build_widgets(self) -> None:
        fonts = self.dialog.fonts
        self.introduction = ctk.CTkLabel(
            self.dialog.content,
            text=self.labels["report_intro"],
            anchor="w",
            justify="left",
            wraplength=400,
            text_color=COLORS["text_secondary"],
            font=fonts.font("body"),
        )
        self.introduction.pack(fill="x", pady=(0, SPACING["md"]))
        self.body = ctk.CTkFrame(self.dialog.content, fg_color="transparent")
        self.body.pack(fill="both", expand=True)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_columnconfigure(1, weight=1)

        self.form = ctk.CTkFrame(self.body, fg_color="transparent")
        self.preview_section = ctk.CTkFrame(
            self.body,
            fg_color=COLORS["surface"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._build_form(fonts)
        self._build_preview(fonts)
        self._build_actions(fonts)
        self._apply_layout("large")
        self.dialog.window.bind("<Configure>", self._on_configure, add="+")
        self.dialog.set_initial_focus(self.summary)

    def _field_label(self, parent: tk.Misc, text: str) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            text_color=COLORS["text"],
            font=self.dialog.fonts.font("body"),
        )
        label.pack(fill="x", pady=(0, SPACING["xs"]))
        return label

    def _build_form(self, fonts: SystemFontResolver) -> None:
        self._field_label(self.form, self.labels["report_summary"] + " *")
        self.summary = ctk.CTkEntry(
            self.form,
            placeholder_text=self.labels["report_summary_placeholder"],
            height=36,
            font=fonts.font("body"),
        )
        self.summary.pack(fill="x")
        self.validation = ctk.CTkLabel(
            self.form,
            text="",
            anchor="w",
            justify="left",
            wraplength=400,
            text_color=COLORS["error"],
            font=fonts.font("secondary"),
        )
        self.validation.pack(fill="x", pady=(SPACING["xs"], SPACING["sm"]))

        self._field_label(self.form, self.labels["report_steps"])
        self.steps = ctk.CTkTextbox(
            self.form, height=112, wrap="word", font=fonts.font("body")
        )
        self.steps.pack(fill="x", pady=(0, SPACING["sm"]))
        self._field_label(self.form, self.labels["report_expected"])
        self.expected = ctk.CTkTextbox(
            self.form, height=88, wrap="word", font=fonts.font("body")
        )
        self.expected.pack(fill="x", pady=(0, SPACING["sm"]))
        if self.error_code:
            ctk.CTkLabel(
                self.form,
                text="{0}: {1}".format(
                    self.labels["report_error_code"], self.error_code
                ),
                anchor="w",
                text_color=COLORS["text_secondary"],
                font=fonts.font("technical", monospace=True),
            ).pack(fill="x", pady=(0, SPACING["sm"]))
        self.diagnostics = ctk.CTkCheckBox(
            self.form,
            text=self.labels["include_diagnostics"],
            variable=self.include_diagnostics,
            command=self._schedule_refresh,
            font=fonts.font("body"),
        )
        self.diagnostics.pack(fill="x", pady=(0, SPACING["xs"]))
        for message in (
            self.labels["diagnostics_consent"],
            self.labels["report_local_help"],
        ):
            ctk.CTkLabel(
                self.form,
                text=message,
                anchor="w",
                justify="left",
                wraplength=400,
                text_color=COLORS["text_secondary"],
                font=fonts.font("secondary"),
            ).pack(fill="x", pady=(0, SPACING["sm"]))
        if not self.has_support_channel:
            self.offline_help = ctk.CTkLabel(
                self.form,
                text=self.labels["support_not_configured"],
                anchor="w",
                justify="left",
                wraplength=400,
                fg_color=COLORS["primary_subtle"],
                corner_radius=6,
                text_color=COLORS["info"],
                font=fonts.font("secondary"),
                padx=SPACING["sm"],
                pady=SPACING["sm"],
            )
            self.offline_help.pack(fill="x", pady=(0, SPACING["sm"]))
        for widget in (self.summary, self.steps, self.expected):
            widget.bind("<KeyRelease>", self._on_form_changed, add="+")

    def _build_preview(self, fonts: SystemFontResolver) -> None:
        heading = ctk.CTkFrame(self.preview_section, fg_color="transparent")
        heading.pack(fill="x", padx=SPACING["md"], pady=(SPACING["md"], 0))
        self.preview_title = ctk.CTkLabel(
            heading,
            text=self.labels["report_preview"],
            anchor="w",
            text_color=COLORS["text"],
            font=fonts.font("panel_title"),
        )
        self.preview_title.pack(side="left", fill="x", expand=True)
        self.preview_toggle = SecondaryButton(
            heading,
            text=self.labels["report_preview_collapse"],
            command=self._toggle_preview,
            width=156,
            height=32,
        )
        self.preview_help = ctk.CTkLabel(
            self.preview_section,
            text=self.labels["report_preview_help"],
            anchor="w",
            justify="left",
            wraplength=400,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.preview_help.pack(
            fill="x", padx=SPACING["md"], pady=(SPACING["xs"], SPACING["sm"])
        )
        self.report = ctk.CTkTextbox(
            self.preview_section,
            height=360,
            wrap="word",
            font=fonts.font("technical", monospace=True),
        )
        self.report.pack(
            fill="both",
            expand=True,
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        self.report.bind("<KeyRelease>", self._on_report_changed, add="+")

    def _build_actions(self, fonts: SystemFontResolver) -> None:
        self.status = ctk.CTkLabel(
            self.dialog.actions,
            text="",
            anchor="w",
            justify="left",
            wraplength=440,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.status.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(SPACING["lg"], SPACING["sm"]),
            pady=SPACING["md"],
        )
        self.close_button = SecondaryButton(
            self.dialog.actions,
            text=self.labels["close_action"],
            command=self.dialog.close,
            width=96,
        )
        self.close_button.pack(
            side="right", padx=(SPACING["xs"], SPACING["lg"]), pady=SPACING["md"]
        )
        self.save_button = SecondaryButton(
            self.dialog.actions,
            text=self.labels["save_report"],
            command=self._save,
            width=132,
        )
        self.save_button.pack(side="right", padx=SPACING["xs"], pady=SPACING["md"])
        self.copy_button = PrimaryButton(
            self.dialog.actions,
            text=self.labels["copy_report"],
            command=self._copy,
            width=128,
        )
        self.copy_button.pack(side="right", padx=SPACING["xs"], pady=SPACING["md"])
        self.review_button = SecondaryButton(
            self.dialog.actions,
            text=self.labels["preview_report"],
            command=lambda: self._refresh_report(auto=False),
            width=128,
        )
        self.review_button.pack(side="right", padx=SPACING["xs"], pady=SPACING["md"])
        if self.has_support_channel:
            self.support_button = SecondaryButton(
                self.dialog.actions,
                text=self.labels["open_support_channel"],
                command=self._open_support,
                width=140,
            )
            self.support_button.pack(
                side="right", padx=SPACING["xs"], pady=SPACING["md"]
            )

    def _on_configure(self, event) -> None:
        if event.widget is not self.dialog.window:
            return
        available = max(280, event.width - (6 * SPACING["lg"]))
        self.introduction.configure(wraplength=available)
        mode = problem_report_mode(event.width)
        column_wrap = (
            available if mode == "compact"
            else max(240, available // 2 - SPACING["md"])
        )
        self.validation.configure(wraplength=column_wrap)
        self.preview_help.configure(wraplength=column_wrap)
        if hasattr(self, "offline_help"):
            self.offline_help.configure(wraplength=column_wrap)
        self._apply_layout(mode)

    def _apply_layout(self, mode: str) -> None:
        if mode == self._mode and self.form.winfo_manager():
            return
        self._mode = mode
        self.form.grid_forget()
        self.preview_section.grid_forget()
        if mode == "compact":
            self._preview_expanded = False
            self.form.grid(row=0, column=0, columnspan=2, sticky="ew")
            self.preview_section.grid(
                row=1,
                column=0,
                columnspan=2,
                sticky="ew",
                pady=(SPACING["md"], 0),
            )
            self.preview_toggle.pack(side="right")
            self._project_preview_visibility()
        else:
            self._preview_expanded = True
            self.form.grid(
                row=0, column=0, sticky="nsew", padx=(0, SPACING["sm"])
            )
            self.preview_section.grid(
                row=0, column=1, sticky="nsew", padx=(SPACING["sm"], 0)
            )
            self.preview_toggle.pack_forget()
            self._project_preview_visibility()
        self._apply_action_layout(mode)

    def _apply_action_layout(self, mode: str) -> None:
        buttons = [
            self.review_button,
            self.copy_button,
            self.save_button,
            self.close_button,
        ]
        support_button = getattr(self, "support_button", None)
        if support_button is not None:
            buttons.insert(0, support_button)
        self.status.pack_forget()
        for button in buttons:
            button.pack_forget()
        if mode == "compact":
            self.status.pack(
                side="top",
                fill="x",
                padx=SPACING["md"],
                pady=(SPACING["sm"], SPACING["xs"]),
            )
            for button in reversed(buttons):
                button.configure(width=92)
                button.pack(
                    side="right",
                    padx=SPACING["xs"],
                    pady=(SPACING["xs"], SPACING["sm"]),
                )
        else:
            self.status.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(SPACING["lg"], SPACING["sm"]),
                pady=SPACING["md"],
            )
            for button in reversed(buttons):
                button.configure(width=128)
                button.pack(
                    side="right",
                    padx=SPACING["xs"],
                    pady=SPACING["md"],
                )

    def _toggle_preview(self) -> None:
        self._preview_expanded = not self._preview_expanded
        self._project_preview_visibility()

    def _project_preview_visibility(self) -> None:
        if self._preview_expanded:
            self.preview_help.pack(
                fill="x",
                padx=SPACING["md"],
                pady=(SPACING["xs"], SPACING["sm"]),
            )
            self.report.pack(
                fill="both",
                expand=True,
                padx=SPACING["md"],
                pady=(0, SPACING["md"]),
            )
            self.preview_toggle.configure(text=self.labels["report_preview_collapse"])
        else:
            self.preview_help.pack_forget()
            self.report.pack_forget()
            self.preview_toggle.configure(text=self.labels["report_preview_expand"])

    def _bounded(self, widget: tk.Misc) -> str:
        value = widget.get("1.0", "end-1c")
        if len(value) > REPORT_TEXT_LIMIT:
            value = value[:REPORT_TEXT_LIMIT]
            widget.delete("1.0", "end")
            widget.insert("1.0", value)
        return value

    def _on_form_changed(self, _event=None) -> None:
        self._bounded(self.steps)
        self._bounded(self.expected)
        self._schedule_refresh()

    def _on_report_changed(self, _event=None) -> None:
        self._bounded(self.report)
        self._report_edited = True

    def _schedule_refresh(self) -> None:
        if self._after_id is not None:
            self.dialog.window.after_cancel(self._after_id)
        self._after_id = self.dialog.window.after(
            REPORT_DEBOUNCE_MS, lambda: self._refresh_report(auto=True)
        )

    def _refresh_report(self, auto: bool) -> bool:
        self._after_id = None
        summary = self.summary.get().strip()
        if not summary:
            self.validation.configure(text=self.labels["report_summary_required"])
            return False
        self.validation.configure(text="")
        self._generated_report = self.build_report(
            summary,
            self._bounded(self.steps),
            self._bounded(self.expected),
            bool(self.include_diagnostics.get()),
        )
        if auto and self._report_edited:
            self.status.configure(text=self.labels["report_preview_edited"])
            return True
        self.report.delete("1.0", "end")
        self.report.insert("1.0", self._generated_report)
        self._report_edited = False
        self.status.configure(text="")
        return True

    def _reviewed_text(self) -> str:
        return self.report.get("1.0", "end-1c")

    def _ensure_reviewed(self) -> bool:
        if not self.summary.get().strip():
            self.validation.configure(text=self.labels["report_summary_required"])
            self.summary.focus_set()
            return False
        if not self._reviewed_text().strip():
            return self._refresh_report(auto=False)
        return True

    def _copy(self) -> None:
        if not self._ensure_reviewed():
            return
        try:
            reviewed = self.sanitize_report(self._reviewed_text())
            self.root.clipboard_clear()
            self.root.clipboard_append(reviewed)
            self.status.configure(text=self.labels["report_copied"])
        except Exception as exc:
            self.status.configure(
                text=self.labels["report_copy_error"].format(error=str(exc))
            )

    def _save(self) -> None:
        if not self._ensure_reviewed():
            return
        selected = filedialog.asksaveasfilename(
            parent=self.dialog.window,
            title=self.labels["report_save_title"],
            defaultextension=".txt",
            filetypes=[(self.labels["report_text_filter"], "*.txt")],
        )
        if not selected:
            return
        try:
            reviewed = self.sanitize_report(self._reviewed_text())
            self.save_report(Path(selected), reviewed)
            self.status.configure(text=self.labels["report_saved"])
        except Exception as exc:
            self.status.configure(
                text=self.labels["report_save_error"].format(error=str(exc))
            )

    def _open_support(self) -> None:
        try:
            self.open_support_page()
        except Exception as exc:
            self.status.configure(
                text=self.labels["support_open_error"].format(error=str(exc))
            )

    def _dismiss(self) -> None:
        if self._after_id is not None:
            self.dialog.window.after_cancel(self._after_id)
            self._after_id = None

    def show(self) -> None:
        self.dialog.show((980, 700), (1120, 820))


class TkDialogs:
    """Call native Tk dialogs without changing their visible contract."""

    def choose_markdown_files(
        self, parent: tk.Misc, title: str, filetypes: list
    ):
        return filedialog.askopenfilenames(
            parent=parent, title=title, filetypes=filetypes
        )

    def choose_css_file(self, parent: tk.Misc, title: str, filetypes: list):
        return filedialog.askopenfilename(
            parent=parent, title=title, filetypes=filetypes
        )

    def choose_output_folder(self, parent: tk.Misc, title: str):
        return filedialog.askdirectory(parent=parent, title=title)

    def ask_collision_continue(
        self,
        root: tk.Misc,
        title: str,
        message: str,
        continue_label: str,
        cancel_label: str,
    ) -> bool:
        choice = self._ask_explicit_choice(
            root,
            title,
            message,
            (("continue", continue_label), ("cancel", cancel_label)),
            default_choice="cancel",
            dismiss_choice="cancel",
        )
        return choice == "continue"

    def ask_overwrite(
        self,
        root: tk.Misc,
        title: str,
        message: str,
        replace_label: str,
        keep_label: str,
        cancel_label: str,
    ):
        choice = self._ask_explicit_choice(
            root,
            title,
            message,
            (
                ("replace", replace_label),
                ("keep", keep_label),
                ("cancel", cancel_label),
            ),
            default_choice="keep",
            dismiss_choice="cancel",
        )
        return {"replace": True, "keep": False, "cancel": None}[choice]

    def ask_trusted_html(
        self,
        parent: tk.Misc,
        title: str,
        message: str,
        allow_label: str,
        cancel_label: str,
    ) -> bool:
        """Confirm trusted HTML centered on the visible advanced editor host."""
        choice = self._ask_explicit_choice(
            parent,
            title,
            message,
            (("allow", allow_label), ("cancel", cancel_label)),
            default_choice="cancel",
            dismiss_choice="cancel",
            center_on_anchor=True,
        )
        return choice == "allow"

    def ask_restore_header_footer(
        self, parent: tk.Misc, title: str, message: str
    ) -> bool:
        """Confirm replacing customized header/footer fields with defaults."""
        return messagebox.askyesno(
            title, message, parent=parent, default=messagebox.NO
        )

    def ask_close_during_conversion(
        self,
        root: tk.Misc,
        title: str,
        message: str,
        continue_label: str,
        cancel_close_label: str,
    ) -> str:
        """Return the explicit close choice, defaulting dismissal to continue."""
        choice = "continue"

        def select(value: str) -> None:
            nonlocal choice
            choice = value

        dialog = GeneralDialog(
            root, title, lambda: select("continue"), scrollable=False
        )
        message_label = ctk.CTkLabel(
            dialog.content,
            text=message,
            anchor="w",
            justify="left",
            wraplength=500,
            text_color=COLORS["text_secondary"],
            font=dialog.fonts.font("body"),
        )
        message_label.pack(fill="x", pady=(0, SPACING["md"]))

        def finish(value: str) -> None:
            select(value)
            dialog.close()

        cancel_button = SecondaryButton(
            dialog.actions,
            text=cancel_close_label,
            command=lambda: finish("cancel_close"),
            tone="danger",
        )
        cancel_button.pack(
            fill="x",
            padx=SPACING["lg"],
            pady=(SPACING["md"], SPACING["xs"]),
        )
        continue_button = PrimaryButton(
            dialog.actions,
            text=continue_label,
            command=lambda: finish("continue"),
        )
        continue_button.pack(
            fill="x",
            padx=SPACING["lg"],
            pady=(SPACING["xs"], SPACING["md"]),
        )
        dialog.set_initial_focus(continue_button)
        dialog.show((520, 280), (560, 420))
        return choice

    def _ask_explicit_choice(
        self,
        root: tk.Misc,
        title: str,
        message: str,
        choices: tuple,
        default_choice: str,
        dismiss_choice: str,
        center_on_anchor: bool = False,
    ) -> str:
        """Show local labelled choices without relying on platform Yes/No copy."""
        choice = dismiss_choice
        owner = root.winfo_toplevel()
        dialog = tk.Toplevel(owner)
        dialog.title(title)
        dialog.transient(owner)
        dialog.resizable(False, False)
        if center_on_anchor:
            dialog.withdraw()

        content = ttk.Frame(dialog, padding=16)
        content.pack(fill="both", expand=True)
        ttk.Label(
            content,
            text=message,
            justify="left",
            wraplength=460,
        ).pack(fill="x")
        actions = ttk.Frame(content)
        actions.pack(fill="x", pady=(16, 0))

        def finish(selected: str) -> None:
            nonlocal choice
            choice = selected
            dialog.destroy()

        def dismiss(event=None) -> str:
            finish(dismiss_choice)
            return "break"

        def activate_default(event=None) -> str:
            finish(default_choice)
            return "break"

        default_button = None
        for value, label in reversed(choices):
            button = ttk.Button(
                actions,
                text=label,
                command=lambda selected=value: finish(selected),
            )
            button.pack(side="right", padx=(8, 0))
            if value == default_choice:
                default_button = button
        dialog.protocol("WM_DELETE_WINDOW", dismiss)
        dialog.bind("<Escape>", dismiss)
        dialog.bind("<Return>", activate_default)
        if center_on_anchor:
            dialog.update_idletasks()
            width = dialog.winfo_reqwidth()
            height = dialog.winfo_reqheight()
            x = root.winfo_rootx() + (root.winfo_width() - width) // 2
            y = root.winfo_rooty() + (root.winfo_height() - height) // 2
            x = max(0, min(x, dialog.winfo_screenwidth() - width))
            y = max(0, min(y, dialog.winfo_screenheight() - height))
            dialog.geometry("+{0}+{1}".format(x, y))
            dialog.deiconify()
        dialog.grab_set()
        if default_button is not None:
            default_button.focus_set()
        dialog.wait_window()
        return choice

    def show_error(self, parent: tk.Misc, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=parent)

    def show_info(self, parent: tk.Misc, title: str, message: str) -> None:
        messagebox.showinfo(title, message, parent=parent)

    def show_shortcuts(
        self,
        root: tk.Misc,
        title: str,
        rows: Sequence[Tuple[str, str]],
        close_label: str,
    ) -> None:
        """Show localized actions and keys as a readable two-column table."""
        dialog = GeneralDialog(root, title, lambda: None)
        table = ctk.CTkFrame(
            dialog.content,
            fg_color=COLORS["surface"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        table.pack(fill="x", pady=(0, SPACING["md"]))
        table.grid_columnconfigure(0, weight=1)
        for row_index, (action, key_value) in enumerate(rows):
            action_label = ctk.CTkLabel(
                table,
                text=action,
                anchor="w",
                text_color=COLORS["text"],
                font=dialog.fonts.font("body"),
            )
            action_label.grid(
                row=row_index,
                column=0,
                sticky="ew",
                padx=(SPACING["md"], SPACING["sm"]),
                pady=SPACING["xs"],
            )
            key_label = ctk.CTkLabel(
                table,
                text=key_value,
                anchor="center",
                fg_color=COLORS["surface_subtle"],
                corner_radius=6,
                text_color=COLORS["text"],
                font=dialog.fonts.font("technical", monospace=True),
                padx=SPACING["sm"],
            )
            key_label.grid(
                row=row_index,
                column=1,
                sticky="e",
                padx=(SPACING["sm"], SPACING["md"]),
                pady=SPACING["xs"],
            )
        close_button = PrimaryButton(
            dialog.actions,
            text=close_label,
            command=dialog.close,
            width=112,
        )
        close_button.pack(
            side="right",
            padx=SPACING["lg"],
            pady=SPACING["md"],
        )
        dialog.set_initial_focus(close_button)
        dialog.show((520, 500), (560, 520))

    def show_about(
        self,
        root: tk.Misc,
        title: str,
        version_text: str,
        technical_heading: str,
        technical_text: str,
        copy_label: str,
        copied_text: str,
        close_label: str,
        local_conversion_text: str,
        no_network_text: str,
        notices_label: str,
        open_notices: Callable[[], None],
    ) -> None:
        """Show structured local identities and an exact clipboard action."""
        dialog = GeneralDialog(root, title, lambda: None)
        body = ctk.CTkFrame(dialog.content, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        identity = ctk.CTkFrame(
            body,
            fg_color=COLORS["surface"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        logo = product_logo(64)
        logo_label = ctk.CTkLabel(identity, text="", image=logo)
        logo_label.pack(anchor="w", padx=SPACING["md"], pady=(SPACING["md"], 0))
        product_label = ctk.CTkLabel(
            identity,
            text=version_text,
            anchor="w",
            text_color=COLORS["text"],
            font=dialog.fonts.font("panel_title"),
        )
        product_label.pack(fill="x", padx=SPACING["md"], pady=SPACING["sm"])
        for message in (local_conversion_text, no_network_text):
            ctk.CTkLabel(
                identity,
                text=message,
                anchor="w",
                justify="left",
                wraplength=300,
                text_color=COLORS["text_secondary"],
                font=dialog.fonts.font("body"),
            ).pack(fill="x", padx=SPACING["md"], pady=(0, SPACING["sm"]))

        technical = ctk.CTkFrame(
            body,
            fg_color=COLORS["surface"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        ctk.CTkLabel(
            technical,
            text=technical_heading,
            anchor="w",
            text_color=COLORS["text"],
            font=dialog.fonts.font("panel_title"),
        ).pack(fill="x", padx=SPACING["md"], pady=SPACING["md"])
        technical_rows = ctk.CTkFrame(technical, fg_color="transparent")
        technical_rows.pack(
            fill="both",
            expand=True,
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        technical_rows.grid_columnconfigure(1, weight=1)
        for row_index, line in enumerate(technical_text.splitlines()):
            label, separator, value = line.partition(": ")
            if not separator:
                value = ""
            ctk.CTkLabel(
                technical_rows,
                text=label,
                anchor="w",
                text_color=COLORS["text_secondary"],
                font=dialog.fonts.font("secondary"),
            ).grid(row=row_index, column=0, sticky="nw", pady=SPACING["xs"])
            ctk.CTkLabel(
                technical_rows,
                text=value,
                anchor="w",
                justify="left",
                wraplength=300,
                text_color=COLORS["text"],
                font=dialog.fonts.font("technical", monospace=True),
            ).grid(
                row=row_index,
                column=1,
                sticky="new",
                padx=(SPACING["md"], 0),
                pady=SPACING["xs"],
            )
        status = ctk.CTkLabel(
            dialog.content,
            text="",
            anchor="w",
            text_color=COLORS["success"],
            font=dialog.fonts.font("secondary"),
        )
        status.pack(fill="x", pady=(SPACING["sm"], 0))

        def copy_information() -> None:
            root.clipboard_clear()
            root.clipboard_append(technical_text)
            status.configure(text=copied_text)

        copy_button = SecondaryButton(
            dialog.actions,
            text=copy_label,
            command=copy_information,
        )
        copy_button.pack(
            side="left",
            padx=(SPACING["sm"], 0),
            pady=SPACING["md"],
        )
        notices_button = SecondaryButton(
            dialog.actions,
            text=notices_label,
            command=open_notices,
        )
        notices_button.pack(
            side="left",
            padx=(SPACING["lg"], 0),
            pady=SPACING["md"],
        )
        close_button = PrimaryButton(
            dialog.actions,
            text=close_label,
            command=dialog.close,
            width=112,
        )
        close_button.pack(
            side="right",
            padx=SPACING["lg"],
            pady=SPACING["md"],
        )

        def layout_columns(event) -> None:
            if event.widget is not dialog.window:
                return
            identity.grid_forget()
            technical.grid_forget()
            if event.width < 680:
                identity.grid(row=0, column=0, columnspan=2, sticky="ew")
                technical.grid(
                    row=1,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    pady=(SPACING["md"], 0),
                )
            else:
                identity.grid(
                    row=0,
                    column=0,
                    sticky="nsew",
                    padx=(0, SPACING["sm"]),
                )
                technical.grid(
                    row=0,
                    column=1,
                    sticky="nsew",
                    padx=(SPACING["sm"], 0),
                )

        dialog.window.bind("<Configure>", layout_columns, add="+")
        identity.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, SPACING["sm"]),
        )
        technical.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(SPACING["sm"], 0),
        )
        dialog.set_initial_focus(close_button)
        dialog.show((760, 560), (820, 680))

    def show_problem_report(
        self,
        root: tk.Misc,
        *,
        labels: dict,
        error_code: str,
        build_report: Callable[[str, str, str, bool], str],
        sanitize_report: Callable[[str], str],
        save_report: Callable[[Path, str], None],
        has_support_channel: bool,
        open_support_page: Callable[[], None],
    ) -> None:
        """Collect, review, copy, and save a report entirely on the device."""
        workflow = ProblemReportDialog(
            root,
            labels=labels,
            error_code=error_code,
            build_report=build_report,
            sanitize_report=sanitize_report,
            save_report=save_report,
            has_support_channel=has_support_channel,
            open_support_page=open_support_page,
        )
        workflow.show()


DEFAULT_TK_DIALOGS = TkDialogs()
