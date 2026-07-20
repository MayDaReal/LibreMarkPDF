"""File, theme, output, and render-option controls for the Tk adapter."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import Iterable, Optional, Union

from ... import core
from .components import configure_icon_button
from .styles import (
    ACTIVE_FILE_ROW_STYLE,
    FILE_LIST_HEIGHT,
    FILE_ROW_HEIGHT,
    ICON_BUTTON_STYLE,
)


class TkInputMixin:
    """Translate Tk input state into shared-core options."""

    def _redraw_drop_zone(self, event=None) -> None:
        self.drop_canvas.delete("all")
        width = self.drop_canvas.winfo_width() or 500
        state = getattr(self, "_drop_zone_state", "empty")
        text = {
            "active": self._t("drop_active"),
            "unsupported": self._t("unsupported_drop"),
        }.get(state, self._drop_zone_text)
        self.drop_canvas.configure(
            highlightthickness=2 if state in ("active", "unsupported") else 1
        )
        if hasattr(self, "browse_button"):
            self.browse_button.config(
                text={
                    "active": self._t("drop_active"),
                    "unsupported": self._t("unsupported_drop"),
                }.get(state, self._t("add_files"))
            )
        self.drop_canvas.create_text(
            width // 2,
            48,
            text=text,
            fill=self.ui_styles.drop_border,
            font="TkDefaultFont",
            width=max(120, width - 32),
            justify="center",
        )

    def _drop_paths(self, event) -> tuple:
        return tuple(self.root.tk.splitlist(event.data))

    def _on_drop_enter(self, event) -> str:
        if self.operation != "idle":
            return "refuse_drop"
        paths = self._drop_paths(event) if event.data else ()
        file_drag = getattr(self, "_dnd_files_type", None) in getattr(
            event, "types", ()
        )
        self._drop_zone_state = (
            "active"
            if file_drag
            or any(
                Path(path).suffix.lower() in (".md", ".markdown")
                for path in paths
            )
            else "unsupported"
        )
        self._redraw_drop_zone()
        return "copy"

    def _on_drop_leave(self, _event=None) -> str:
        self._drop_zone_state = "empty"
        self._redraw_drop_zone()
        return "copy"

    def _on_drop(self, event) -> str:
        if self.operation != "idle":
            return "refuse_drop"
        self._drop_zone_state = "empty"
        self._redraw_drop_zone()
        self._add_files(self.root.tk.splitlist(event.data))
        return "copy"

    def _browse_files(self) -> None:
        if self.operation != "idle":
            return
        paths = self.dialogs.choose_markdown_files(
            self._t("choose_markdown_title"),
            [(self._t("markdown_filter_name"), "*.md *.markdown")],
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths: Iterable[Union[str, Path]]) -> None:
        if self.operation != "idle":
            return
        added = []
        duplicates = 0
        unsupported = 0
        for raw_path in paths:
            path = Path(raw_path)
            if path.suffix.lower() not in (".md", ".markdown"):
                unsupported += 1
            elif path in self.files:
                duplicates += 1
            else:
                self.files.append(path)
                added.append(path)
        if self.active_file not in self.files:
            self.active_file = added[0] if added else None
        if added:
            self._render_file_list(focus_path=added[0])
            self._refresh_generate_button()
            self._schedule_preview()
        if duplicates or unsupported:
            self._set_status(
                "files_add_summary",
                added=len(added),
                duplicates=duplicates,
                unsupported=unsupported,
            )
        elif len(added) == 1:
            self._set_status("files_added_one")
        elif added:
            self._set_status("files_added_many", count=len(added))

    def _select_file(self, path: Path) -> None:
        if self.operation != "idle" or path not in self.files:
            return
        self.active_file = path
        self._render_file_list(focus_path=path)
        self._schedule_preview()

    def _remove_file(self, path: Path) -> None:
        if self.operation != "idle":
            return
        try:
            removed_index = self.files.index(path)
        except ValueError:
            return
        was_active = path == self.active_file
        self.files = [item for item in self.files if item != path]
        if was_active:
            if self.files:
                self.active_file = self.files[min(removed_index, len(self.files) - 1)]
            else:
                self.active_file = None
        self._render_file_list(focus_path=self.active_file)
        self._refresh_generate_button()
        if self.files:
            self._schedule_preview()
        else:
            self._invalidate_preview(clear_image=True)

    def _clear_files(self) -> None:
        if self.operation == "idle":
            self.files = []
            self.active_file = None
            self._render_file_list()
            self._refresh_generate_button()
            self._invalidate_preview(clear_image=True)

    def _render_file_list(self, focus_path: Optional[Path] = None) -> None:
        for widget in self._file_operation_controls:
            if widget in self._operation_controls:
                self._operation_controls.remove(widget)
        self._file_operation_controls = []
        for child in self.file_list_frame.winfo_children():
            child.destroy()
        count = len(self.files)
        self.file_count_label.config(
            text=self._t(
                "file_count_one" if count == 1 else "file_count_many",
                count=count,
            )
        )
        if count:
            self.drop_canvas.pack_forget()
            self.file_box.pack(fill="x")
            self.clear_files_button.pack(side="right")
        else:
            self.file_box.pack_forget()
            self.clear_files_button.pack_forget()
            self.drop_canvas.pack(fill="x", before=self.browse_button.master)
        list_height = min(
            FILE_LIST_HEIGHT * 2,
            max(FILE_ROW_HEIGHT, count * FILE_ROW_HEIGHT),
        )
        self.file_canvas.configure(height=list_height)
        self._file_row_buttons = {}
        self.active_file_var.set(
            str(self.active_file) if self.active_file is not None else ""
        )
        for path in self.files:
            row = ttk.Frame(
                self.file_list_frame,
                padding=(4, 2),
                height=FILE_ROW_HEIGHT,
            )
            row.pack(fill="x")
            row.pack_propagate(False)
            selector = ttk.Radiobutton(
                row,
                text=path.name,
                value=str(path),
                variable=self.active_file_var,
                command=lambda selected=path: self._select_file(selected),
                style=(
                    ACTIVE_FILE_ROW_STYLE
                    if path == self.active_file
                    else "TRadiobutton"
                ),
            )
            selector.pack(side="left", fill="x", expand=True)
            selector.bind(
                "<Return>",
                lambda event, selected=path: self._select_file(selected),
            )
            selector.bind(
                "<Delete>",
                lambda event, selected=path: self._remove_file(selected),
            )
            parent = ttk.Label(row, text=str(path.parent), anchor="w")
            parent.pack(
                side="left", fill="x", expand=True
            )
            for target in (row, parent):
                target.bind(
                    "<Button-1>",
                    lambda event, selected=path: self._select_file(selected),
                )
            button = ttk.Button(
                row,
                command=lambda selected=path: self._remove_file(selected),
                style=ICON_BUTTON_STYLE,
            )
            accessible_name = self._t("remove_file_a11y", name=path.name)
            configure_icon_button(button, self.ui_icons.remove, accessible_name)
            button.pack(side="right")
            self._file_row_buttons[path] = selector
            self._file_operation_controls.extend((selector, button))
        self._operation_controls.extend(self._file_operation_controls)
        if self.operation != "idle":
            for widget in self._file_operation_controls:
                widget.config(state="disabled")
        if focus_path in self._file_row_buttons:
            self._file_row_buttons[focus_path].focus_set()

    def _choose_css(self) -> None:
        path = self.dialogs.choose_css_file(
            self._t("choose_css_title"),
            [(self._t("css_filter_name"), "*.css")],
        )
        if path:
            self.css_path = path
            self._refresh_css_entry()
            self._render_theme_cards()
            self._schedule_preview()

    def _reset_css(self) -> None:
        self.css_path = None
        self._refresh_css_entry()
        self._render_theme_cards()
        self._schedule_preview()

    def _refresh_css_entry(self) -> None:
        value = self.css_path or self._t("css_from_theme_value")
        self.css_entry.config(state="normal")
        self.css_entry.delete(0, "end")
        self.css_entry.insert(0, value)
        self.css_entry.config(state="readonly")

    def _select_theme(self, reference: str) -> None:
        if self.operation != "idle":
            return
        self.theme_var.set(reference)
        self.css_path = None
        self._refresh_css_entry()
        self._render_theme_cards()
        self._schedule_preview()

    def _render_theme_cards(self) -> None:
        for child in self.theme_cards.winfo_children():
            child.destroy()
        self._theme_buttons = []
        try:
            themes = core.list_themes()
        except Exception as exc:
            themes = [core.show_theme(core.DEFAULT_THEME_ID)]
            self._set_status("status_theme_error", error=str(exc))
        for info in themes:
            card = ttk.Radiobutton(
                self.theme_cards,
                text="{0} ({1})".format(info.names[self.lang], info.reference),
                value=info.reference,
                variable=self.theme_var,
                command=lambda ref=info.reference: self._select_theme(ref),
            )
            card.pack(side="left", padx=(0, 8), pady=2)
            if self.css_path:
                card.config(state="disabled")
            self._theme_buttons.append(card)
        if self.operation != "idle":
            for card in self._theme_buttons:
                card.config(state="disabled")

    def _choose_output_dir(self) -> None:
        path = self.dialogs.choose_output_folder(
            self._t("choose_output_folder_title")
        )
        if path:
            self.output_dir = path
            self._refresh_output_entry()

    def _reset_output_dir(self) -> None:
        self.output_dir = None
        self._refresh_output_entry()

    def _refresh_output_entry(self) -> None:
        value = self.output_dir or self._t("output_default_value")
        self.output_entry.config(state="normal")
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, value)
        self.output_entry.config(state="readonly")

    def _toggle_advanced(self) -> None:
        self.advanced_open.set(not self.advanced_open.get())
        if self.advanced_open.get():
            self.advanced_content.pack(fill="x")
        else:
            self.advanced_content.pack_forget()
        self.advanced_toggle.config(
            text=("\u25be " if self.advanced_open.get() else "\u25b8 ")
            + self._t("advanced_toggle")
        )

    def _current_header_footer(self) -> core.HeaderFooterConfig:
        return core.HeaderFooterConfig(
            top_left=self.hf_vars["header_left"].get(),
            top_center=self.hf_vars["header_center"].get(),
            top_right=self.hf_vars["header_right"].get(),
            bottom_left=self.hf_vars["footer_left"].get(),
            bottom_center=self.hf_vars["footer_center"].get(),
            bottom_right=self.hf_vars["footer_right"].get(),
        )

    def _render_options(self) -> dict:
        return {
            "css_path": self.css_path,
            "header_footer": self._current_header_footer(),
            "render_date": self.render_date_var.get().strip() or None,
            "trusted_html": self.trusted_html_var.get(),
            "theme": None if self.css_path else self.theme_var.get(),
        }
