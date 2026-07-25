"""Top-level modern shell with fixed header and action regions."""

from __future__ import annotations

import customtkinter as ctk

from .theme import COLORS


class AppShell(ctk.CTkFrame):
    """Own the non-scrolling window regions around reusable content panels."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "corner_radius": 0,
            "fg_color": COLORS["app_bg"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.content = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=COLORS["app_bg"],
        )
        self.content.grid(row=1, column=0, sticky="nsew")

    def attach_header(self, header) -> None:
        """Place a header in the shell's fixed top region."""
        header.grid(row=0, column=0, sticky="ew")

    def attach_action_bar(self, action_bar) -> None:
        """Place an action bar in the shell's fixed bottom region."""
        action_bar.grid(row=2, column=0, sticky="ew")
