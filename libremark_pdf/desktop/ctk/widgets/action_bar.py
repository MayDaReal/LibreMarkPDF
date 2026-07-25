"""Fixed modern action bar for the ready shell state."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

import customtkinter as ctk

from ..components import PrimaryButton, SecondaryButton
from ..theme import COLORS, SPACING, SystemFontResolver


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
    """Keep the primary action fixed and centered in the whole window."""

    def __init__(
        self,
        master,
        fonts: SystemFontResolver,
        on_generate: Callable[[], None],
        on_cancel: Callable[[], None],
        progress_variable: tk.Variable,
        generate_icon,
    ) -> None:
        super().__init__(
            master,
            height=64,
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
        self.status_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(SPACING["lg"], SPACING["sm"]),
            pady=SPACING["sm"],
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
        self.generate_button.grid(
            row=0,
            column=1,
            pady=SPACING["sm"],
        )
        self.cancel_button = SecondaryButton(
            self,
            text="",
            command=on_cancel,
            width=190,
            font=fonts.font("body"),
        )
        self.cancel_button.grid(
            row=0,
            column=2,
            sticky="e",
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=SPACING["sm"],
        )
        self.progress = ttk.Progressbar(
            self,
            variable=progress_variable,
            maximum=1,
            takefocus=True,
        )
        self.progress.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(0, SPACING["sm"]),
        )
        self.cancel_button.grid_remove()
        self.progress.grid_remove()
        self._layout_mode = "large"

    def set_conversion_active(self, active: bool) -> None:
        """Show legacy progress controls only while a conversion is active."""
        if active:
            self.cancel_button.grid()
            self.progress.grid()
        else:
            self.cancel_button.grid_remove()
            self.progress.grid_remove()

    def set_layout_mode(self, mode: str) -> None:
        """Project the same actions into the compact or full-width layout."""
        if mode == self._layout_mode:
            return
        self._layout_mode = mode
        conversion_active = bool(self.progress.winfo_manager())
        for widget in (
            self.status_label,
            self.generate_button,
            self.cancel_button,
            self.progress,
        ):
            widget.grid_forget()
        if mode == "compact":
            self.status_label.grid(
                row=0,
                column=0,
                columnspan=3,
                sticky="ew",
                padx=SPACING["md"],
                pady=(SPACING["xs"], 0),
            )
            self.generate_button.grid(
                row=1,
                column=0,
                columnspan=3,
                sticky="ew",
                padx=SPACING["md"],
                pady=SPACING["xs"],
            )
            if conversion_active:
                self.cancel_button.grid(
                    row=2,
                    column=0,
                    columnspan=3,
                    sticky="ew",
                    padx=SPACING["md"],
                    pady=(0, SPACING["sm"]),
                )
                self.progress.grid(
                    row=3,
                    column=0,
                    columnspan=3,
                    sticky="ew",
                    padx=SPACING["md"],
                    pady=(0, SPACING["sm"]),
                )
            return
        self.status_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(SPACING["lg"], SPACING["sm"]),
            pady=SPACING["sm"],
        )
        self.generate_button.configure(width=280)
        self.generate_button.grid(row=0, column=1, pady=SPACING["sm"])
        if conversion_active:
            self.cancel_button.grid(
                row=0,
                column=2,
                sticky="e",
                padx=(SPACING["sm"], SPACING["lg"]),
                pady=SPACING["sm"],
            )
            self.progress.grid(
                row=1,
                column=0,
                columnspan=3,
                sticky="ew",
                padx=SPACING["lg"],
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
