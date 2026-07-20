"""Small reusable Tk components for accessible desktop actions."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional


REMOVE_ICON_XBM = """
#define remove_width 16
#define remove_height 16
static unsigned char remove_bits[] = {
   0x00, 0x00, 0x02, 0x40, 0x06, 0x60, 0x0c, 0x30,
   0x18, 0x18, 0x30, 0x0c, 0x60, 0x06, 0xc0, 0x03,
   0xc0, 0x03, 0x60, 0x06, 0x30, 0x0c, 0x18, 0x18,
   0x0c, 0x30, 0x06, 0x60, 0x02, 0x40, 0x00, 0x00};
"""


class UiIconRegistry:
    """Own local UI images for the lifetime of a Tk application."""

    def __init__(self, root: tk.Misc) -> None:
        foreground = ttk.Style(root).lookup("TButton", "foreground") or "black"
        self.remove = tk.BitmapImage(
            master=root,
            data=REMOVE_ICON_XBM,
            foreground=foreground,
        )


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


def configure_icon_button(
    button: ttk.Button,
    image: tk.BitmapImage,
    accessible_name: str,
) -> Tooltip:
    """Configure an image-only button while retaining localized Tk text."""
    button.configure(
        text=accessible_name,
        image=image,
        compound="none",
        takefocus=True,
        width=2,
    )
    button.accessible_name = accessible_name
    tooltip = Tooltip(button, accessible_name)
    button.tooltip = tooltip
    return tooltip
