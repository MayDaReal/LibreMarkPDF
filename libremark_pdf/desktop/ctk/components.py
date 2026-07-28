"""Atomic CustomTkinter components for the modern desktop interface."""

from __future__ import annotations

import os
import tkinter as tk
from typing import Callable, Dict, Optional

import customtkinter as ctk

from .theme import COLORS, RADII, SIZES, SPACING, SystemFontResolver


def monitor_work_area(widget: tk.Misc):
    """Return the work area containing a widget, including virtual offsets."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class MonitorInfo(ctypes.Structure):
                _fields_ = (
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                )

            monitor_from_window = ctypes.windll.user32.MonitorFromWindow
            monitor_from_window.argtypes = (
                wintypes.HWND,
                wintypes.DWORD,
            )
            monitor_from_window.restype = wintypes.HANDLE
            get_monitor_info = ctypes.windll.user32.GetMonitorInfoW
            get_monitor_info.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(MonitorInfo),
            )
            get_monitor_info.restype = wintypes.BOOL
            monitor = monitor_from_window(widget.winfo_id(), 2)
            information = MonitorInfo()
            information.cbSize = ctypes.sizeof(MonitorInfo)
            if monitor and get_monitor_info(
                monitor,
                ctypes.byref(information),
            ):
                rectangle = information.rcWork
                return (
                    rectangle.left,
                    rectangle.top,
                    rectangle.right - rectangle.left,
                    rectangle.bottom - rectangle.top,
                )
        except (AttributeError, OSError, ctypes.ArgumentError, tk.TclError):
            pass
    return (
        0,
        0,
        widget.winfo_screenwidth(),
        widget.winfo_screenheight(),
    )


def _tooltip_position(
    widget_bounds,
    tooltip_size,
    work_area,
):
    """Place a tooltip below its widget and inside one monitor work area."""
    widget_x, widget_y, widget_width, widget_height = widget_bounds
    width, height = tooltip_size
    screen_x, screen_y, screen_width, screen_height = work_area
    desired_x = widget_x
    desired_y = widget_y + widget_height + SPACING["xs"]
    screen_right = screen_x + screen_width
    screen_bottom = screen_y + screen_height
    x = max(screen_x, min(desired_x, screen_right - width))
    if desired_y + height > screen_bottom:
        desired_y = widget_y - height - SPACING["xs"]
    y = max(screen_y, min(desired_y, screen_bottom - height))
    return x, y


class FocusRing:
    """Apply a visible two-pixel focus border through public widget APIs."""

    def __init__(
        self,
        widget: ctk.CTkButton,
        normal_color: str,
        normal_width: int,
        focus_color: str,
    ) -> None:
        self.widget = widget
        self.normal_color = normal_color
        self.normal_width = normal_width
        self.focus_color = focus_color
        widget.bind("<FocusIn>", self.show, add="+")
        widget.bind("<FocusOut>", self.hide, add="+")

    def show(self, _event=None) -> None:
        """Render the visible keyboard-focus border."""
        self.widget.configure(border_color=self.focus_color, border_width=2)

    def hide(self, _event=None) -> None:
        """Restore the component's normal border."""
        self.widget.configure(
            border_color=self.normal_color,
            border_width=self.normal_width,
        )


class Tooltip:
    """Display localized, non-interactive help within screen boundaries."""

    def __init__(
        self,
        widget: tk.Misc,
        text: str,
        delay_ms: int = 600,
    ) -> None:
        if delay_ms < 500 or delay_ms > 700:
            raise ValueError("Tooltip delay must be between 500 and 700 ms")
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None  # type: Optional[str]
        self._window = None  # type: Optional[tk.Toplevel]
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Motion>", self._motion, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<Button>", self.hide, add="+")
        widget.bind("<Escape>", self.hide, add="+")
        widget.bind("<FocusIn>", self.schedule, add="+")
        widget.bind("<FocusOut>", self.hide, add="+")
        widget.bind("<Destroy>", self.hide, add="+")

    @property
    def visible(self) -> bool:
        """Return whether the tooltip window currently exists."""
        return self._window is not None

    @property
    def bounds(self):
        """Return visible screen bounds as x, y, width and height."""
        if self._window is None:
            return None
        self._window.update_idletasks()
        return (
            self._window.winfo_rootx(),
            self._window.winfo_rooty(),
            self._window.winfo_width(),
            self._window.winfo_height(),
        )

    def update_text(self, text: str) -> None:
        """Replace localized help and close any visible stale copy."""
        self.text = text
        self.hide()

    def _motion(self, _event=None) -> None:
        self.hide()
        if self.text:
            self._after_id = self.widget.after(self.delay_ms, self._show)

    def schedule(self, _event=None) -> None:
        """Schedule localized help after the prescribed hover delay."""
        self.hide()
        if self.text:
            self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self) -> None:
        self._after_id = None
        if self._window is not None or not self.text:
            return
        window = tk.Toplevel(self.widget)
        window.wm_overrideredirect(True)
        window.wm_attributes("-topmost", True)
        if os.name == "nt":
            try:
                window.wm_attributes("-disabled", True)
            except tk.TclError:
                pass
        label = tk.Label(
            window,
            text=self.text,
            background=COLORS["text"],
            foreground=COLORS["surface"],
            borderwidth=0,
            padx=SPACING["sm"],
            pady=SPACING["xs"],
        )
        label.pack()
        window.update_idletasks()
        width = window.winfo_reqwidth()
        height = window.winfo_reqheight()
        x, y = _tooltip_position(
            (
                self.widget.winfo_rootx(),
                self.widget.winfo_rooty(),
                self.widget.winfo_width(),
                self.widget.winfo_height(),
            ),
            (width, height),
            monitor_work_area(self.widget),
        )
        window.wm_geometry("+{0}+{1}".format(x, y))
        self._window = window

    def hide(self, _event=None) -> None:
        """Cancel a pending tooltip and close the visible window."""
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._window is not None:
            self._window.destroy()
            self._window = None


