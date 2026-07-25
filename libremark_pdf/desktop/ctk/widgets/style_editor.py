"""Modern PDF-style editor projected from the desktop settings draft."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Mapping, Sequence, Tuple

import customtkinter as ctk

from ..components import PrimaryButton, SecondaryButton
from ..theme import COLORS, SPACING, SystemFontResolver


class StyleEditorPanel(ctk.CTkFrame):
    """Edit the theme/CSS draft without owning application state."""

    def __init__(
        self,
        master,
        fonts: SystemFontResolver,
        style_mode_var: tk.StringVar,
        theme_display_var: tk.StringVar,
        css_display_var: tk.StringVar,
        error_var: tk.StringVar,
        on_mode_changed: Callable[[], None],
        on_theme_changed: Callable[[str], None],
        on_choose_css: Callable[[], None],
        on_save: Callable[[], None],
        on_cancel: Callable[[], None],
        show_back: bool = False,
    ) -> None:
        super().__init__(master, fg_color=COLORS["app_bg"], corner_radius=0)
        self._fonts = fonts
        self._on_theme_changed = on_theme_changed
        self._theme_references = ()  # type: Tuple[str, ...]
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

        self.theme_radio = ttk.Radiobutton(
            self.content,
            variable=style_mode_var,
            value="theme",
            command=on_mode_changed,
        )
        self.theme_radio.grid(
            row=0, column=0, sticky="w", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"])
        )
        self.theme_combo = ttk.Combobox(
            self.content,
            textvariable=theme_display_var,
            state="readonly",
        )
        self.theme_combo.grid(
            row=1, column=0, sticky="ew", padx=SPACING["lg"]
        )
        self.theme_combo.bind("<<ComboboxSelected>>", self._select_theme)
        self.theme_technical_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            text_color=COLORS["text_muted"],
            font=fonts.font("secondary"),
        )
        self.theme_technical_label.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=SPACING["lg"],
            pady=(SPACING["xs"], SPACING["lg"]),
        )

        self.css_radio = ttk.Radiobutton(
            self.content,
            variable=style_mode_var,
            value="css",
            command=on_mode_changed,
        )
        self.css_radio.grid(
            row=3, column=0, sticky="w", padx=SPACING["lg"], pady=(0, SPACING["sm"])
        )
        self.css_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.css_row.grid(row=4, column=0, sticky="ew", padx=SPACING["lg"])
        self.css_row.grid_columnconfigure(0, weight=1)
        self.css_entry = ttk.Entry(
            self.css_row,
            textvariable=css_display_var,
            state="readonly",
        )
        self.css_entry.grid(row=0, column=0, sticky="ew")
        self.choose_button = SecondaryButton(
            self.css_row,
            text="",
            command=on_choose_css,
            width=132,
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
            row=5,
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

    def _select_theme(self, _event=None) -> None:
        index = self.theme_combo.current()
        if 0 <= index < len(self._theme_references):
            self._on_theme_changed(self._theme_references[index])

    def set_themes(
        self,
        themes: Sequence[Tuple[str, str]],
        selected_reference: str,
        technical_text: str,
    ) -> None:
        """Project localized theme names while retaining stable references."""
        self._theme_references = tuple(reference for reference, _name in themes)
        names = tuple(name for _reference, name in themes)
        self.theme_combo.configure(values=names)
        try:
            index = self._theme_references.index(selected_reference)
        except ValueError:
            index = 0 if names else -1
        if index >= 0:
            self.theme_combo.current(index)
        self.theme_technical_label.configure(text=technical_text)

    def set_mode(self, mode: str) -> None:
        """Expose only controls relevant to the exclusive draft choice."""
        self.theme_combo.configure(state="readonly" if mode == "theme" else "disabled")
        self.css_entry.configure(state="readonly")

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update visible copy without changing draft variables."""
        self.title_label.configure(text=labels["title"])
        self.description_label.configure(text=labels["description"])
        self.back_button.configure(text=labels["back"])
        self.theme_radio.configure(text=labels["local_theme"])
        self.css_radio.configure(text=labels["custom_css"])
        self.choose_button.configure(text=labels["choose_css"])
        self.cancel_button.configure(text=labels["cancel"])
        self.save_button.configure(text=labels["save"])

    def focus_initial(self, mode: str) -> None:
        """Place keyboard focus on the active choice."""
        (self.css_radio if mode == "css" else self.theme_radio).focus_set()


__all__ = ("StyleEditorPanel",)
