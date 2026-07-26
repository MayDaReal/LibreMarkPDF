"""Responsive projection of authoritative desktop conversion results."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Sequence

import customtkinter as ctk

from ..assets import UiAssetRegistry
from ..components import (
    CardFrame,
    IconButton,
    SecondaryButton,
    SectionTitle,
    StatusBadge,
    Tooltip,
)
from ..theme import COLORS, SIZES, SPACING, SystemFontResolver
from .file_row import middle_elide


_STATUS_TONES = {
    "ok": "success",
    "error": "error",
    "kept": "neutral",
    "cancelled": "neutral",
}

_LARGE_COLUMN_WEIGHTS = (28, 18, 34, 20)

_STATUS_ICONS = {
    "ok": "check-circle-fill",
    "error": "exclamation-circle-fill",
    "kept": "info-circle-fill",
    "cancelled": "dash",
}

class ResultRow(CardFrame):
    """One focusable result rendered as a table row or compact card."""

    def __init__(
        self,
        master,
        result: Mapping[str, object],
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        assets: UiAssetRegistry,
        mode: str,
        expanded: bool,
        on_focus_relative: Callable[[str, int], None],
        on_select: Callable[[str], None],
        on_toggle_details: Callable[[str], None],
        on_open: Callable[[Path], None],
        on_copy: Callable[[dict], None],
        on_report: Callable[[str, str], None],
    ) -> None:
        super().__init__(master, corner_radius=6)
        self.result = dict(result)
        self.source_id = str(self.result["input"])
        self._labels = dict(labels)
        self._assets = assets
        self._mode = mode
        self._expanded = expanded
        self._on_focus_relative = on_focus_relative
        self._on_select = on_select
        self._on_toggle_details = on_toggle_details
        self._selected = False
        self.action_buttons = []  # type: list[IconButton]
        self.details_button = None  # type: Optional[IconButton]
        self.details_frame = None  # type: Optional[ctk.CTkFrame]

        tk.Frame.configure(self, takefocus=True)
        self.bind("<Up>", lambda _event: self._move_focus(-1), add="+")
        self.bind("<Down>", lambda _event: self._move_focus(1), add="+")
        self.bind("<FocusIn>", self._show_focus, add="+")
        self.bind("<FocusOut>", self._hide_focus, add="+")
        self.bind("<Button-1>", self._select_pointer, add="+")

        source = Path(self.source_id)
        output_value = self.result.get("output")
        output = Path(str(output_value)) if output_value else None
        status = str(self.result["status"])
        status_text = self._labels["result_status_{0}".format(status)]

        if mode == "compact":
            self._build_compact(
                source,
                output,
                status,
                status_text,
                fonts,
                on_open,
                on_copy,
                on_report,
            )
        else:
            self._build_large(
                source,
                output,
                status,
                status_text,
                fonts,
                on_open,
                on_copy,
                on_report,
            )

    def _build_large(
        self,
        source: Path,
        output: Optional[Path],
        status: str,
        status_text: str,
        fonts: SystemFontResolver,
        on_open: Callable[[Path], None],
        on_copy: Callable[[dict], None],
        on_report: Callable[[str, str], None],
    ) -> None:
        for column, weight in enumerate(_LARGE_COLUMN_WEIGHTS):
            self.grid_columnconfigure(column, weight=weight, uniform="result")
        source_label = self._value_label(
            self,
            middle_elide(source.name, 36),
            str(source),
            fonts,
            elide_text=source.name,
        )
        self.source_label = source_label
        source_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(SPACING["md"], SPACING["sm"]),
            pady=SPACING["sm"],
        )
        badge = StatusBadge(
            self,
            text=status_text,
            tone=_STATUS_TONES[status],
            font=fonts.font("badge"),
            image=self._assets.image(
                _STATUS_ICONS[status], size=16, color=_STATUS_TONES[status]
            ),
            compound="left",
        )
        badge.grid(row=0, column=1, sticky="w", padx=SPACING["xs"])
        output_text = (
            self._error_summary()
            if status == "error" and output is None
            else output.name if output else "—"
        )
        output_label = self._value_label(
            self,
            middle_elide(output_text, 48),
            str(output) if output else output_text,
            fonts,
            elide_text=output_text,
        )
        self.output_label = output_label
        output_label.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=SPACING["sm"],
        )
        actions = ctk.CTkFrame(
            self, fg_color="transparent", width=1, height=1
        )
        actions.grid(
            row=0,
            column=3,
            sticky="e",
            padx=(SPACING["sm"], SPACING["md"]),
            pady=SPACING["xs"],
        )
        self._build_actions(
            actions, output, status, fonts, on_open, on_copy, on_report
        )
        self._build_details(fonts, row=1, columnspan=4)

    def _build_compact(
        self,
        source: Path,
        output: Optional[Path],
        status: str,
        status_text: str,
        fonts: SystemFontResolver,
        on_open: Callable[[Path], None],
        on_copy: Callable[[dict], None],
        on_report: Callable[[str, str], None],
    ) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=0)
        status_icon = ctk.CTkLabel(
            self,
            text="",
            image=self._assets.image(
                _STATUS_ICONS[status], size=24, color=_STATUS_TONES[status]
            ),
            width=24,
        )
        status_icon.grid(
            row=0,
            column=0,
            padx=(SPACING["md"], SPACING["sm"]),
            pady=SPACING["sm"],
        )
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew", pady=SPACING["xs"])
        text_frame.grid_columnconfigure(0, weight=1)
        name = self._value_label(
            text_frame,
            middle_elide(source.name, 32),
            str(source),
            fonts,
            elide_text=source.name,
        )
        self.source_label = name
        name.configure(font=fonts.font("label"))
        name.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        badge = StatusBadge(
            self,
            text=status_text,
            tone=_STATUS_TONES[status],
            font=fonts.font("badge"),
        )
        badge.grid(
            row=0,
            column=2,
            sticky="e",
            padx=SPACING["sm"],
        )
        if status == "ok":
            description = self._labels["result_output_value"].format(
                output=output.name if output else "—"
            )
        elif status == "kept":
            description = self._labels["result_kept_summary"].format(
                output=output.name if output else "—"
            )
        elif status == "error":
            description = self._error_summary()
        else:
            description = self._labels["result_cancelled_summary"]
        description_label = self._value_label(
            text_frame,
            middle_elide(description, 48),
            description,
            fonts,
            secondary=True,
            elide_text=description,
        )
        description_label.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        actions = ctk.CTkFrame(
            self, fg_color="transparent", width=1, height=1
        )
        actions.grid(
            row=0,
            column=3,
            sticky="e",
            padx=(0, SPACING["sm"]),
            pady=SPACING["xs"],
        )
        self._build_actions(
            actions, output, status, fonts, on_open, on_copy, on_report
        )
        self._build_details(fonts, row=1, columnspan=4)

    def _value_label(
        self,
        master,
        text: str,
        full_text: str,
        fonts: SystemFontResolver,
        secondary: bool = False,
        elide_text: Optional[str] = None,
    ) -> ctk.CTkLabel:
        font = fonts.font("secondary" if secondary else "body")
        label = ctk.CTkLabel(
            master,
            text=text,
            anchor="w",
            justify="left",
            text_color=(
                COLORS["text_secondary"] if secondary else COLORS["text"]
            ),
            font=font,
        )
        label.tooltip = Tooltip(label, full_text)
        label.bind("<Button-1>", self._select_pointer, add="+")
        if elide_text is not None:
            label.bind(
                "<Configure>",
                lambda event: self._resize_elided_label(
                    label, event.width, elide_text, font
                ),
                add="+",
            )
        return label

    @staticmethod
    def _resize_elided_label(label, width: int, text: str, font) -> None:
        available = max(1, int(width))
        if font.measure(text) <= available:
            display = text
        else:
            low = 5
            high = len(text)
            while low < high:
                limit = (low + high + 1) // 2
                candidate = middle_elide(text, limit)
                if font.measure(candidate) <= available:
                    low = limit
                else:
                    high = limit - 1
            display = middle_elide(text, low)
        if label.cget("text") != display:
            label.configure(text=display)

    def _build_actions(
        self,
        master,
        output: Optional[Path],
        status: str,
        _fonts: SystemFontResolver,
        on_open: Callable[[Path], None],
        on_copy: Callable[[dict], None],
        on_report: Callable[[str, str], None],
    ) -> None:
        actions = []
        if status == "ok" and output is not None:
            actions.extend((
                (
                    "box-arrow-up-right",
                    self._labels["open_pdf"],
                    lambda: on_open(output),
                ),
                (
                    "folder2-open",
                    self._labels["open_folder"],
                    lambda: on_open(output.parent),
                ),
            ))
        elif status == "error":
            actions.extend((
                (
                    "copy",
                    self._labels["copy_details"],
                    lambda: on_copy(self.result),
                ),
                (
                    "bug",
                    self._labels["report_issue_action"],
                    lambda: on_report(
                        str(self.result.get("error_code") or "UNKNOWN"),
                        str(self.result.get("error") or ""),
                    ),
                ),
            ))
        for index, (icon, label, command) in enumerate(actions):
            button = IconButton(
                master,
                image=self._assets.image(icon, size=16, color="neutral"),
                accessible_name=label,
                command=command,
            )
            button.grid(
                row=0,
                column=index,
                padx=(0, SPACING["xs"]),
            )
            self.action_buttons.append(button)
        if status in ("error", "cancelled") and (
            self.result.get("error") or self.result.get("error_code")
        ):
            detail_label = self._labels[
                "hide_details" if self._expanded else "show_details"
            ]
            self.details_button = IconButton(
                master,
                image=self._assets.image(
                    "info-circle-fill", size=16, color="neutral"
                ),
                accessible_name=detail_label,
                command=lambda: self._on_toggle_details(self.source_id),
            )
            self.details_button.grid(
                row=0,
                column=len(actions),
                padx=(0, SPACING["xs"]),
            )
            self.action_buttons.append(self.details_button)

    def _build_details(
        self,
        fonts: SystemFontResolver,
        row: int,
        columnspan: int,
    ) -> None:
        if not self._expanded:
            return
        details = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface_subtle"],
            corner_radius=6,
        )
        self.details_frame = details
        details.grid(
            row=row,
            column=0,
            columnspan=columnspan,
            sticky="ew",
            padx=SPACING["md"],
            pady=(0, SPACING["md"]),
        )
        details.grid_columnconfigure(0, weight=1)
        code = str(self.result.get("error_code") or "UNKNOWN")
        ctk.CTkLabel(
            details,
            text=self._labels["result_error_code"].format(code=code),
            anchor="w",
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["xs"]),
        )
        raw_details = str(
            self.result.get("error_details")
            or self.result.get("error")
            or ""
        )
        detail_lines = raw_details.splitlines()
        if detail_lines and detail_lines[0].strip() == self._error_summary().strip():
            detail_lines = detail_lines[1:]
        technical_details = "\n".join(detail_lines).strip()
        if technical_details:
            ctk.CTkLabel(
                details,
                text=technical_details,
                anchor="w",
                justify="left",
                wraplength=760,
                text_color=COLORS["text_secondary"],
                font=fonts.font("secondary", monospace=True),
            ).grid(
                row=1,
                column=0,
                sticky="ew",
                padx=SPACING["md"],
                pady=(0, SPACING["sm"]),
            )

    def _error_summary(self) -> str:
        message = str(self.result.get("error") or "")
        return message.splitlines()[0] if message else "—"

    def _select_pointer(self, _event=None) -> str:
        self.focus_set()
        self._on_select(self.source_id)
        return "break"

    def _move_focus(self, direction: int) -> str:
        self._on_focus_relative(self.source_id, direction)
        return "break"

    def _show_focus(self, _event=None) -> None:
        self._on_select(self.source_id)
        self.configure(border_color=COLORS["primary"], border_width=2)

    def _hide_focus(self, _event=None) -> None:
        self.configure(
            border_color=(
                COLORS["primary"] if self._selected else COLORS["border"]
            ),
            border_width=1,
        )

    def set_selected(self, selected: bool) -> None:
        """Keep the selected result visibly distinct from keyboard focus."""
        self._selected = selected
        self.configure(
            fg_color=(
                COLORS["surface_selected"] if selected else COLORS["surface"]
            ),
            border_color=(
                COLORS["primary"] if selected else COLORS["border"]
            ),
        )


class ResultsView(CardFrame):
    """Render one ordered result projection in large and compact layouts."""

    def __init__(
        self,
        master,
        labels: Mapping[str, str],
        fonts: SystemFontResolver,
        assets: UiAssetRegistry,
        on_clear: Callable[[], None],
        on_open: Callable[[Path], None],
        on_copy: Callable[[dict], None],
        on_report: Callable[[str, str], None],
        on_collapsed_changed: Callable[[bool], None],
        on_details_changed: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._labels = dict(labels)
        self._fonts = fonts
        self._assets = assets
        self._on_clear = on_clear
        self._on_open = on_open
        self._on_copy = on_copy
        self._on_report = on_report
        self._on_collapsed_changed = on_collapsed_changed
        self._on_details_changed = on_details_changed
        self._mode = "large"
        self._collapsed = True
        self._conversion_active = False
        self._expanded_sources = set()  # type: set[str]
        self._source_ids = []  # type: list[str]
        self._selected_source = None  # type: Optional[str]
        self.rows = {}  # type: Dict[str, ResultRow]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["md"],
            pady=SPACING["sm"],
        )
        header.grid_columnconfigure(2, weight=1)
        self.title_label = SectionTitle(
            header,
            text=self._labels["results_heading"],
            fonts=fonts,
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.header_summary = ctk.CTkLabel(
            header,
            text="",
            anchor="w",
            text_color=COLORS["text_secondary"],
            font=fonts.font("secondary"),
        )
        self.header_summary.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(SPACING["md"], SPACING["sm"]),
        )
        self.clear_button = IconButton(
            header,
            image=assets.image("trash3", size=16, color="neutral"),
            accessible_name=self._labels["clear_results"],
            command=self._on_clear,
        )
        self.clear_button.grid(row=0, column=3, sticky="e")
        self.collapse_button = SecondaryButton(
            header,
            text="⌄",
            command=self.toggle_collapsed,
            height=SIZES["icon_button"],
            width=SIZES["icon_button"],
            font=fonts.font("secondary"),
        )
        self.collapse_tooltip = Tooltip(
            self.collapse_button, self._labels["expand_results"]
        )
        self.collapse_button.grid(
            row=0,
            column=4,
            sticky="e",
            padx=(SPACING["xs"], 0),
        )

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)
        self.column_header = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["surface_subtle"],
            corner_radius=0,
        )
        for column, weight in enumerate(_LARGE_COLUMN_WEIGHTS):
            self.column_header.grid_columnconfigure(
                column, weight=weight, uniform="result-header"
            )
        self.column_labels = []
        for column, key in enumerate((
            "result_file_heading",
            "result_status_heading",
            "result_output_heading",
            "result_actions_heading",
        )):
            label = ctk.CTkLabel(
                self.column_header,
                text=self._labels[key],
                anchor="w" if column < 3 else "center",
                text_color=COLORS["text"],
                font=fonts.font("badge"),
            )
            label.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=SPACING["md"] if column < 3 else 0,
                pady=SPACING["xs"],
            )
            self.column_labels.append(label)
        self.global_error_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            justify="left",
            wraplength=900,
            text_color=COLORS["error"],
            font=fonts.font("body"),
        )
        self.list_view = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
            corner_radius=0,
        )
        self.list_view.grid_columnconfigure(0, weight=1)
        self.empty_label = ctk.CTkLabel(
            self.list_view,
            text=self._labels["results_empty"],
            text_color=COLORS["text_secondary"],
            font=fonts.font("body"),
        )
        self.summary_label = self.header_summary
        self._layout_content()

    @property
    def mode(self) -> str:
        """Return the current public projection mode."""
        return self._mode

    @property
    def collapsed(self) -> bool:
        """Return whether the non-compact content is hidden."""
        return self._collapsed

    @property
    def has_horizontal_scroll(self) -> bool:
        """Compact results intentionally expose vertical scrolling only."""
        return False

    def set_layout_mode(self, mode: str) -> None:
        """Switch presentation without changing result or detail state."""
        normalized = "compact" if mode == "compact" else "large"
        if normalized == self._mode:
            self._layout_content()
            return
        self._mode = normalized
        self._layout_content()

    def set_collapsed(self, collapsed: bool) -> None:
        """Collapse the bounded desktop panel; compact tabs stay expanded."""
        if self._mode == "compact":
            return
        collapsed = bool(collapsed)
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self._layout_content()
        self._on_collapsed_changed(collapsed)

    def toggle_collapsed(self) -> str:
        self.set_collapsed(not self._collapsed)
        return "break"

    def set_conversion_active(self, active: bool) -> None:
        """Hide destructive-looking UI clearing while conversion is active."""
        self._conversion_active = bool(active)
        self._update_clear_visibility()

    def set_results(
        self,
        results: Sequence[Mapping[str, object]],
        summary: str,
        global_error: Optional[str] = None,
    ) -> None:
        """Project authoritative ordered results without deduplication."""
        focused_source = self._focused_source()
        for row in self.rows.values():
            row.destroy()
        self.rows = {}
        self._source_ids = [str(result["input"]) for result in results]
        self._expanded_sources.intersection_update(self._source_ids)
        if self._selected_source not in self._source_ids:
            self._selected_source = None
        self.empty_label.grid_forget()
        if not results:
            self.empty_label.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=SPACING["md"],
                pady=SPACING["xl"],
            )
        for index, result in enumerate(results):
            source_id = str(result["input"])
            row = ResultRow(
                self.list_view,
                result=result,
                labels=self._labels,
                fonts=self._fonts,
                assets=self._assets,
                mode=self._mode,
                expanded=source_id in self._expanded_sources,
                on_focus_relative=self.focus_relative,
                on_select=self.select_source,
                on_toggle_details=self.toggle_details,
                on_open=self._on_open,
                on_copy=self._on_copy,
                on_report=self._on_report,
            )
            row.grid(
                row=index,
                column=0,
                sticky="ew",
                padx=SPACING["xs"],
                pady=(0, SPACING["xs"]),
            )
            self.rows[source_id] = row
        self.summary_label.configure(text=summary)
        self.header_summary.configure(text=summary)
        if global_error:
            self.global_error_label.configure(
                text="{0}: {1}".format(
                    self._labels["batch_error"], global_error
                )
            )
            self.global_error_label.grid(
                row=1,
                column=0,
                sticky="ew",
                padx=SPACING["md"],
                pady=(0, SPACING["sm"]),
            )
        else:
            self.global_error_label.grid_forget()
        if self._selected_source in self.rows:
            self.rows[self._selected_source].set_selected(True)
        self._update_clear_visibility(
            has_content=bool(results or global_error)
        )
        if focused_source in self.rows:
            self.after_idle(self.rows[focused_source].focus_set)

    def select_source(self, source_id: str) -> None:
        """Keep one visibly selected result without changing source order."""
        previous = self._selected_source
        self._selected_source = source_id
        for identifier in (previous, source_id):
            if identifier in self.rows:
                self.rows[identifier].set_selected(identifier == source_id)

    def focus_relative(self, source_id: str, direction: int) -> None:
        """Move keyboard focus through the ordered result projection."""
        try:
            index = self._source_ids.index(source_id)
        except ValueError:
            return
        target = max(0, min(len(self._source_ids) - 1, index + direction))
        target_id = self._source_ids[target]
        self.select_source(target_id)
        self.rows[target_id].focus_set()

    def focus_result(self, source_id: str) -> None:
        """Focus a particular result when a terminal error needs attention."""
        if source_id in self.rows:
            self.select_source(source_id)
            self.after_idle(self.rows[source_id].focus_set)

    def focus_results(self) -> None:
        """Focus the first projected result when no item-specific error exists."""
        if self._source_ids:
            self.focus_result(self._source_ids[0])
        else:
            self.collapse_button.focus_set()

    def toggle_details(self, source_id: str) -> None:
        """Persist detail expansion across progress and translation rebuilds."""
        if source_id in self._expanded_sources:
            self._expanded_sources.remove(source_id)
        else:
            self._expanded_sources.add(source_id)
        self._on_details_changed()

    def retranslate(self, labels: Mapping[str, str]) -> None:
        """Update stable panel copy; the owner reprojects authoritative rows."""
        self._labels = dict(labels)
        self.title_label.configure(text=self._labels["results_heading"])
        self.empty_label.configure(text=self._labels["results_empty"])
        self.clear_button.update_accessible_name(
            self._labels["clear_results"]
        )
        for label, key in zip(self.column_labels, (
            "result_file_heading",
            "result_status_heading",
            "result_output_heading",
            "result_actions_heading",
        )):
            label.configure(text=self._labels[key])
        self._update_collapse_text()

    def _layout_content(self) -> None:
        self.content.grid_forget()
        self.column_header.grid_forget()
        if self._mode == "compact":
            self.collapse_button.grid_remove()
            show_content = True
        else:
            self.collapse_button.grid()
            show_content = not self._collapsed
        self._update_collapse_text()
        if not show_content:
            return
        self.content.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=SPACING["xs"],
            pady=(0, SPACING["sm"]),
        )
        if self._mode == "large":
            self.column_header.grid(row=0, column=0, sticky="ew")
        self.list_view.grid(row=2, column=0, sticky="nsew")

    def _update_collapse_text(self) -> None:
        label = self._labels[
            "expand_results" if self._collapsed else "collapse_results"
        ]
        self.collapse_button.configure(text="⌃" if self._collapsed else "⌄")
        self.collapse_button.accessible_name = label
        self.collapse_tooltip.update_text(label)

    def _update_clear_visibility(
        self, has_content: Optional[bool] = None
    ) -> None:
        if has_content is None:
            has_content = bool(self._source_ids) or bool(
                self.global_error_label.winfo_manager()
            )
        self.clear_button.configure(
            state="disabled" if self._conversion_active else "normal"
        )
        if has_content and not self._conversion_active:
            self.clear_button.grid()
        else:
            self.clear_button.grid_remove()

    def _focused_source(self) -> Optional[str]:
        focus = self.focus_get()
        for source_id, row in self.rows.items():
            current = focus
            while current is not None:
                if current is row:
                    return source_id
                current = getattr(current, "master", None)
        return None