class _ButtonBase(ctk.CTkButton):
    """Shared keyboard and focus behavior for text and icon buttons."""

    def __init__(
        self,
        master,
        focus_color: str,
        normal_border_color: str,
        normal_border_width: int,
        normal_fg_color: str,
        hover_fg_color: str,
        pressed_fg_color: str,
        disabled_fg_color: str,
        **kwargs
    ) -> None:
        self._normal_fg_color = normal_fg_color
        self._hover_fg_color = hover_fg_color
        self._pressed_fg_color = pressed_fg_color
        self._disabled_fg_color = disabled_fg_color
        initial_state = kwargs.get("state", "normal")
        super().__init__(master, **kwargs)
        # CTkButton rejects the standard Tk option in its constructor. Applying
        # it to the inherited public Tk frame keeps the whole control tabbable.
        tk.Frame.configure(self, takefocus=True)
        self.focus_ring = FocusRing(
            self,
            normal_color=normal_border_color,
            normal_width=normal_border_width,
            focus_color=focus_color,
        )
        self.bind("<Return>", self._keyboard_invoke, add="+")
        self.bind("<space>", self._keyboard_invoke, add="+")
        self.bind("<ButtonPress-1>", self._show_pressed, add="+")
        self.bind("<ButtonRelease-1>", self._restore_normal, add="+")
        if initial_state == "disabled":
            ctk.CTkButton.configure(
                self,
                fg_color=self._disabled_fg_color,
            )

    def _keyboard_invoke(self, _event=None):
        if self.cget("state") != "disabled":
            self.invoke()
        return "break"

    def _show_pressed(self, _event=None) -> None:
        self.set_interaction_state("pressed")

    def _restore_normal(self, _event=None) -> None:
        self.set_interaction_state("normal")

    def set_interaction_state(self, state: str) -> None:
        """Render a normal, hover or pressed state for public UI probes."""
        colors = {
            "normal": self._normal_fg_color,
            "hover": self._hover_fg_color,
            "pressed": self._pressed_fg_color,
        }
        if state not in colors:
            raise ValueError(
                "Unknown button interaction state: {0}".format(state)
            )
        if self.cget("state") != "disabled":
            ctk.CTkButton.configure(self, fg_color=colors[state])

    def configure(self, require_redraw=False, **kwargs):
        """Preserve tokenized visuals when the public disabled state changes."""
        state = kwargs.get("state")
        result = super().configure(require_redraw=require_redraw, **kwargs)
        if state == "disabled":
            self.focus_ring.hide()
            super().configure(
                fg_color=self._disabled_fg_color,
                require_redraw=True,
            )
        elif state == "normal":
            super().configure(
                fg_color=self._normal_fg_color,
                require_redraw=True,
            )
        return result

    config = configure


class PrimaryButton(_ButtonBase):
    """Visually dominant application action."""

    def __init__(self, master, text: str, command: Callable[[], None], **kwargs):
        defaults = {
            "text": text,
            "command": command,
            "height": SIZES["primary_button"],
            "corner_radius": RADII["control"],
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["primary_hover"],
            "border_color": COLORS["primary"],
            "border_width": 0,
            "text_color": COLORS["surface"],
            "text_color_disabled": COLORS["text_muted"],
        }
        defaults.update(kwargs)
        super().__init__(
            master,
            focus_color=COLORS["surface"],
            normal_border_color=COLORS["primary"],
            normal_border_width=0,
            normal_fg_color=COLORS["primary"],
            hover_fg_color=COLORS["primary_hover"],
            pressed_fg_color=COLORS["primary_pressed"],
            disabled_fg_color=COLORS["surface_hover"],
            **defaults
        )


