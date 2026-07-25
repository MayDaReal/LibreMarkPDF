"""Small reusable Tk components for accessible desktop actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional


class Tooltip:
    """Show localized help for a widget on pointer hover or keyboard focus."""

    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None  # type: Optional[str]
        self._window = None  # type: Optional[tk.Toplevel]
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<FocusIn>", self._schedule, add="+")
        widget.bind("<FocusOut>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        self._after_id = None
        if self._window is not None or not self.text:
            return
        window = tk.Toplevel(self.widget)
        window.wm_overrideredirect(True)
        window.wm_geometry(
            "+{0}+{1}".format(
                self.widget.winfo_rootx(),
                self.widget.winfo_rooty() + self.widget.winfo_height() + 4,
            )
        )
        ttk.Label(window, text=self.text, padding=(6, 3)).pack()
        self._window = window

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None


def configure_symbol_button(
    button: ttk.Button,
    symbol: str,
    accessible_name: str,
) -> Tooltip:
    """Configure a local symbol action with keyboard and tooltip support."""
    button.configure(text=symbol, takefocus=True, width=3)
    button.accessible_name = accessible_name
    tooltip = Tooltip(button, accessible_name)
    button.tooltip = tooltip
    return tooltip
