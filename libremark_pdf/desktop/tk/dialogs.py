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
        self.window.grab_set()
        if self.initial_focus is not None:
            self.window.after_idle(self._focus_initial)
        self.window.wait_window()
        trigger = self.trigger
        try:
            if trigger is not None and trigger.winfo_exists():
                self.owner.focus_force()
                self.owner.after(100, trigger.focus_force)
        except (AttributeError, tk.TclError):
            pass


class TkDialogs:
    """Call native Tk dialogs without changing their visible contract."""

    def choose_markdown_files(self, title: str, filetypes: list):
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)

    def choose_css_file(self, title: str, filetypes: list):
        return filedialog.askopenfilename(title=title, filetypes=filetypes)

    def choose_output_folder(self, title: str):
        return filedialog.askdirectory(title=title)

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

    def ask_restore_header_footer(self, title: str, message: str) -> bool:
        """Confirm replacing customized header/footer fields with defaults."""
        return messagebox.askyesno(title, message, default=messagebox.NO)

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

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

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
            padx=SPACING["lg"],
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
        save_report: Callable[[Path, str], None],
        has_support_channel: bool,
        open_support_page: Callable[[], None],
    ) -> None:
        """Collect, review, copy, and save a report entirely on the device."""
        dialog = tk.Toplevel(root)
        dialog.title(labels["report_title"])
        dialog.transient(root)
        dialog.resizable(True, True)
        dialog.minsize(600, 620)

        content = ttk.Frame(dialog, padding=16)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        row = 0
        ttk.Label(content, text=labels["report_summary"]).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        summary = ttk.Entry(content, takefocus=True)
        summary.grid(row=row, column=0, sticky="ew", pady=(4, 10))
        row += 1
        ttk.Label(content, text=labels["report_steps"]).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        steps = tk.Text(content, height=3, wrap="word", takefocus=True)
        steps.grid(row=row, column=0, sticky="ew", pady=(4, 10))
        row += 1
        ttk.Label(content, text=labels["report_expected"]).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        expected = tk.Text(content, height=2, wrap="word", takefocus=True)
        expected.grid(row=row, column=0, sticky="ew", pady=(4, 10))
        row += 1
        if error_code:
            ttk.Label(
                content,
                text="{0}: {1}".format(labels["report_error_code"], error_code),
            ).grid(row=row, column=0, sticky="w", pady=(0, 8))
            row += 1

        include_diagnostics = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            content,
            text=labels["include_diagnostics"],
            variable=include_diagnostics,
            takefocus=True,
        ).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Label(
            content,
            text=labels["diagnostics_consent"],
            justify="left",
            wraplength=680,
        ).grid(row=row, column=0, sticky="ew", pady=(2, 8))
        row += 1
        ttk.Label(
            content,
            text=labels["report_local_help"],
            justify="left",
            wraplength=680,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))
        row += 1

        review_button = ttk.Button(content, text=labels["preview_report"])
        review_button.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        ttk.Label(content, text=labels["report_preview"]).grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        report = tk.Text(content, height=12, wrap="word", takefocus=True)
        content.rowconfigure(row, weight=1)
        report.grid(row=row, column=0, sticky="nsew", pady=(4, 4))
        row += 1
        status = ttk.Label(content, takefocus=True, wraplength=680)
        status.grid(row=row, column=0, sticky="ew")
        row += 1
        if not has_support_channel:
            ttk.Label(
                content,
                text=labels["support_not_configured"],
                justify="left",
                wraplength=680,
            ).grid(row=row, column=0, sticky="ew", pady=(4, 0))
            row += 1
        actions = ttk.Frame(content)
        actions.grid(row=row, column=0, sticky="ew", pady=(12, 0))

        def reviewed_text() -> str:
            return report.get("1.0", "end-1c")

        def refresh_report() -> bool:
            summary_text = summary.get().strip()
            if not summary_text:
                status.configure(text=labels["report_summary_required"])
                summary.focus_set()
                return False
            text = build_report(
                summary_text,
                steps.get("1.0", "end-1c"),
                expected.get("1.0", "end-1c"),
                bool(include_diagnostics.get()),
            )
            report.delete("1.0", "end")
            report.insert("1.0", text)
            report.focus_set()
            status.configure(text="")
            return True

        def ensure_reviewed() -> bool:
            if reviewed_text().strip():
                return True
            refresh_report()
            return False

        def copy() -> None:
            if not ensure_reviewed():
                return
            try:
                root.clipboard_clear()
                root.clipboard_append(reviewed_text())
                status.configure(text=labels["report_copied"])
            except Exception as exc:
                status.configure(
                    text=labels["report_copy_error"].format(error=str(exc))
                )

        def save() -> None:
            if not ensure_reviewed():
                return
            selected = filedialog.asksaveasfilename(
                parent=dialog,
                title=labels["report_save_title"],
                defaultextension=".txt",
                filetypes=[(labels["report_text_filter"], "*.txt")],
            )
            if not selected:
                return
            try:
                save_report(Path(selected), reviewed_text())
                status.configure(
                    text=labels["report_saved"].format(path=selected)
                )
            except Exception as exc:
                status.configure(
                    text=labels["report_save_error"].format(error=str(exc))
                )

        def open_support() -> None:
            try:
                open_support_page()
            except Exception as exc:
                status.configure(
                    text=labels["support_open_error"].format(error=str(exc))
                )

        def close(event=None) -> str:
            dialog.destroy()
            return "break"

        def select_report(event=None) -> str:
            report.tag_add("sel", "1.0", "end-1c")
            return "break"

        review_button.configure(command=refresh_report)
        ttk.Button(actions, text=labels["copy_report"], command=copy).pack(
            side="left"
        )
        ttk.Button(actions, text=labels["save_report"], command=save).pack(
            side="left", padx=(8, 0)
        )
        if has_support_channel:
            ttk.Button(
                actions,
                text=labels["open_support_channel"],
                command=open_support,
            ).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text=labels["close_action"], command=close).pack(
            side="right"
        )
        report.bind("<Control-a>", select_report)
        dialog.protocol("WM_DELETE_WINDOW", close)
        dialog.bind("<Escape>", close)
        dialog.grab_set()
        summary.focus_set()
        dialog.wait_window()


DEFAULT_TK_DIALOGS = TkDialogs()
