"""Stable four-tab navigation for the compact desktop layout."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Mapping, Sequence

import customtkinter as ctk

from ..components import FocusRing
from ..theme import COLORS, RADII, SIZES, SPACING, SystemFontResolver


class CompactTabBar(ctk.CTkFrame):
    """Select one reusable content panel without owning application state."""

    TAB_NAMES = ("files", "preview", "settings", "results")

    def __init__(
        self,
        master,
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        on_select: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            height=SIZES["tab"],
            corner_radius=0,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        self.grid_propagate(False)
        self._active = "files"
        self._on_select = on_select
        self.buttons = {}  # type: Dict[str, ctk.CTkButton]
        for index, name in enumerate(self.TAB_NAMES):
            self.grid_columnconfigure(index, weight=1, uniform="compact-tab")
            button = ctk.CTkButton(
                self,
                text=labels[name],
                command=lambda selected=name: self.select(selected),
                height=SIZES["tab"],
                corner_radius=RADII["control"],
                fg_color="transparent",
                hover_color=COLORS["surface_hover"],
                border_color=COLORS["surface"],
                border_width=1,
                text_color=COLORS["text_secondary"],
                font=fonts.font("secondary"),
            )
            tk.Frame.configure(button, takefocus=True)
            FocusRing(
                button,
                normal_color=COLORS["surface"],
                normal_width=1,
                focus_color=COLORS["primary"],
            )
            button.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=(SPACING["xs"] if index == 0 else 0, SPACING["xs"]),
            )
            button.bind("<Return>", lambda _event, tab=name: self.select(tab))
            button.bind("<space>", lambda _event, tab=name: self.select(tab))
            button.bind("<Left>", lambda _event, tab=name: self._move(tab, -1))
            button.bind("<Right>", lambda _event, tab=name: self._move(tab, 1))
            button.bind("<Home>", lambda _event: self._focus("files"))
            button.bind("<End>", lambda _event: self._focus("results"))
            self.buttons[name] = button
        self.set_active("files")

    @property
    def active(self) -> str:
        """Return the selected session tab."""
        return self._active

    def select(self, name: str):
        """Notify the layout owner of an explicit tab selection."""
        if name not in self.buttons:
            raise ValueError("Unknown compact tab: {0}".format(name))
        self._on_select(name)
        return "break"

    def set_active(self, name: str) -> None:
        """Project active state without invoking the selection callback."""
        if name not in self.buttons:
            raise ValueError("Unknown compact tab: {0}".format(name))
        self._active = name
        for tab_name, button in self.buttons.items():
            selected = tab_name == name
            button.configure(
                fg_color=(
                    COLORS["primary_subtle"] if selected else "transparent"
                ),
                text_color=(
                    COLORS["primary"] if selected else COLORS["text_secondary"]
                ),
            )

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update all four labels without changing the active tab."""
        for name, button in self.buttons.items():
            button.configure(text=labels[name])

    def focus_active(self) -> None:
        """Move focus to the selected visible tab control."""
        self.buttons[self._active].focus_set()

    def _move(self, current: str, delta: int):
        index = self.TAB_NAMES.index(current)
        target = self.TAB_NAMES[(index + delta) % len(self.TAB_NAMES)]
        self.select(target)
        self._focus(target)
        return "break"

    def _focus(self, name: str):
        self.buttons[name].focus_set()
        return "break"


__all__: Sequence[str] = ("CompactTabBar",)