class SecondaryButton(_ButtonBase):
    """Outlined secondary application action."""

    def __init__(self, master, text: str, command: Callable[[], None], **kwargs):
        tone = kwargs.pop("tone", "default")
        if tone not in ("default", "danger"):
            raise ValueError("Unknown secondary button tone: {0}".format(tone))
        border_color = (
            COLORS["error"] if tone == "danger" else COLORS["border_strong"]
        )
        text_color = COLORS["error"] if tone == "danger" else COLORS["primary"]
        hover_color = (
            COLORS["error_subtle"]
            if tone == "danger"
            else COLORS["surface_hover"]
        )
        defaults = {
            "text": text,
            "command": command,
            "height": SIZES["button"],
            "corner_radius": RADII["control"],
            "fg_color": "transparent",
            "hover_color": hover_color,
            "border_color": border_color,
            "border_width": 1,
            "text_color": text_color,
            "text_color_disabled": COLORS["text_muted"],
        }
        defaults.update(kwargs)
        super().__init__(
            master,
            focus_color=COLORS["primary"],
            normal_border_color=border_color,
            normal_border_width=1,
            normal_fg_color="transparent",
            hover_fg_color=hover_color,
            pressed_fg_color=(
                COLORS["error_subtle"]
                if tone == "danger"
                else COLORS["surface_selected"]
            ),
            disabled_fg_color=COLORS["surface_hover"],
            **defaults
        )


class IconButton(_ButtonBase):
    """Compact icon-only action with a localized accessible name."""

    def __init__(
        self,
        master,
        image: ctk.CTkImage,
        accessible_name: str,
        command: Callable[[], None],
        **kwargs
    ) -> None:
        defaults = {
            "text": "",
            "image": image,
            "command": command,
            "width": SIZES["icon_button"],
            "height": SIZES["icon_button"],
            "corner_radius": RADII["control"],
            "fg_color": "transparent",
            "hover_color": COLORS["surface_hover"],
            "border_color": COLORS["border"],
            "border_width": 1,
            "text_color": COLORS["text"],
        }
        defaults.update(kwargs)
        super().__init__(
            master,
            focus_color=COLORS["primary"],
            normal_border_color=COLORS["border"],
            normal_border_width=1,
            normal_fg_color="transparent",
            hover_fg_color=COLORS["surface_hover"],
            pressed_fg_color=COLORS["primary_subtle"],
            disabled_fg_color=COLORS["surface_hover"],
            **defaults
        )
        self.accessible_name = accessible_name
        self.tooltip = Tooltip(self, accessible_name)

    def update_accessible_name(self, accessible_name: str) -> None:
        """Retranslate the accessible name and its tooltip."""
        self.accessible_name = accessible_name
        self.tooltip.update_text(accessible_name)


_BADGE_COLORS = {
    "neutral": (COLORS["surface_subtle"], COLORS["text_secondary"]),
    "success": (COLORS["success_subtle"], COLORS["success"]),
    "warning": (COLORS["warning_subtle"], COLORS["warning"]),
    "error": (COLORS["error_subtle"], COLORS["error"]),
    "info": (COLORS["info_subtle"], COLORS["info"]),
}


class StatusBadge(ctk.CTkLabel):
    """Textual status indicator whose meaning does not depend on color."""

    def __init__(
        self,
        master,
        text: str,
        tone: str = "neutral",
        image: Optional[ctk.CTkImage] = None,
        **kwargs
    ) -> None:
        if tone not in _BADGE_COLORS:
            raise ValueError("Unknown status badge tone: {0}".format(tone))
        background, foreground = _BADGE_COLORS[tone]
        defaults = {
            "text": text,
            "image": image,
            "compound": "left",
            "height": 24,
            "corner_radius": RADII["pill"],
            "fg_color": background,
            "text_color": foreground,
            "padx": SPACING["sm"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)
        self.tone = tone


class SectionTitle(ctk.CTkLabel):
    """Consistent left-aligned panel title."""

    def __init__(
        self,
        master,
        text: str,
        fonts: SystemFontResolver,
        **kwargs
    ) -> None:
        defaults = {
            "text": text,
            "anchor": "w",
            "text_color": COLORS["text"],
            "font": fonts.font("panel_title"),
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class CardFrame(ctk.CTkFrame):
    """Single-border surface used by modern interface cards."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "corner_radius": RADII["card"],
            "fg_color": COLORS["surface"],
            "border_color": COLORS["border"],
            "border_width": 1,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


ATOMIC_COMPONENTS = {
    "CardFrame": CardFrame,
    "IconButton": IconButton,
    "PrimaryButton": PrimaryButton,
    "SecondaryButton": SecondaryButton,
    "SectionTitle": SectionTitle,
    "StatusBadge": StatusBadge,
    "Tooltip": Tooltip,
    "FocusRing": FocusRing,
}  # type: Dict[str, object]
