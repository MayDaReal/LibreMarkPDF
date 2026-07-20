"""Injectable boundary for the existing native Tk dialogs."""

from __future__ import annotations

from tkinter import filedialog, messagebox


class TkDialogs:
    """Call native Tk dialogs without changing their visible contract."""

    def choose_markdown_files(self, title: str, filetypes: list):
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)

    def choose_css_file(self, title: str, filetypes: list):
        return filedialog.askopenfilename(title=title, filetypes=filetypes)

    def choose_output_folder(self, title: str):
        return filedialog.askdirectory(title=title)

    def ask_collision_continue(self, title: str, message: str) -> bool:
        return messagebox.askokcancel(title, message)

    def ask_overwrite(self, title: str, message: str):
        return messagebox.askyesnocancel(title, message)

    def ask_trusted_html(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, default=messagebox.NO)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)


DEFAULT_TK_DIALOGS = TkDialogs()
