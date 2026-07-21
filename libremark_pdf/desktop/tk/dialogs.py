"""Injectable boundary for the existing native Tk dialogs."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


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

    def ask_trusted_html(self, title: str, message: str) -> bool:
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
        return self._ask_explicit_choice(
            root,
            title,
            message,
            (
                ("continue", continue_label),
                ("cancel_close", cancel_close_label),
            ),
            default_choice="continue",
            dismiss_choice="continue",
        )

    def _ask_explicit_choice(
        self,
        root: tk.Misc,
        title: str,
        message: str,
        choices: tuple,
        default_choice: str,
        dismiss_choice: str,
    ) -> str:
        """Show local labelled choices without relying on platform Yes/No copy."""
        choice = dismiss_choice
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.transient(root)
        dialog.resizable(False, False)

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
        dialog.grab_set()
        if default_button is not None:
            default_button.focus_set()
        dialog.wait_window()
        return choice

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)


DEFAULT_TK_DIALOGS = TkDialogs()
