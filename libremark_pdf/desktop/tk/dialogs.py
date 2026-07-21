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
    ) -> None:
        """Show selectable local identities and an explicit clipboard action."""
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.transient(root)
        dialog.resizable(True, True)

        content = ttk.Frame(dialog, padding=16)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text=version_text).pack(anchor="w")
        ttk.Label(content, text=technical_heading).pack(
            anchor="w", pady=(16, 4)
        )
        details = tk.Text(
            content,
            width=62,
            height=8,
            wrap="none",
            takefocus=True,
        )
        details.insert("1.0", technical_text)
        details.configure(state="disabled")
        details.pack(fill="both", expand=True)
        status = ttk.Label(content, takefocus=True)
        status.pack(fill="x", pady=(4, 0))
        actions = ttk.Frame(content)
        actions.pack(fill="x", pady=(12, 0))

        def copy_information() -> None:
            root.clipboard_clear()
            root.clipboard_append(technical_text)
            status.configure(text=copied_text)

        def close(event=None) -> str:
            dialog.destroy()
            return "break"

        def select_all(event=None) -> str:
            details.tag_add("sel", "1.0", "end-1c")
            return "break"

        copy_button = ttk.Button(
            actions,
            text=copy_label,
            command=copy_information,
        )
        copy_button.pack(side="left")
        ttk.Button(actions, text=close_label, command=close).pack(side="right")
        details.bind("<Control-a>", select_all)
        dialog.protocol("WM_DELETE_WINDOW", close)
        dialog.bind("<Escape>", close)
        dialog.grab_set()
        copy_button.focus_set()
        dialog.wait_window()


DEFAULT_TK_DIALOGS = TkDialogs()
