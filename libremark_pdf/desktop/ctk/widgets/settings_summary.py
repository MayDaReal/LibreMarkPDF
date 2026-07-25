"""Modern settings summaries backed by the desktop application's live state."""

from __future__ import annotations

from typing import Callable, Dict, Mapping, Sequence

import customtkinter as ctk

from ..components import CardFrame, SecondaryButton, SectionTitle, Tooltip
from ..assets import UiAssetRegistry
from ..theme import COLORS, RADII, SPACING, SystemFontResolver


class SettingsSummaryRow(ctk.CTkFrame):
    """Present one setting family and its complete active summary."""

    def __init__(
        self,
        master,
        name: str,
        fonts: SystemFontResolver,
        icon,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface_subtle"],
            corner_radius=RADII["card"],
            border_width=1,
            border_color=COLORS["border"],
            height=44,
            width=1,
        )
        self.grid_propagate(False)
        self.name = name
        self._fonts = fonts
        self._complete_summary = ""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.icon_label = ctk.CTkLabel(
            self,
            text="",
            image=icon,
            width=20,
            height=20,
        )
        self.icon_label.grid(
            row=0,
            column=0,
            padx=(SPACING["sm"], SPACING["xs"]),
        )

        self.title_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            width=132,
            height=20,
            text_color=COLORS["text"],
            font=fonts.font("label"),
        )
        self.title_label.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, SPACING["sm"]),
        )
        self.summary_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            width=1,
            height=20,
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.summary_label.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(0, SPACING["xs"]),
        )
        self.summary_tooltip = Tooltip(self.summary_label, "")
        self.bind("<Configure>", self._refresh_elision, add="+")
        self.summary_label.bind(
            "<Configure>",
            self._refresh_elision,
            add="+",
        )

    def set_title_width(self, width: int) -> None:
        """Keep every row's description on the same vertical guide."""
        self.title_label.configure(width=width)

    def update_copy(self, title: str, summary: str) -> None:
        """Retranslate the row and project its current complete summary."""
        self.title_label.configure(text=title)
        self._complete_summary = summary
        self.summary_tooltip.update_text(summary)
        self.after_idle(self._refresh_elision)

    def _refresh_elision(self, _event=None) -> None:
        if not self.winfo_exists():
            return
        available = max(40, self.summary_label.winfo_width())
        text = self._complete_summary
        font = self._fonts.font("secondary")
        if font.measure(text) <= available:
            display = text
        else:
            suffix = "…"
            low, high = 0, len(text)
            while low < high:
                middle = (low + high + 1) // 2
                candidate = text[:middle].rstrip() + suffix
                if font.measure(candidate) <= available:
                    low = middle
                else:
                    high = middle - 1
            display = text[:low].rstrip() + suffix
        self.summary_label.configure(text=display)


class SettingsSummaryPanel(CardFrame):
    """Display exactly four localized settings summaries."""

    ROW_NAMES = ("style", "destination", "header_footer", "other")

    def __init__(
        self,
        master,
        labels: Mapping[str, str],
        summaries: Mapping[str, str],
        fonts: SystemFontResolver,
        assets: UiAssetRegistry,
        on_edit: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.title_label = SectionTitle(
            self,
            text=labels["settings_heading"],
            fonts=fonts,
            height=20,
        )
        self.title_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(SPACING["md"], SPACING["sm"]),
            pady=SPACING["md"],
        )
        self.edit_button = SecondaryButton(
            self,
            text=labels["edit"],
            command=on_edit,
            height=30,
            width=76,
            font=fonts.font("secondary"),
        )
        self.edit_button.grid(
            row=0,
            column=1,
            padx=(SPACING["sm"], SPACING["md"]),
            pady=SPACING["md"],
        )
        self.rows = {}  # type: Dict[str, SettingsSummaryRow]
        icons = {
            "style": "pencil",
            "destination": "folder2-open",
            "header_footer": "file-earmark-text",
            "other": "three-dots-vertical",
        }
        for row_number, name in enumerate(self.ROW_NAMES, start=1):
            row = SettingsSummaryRow(
                self,
                name,
                fonts,
                assets.image(icons[name], size=16, color="neutral"),
            )
            row.grid(
                row=row_number,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=SPACING["md"],
                pady=(0, SPACING["xs"]),
            )
            self.rows[name] = row
        self.retranslate(labels, summaries)

    def retranslate(
        self,
        labels: Mapping[str, str],
        summaries: Mapping[str, str],
    ) -> None:
        """Update copy in place without rebuilding any row."""
        self.title_label.configure(text=labels["settings_heading"])
        self.edit_button.configure(text=labels["edit"])
        title_width = max(
            132,
            max(
                self.rows[name]._fonts.font("label").measure(labels[name])
                for name in self.ROW_NAMES
            ),
        )
        for name in self.ROW_NAMES:
            self.rows[name].set_title_width(title_width)
            self.rows[name].update_copy(
                labels[name],
                summaries[name],
            )

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the single settings editor action."""
        self.edit_button.configure(state="normal" if enabled else "disabled")


__all__: Sequence[str] = ("SettingsSummaryPanel", "SettingsSummaryRow")
