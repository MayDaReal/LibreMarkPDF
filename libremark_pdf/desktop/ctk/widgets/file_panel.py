"""Modern, reusable file-list panel for the desktop adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Sequence

import customtkinter as ctk

from ..assets import UiAssetRegistry
from ..components import (
    CardFrame,
    IconButton,
    SecondaryButton,
    SectionTitle,
)
from ..theme import COLORS, SIZES, SPACING, SystemFontResolver
from .file_row import FileRow


class FilesPanel(CardFrame):
    """Project authoritative batch state as stable modern file rows."""

    def __init__(
        self,
        master,
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        assets: UiAssetRegistry,
        has_drag_and_drop: bool,
        on_add: Callable[[], None],
        on_select: Callable[[Path], None],
        on_show_source: Callable[[Path], None],
        on_copy_path: Callable[[Path], None],
        on_remove: Callable[[Path], None],
        on_clear: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._labels = dict(labels)
        self._fonts = fonts
        self._assets = assets
        self._has_drag_and_drop = has_drag_and_drop
        self._on_add = on_add
        self._on_select = on_select
        self._on_show_source = on_show_source
        self._on_copy_path = on_copy_path
        self._on_remove = on_remove
        self._on_clear = on_clear
        self._paths = []  # type: list[Path]
        self.rows = {}  # type: Dict[Path, FileRow]
        self._active = None  # type: Optional[Path]
        self._mutation_enabled = True
        self._selection_enabled = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.title_label = SectionTitle(
            self,
            text=self._labels["files_heading"],
            fonts=fonts,
            height=20,
        )
        self.title_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], 0),
        )

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["sm"]),
        )
        header.grid_columnconfigure(0, weight=1)
        self.count_label = ctk.CTkLabel(
            header,
            text="",
            anchor="w",
            height=18,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.count_label.grid(row=0, column=0, sticky="ew")
        self._add_font = fonts.font("secondary")
        add_text = self._labels["add_files"]
        self.add_button = SecondaryButton(
            header,
            text=add_text,
            command=on_add,
            image=assets.image("plus", size=16, color="accent"),
            compound="left",
            width=self._add_button_width(add_text),
            height=SIZES["icon_button"],
            font=self._add_font,
        )
        self.add_button.grid(row=0, column=1, padx=(SPACING["sm"], 0))
        self.clear_button = IconButton(
            header,
            image=assets.image("trash3", size=16, color="neutral"),
            accessible_name=self._labels["all_remove_action"],
            command=self._on_clear,
        )
        self.clear_button.grid(
            row=0,
            column=2,
            padx=(SPACING["xs"], 0),
        )

        self.disabled_reason = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )

        empty_text_key = (
            "drop_or_browse"
            if has_drag_and_drop
            else "browse_without_dnd"
        )
        self.empty_state = SecondaryButton(
            self,
            text=self._labels[empty_text_key],
            command=on_add,
            image=assets.image("file-earmark-text", size=24, color="accent"),
            compound="top",
            width=1,
            height=120,
            font=fonts.font("body"),
        )
        self.empty_state.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )

        self.list_view = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            height=176,
        )
        self.list_view.grid_columnconfigure(0, weight=1)
        self._set_count_text(0)
        self._show_empty()

    @property
    def drop_targets(self) -> tuple:
        """Return public widgets that accept optional file drops."""
        return (self, self.empty_state, self.add_button, self.list_view)

    def _show_empty(self) -> None:
        self.list_view.grid_forget()
        self.empty_state.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        self.clear_button.grid_remove()

    def _show_list(self) -> None:
        self.empty_state.grid_forget()
        self.list_view.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=SPACING["xs"],
            pady=(0, SPACING["sm"]),
        )
        self.clear_button.grid()

    def _set_count_text(self, count: int) -> None:
        key = "file_count_one" if count == 1 else "file_count_many"
        self.count_label.configure(
            text=self._labels[key].format(count=count)
        )

    def _add_button_width(self, text: str) -> int:
        return max(
            104,
            self._add_font.measure(text) + 16 + SPACING["xl"],
        )

    def set_files(
        self,
        paths: Sequence[Path],
        active: Optional[Path],
        focus_path: Optional[Path] = None,
    ) -> None:
        """Diff authoritative paths and preserve existing row instances."""
        new_paths = list(paths)
        new_set = set(new_paths)
        for path in list(self.rows):
            if path not in new_set:
                self.rows.pop(path).destroy()
        for path in new_paths:
            if path not in self.rows:
                self.rows[path] = FileRow(
                    self.list_view,
                    path=path,
                    labels=self._labels,
                    fonts=self._fonts,
                    document_icon=self._assets.image(
                        "file-earmark-text", size=24, color="accent"
                    ),
                    menu_icon=self._assets.image(
                        "three-dots-vertical", size=16, color="neutral"
                    ),
                    on_select=self._on_select,
                    on_focus_relative=self.focus_relative,
                    on_show_source=self._on_show_source,
                    on_copy_path=self._on_copy_path,
                    on_remove=self._on_remove,
                )
                self.rows[path].set_enabled(
                    self._mutation_enabled,
                    self._selection_enabled,
                )
                self.rows[path].set_selected(path == active)
        for index, path in enumerate(new_paths):
            self.rows[path].grid(
                row=index,
                column=0,
                sticky="ew",
                padx=SPACING["xs"],
                pady=(0, SPACING["xs"]),
            )
        self._paths = new_paths
        self._set_count_text(len(new_paths))
        if new_paths:
            self._show_list()
        else:
            self._show_empty()
        self.set_active(active)
        if focus_path in self.rows:
            self.after_idle(self.rows[focus_path].focus_set)
        elif not new_paths and focus_path is None:
            self.after_idle(self.add_button.focus_set)

    def set_active(self, active: Optional[Path]) -> None:
        """Update only rows whose active-preview state changed."""
        previous = self._active
        self._active = active
        for path in (previous, active):
            if path in self.rows:
                self.rows[path].set_selected(path == active)

    def focus_relative(self, path: Path, direction: int) -> None:
        """Move keyboard focus between rows without changing selection."""
        try:
            index = self._paths.index(path)
        except ValueError:
            return
        target = max(0, min(len(self._paths) - 1, index + direction))
        self.rows[self._paths[target]].focus_set()

    def focus_add(self) -> None:
        """Move focus to the primary add action."""
        self.add_button.focus_set()

    def set_interaction_enabled(
        self,
        mutation_enabled: bool,
        selection_enabled: bool,
        reason: str = "",
    ) -> None:
        """Disable batch mutations during conversion with an explicit reason."""
        self._mutation_enabled = mutation_enabled
        self._selection_enabled = selection_enabled
        state = "normal" if mutation_enabled else "disabled"
        self.add_button.configure(state=state)
        self.empty_state.configure(state=state)
        self.clear_button.configure(state=state)
        for row in self.rows.values():
            row.set_enabled(mutation_enabled, selection_enabled)
        if mutation_enabled or not reason:
            self.disabled_reason.grid_forget()
        else:
            self.disabled_reason.configure(text=reason)
            self.disabled_reason.grid(
                row=2,
                column=0,
                sticky="ew",
                padx=SPACING["md"],
                pady=(0, SPACING["sm"]),
            )

    def set_conversion_states(
        self,
        states: Mapping[Path, Optional[str]],
    ) -> None:
        """Apply per-file conversion state without recreating rows."""
        for path, row in self.rows.items():
            row.set_conversion_status(states.get(path))

    def set_drop_state(self, state: str) -> None:
        """Reflect valid and invalid drag hover using tokenized colors."""
        text_key = {
            "active": "drop_active",
            "unsupported": "unsupported_drop",
        }.get(
            state,
            "drop_or_browse"
            if self._has_drag_and_drop
            else "browse_without_dnd",
        )
        colors = {
            "active": (COLORS["primary_subtle"], COLORS["primary"]),
            "unsupported": (COLORS["error_subtle"], COLORS["error"]),
        }
        background, border = colors.get(
            state, ("transparent", COLORS["border_strong"])
        )
        self.configure(
            border_color=(
                border if state in ("active", "unsupported") else COLORS["border"]
            )
        )
        button_text = (
            self._labels[text_key]
            if state in ("active", "unsupported")
            else self._labels["add_files"]
        )
        self.add_button.configure(
            text=button_text,
            width=self._add_button_width(button_text),
        )
        self.empty_state.configure(
            text=self._labels[text_key],
            fg_color=background,
            border_color=border,
        )

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Refresh all panel copy while retaining row objects and focus."""
        self._labels = dict(labels)
        self.title_label.configure(text=self._labels["files_heading"])
        self.add_button.configure(text=self._labels["add_files"])
        self.clear_button.update_accessible_name(
            self._labels["all_remove_action"]
        )
        self._set_count_text(len(self._paths))
        self.set_drop_state("empty")
        for row in self.rows.values():
            row.retranslate(self._labels)
