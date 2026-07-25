"""Modern header/footer editor projected from the desktop settings draft."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Mapping, Sequence

import customtkinter as ctk

from ..components import PrimaryButton, SecondaryButton
from ..theme import COLORS, SPACING, SystemFontResolver


FIELD_GROUPS = (
    ("header", ("header_left", "header_center", "header_right")),
    ("footer", ("footer_left", "footer_center", "footer_right")),
)
TOKENS = ("{titre}", "{title}", "{date}", "{page}", "{total}")


class _AutoScrollSurface(ctk.CTkFrame):
    """Show a vertical scrollbar only when the contained form is clipped."""

    def __init__(self, master) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            self,
            background=COLORS["surface"],
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(1, 0), pady=1)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content = ctk.CTkFrame(
            self.canvas,
            fg_color=COLORS["surface"],
            corner_radius=0,
        )
        self._window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self._scrollbar_visible = False
        self.content.bind("<Configure>", self._sync_geometry, add="+")
        self.canvas.bind("<Configure>", self._sync_geometry, add="+")

    @property
    def scrollbar_visible(self) -> bool:
        """Report whether overflow currently requires vertical scrolling."""
        return self._scrollbar_visible

    def _sync_geometry(self, _event=None) -> None:
        canvas_width = max(1, self.canvas.winfo_width())
        self.canvas.itemconfigure(self._window, width=canvas_width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        required = self.content.winfo_reqheight()
        available = self.canvas.winfo_height()
        needs_scrollbar = available > 1 and required > available
        if needs_scrollbar == self._scrollbar_visible:
            return
        self._scrollbar_visible = needs_scrollbar
        if needs_scrollbar:
            self.scrollbar.grid(row=0, column=1, sticky="ns", pady=1)
        else:
            self.scrollbar.grid_remove()
            self.canvas.yview_moveto(0)
        self.after_idle(self._sync_geometry)

    def bind_mousewheel(self) -> None:
        """Bind wheel scrolling to the completed local form tree."""
        pending = [self.canvas, self.content]
        while pending:
            widget = pending.pop()
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
            pending.extend(widget.winfo_children())

    def _on_mousewheel(self, event):
        if not self._scrollbar_visible:
            return None
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


class HeaderFooterEditorPanel(ctk.CTkFrame):
    """Edit six labelled fields and insert supported tokens into the draft."""

    def __init__(
        self,
        master,
        fonts: SystemFontResolver,
        field_vars: Mapping[str, tk.StringVar],
        on_restore_defaults: Callable[[], None],
        on_save: Callable[[], None],
        on_cancel: Callable[[], None],
        show_back: bool = False,
    ) -> None:
        super().__init__(master, fg_color=COLORS["app_bg"], corner_radius=0)
        self._active_field = "header_left"
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
            self.header, text="", command=on_cancel, width=88, height=32
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
            row=1, column=0, sticky="ew", padx=SPACING["lg"]
        )

        self.content_surface = _AutoScrollSurface(self)
        self.content_surface.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=SPACING["lg"],
            pady=SPACING["md"],
        )
        self.content = self.content_surface.content
        self.grid_rowconfigure(2, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.group_labels = {}
        self.field_labels = {}
        self.entries = {}
        row_number = 0
        for group, keys in FIELD_GROUPS:
            group_label = ctk.CTkLabel(
                self.content,
                text="",
                anchor="w",
                text_color=COLORS["text"],
                font=fonts.font("label"),
            )
            group_label.grid(
                row=row_number,
                column=0,
                sticky="ew",
                padx=SPACING["md"],
                pady=(SPACING["md"] if row_number == 0 else SPACING["lg"], SPACING["xs"]),
            )
            self.group_labels[group] = group_label
            row_number += 1
            fields = ctk.CTkFrame(self.content, fg_color="transparent")
            fields.grid(
                row=row_number,
                column=0,
                sticky="ew",
                padx=SPACING["md"],
            )
            for column in range(3):
                fields.grid_columnconfigure(column, weight=1)
            for index, key in enumerate(keys):
                field = ctk.CTkFrame(fields, fg_color="transparent")
                field.grid(
                    row=0,
                    column=index,
                    sticky="ew",
                    padx=(0, 0 if index == 2 else SPACING["sm"]),
                )
                field.grid_columnconfigure(0, weight=1)
                label = ctk.CTkLabel(
                    field,
                    text="",
                    anchor="w",
                    text_color=COLORS["text_secondary"],
                    font=fonts.font("secondary"),
                )
                label.grid(row=0, column=0, sticky="ew")
                entry = ttk.Entry(field, textvariable=field_vars[key])
                entry.grid(row=1, column=0, sticky="ew")
                entry.bind(
                    "<FocusIn>",
                    lambda _event, field_key=key: self._set_active_field(field_key),
                    add="+",
                )
                self.field_labels[key] = label
                self.entries[key] = entry
            row_number += 1

        self.tokens_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            text_color=COLORS["text"],
            font=fonts.font("label"),
        )
        self.tokens_label.grid(
            row=row_number,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["lg"], SPACING["xs"]),
        )
        row_number += 1
        self.token_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.token_row.grid(
            row=row_number, column=0, sticky="ew", padx=SPACING["md"]
        )
        self.token_buttons = {}
        for index, token in enumerate(TOKENS):
            button = SecondaryButton(
                self.token_row,
                text=token,
                command=lambda value=token: self.insert_token(value),
                width=78,
                height=30,
            )
            button.grid(row=0, column=index, padx=(0, SPACING["xs"]))
            self.token_buttons[token] = button
        row_number += 1
        self.token_help_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            justify="left",
            wraplength=560,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.token_help_label.grid(
            row=row_number,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["xs"], SPACING["md"]),
        )
        row_number += 1
        self.restore_button = SecondaryButton(
            self.content,
            text="",
            command=on_restore_defaults,
            width=176,
        )
        self.restore_button.grid(
            row=row_number,
            column=0,
            sticky="e",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
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
        self.content_surface.bind_mousewheel()

    @property
    def scrollbar_visible(self) -> bool:
        """Report whether the form currently needs vertical scrolling."""
        return self.content_surface.scrollbar_visible

    def _set_active_field(self, key: str) -> None:
        self._active_field = key

    def insert_token(self, token: str) -> None:
        """Insert a supported token at the active field's cursor position."""
        if token not in TOKENS:
            raise ValueError("Unsupported header/footer token: {0}".format(token))
        entry = self.entries[self._active_field]
        try:
            if entry.selection_present():
                entry.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        entry.insert(entry.index("insert"), token)
        entry.focus_set()

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update labels without translating or clearing user field values."""
        self.title_label.configure(text=labels["title"])
        self.description_label.configure(text=labels["description"])
        self.back_button.configure(text=labels["back"])
        self.group_labels["header"].configure(text=labels["header"])
        self.group_labels["footer"].configure(text=labels["footer"])
        for key in self.field_labels:
            position = key.rsplit("_", 1)[1]
            self.field_labels[key].configure(text=labels[position])
        self.tokens_label.configure(text=labels["tokens"])
        self.token_help_label.configure(text=labels["token_help"])
        self.restore_button.configure(text=labels["restore"])
        self.cancel_button.configure(text=labels["cancel"])
        self.save_button.configure(text=labels["save"])

    def focus_initial(self) -> None:
        """Place initial focus in the first header field."""
        self._active_field = "header_left"
        self.entries[self._active_field].focus_set()


__all__: Sequence[str] = ("HeaderFooterEditorPanel",)
