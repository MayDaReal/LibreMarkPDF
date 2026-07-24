"""Central light-theme tokens and system font resolution."""

from __future__ import annotations

import os
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from typing import Dict, Mapping, Tuple

import customtkinter as ctk


COLORS = {
    "app_bg": "#F5F7FA",
    "surface": "#FFFFFF",
    "surface_subtle": "#F8FAFC",
    "surface_selected": "#EAF2FF",
    "surface_hover": "#F1F5F9",
    "border": "#D7DEE8",
    "border_strong": "#B8C4D4",
    "text": "#172033",
    "text_secondary": "#5B6678",
    "text_muted": "#7A8494",
    "primary": "#0B5ED7",
    "primary_hover": "#084DB4",
    "primary_pressed": "#073F94",
    "primary_subtle": "#E8F1FF",
    "success": "#16803C",
    "success_subtle": "#EAF7EE",
    "warning": "#A15C00",
    "warning_subtle": "#FFF4E0",
    "error": "#C62828",
    "error_subtle": "#FDECEC",
    "info": "#1769C2",
    "info_subtle": "#EAF3FF",
    "preview_bg": "#E8EBF0",
    "page_bg": "#FFFFFF",
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

RADII = {
    "control": 6,
    "card": 8,
    "dialog_panel": 8,
    "pill": 999,
}

SIZES = {
    "button": 36,
    "primary_button": 40,
    "icon_button": 32,
    "field": 36,
    "tab": 38,
    "header": 56,
}

FONT_SPECS = {
    "product": (17, "bold"),
    "panel_title": (14, "bold"),
    "dialog_title": (18, "bold"),
    "label": (13, "bold"),
    "body": (13, "normal"),
    "secondary": (12, "normal"),
    "badge": (11, "bold"),
    "technical": (12, "normal"),
}

ICON_COLORS = {
    "neutral": COLORS["text"],
    "accent": COLORS["primary"],
    "success": COLORS["success"],
    "error": COLORS["error"],
}


@dataclass(frozen=True)
class FontFamilies:
    """Resolved installed font families for interface and technical text."""

    interface: str
    monospace: str


class SystemFontResolver:
    """Resolve the prescribed system font stack without bundling UI fonts."""

    WINDOWS_UI = ("Segoe UI", "TkDefaultFont")
    OTHER_UI = ("Noto Sans", "DejaVu Sans", "TkDefaultFont")
    WINDOWS_MONO = ("Cascadia Mono", "Consolas", "TkFixedFont")
    OTHER_MONO = ("Cascadia Mono", "Consolas", "DejaVu Sans Mono", "TkFixedFont")

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self._installed = {
            family.casefold(): family for family in tkfont.families(root)
        }
        self.families = FontFamilies(
            interface=self._first_available(
                self.WINDOWS_UI if os.name == "nt" else self.OTHER_UI
            ),
            monospace=self._first_available(
                self.WINDOWS_MONO if os.name == "nt" else self.OTHER_MONO
            ),
        )
        self._fonts = {}  # type: Dict[Tuple[str, bool], ctk.CTkFont]

    def _first_available(self, candidates: Tuple[str, ...]) -> str:
        for candidate in candidates:
            installed = self._installed.get(candidate.casefold())
            if installed:
                return installed
            if candidate.startswith("Tk"):
                return candidate
        return candidates[-1]

    def font(self, role: str, monospace: bool = False) -> ctk.CTkFont:
        """Return a retained CustomTkinter font for a named typography role."""
        if role not in FONT_SPECS:
            raise KeyError("Unknown typography role: {0}".format(role))
        key = (role, monospace)
        if key not in self._fonts:
            size, weight = FONT_SPECS[role]
            family = (
                self.families.monospace
                if monospace
                else self.families.interface
            )
            self._fonts[key] = ctk.CTkFont(
                family=family,
                size=size,
                weight=weight,
            )
        return self._fonts[key]

    @property
    def retained_fonts(self) -> Mapping[Tuple[str, bool], ctk.CTkFont]:
        """Expose retained font objects for diagnostics and tests."""
        return dict(self._fonts)


def install_light_theme() -> None:
    """Keep the application in the mandatory light appearance mode."""
    ctk.set_appearance_mode("light")
