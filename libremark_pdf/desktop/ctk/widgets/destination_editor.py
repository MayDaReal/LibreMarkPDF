"""Modern destination editor projected from the desktop settings draft."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Mapping, Sequence

import customtkinter as ctk

from ..components import PrimaryButton, SecondaryButton
from ..theme import COLORS, SPACING, SystemFontResolver


class DestinationEditorPanel(ctk.CTkFrame):
    """Edit the output-folder draft without owning application state."""

    def __init__(
        self,
        master,
        fonts: SystemFontResolver,
        mode_var: tk.StringVar,
        path_var: tk.StringVar,
        error_var: tk.StringVar,
        on_mode_changed: Callable[[], None],
        on_choose_folder: Callable[[], None],
        on_save: Callable[[], None],
        on_cancel: Callable[[], None],
        show_back: bool = False,
    ) -> None:
        super().__init__(master, fg_color=COLORS["app_bg"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["lg"], SPACING["md"]),
        )
        self.header.grid_columnconfigure(1, weight=1)
        self.back_button = SecondaryButton(
            self.header,
            text="",
            command=on_cancel,
            width=88,
            height=32,
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
            row=1,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
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
            pady=SPACING["lg"],
        )
        self.grid_rowconfigure(2, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.source_radio = ttk.Radiobutton(
            self.content,
            variable=mode_var,
            value="source",
            command=on_mode_changed,
        )
        self.source_radio.grid(
            row=0,
            column=0,
            sticky="w",
            padx=SPACING["lg"],
            pady=(SPACING["lg"], SPACING["lg"]),
        )
        self.custom_radio = ttk.Radiobutton(
            self.content,
            variable=mode_var,
            value="custom",
            command=on_mode_changed,
        )
        self.custom_radio.grid(
            row=1,
            column=0,
            sticky="w",
            padx=SPACING["lg"],
            pady=(0, SPACING["sm"]),
        )
        self.path_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.path_row.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"])
        self.path_row.grid_columnconfigure(0, weight=1)
        self.path_entry = ttk.Entry(
            self.path_row,
            textvariable=path_var,
            state="readonly",
        )
        self.path_entry.grid(row=0, column=0, sticky="ew")
        self.choose_button = SecondaryButton(
            self.path_row,
            text="",
            command=on_choose_folder,
            width=112,
        )
        self.choose_button.grid(row=0, column=1, padx=(SPACING["sm"], 0))
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
            row=3,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["xs"], SPACING["lg"]),
        )

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
            row=0, column=1, padx=(SPACING["sm"], 0), pady=SPACING["md"]
        )
        self.save_button = PrimaryButton(
            self.actions, text="", command=on_save, width=104
        )
        self.save_button.grid(
            row=0,
            column=2,
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=SPACING["md"],
        )

    def set_mode(self, mode: str) -> None:
        """Disable the custom path controls when source folders are active."""
        state = "normal" if mode == "custom" else "disabled"
        self.path_entry.configure(state="readonly" if mode == "custom" else "disabled")
        self.choose_button.configure(state=state)

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update visible copy without changing the destination draft."""
        self.title_label.configure(text=labels["title"])
        self.description_label.configure(text=labels["description"])
        self.back_button.configure(text=labels["back"])
        self.source_radio.configure(text=labels["source"])
        self.custom_radio.configure(text=labels["custom"])
        self.choose_button.configure(text=labels["choose"])
        self.cancel_button.configure(text=labels["cancel"])
        self.save_button.configure(text=labels["save"])

    def focus_initial(self, mode: str) -> None:
        """Place keyboard focus on the active exclusive choice."""
        (self.custom_radio if mode == "custom" else self.source_radio).focus_set()


__all__: Sequence[str] = ("DestinationEditorPanel",)
