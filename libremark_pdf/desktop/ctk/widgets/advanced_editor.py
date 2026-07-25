"""Modern advanced-options editor projected from the desktop settings draft."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Mapping, Sequence

import customtkinter as ctk

from ..components import PrimaryButton, SecondaryButton
from ..theme import COLORS, SPACING, SystemFontResolver


class AdvancedEditorPanel(ctk.CTkFrame):
    """Edit render date and trusted static HTML without owning application state."""

    def __init__(
        self,
        master,
        fonts: SystemFontResolver,
        render_date_var: tk.StringVar,
        trusted_html_var: tk.BooleanVar,
        error_var: tk.StringVar,
        on_trusted_html_changed: Callable[[], None],
        on_save: Callable[[], None],
        on_cancel: Callable[[], None],
        show_back: bool = False,
    ) -> None:
        super().__init__(master, fg_color=COLORS["app_bg"], corner_radius=0)
        self._error_var = error_var
        self.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["md"], SPACING["xs"]),
        )
        self.header.grid_columnconfigure(1, weight=1)
        self.back_button = SecondaryButton(
            self.header, text="", command=on_cancel, width=88, height=32
        )
        if show_back:
            self.back_button.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        self.title_label = ctk.CTkLabel(
            self.header,
            text="",
            anchor="w",
            text_color=COLORS["text"],
            font=fonts.font("dialog_title"),
        )
        self.title_label.grid(row=0, column=1, sticky="ew")
        self.description_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            justify="left",
            wraplength=600,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.description_label.grid(
            row=1, column=0, sticky="ew", padx=SPACING["lg"]
        )

        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.content.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=SPACING["lg"],
            pady=SPACING["sm"],
        )
        self.grid_rowconfigure(2, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.date_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            text_color=COLORS["text"],
            font=fonts.font("label"),
        )
        self.date_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["md"], SPACING["xs"]),
        )
        self.date_entry = ttk.Entry(
            self.content,
            textvariable=render_date_var,
        )
        self.date_entry.grid(
            row=1, column=0, sticky="ew", padx=SPACING["lg"]
        )
        self.date_help_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            justify="left",
            wraplength=560,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.date_help_label.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["xs"], 0),
        )
        self.error_label = ctk.CTkLabel(
            self.content,
            textvariable=error_var,
            anchor="w",
            justify="left",
            wraplength=560,
            text_color=COLORS["error"],
            font=fonts.font("secondary"),
        )
        self.error_label.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["xs"], 0),
        )
        self.trusted_html_switch = ctk.CTkSwitch(
            self.content,
            text="",
            variable=trusted_html_var,
            command=on_trusted_html_changed,
            onvalue=True,
            offvalue=False,
            font=fonts.font("label"),
        )
        self.trusted_html_switch.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["sm"], 0),
        )
        self.security_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            justify="left",
            wraplength=560,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.security_label.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["xs"], SPACING["md"]),
        )
        error_var.trace_add("write", self._sync_date_message)
        self._sync_date_message()

        self.actions = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=0,
        )
        self.actions.grid(row=3, column=0, sticky="ew")
        self.actions.grid_columnconfigure(0, weight=1)
        self.cancel_button = SecondaryButton(
            self.actions, text="", command=on_cancel, width=104
        )
        self.cancel_button.grid(
            row=0, column=1, padx=(SPACING["sm"], 0), pady=SPACING["sm"]
        )
        self.save_button = PrimaryButton(
            self.actions, text="", command=on_save, width=104
        )
        self.save_button.grid(
            row=0,
            column=2,
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=SPACING["sm"],
        )

    def _sync_date_message(self, *unused) -> None:
        """Use one compact inline row for automatic help or validation."""
        if self._error_var.get():
            self.date_help_label.grid_remove()
            self.error_label.grid()
        else:
            self.error_label.grid_remove()
            self.date_help_label.grid()

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update copy without changing either draft value."""
        self.title_label.configure(text=labels["title"])
        self.description_label.configure(text=labels["description"])
        self.back_button.configure(text=labels["back"])
        self.date_label.configure(text=labels["date"])
        self.date_help_label.configure(text=labels["date_help"])
        self.trusted_html_switch.configure(text=labels["trusted_html"])
        self.security_label.configure(text=labels["security"])
        self.cancel_button.configure(text=labels["cancel"])
        self.save_button.configure(text=labels["save"])

    def focus_initial(self) -> None:
        """Place initial keyboard focus in the render-date field."""
        self.date_entry.focus_set()


__all__: Sequence[str] = ("AdvancedEditorPanel",)
