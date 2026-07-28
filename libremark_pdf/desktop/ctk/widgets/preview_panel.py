"""Modern preview presentation around the desktop adapter's Tk canvas."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Mapping, Optional

import customtkinter as ctk

from ..assets import UiAssetRegistry
from ..components import (
    AppMenu,
    CardFrame,
    IconButton,
    SecondaryButton,
    StatusBadge,
    Tooltip,
)
from ..theme import COLORS, RADII, SPACING, SystemFontResolver


class PreviewToolbar(ctk.CTkFrame):
    """Expose preview navigation, zoom and fit actions in responsive order."""

    def __init__(
        self,
        master,
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        assets: UiAssetRegistry,
        on_refresh: Callable[[], None],
        on_previous: Callable[[], None],
        on_next: Callable[[], None],
        on_zoom_out: Callable[[], None],
        on_zoom_in: Callable[[], None],
        on_fit_page: Callable[[], None],
        on_fit_width: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface"],
            corner_radius=RADII["control"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self._labels = dict(labels)
        self._layout_mode = None  # type: Optional[str]
        self.refresh_button = IconButton(
            self,
            image=assets.image("arrow-clockwise", size=20, color="neutral"),
            accessible_name=labels["refresh_preview_a11y"],
            command=on_refresh,
        )
        self.previous_button = IconButton(
            self,
            image=assets.image("chevron-left", size=20, color="neutral"),
            accessible_name=labels["previous_page_a11y"],
            command=on_previous,
        )
        self.page_label = ctk.CTkLabel(
            self,
            text="",
            width=112,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.next_button = IconButton(
            self,
            image=assets.image("chevron-right", size=20, color="neutral"),
            accessible_name=labels["next_page_a11y"],
            command=on_next,
        )
        self.zoom_out_button = IconButton(
            self,
            image=assets.image("dash", size=20, color="neutral"),
            accessible_name=labels["zoom_out_a11y"],
            command=on_zoom_out,
        )
        self.zoom_label = ctk.CTkLabel(
            self,
            text="",
            width=62,
            text_color=COLORS["text"],
            font=fonts.font("secondary"),
        )
        self.zoom_in_button = IconButton(
            self,
            image=assets.image("plus", size=20, color="neutral"),
            accessible_name=labels["zoom_in_a11y"],
            command=on_zoom_in,
        )
        self.fit_page_button = SecondaryButton(
            self,
            text=labels["fit_page"],
            command=on_fit_page,
            height=32,
            width=92,
            font=fonts.font("secondary"),
        )
        self.fit_width_button = SecondaryButton(
            self,
            text=labels["fit_width"],
            command=on_fit_width,
            height=32,
            width=92,
            font=fonts.font("secondary"),
        )
        self.overflow_button = IconButton(
            self,
            image=assets.image("three-dots-vertical", size=20, color="neutral"),
            accessible_name=labels["preview_more_a11y"],
            command=self._post_overflow,
        )
        self.overflow_menu = AppMenu(self, font=fonts.font("body"))
        self._on_fit_page = on_fit_page
        self._on_fit_width = on_fit_width
        self.grid_columnconfigure(2, weight=1)
        self.retranslate(labels)
        self.set_layout_mode("large")

    @property
    def ordered_controls(self) -> tuple:
        """Return the normative large-toolbar order for public UI probes."""
        return (
            self.refresh_button,
            self.previous_button,
            self.page_label,
            self.next_button,
            self.zoom_out_button,
            self.zoom_label,
            self.zoom_in_button,
            self.fit_page_button,
            self.fit_width_button,
        )

    def _post_overflow(self) -> None:
        self.overflow_button.tooltip.hide()
        self.overflow_menu.tk_popup(
            self.overflow_button.winfo_rootx(),
            self.overflow_button.winfo_rooty()
            + self.overflow_button.winfo_height(),
        )

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update visible, accessible and overflow-menu copy in place."""
        self._labels = dict(labels)
        for button, key in (
            (self.refresh_button, "refresh_preview_a11y"),
            (self.previous_button, "previous_page_a11y"),
            (self.next_button, "next_page_a11y"),
            (self.zoom_out_button, "zoom_out_a11y"),
            (self.zoom_in_button, "zoom_in_a11y"),
            (self.overflow_button, "preview_more_a11y"),
        ):
            button.update_accessible_name(labels[key])
        self.fit_page_button.configure(text=labels["fit_page"])
        self.fit_width_button.configure(text=labels["fit_width"])
        if self.overflow_menu.index("end") is None:
            self.overflow_menu.add_command(
                label=labels["fit_page"], command=self._on_fit_page
            )
            self.overflow_menu.add_command(
                label=labels["fit_width"], command=self._on_fit_width
            )
        else:
            self.overflow_menu.entryconfigure(0, label=labels["fit_page"])
            self.overflow_menu.entryconfigure(1, label=labels["fit_width"])

    def set_layout_mode(self, mode: str) -> None:
        """Lay out existing controls without changing preview state."""
        if mode not in ("large", "medium", "compact"):
            raise ValueError("Unknown preview layout mode: {0}".format(mode))
        if mode == self._layout_mode:
            return
        self._layout_mode = mode
        for control in self.ordered_controls + (self.overflow_button,):
            control.grid_forget()
        controls = self.ordered_controls[:7]
        for column, control in enumerate(controls):
            control.grid(
                row=0,
                column=column,
                sticky="ew" if control is self.page_label else "",
                padx=(SPACING["sm"], 0),
                pady=SPACING["sm"],
            )
        if mode == "large":
            self.fit_page_button.grid(
                row=0, column=7, padx=(SPACING["md"], 0), pady=SPACING["sm"]
            )
            self.fit_width_button.grid(
                row=0,
                column=8,
                padx=(SPACING["sm"], SPACING["sm"]),
                pady=SPACING["sm"],
            )
        else:
            self.overflow_button.grid(
                row=0,
                column=7,
                padx=(SPACING["md"], SPACING["sm"]),
                pady=SPACING["sm"],
            )


