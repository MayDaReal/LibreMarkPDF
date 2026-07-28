"""Modern file-card row for the desktop batch and active preview."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable, Mapping, Optional

import customtkinter as ctk

from ..components import AppMenu, CardFrame, IconButton, StatusBadge, Tooltip
from ..theme import COLORS, SPACING, SystemFontResolver


def middle_elide(text: str, limit: int) -> str:
    """Preserve both ends of a path within a deterministic character budget."""
    if limit < 5 or len(text) <= limit:
        return text
    left = (limit - 1) // 2
    right = limit - left - 1
    return "{0}…{1}".format(text[:left], text[-right:])


_STATUS_TONES = {
    "pending": "neutral",
    "running": "info",
    "ok": "success",
    "error": "error",
    "kept": "neutral",
    "cancelled": "neutral",
}


class FileRow(CardFrame):
    """Selectable file card with keyboard navigation and a native action menu."""

    def __init__(
        self,
        master,
        path: Path,
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        document_icon: ctk.CTkImage,
        reveal_icon: ctk.CTkImage,
        copy_icon: ctk.CTkImage,
        remove_icon: ctk.CTkImage,
        on_select: Callable[[Path], None],
        on_focus_relative: Callable[[Path, int], None],
        on_show_source: Callable[[Path], None],
        on_copy_path: Callable[[Path], None],
        on_remove: Callable[[Path], None],
    ) -> None:
        super().__init__(master, height=58)
        self.path = path
        self._labels = dict(labels)
        self._on_select = on_select
        self._on_focus_relative = on_focus_relative
        self._on_show_source = on_show_source
        self._on_copy_path = on_copy_path
        self._on_remove = on_remove
        self._selected = False
        self._mutation_enabled = True
        self._selection_enabled = True
        self._conversion_status = None  # type: Optional[str]
        self._path_text = str(path.parent)
        self._path_width = 0
        self._path_font = fonts.font("secondary")

        tk.Frame.configure(self, takefocus=True)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.document_label = ctk.CTkLabel(
            self,
            text="",
            image=document_icon,
            width=24,
            fg_color="transparent",
        )
        self.document_label.grid(
            row=0,
            column=0,
            padx=(SPACING["md"], SPACING["sm"]),
            pady=SPACING["sm"],
        )
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.text_frame.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=SPACING["xs"],
        )
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.name_label = ctk.CTkLabel(
            self.text_frame,
            text=path.name,
            anchor="w",
            text_color=COLORS["text"],
            font=fonts.font("label"),
        )
        self.name_label.grid(row=0, column=0, sticky="ew")
        self.name_tooltip = Tooltip(self.name_label, path.name)
        self.path_label = ctk.CTkLabel(
            self.text_frame,
            text=self._path_text,
            anchor="w",
            text_color=COLORS["text_secondary"],
            font=self._path_font,
        )
        self.path_label.grid(row=1, column=0, sticky="ew")
        self.path_tooltip = Tooltip(self.path_label, self._path_text)

        self.badges = ctk.CTkFrame(self, fg_color="transparent")
        self.badges.grid_columnconfigure(0, weight=1)
        self.active_badge = StatusBadge(
            self.badges,
            text=self._labels["active_preview_badge"],
            tone="info",
            font=fonts.font("badge"),
        )
        self.conversion_badge = None  # type: Optional[StatusBadge]

        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.reveal_button = IconButton(
            self.actions,
            image=reveal_icon,
            accessible_name=self._labels["reveal_source"],
            command=lambda: self._on_show_source(self.path),
        )
        self.copy_button = IconButton(
            self.actions,
            image=copy_icon,
            accessible_name=self._labels["copy_path"],
            command=lambda: self._on_copy_path(self.path),
        )
        self.remove_button = IconButton(
            self.actions,
            image=remove_icon,
            accessible_name=self._labels["remove_from_batch"],
            command=self.remove,
        )
        self.actions.grid(
            row=0, column=3,
            padx=(SPACING["sm"], SPACING["sm"]),
            pady=SPACING["sm"],
        )
        self.set_layout_mode("large")

        for widget in (
            self,
            self.document_label,
            self.text_frame,
            self.name_label,
            self.path_label,
            self.badges,
        ):
            widget.bind("<Button-1>", self._activate_pointer, add="+")
        self.bind("<Return>", self._activate_keyboard, add="+")
        self.bind("<space>", self._activate_keyboard, add="+")
        self.bind("<Up>", lambda _event: self._move_focus(-1), add="+")
        self.bind("<Down>", lambda _event: self._move_focus(1), add="+")
        self.bind("<Delete>", self._remove_keyboard, add="+")
        self.bind("<KeyPress-Menu>", self._open_menu_keyboard, add="+")
        self.bind("<Shift-F10>", self._open_menu_keyboard, add="+")
        self.bind("<FocusIn>", self._show_focus, add="+")
        self.bind("<FocusOut>", self._hide_focus, add="+")
        self.text_frame.bind("<Configure>", self._resize_path, add="+")

    def _activate_pointer(self, _event=None) -> str:
        self.focus_set()
        return self._activate_keyboard()

    def _activate_keyboard(self, _event=None) -> str:
        self.activate()
        return "break"

    def activate(self) -> None:
        """Request active-preview selection when currently permitted."""
        if self._selection_enabled:
            self._on_select(self.path)

    def _move_focus(self, direction: int) -> str:
        self._on_focus_relative(self.path, direction)
        return "break"

    def _remove_keyboard(self, _event=None) -> str:
        self.remove()
        return "break"

    def remove(self) -> None:
        """Request removal when batch mutation is currently permitted."""
        if self._mutation_enabled:
            self._on_remove(self.path)

    def _open_menu_keyboard(self, _event=None) -> str:
        self.open_menu()
        return "break"

    def _show_focus(self, _event=None) -> None:
        self.configure(border_color=COLORS["primary"], border_width=2)

    def _hide_focus(self, _event=None) -> None:
        self.configure(
            border_color=(
                COLORS["primary"] if self._selected else COLORS["border"]
            ),
            border_width=1,
        )

    def _resize_path(self, event) -> None:
        available_width = max(1, int(event.width))
        if available_width == self._path_width:
            return
        self._path_width = available_width
        if self._path_font.measure(self._path_text) <= available_width:
            display_text = self._path_text
        else:
            low = 5
            high = len(self._path_text)
            while low < high:
                limit = (low + high + 1) // 2
                candidate = middle_elide(self._path_text, limit)
                if self._path_font.measure(candidate) <= available_width:
                    low = limit
                else:
                    high = limit - 1
            display_text = middle_elide(self._path_text, low)
        self.path_label.configure(text=display_text)

    def open_menu(self) -> None:
        """Open the keyboard-native row menu without activating the row."""
        menu = AppMenu(self, font=self._path_font)
        menu.add_command(
            label=self._labels["reveal_source"],
            command=lambda: self._on_show_source(self.path),
        )
        menu.add_command(
            label=self._labels["copy_path"],
            command=lambda: self._on_copy_path(self.path),
        )
        menu.add_separator()
        menu.add_command(
            label=self._labels["remove_from_batch"],
            command=lambda: self._on_remove(self.path),
            state="normal" if self._mutation_enabled else "disabled",
        )
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def set_layout_mode(self, mode: str) -> None:
        """Keep direct row actions available at every supported width."""
        if mode not in ("large", "medium", "compact"):
            raise ValueError("Unknown file-row layout mode: {0}".format(mode))
        for button in (
            self.reveal_button,
            self.copy_button,
            self.remove_button,
        ):
            button.grid_forget()
        self.reveal_button.grid(row=0, column=0)
        self.copy_button.grid(
            row=0, column=1, padx=(SPACING["xs"], 0)
        )
        self.remove_button.grid(
            row=0, column=2, padx=(SPACING["xs"], 0)
        )

    def set_selected(self, selected: bool) -> None:
        """Update active-preview styling without rebuilding the row."""
        self._selected = selected
        self.configure(
            fg_color=(
                COLORS["surface_selected"] if selected else COLORS["surface"]
            ),
            border_color=(
                COLORS["primary"] if selected else COLORS["border"]
            ),
        )
        self._update_badges_layout()

    def _update_badges_layout(self) -> None:
        self.active_badge.grid_forget()
        if self.conversion_badge is not None:
            self.conversion_badge.grid_forget()

        row = 0
        if self._selected:
            self.active_badge.grid(row=row, column=0, sticky="ew")
            row += 1
        if self.conversion_badge is not None:
            self.conversion_badge.grid(row=row, column=0, sticky="ew")

        if self._selected or self._conversion_status is not None:
            vertical_padding = (
                SPACING["xs"]
                if self._selected and self._conversion_status is not None
                else SPACING["sm"]
            )
            self.badges.grid(
                row=0,
                column=2,
                padx=(SPACING["sm"], 0),
                pady=vertical_padding,
            )
        else:
            self.badges.grid_forget()

    def set_enabled(
        self,
        mutation_enabled: bool,
        selection_enabled: bool,
    ) -> None:
        """Apply conversion-time interaction restrictions."""
        self._mutation_enabled = mutation_enabled
        self._selection_enabled = selection_enabled
        self.remove_button.configure(
            state="normal" if mutation_enabled else "disabled"
        )

    def set_conversion_status(self, status: Optional[str]) -> None:
        """Update a per-file conversion badge without replacing the row."""
        if status == self._conversion_status:
            return
        self._conversion_status = status
        if self.conversion_badge is not None:
            self.conversion_badge.destroy()
            self.conversion_badge = None
        if status is None:
            self._update_badges_layout()
            return
        self.conversion_badge = StatusBadge(
            self.badges,
            text=self._labels["conversion_{0}".format(status)],
            tone=_STATUS_TONES[status],
        )
        self._update_badges_layout()

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Refresh visible and accessible copy without replacing the row."""
        self._labels = dict(labels)
        self.active_badge.configure(text=self._labels["active_preview_badge"])
        self.reveal_button.update_accessible_name(self._labels["reveal_source"])
        self.copy_button.update_accessible_name(self._labels["copy_path"])
        self.remove_button.update_accessible_name(
            self._labels["remove_from_batch"]
        )
        if self._conversion_status is not None:
            self.conversion_badge.configure(
                text=self._labels[
                    "conversion_{0}".format(self._conversion_status)
                ]
            )