class PreviewPanel(CardFrame):
    """Present one reusable preview canvas and its localized state."""

    def __init__(
        self,
        master,
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        assets: UiAssetRegistry,
        on_add_files: Callable[[], None],
        on_refresh: Callable[[], None],
        on_previous: Callable[[], None],
        on_next: Callable[[], None],
        on_zoom_out: Callable[[], None],
        on_zoom_in: Callable[[], None],
        on_fit_page: Callable[[], None],
        on_fit_width: Callable[[], None],
        on_retry: Callable[[], None],
        on_copy_details: Callable[[], None],
        on_report: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._labels = dict(labels)
        self._filename = ""
        self._filename_max_width = 260
        self._state = "empty"
        self._state_message = labels["preview_empty"]
        self._filename_font = fonts.font("panel_title")
        self.grid_columnconfigure(0, weight=1)
        # Tk scrollbars consume roughly 12 logical pixels when present; keep
        # the actual canvas viewport at the 180 px compact minimum.
        self.grid_rowconfigure(3, weight=1, minsize=192)
        self.header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["md"], SPACING["xs"]),
        )
        self.header.grid_columnconfigure(2, weight=1)
        self.filename_label = ctk.CTkLabel(
            self.header,
            text=labels["preview_heading"],
            anchor="w",
            width=1,
            text_color=COLORS["text"],
            font=self._filename_font,
        )
        self.filename_label.grid(row=0, column=0, sticky="ew")
        self.filename_label.bind(
            "<Configure>", self._refresh_filename_elision, add="+"
        )
        self.filename_tooltip = Tooltip(self.filename_label, "")
        self.state_badge = StatusBadge(
            self.header,
            text="",
            tone="info",
            image=assets.image("arrow-clockwise", size=16, color="accent"),
            fg_color="transparent",
            text_color=COLORS["text_secondary"],
            padx=0,
        )

        self.toolbar = PreviewToolbar(
            self,
            labels=labels,
            fonts=fonts,
            assets=assets,
            on_refresh=on_refresh,
            on_previous=on_previous,
            on_next=on_next,
            on_zoom_out=on_zoom_out,
            on_zoom_in=on_zoom_in,
            on_fit_page=on_fit_page,
            on_fit_width=on_fit_width,
        )
        self.toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["sm"]),
        )

        self.message_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface_subtle"],
            corner_radius=RADII["control"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.message_frame.grid_columnconfigure(0, weight=1)
        self.message_label = ctk.CTkLabel(
            self.message_frame,
            text="",
            anchor="w",
            justify="left",
            wraplength=520,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.message_label.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["xs"]),
        )
        self.add_files_button = SecondaryButton(
            self.message_frame,
            text=labels["add_files"],
            command=on_add_files,
            height=32,
            font=fonts.font("secondary"),
        )
        self.retry_button = SecondaryButton(
            self.message_frame,
            text=labels["preview_retry"],
            command=on_retry,
            height=32,
            font=fonts.font("secondary"),
        )
        self.copy_button = SecondaryButton(
            self.message_frame,
            text=labels["copy_details"],
            command=on_copy_details,
            height=32,
            font=fonts.font("secondary"),
        )
        self.report_button = SecondaryButton(
            self.message_frame,
            text=labels["report_issue_action"],
            command=on_report,
            height=32,
            font=fonts.font("secondary"),
        )

        self.canvas_frame = tk.Frame(self, background=COLORS["preview_bg"])
        self.canvas_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            self.canvas_frame,
            height=320,
            bg=COLORS["preview_bg"],
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            highlightthickness=1,
            takefocus=True,
        )
        self.vertical_scrollbar = ttk.Scrollbar(
            self.canvas_frame, orient="vertical", command=self.canvas.yview
        )
        self.horizontal_scrollbar = ttk.Scrollbar(
            self.canvas_frame, orient="horizontal", command=self.canvas.xview
        )
        self.canvas.configure(
            yscrollcommand=self.vertical_scrollbar.set,
            xscrollcommand=self.horizontal_scrollbar.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.accessible_name = labels["preview_canvas_a11y"]
        self._layout_mode = "large"
        self.set_state("empty", labels["preview_empty"])

    def set_filename(self, filename: str) -> None:
        """Show the active filename and retain its complete tooltip value."""
        self._filename = filename
        self.filename_tooltip.update_text(filename)
        self._refresh_filename_elision()

    def _refresh_filename_elision(self, _event=None) -> None:
        text = self._filename or self._labels["preview_heading"]
        available = self._filename_max_width
        if self._filename_font.measure(text) <= available:
            display = text
        else:
            suffix = "…"
            low, high = 0, len(text)
            while low < high:
                middle = (low + high + 1) // 2
                candidate = text[:middle].rstrip() + suffix
                if self._filename_font.measure(candidate) <= available:
                    low = middle
                else:
                    high = middle - 1
            display = text[:low].rstrip() + suffix
        self.filename_label.configure(
            text=display,
            width=min(available, max(80, self._filename_font.measure(display) + 4)),
        )

    def set_state(self, state: str, message: str) -> None:
        """Project a preview state without touching the canvas image."""
        if state not in (
            "empty", "scheduled", "rendering", "ready", "error", "unavailable"
        ):
            raise ValueError("Unknown preview state: {0}".format(state))
        self._state = state
        self._state_message = message
        self.message_label.configure(text=message)
        self.message_frame.grid_forget()
        self.state_badge.grid_forget()
        for button in (
            self.add_files_button,
            self.retry_button,
            self.copy_button,
            self.report_button,
        ):
            button.grid_forget()
        if state in ("scheduled", "rendering"):
            self.state_badge.configure(text=message)
            self.state_badge.grid(
                row=0,
                column=1,
                sticky="w",
                padx=(SPACING["sm"], 0),
            )
            return
        if state == "ready":
            return
        if state == "empty" and self._layout_mode != "compact":
            return
        self.message_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["sm"]),
        )
        if state == "empty" and self._layout_mode == "compact":
            self.add_files_button.grid(
                row=1,
                column=0,
                sticky="w",
                padx=SPACING["md"],
                pady=(0, SPACING["sm"]),
            )
        elif state in ("error", "unavailable"):
            actions = (self.retry_button, self.copy_button, self.report_button)
            for column, button in enumerate(actions):
                button.grid(
                    row=1,
                    column=column,
                    sticky="w",
                    padx=(SPACING["md"] if column == 0 else 0, SPACING["sm"]),
                    pady=(0, SPACING["sm"]),
                )

    def set_layout_mode(self, mode: str) -> None:
        """Adapt toolbar actions while retaining the same child widgets."""
        self._layout_mode = mode
        self.toolbar.set_layout_mode(mode)
        self._filename_max_width = {
            "large": 260,
            "medium": 220,
            "compact": 220,
        }[mode]
        self._refresh_filename_elision()
        self.toolbar.grid_configure(sticky="ew")
        self.set_state(self._state, self._state_message)

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Retranslate controls without rebuilding or clearing preview state."""
        self._labels = dict(labels)
        self.toolbar.retranslate(labels)
        self.add_files_button.configure(text=labels["add_files"])
        self.retry_button.configure(text=labels["preview_retry"])
        self.copy_button.configure(text=labels["copy_details"])
        self.report_button.configure(text=labels["report_issue_action"])
        self.canvas.accessible_name = labels["preview_canvas_a11y"]
        self.set_filename(self._filename)


__all__ = ("PreviewPanel", "PreviewToolbar")
