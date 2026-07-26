"""File, theme, output, and render-option controls for the Tk adapter."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Iterable, Optional, Union

from ... import core
from .styles import (
    SPACE_SM,
)


class TkInputMixin:
    """Translate Tk input state into shared-core options."""

    def _redraw_drop_zone(self, event=None) -> None:
        state = getattr(self, "_drop_zone_state", "empty")
        if hasattr(self, "files_panel"):
            self.files_panel.set_drop_state(state)

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
        was_empty = not self.files
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
            if was_empty:
                self._preview_fit_mode = "page"
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
        if added or duplicates or unsupported:
            self._schedule_file_feedback_clear()

    def _format_files_add_summary(
        self, added: int, duplicates: int, unsupported: int
    ) -> str:
        messages = []
        if added:
            messages.append(
                self._tp(
                    "file_feedback_added_one",
                    "file_feedback_added_many",
                    added,
                )
            )
        for count, one_key, many_key in (
            (
                duplicates,
                "file_feedback_duplicate_one",
                "file_feedback_duplicate_many",
            ),
            (
                unsupported,
                "file_feedback_unsupported_one",
                "file_feedback_unsupported_many",
            ),
        ):
            if count:
                messages.append(self._tp(one_key, many_key, count))
        return " · ".join(messages)

    def _schedule_file_feedback_clear(self) -> None:
        if not hasattr(self, "root"):
            return
        previous = getattr(self, "_file_feedback_after", None)
        if previous is not None:
            self.root.after_cancel(previous)

        def clear_feedback() -> None:
            self._file_feedback_after = None
            if self._status_key in (
                "files_add_summary",
                "files_added_one",
                "files_added_many",
            ):
                self._set_status("status_ready")

        self._file_feedback_after = self.root.after(6000, clear_feedback)

    def _select_file(self, path: Path) -> None:
        if self.operation != "idle" or path not in self.files:
            return
        active_changed = path != self.active_file
        self.active_file = path
        if active_changed:
            self._preview_fit_mode = "page"
        self._render_file_list(focus_path=path)
        self._schedule_preview()

    def _show_source_file(self, path: Path) -> None:
        try:
            self.services.open_path(path.parent)
        except Exception as exc:
            self.dialogs.show_error(
                self._t("error_title"),
                self._t("open_error", error=str(exc)),
            )

    def _copy_source_path(self, path: Path) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(str(path))

    def _remove_file(self, path: Path) -> None:
        if self.operation != "idle":
            return
        try:
            removed_index = self.files.index(path)
        except ValueError:
            return
        was_active = path == self.active_file
        self.files = [item for item in self.files if item != path]
        focus_path = (
            self.files[min(removed_index, len(self.files) - 1)]
            if self.files
            else None
        )
        if was_active:
            if self.files:
                self.active_file = self.files[min(removed_index, len(self.files) - 1)]
                self._preview_fit_mode = "page"
            else:
                self.active_file = None
        getattr(self, "_file_conversion_states", {}).pop(path, None)
        self._render_file_list(focus_path=focus_path)
        self._refresh_generate_button()
        if self.files:
            self._schedule_preview()
        else:
            self._invalidate_preview(clear_image=True)

    def _clear_files(self) -> None:
        if self.operation == "idle":
            self.files = []
            self.active_file = None
            self._file_conversion_states = {}
            self._render_file_list()
            self._refresh_generate_button()
            self._invalidate_preview(clear_image=True)

    def _render_file_list(self, focus_path: Optional[Path] = None) -> None:
        self.files_panel.set_files(
            self.files,
            active=self.active_file,
            focus_path=focus_path,
        )
        self.files_panel.set_conversion_states(
            getattr(self, "_file_conversion_states", {})
        )
        self._refresh_accordion_headers()

    def _choose_css(self) -> None:
        path = self.dialogs.choose_css_file(
            self._t("choose_css_title"),
            [(self._t("css_filter_name"), "*.css")],
        )
        if path:
            self._settings_draft_css_path = path
            self._settings_draft_style_mode_var.set("css")
            self._refresh_css_entry()
            self._render_theme_cards()
            if getattr(self, "_style_editor_open", False):
                self._refresh_style_editors()
                self._schedule_style_draft_preview()

    def _activate_css_mode(self) -> None:
        if self._settings_draft_css_path:
            return
        self._choose_css()
        if not self._settings_draft_css_path:
            self._settings_draft_style_mode_var.set("theme")

    def _reset_css(self) -> None:
        self._settings_draft_css_path = None
        self._settings_draft_style_mode_var.set("theme")
        self._refresh_css_entry()
        self._render_theme_cards()

    def _refresh_css_entry(self) -> None:
        value = (
            self._settings_draft_css_path
            or self._t("css_from_theme_value")
        )
        self.css_entry.config(state="normal")
        self.css_entry.delete(0, "end")
        self.css_entry.insert(0, value)
        self.css_entry.config(state="readonly")
        self._refresh_accordion_headers()

    def _select_theme(self, reference: str) -> None:
        if self.operation != "idle":
            return
        self._settings_draft_theme_var.set(reference)
        self._settings_draft_css_path = None
        self._settings_draft_style_mode_var.set("theme")
        self._refresh_css_entry()
        self._render_theme_cards()

    def _render_theme_cards(self) -> None:
        for child in self.theme_cards.winfo_children():
            child.destroy()
        self._theme_buttons = []
        self._theme_summaries = {}
        try:
            themes = core.list_themes()
        except Exception as exc:
            themes = [core.show_theme(core.DEFAULT_THEME_ID)]
            self._set_status("status_theme_error", error=str(exc))
        for info in themes:
            self._theme_summaries[info.reference] = info.names[self.lang]
            card = ttk.Radiobutton(
                self.theme_cards,
                text="{0} ({1})".format(info.names[self.lang], info.reference),
                value=info.reference,
                variable=self._settings_draft_theme_var,
                command=lambda ref=info.reference: self._select_theme(ref),
            )
            card.pack(side="left", padx=(0, 8), pady=2)
            if self._settings_draft_css_path:
                card.config(state="disabled")
            self._theme_buttons.append(card)
        if self.operation != "idle":
            for card in self._theme_buttons:
                card.config(state="disabled")
        self._refresh_accordion_headers()

    def _style_editor_labels(self) -> dict:
        return {
            "title": self._t("style_editor_title"),
            "description": self._t("style_editor_description"),
            "back": self._t("back_settings"),
            "local_theme": self._t("local_theme"),
            "custom_css": self._t("custom_css"),
            "choose_css": self._t("choose_css"),
            "cancel": self._t("cancel_settings"),
            "save": self._t("save_settings"),
        }

    def _style_editor_themes(self) -> list:
        try:
            return core.list_themes()
        except Exception as exc:
            self._set_status("status_theme_error", error=str(exc))
            return [core.show_theme(core.DEFAULT_THEME_ID)]

    def _refresh_style_editors(self) -> None:
        if not hasattr(self, "style_dialog_editor"):
            return
        themes = self._style_editor_themes()
        selected = self._settings_draft_theme_var.get()
        selected_info = next(
            (info for info in themes if info.reference == selected),
            themes[0],
        )
        self._style_theme_display_var.set(selected_info.names[self.lang])
        self._style_css_display_var.set(
            self._settings_draft_css_path or self._t("css_empty_state")
        )
        labels = self._style_editor_labels()
        choices = tuple(
            (info.reference, info.names[self.lang]) for info in themes
        )
        technical = self._t(
            "style_theme_technical", reference=selected_info.reference
        )
        mode = self._settings_draft_style_mode_var.get()
        for editor in (self.style_dialog_editor, self.compact_style_editor):
            editor.retranslate(labels)
            editor.set_themes(choices, selected_info.reference, technical)
            editor.set_mode(mode)

    def _on_style_mode_changed(self) -> None:
        if self._settings_draft_style_mode_var.get() == "css" and not (
            self._settings_draft_css_path
        ):
            self._choose_css()
            if not self._settings_draft_css_path:
                self._settings_draft_style_mode_var.set("theme")
        self._refresh_style_editors()
        self._schedule_style_draft_preview()

    def _select_style_theme(self, reference: str) -> None:
        self._settings_draft_theme_var.set(reference)
        self._settings_draft_style_mode_var.set("theme")
        self._refresh_style_editors()
        self._schedule_style_draft_preview()

    def _draft_style_render_options(self) -> dict:
        options = self._render_options()
        if self._settings_draft_style_mode_var.get() == "css":
            options["css_path"] = self._settings_draft_css_path
            options["theme"] = None
        else:
            options["css_path"] = None
            options["theme"] = self._settings_draft_theme_var.get()
        return options

    def _validate_style_draft(self) -> bool:
        if (
            self._settings_draft_style_mode_var.get() == "css"
            and not self._settings_draft_css_path
        ):
            self._style_error_var.set(self._t("css_validation_required"))
            return False
        try:
            core.render_profile_for_options(**self._draft_style_render_options())
        except Exception:
            self._style_error_var.set(self._t("css_validation_invalid"))
            return False
        self._style_error_var.set("")
        return True

    def _schedule_style_draft_preview(self) -> None:
        if not getattr(self, "_style_editor_open", False):
            return
        if not self._validate_style_draft():
            self._invalidate_preview()
            return
        self._schedule_preview()

    def _preview_render_options(self) -> dict:
        if getattr(self, "_style_editor_open", False):
            return self._draft_style_render_options()
        if getattr(self, "_header_footer_editor_open", False):
            return self._draft_header_footer_render_options()
        if getattr(self, "_advanced_editor_open", False):
            return self._draft_advanced_render_options()
        return self._render_options()

    def _capture_preview_snapshot(self) -> dict:
        return {
            "png": self._preview_png,
            "state": self._preview_state,
            "error": self._preview_error,
            "page": self._preview_page,
            "total_pages": self._preview_total_pages,
            "pages": dict(self._preview_pages),
            "page_pending": self._preview_page_pending,
            "failed_page": self._preview_failed_page,
            "status_key": self._status_key,
            "status_kwargs": dict(self._status_kwargs),
        }

    def _restore_preview_snapshot(self, snapshot: dict) -> None:
        self._invalidate_preview()
        self._preview_running = False
        self._preview_active_request = None
        self._preview_png = snapshot["png"]
        self._preview_state = snapshot["state"]
        self._preview_error = snapshot["error"]
        self._preview_page = snapshot["page"]
        self._preview_total_pages = snapshot["total_pages"]
        self._preview_pages = dict(snapshot["pages"])
        self._preview_page_pending = snapshot["page_pending"]
        self._preview_failed_page = snapshot["failed_page"]
        if self._preview_png is not None:
            self._redraw_preview()
        else:
            self._draw_preview_state()
        self._refresh_preview_ui()
        self._refresh_generate_button()
        self._set_status(snapshot["status_key"], **snapshot["status_kwargs"])

    def _open_style_editor(self) -> str:
        if self.operation != "idle":
            return "break"
        if getattr(self, "_destination_editor_open", False):
            return "break"
        if getattr(self, "_header_footer_editor_open", False):
            return "break"
        if getattr(self, "_advanced_editor_open", False):
            return "break"
        if self._style_editor_open:
            self._show_style_editor_host()
            return "break"
        self._settings_dialog["snapshot"] = self._settings_snapshot()
        self._load_settings_draft(self._settings_dialog["snapshot"])
        self._style_editor_preview_snapshot = self._capture_preview_snapshot()
        self._settings_dialog["return_focus"] = self.root.focus_get()
        self._style_error_var.set("")
        self._style_editor_open = True
        self._refresh_style_editors()
        self._show_style_editor_host()
        return "break"

    def _position_style_dialog(self) -> None:
        dialog = self._style_dialog
        width = max(560, min(680, self.root.winfo_width() - 48))
        height = max(520, min(620, self.root.winfo_height() - 48))
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - height) // 2)
        dialog.geometry("{0}x{1}+{2}+{3}".format(width, height, x, y))

    def _show_style_editor_host(self) -> None:
        if not self._style_editor_open:
            return
        dialog = self._style_dialog
        if self._layout_mode == "compact":
            if dialog.grab_current() is dialog:
                dialog.grab_release()
            dialog.withdraw()
            self._active_compact_tab = "settings"
            self._show_active_compact_section()
            self.compact_style_editor.focus_initial(
                self._settings_draft_style_mode_var.get()
            )
            return
        self.compact_style_editor.grid_forget()
        self._position_style_dialog()
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        self.style_dialog_editor.focus_initial(
            self._settings_draft_style_mode_var.get()
        )

    def _close_style_editor(self) -> str:
        dialog = self._style_dialog
        if dialog.grab_current() is dialog:
            dialog.grab_release()
        dialog.withdraw()
        self.compact_style_editor.grid_forget()
        self._style_editor_open = False
        if self._layout_mode == "compact":
            self._show_active_compact_section()
        focus = self._settings_dialog.get("return_focus")
        try:
            (focus or self.settings_panel.rows["style"]).focus_set()
        except tk.TclError:
            self.root.focus_set()
        return "break"

    def _save_style_editor(self) -> str:
        if not self._validate_style_draft():
            return "break"
        mode = self._settings_draft_style_mode_var.get()
        self.css_path = (
            self._settings_draft_css_path if mode == "css" else None
        )
        self.style_mode_var.set(mode)
        self.theme_var.set(self._settings_draft_theme_var.get())
        self._refresh_accordion_headers()
        return self._close_style_editor()

    def _cancel_style_editor(self, _event=None) -> str:
        if not getattr(self, "_style_editor_open", False):
            return "break"
        snapshot = self._settings_dialog.get("snapshot")
        if snapshot is not None:
            self._load_settings_draft(snapshot)
        preview = self._style_editor_preview_snapshot
        if preview is not None:
            self._restore_preview_snapshot(preview)
        return self._close_style_editor()

    def _choose_output_dir(self) -> None:
        path = self.dialogs.choose_output_folder(
            self._t("choose_output_folder_title")
        )
        if path:
            self._settings_draft_output_dir = path
            if hasattr(self, "_destination_mode_var"):
                self._destination_mode_var.set("custom")
            self._refresh_output_entry()

    def _reset_output_dir(self) -> None:
        self._settings_draft_output_dir = None
        if hasattr(self, "_destination_mode_var"):
            self._destination_mode_var.set("source")
        self._refresh_output_entry()

    def _refresh_output_entry(self) -> None:
        value = (
            self._settings_draft_output_dir
            or self._t("output_default_value")
        )
        self.output_entry.config(state="normal")
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, value)
        self.output_entry.config(state="readonly")
        self._refresh_destination_editors()
        self._refresh_accordion_headers()

    def _destination_editor_labels(self) -> dict:
        return {
            "title": self._t("destination_editor_title"),
            "description": self._t("destination_editor_description"),
            "back": self._t("back_settings"),
            "source": self._t("destination_source_option"),
            "custom": self._t("destination_custom_option"),
            "choose": self._t("destination_choose_folder"),
            "cancel": self._t("cancel_settings"),
            "save": self._t("save_settings"),
        }

    def _refresh_destination_editors(self) -> None:
        if not hasattr(self, "destination_dialog_editor"):
            return
        mode = "custom" if self._settings_draft_output_dir else "source"
        self._destination_mode_var.set(mode)
        self._destination_path_var.set(
            self._settings_draft_output_dir
            or self._t("destination_no_folder_selected")
        )
        labels = self._destination_editor_labels()
        for editor in (
            self.destination_dialog_editor,
            self.compact_destination_editor,
        ):
            editor.retranslate(labels)
            editor.set_mode(mode)

    def _on_destination_mode_changed(self) -> None:
        mode = self._destination_mode_var.get()
        self._destination_error_var.set("")
        if mode == "source":
            self._settings_draft_output_dir = None
            self._refresh_output_entry()
            return
        if not self._settings_draft_output_dir:
            self._choose_destination_folder()
            if not self._settings_draft_output_dir:
                self._destination_mode_var.set("source")
        self._refresh_destination_editors()

    def _choose_destination_folder(self) -> None:
        self._choose_output_dir()
        self._refresh_destination_editors()

    def _validate_destination_draft(self) -> bool:
        if (
            self._destination_mode_var.get() == "custom"
            and not self._settings_draft_output_dir
        ):
            self._destination_error_var.set(
                self._t("destination_validation_required")
            )
            return False
        self._destination_error_var.set("")
        return True

    def _open_destination_editor(self) -> str:
        if self.operation != "idle":
            return "break"
        if getattr(self, "_style_editor_open", False):
            return "break"
        if getattr(self, "_header_footer_editor_open", False):
            return "break"
        if getattr(self, "_advanced_editor_open", False):
            return "break"
        if self._destination_editor_open:
            self._show_destination_editor_host()
            return "break"
        self._settings_dialog["snapshot"] = self._settings_snapshot()
        self._load_settings_draft(self._settings_dialog["snapshot"])
        self._settings_dialog["return_focus"] = self.root.focus_get()
        self._destination_error_var.set("")
        self._destination_editor_open = True
        self._refresh_destination_editors()
        self._show_destination_editor_host()
        return "break"

    def _position_destination_dialog(self) -> None:
        dialog = self._destination_dialog
        width = max(560, min(680, self.root.winfo_width() - 48))
        height = max(520, min(580, self.root.winfo_height() - 48))
        x = self.root.winfo_rootx() + max(
            0, (self.root.winfo_width() - width) // 2
        )
        y = self.root.winfo_rooty() + max(
            0, (self.root.winfo_height() - height) // 2
        )
        dialog.geometry("{0}x{1}+{2}+{3}".format(width, height, x, y))

    def _show_destination_editor_host(self) -> None:
        if not self._destination_editor_open:
            return
        dialog = self._destination_dialog
        mode = self._destination_mode_var.get()
        if self._layout_mode == "compact":
            if dialog.grab_current() is dialog:
                dialog.grab_release()
            dialog.withdraw()
            self._active_compact_tab = "settings"
            self._show_active_compact_section()
            self.compact_destination_editor.focus_initial(mode)
            return
        self.compact_destination_editor.grid_forget()
        self._position_destination_dialog()
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        self.destination_dialog_editor.focus_initial(mode)

    def _close_destination_editor(self) -> str:
        dialog = self._destination_dialog
        if dialog.grab_current() is dialog:
            dialog.grab_release()
        dialog.withdraw()
        self.compact_destination_editor.grid_forget()
        self._destination_editor_open = False
        if self._layout_mode == "compact":
            self._show_active_compact_section()
        focus = self._settings_dialog.get("return_focus")
        try:
            (focus or self.settings_panel.rows["destination"]).focus_set()
        except tk.TclError:
            self.root.focus_set()
        return "break"

    def _save_destination_editor(self) -> str:
        if not self._validate_destination_draft():
            return "break"
        self.output_dir = self._settings_draft_output_dir
        self._refresh_output_entry()
        self._refresh_accordion_headers()
        return self._close_destination_editor()

    def _cancel_destination_editor(self, _event=None) -> str:
        if not getattr(self, "_destination_editor_open", False):
            return "break"
        snapshot = self._settings_dialog.get("snapshot")
        if snapshot is not None:
            self._load_settings_draft(snapshot)
        return self._close_destination_editor()

    @staticmethod
    def _header_footer_defaults() -> dict:
        return {
            "header_left": "",
            "header_center": "",
            "header_right": "",
            "footer_left": "",
            "footer_center": "Page {page} / {total}",
            "footer_right": "",
        }

    def _header_footer_editor_labels(self) -> dict:
        return {
            "title": self._t("header_footer_editor_title"),
            "description": self._t("header_footer_editor_description"),
            "back": self._t("back_settings"),
            "header": self._t("header_label"),
            "footer": self._t("footer_label"),
            "left": self._t("position_left"),
            "center": self._t("position_center"),
            "right": self._t("position_right"),
            "tokens": self._t("header_footer_tokens_label"),
            "token_help": self._t("header_footer_token_help"),
            "restore": self._t("reset_header_footer"),
            "cancel": self._t("cancel_settings"),
            "save": self._t("save_settings"),
        }

    def _refresh_header_footer_editors(self) -> None:
        if not hasattr(self, "header_footer_dialog_editor"):
            return
        labels = self._header_footer_editor_labels()
        for editor in (
            self.header_footer_dialog_editor,
            self.compact_header_footer_editor,
        ):
            editor.retranslate(labels)

    def _draft_header_footer_config(self) -> core.HeaderFooterConfig:
        return core.HeaderFooterConfig(
            top_left=self._settings_draft_hf_vars["header_left"].get(),
            top_center=self._settings_draft_hf_vars["header_center"].get(),
            top_right=self._settings_draft_hf_vars["header_right"].get(),
            bottom_left=self._settings_draft_hf_vars["footer_left"].get(),
            bottom_center=self._settings_draft_hf_vars["footer_center"].get(),
            bottom_right=self._settings_draft_hf_vars["footer_right"].get(),
        )

    def _draft_header_footer_render_options(self) -> dict:
        options = self._render_options()
        options["header_footer"] = self._draft_header_footer_config()
        return options

    def _validate_header_footer_draft(self) -> bool:
        try:
            core.render_profile_for_options(
                **self._draft_header_footer_render_options()
            )
        except Exception:
            return False
        return True

    def _on_header_footer_draft_changed(self, *unused) -> None:
        if not getattr(self, "_header_footer_editor_open", False):
            return
        if not self._validate_header_footer_draft():
            self._invalidate_preview()
            return
        self._schedule_preview()

    def _restore_header_footer_defaults(self) -> None:
        defaults = self._header_footer_defaults()
        customized = any(
            self._settings_draft_hf_vars[key].get() != value
            for key, value in defaults.items()
        )
        if customized and not self.dialogs.ask_restore_header_footer(
            self._t("restore_header_footer_title"),
            self._t("restore_header_footer_question"),
        ):
            return
        for key, value in defaults.items():
            self._settings_draft_hf_vars[key].set(value)

    def _open_header_footer_editor(self) -> str:
        if self.operation != "idle":
            return "break"
        if (
            getattr(self, "_style_editor_open", False)
            or getattr(self, "_destination_editor_open", False)
            or getattr(self, "_advanced_editor_open", False)
        ):
            return "break"
        if self._header_footer_editor_open:
            self._show_header_footer_editor_host()
            return "break"
        self._settings_dialog["snapshot"] = self._settings_snapshot()
        self._load_settings_draft(self._settings_dialog["snapshot"])
        self._header_footer_editor_preview_snapshot = (
            self._capture_preview_snapshot()
        )
        self._settings_dialog["return_focus"] = self.root.focus_get()
        self._header_footer_editor_open = True
        self._refresh_header_footer_editors()
        self._show_header_footer_editor_host()
        return "break"

    def _position_header_footer_dialog(self) -> None:
        dialog = self._header_footer_dialog
        width = max(560, min(720, self.root.winfo_width() - 48))
        height = max(520, min(680, self.root.winfo_height() - 48))
        x = self.root.winfo_rootx() + max(
            0, (self.root.winfo_width() - width) // 2
        )
        y = self.root.winfo_rooty() + max(
            0, (self.root.winfo_height() - height) // 2
        )
        dialog.geometry("{0}x{1}+{2}+{3}".format(width, height, x, y))

    def _show_header_footer_editor_host(self) -> None:
        if not self._header_footer_editor_open:
            return
        dialog = self._header_footer_dialog
        if self._layout_mode == "compact":
            if dialog.grab_current() is dialog:
                dialog.grab_release()
            dialog.withdraw()
            self._active_compact_tab = "settings"
            self._show_active_compact_section()
            self.compact_header_footer_editor.focus_initial()
            return
        self.compact_header_footer_editor.grid_forget()
        self._position_header_footer_dialog()
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        self.header_footer_dialog_editor.focus_initial()

    def _close_header_footer_editor(self) -> str:
        dialog = self._header_footer_dialog
        if dialog.grab_current() is dialog:
            dialog.grab_release()
        dialog.withdraw()
        self.compact_header_footer_editor.grid_forget()
        self._header_footer_editor_open = False
        if self._layout_mode == "compact":
            self._show_active_compact_section()
        focus = self._settings_dialog.get("return_focus")
        try:
            (focus or self.settings_panel.rows["header_footer"]).focus_set()
        except tk.TclError:
            self.root.focus_set()
        return "break"

    def _save_header_footer_editor(self) -> str:
        if not self._validate_header_footer_draft():
            return "break"
        for key, variable in self.hf_vars.items():
            draft_value = self._settings_draft_hf_vars[key].get()
            if variable.get() != draft_value:
                variable.set(draft_value)
        self._refresh_accordion_headers()
        return self._close_header_footer_editor()

    def _cancel_header_footer_editor(self, _event=None) -> str:
        if not getattr(self, "_header_footer_editor_open", False):
            return "break"
        self._header_footer_editor_open = False
        snapshot = self._settings_dialog.get("snapshot")
        if snapshot is not None:
            self._load_settings_draft(snapshot)
        preview = self._header_footer_editor_preview_snapshot
        if preview is not None:
            self._restore_preview_snapshot(preview)
        return self._close_header_footer_editor()

    def _advanced_editor_labels(self) -> dict:
        return {
            "title": self._t("advanced_editor_title"),
            "description": self._t("advanced_editor_description"),
            "back": self._t("back_settings"),
            "date": self._t("render_date"),
            "date_help": self._t("render_date_automatic_help"),
            "trusted_html": self._t("trusted_html"),
            "security": self._t("trusted_html_help"),
            "cancel": self._t("cancel_settings"),
            "save": self._t("save_settings"),
        }

    def _refresh_advanced_editors(self) -> None:
        if not hasattr(self, "advanced_dialog_editor"):
            return
        labels = self._advanced_editor_labels()
        for editor in (
            self.advanced_dialog_editor,
            self.compact_advanced_editor,
        ):
            editor.retranslate(labels)

    def _draft_advanced_render_options(self) -> dict:
        options = dict(self._render_options())
        options["render_date"] = (
            self._settings_draft_render_date_var.get().strip() or None
        )
        options["trusted_html"] = (
            self._settings_draft_trusted_html_var.get()
        )
        return options

    def _validate_advanced_draft(self) -> bool:
        try:
            core.render_profile_for_options(
                **self._draft_advanced_render_options()
            )
        except Exception:
            self._advanced_error_var.set(
                self._t("render_date_validation_invalid")
            )
            return False
        self._advanced_error_var.set("")
        return True

    def _on_advanced_date_changed(self, *unused) -> None:
        if not getattr(self, "_advanced_editor_open", False):
            return
        if not self._validate_advanced_draft():
            self._invalidate_preview()
            return
        self._schedule_preview()

    def _on_advanced_trusted_html_changed(self) -> None:
        enabled = self._settings_draft_trusted_html_var.get()
        if enabled and not self._trusted_html_confirmed:
            confirmed = self.dialogs.ask_trusted_html(
                (
                    self.compact_advanced_editor
                    if self._layout_mode == "compact"
                    else self._advanced_dialog
                ),
                self._t("trusted_html_confirm_title"),
                self._t("trusted_html_confirm"),
                self._t("trusted_html_allow"),
                self._t("cancel_settings"),
            )
            if not confirmed:
                self._settings_draft_trusted_html_var.set(False)
                editor = (
                    self.compact_advanced_editor
                    if self._layout_mode == "compact"
                    else self.advanced_dialog_editor
                )
                editor.trusted_html_switch.focus_set()
                return
            self._trusted_html_confirmed = True
        if self._validate_advanced_draft():
            self._schedule_preview()

    def _open_advanced_editor(self) -> str:
        if self.operation != "idle":
            return "break"
        if (
            getattr(self, "_style_editor_open", False)
            or getattr(self, "_destination_editor_open", False)
            or getattr(self, "_header_footer_editor_open", False)
        ):
            return "break"
        if self._advanced_editor_open:
            self._show_advanced_editor_host()
            return "break"
        self._settings_dialog["snapshot"] = self._settings_snapshot()
        self._load_settings_draft(self._settings_dialog["snapshot"])
        self._advanced_editor_preview_snapshot = self._capture_preview_snapshot()
        self._settings_dialog["return_focus"] = self.root.focus_get()
        self._advanced_error_var.set("")
        self._advanced_editor_open = True
        self._refresh_advanced_editors()
        self._show_advanced_editor_host()
        return "break"

    def _position_advanced_dialog(self) -> None:
        dialog = self._advanced_dialog
        width = max(560, min(680, self.root.winfo_width() - 48))
        height = max(520, min(600, self.root.winfo_height() - 48))
        x = self.root.winfo_rootx() + max(
            0, (self.root.winfo_width() - width) // 2
        )
        y = self.root.winfo_rooty() + max(
            0, (self.root.winfo_height() - height) // 2
        )
        dialog.geometry("{0}x{1}+{2}+{3}".format(width, height, x, y))

    def _show_advanced_editor_host(self) -> None:
        if not self._advanced_editor_open:
            return
        dialog = self._advanced_dialog
        if self._layout_mode == "compact":
            if dialog.grab_current() is dialog:
                dialog.grab_release()
            dialog.withdraw()
            self._active_compact_tab = "settings"
            self._show_active_compact_section()
            self.compact_advanced_editor.focus_initial()
            return
        self.compact_advanced_editor.grid_forget()
        self._position_advanced_dialog()
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        self.advanced_dialog_editor.focus_initial()

    def _close_advanced_editor(self) -> str:
        dialog = self._advanced_dialog
        if dialog.grab_current() is dialog:
            dialog.grab_release()
        dialog.withdraw()
        self.compact_advanced_editor.grid_forget()
        self._advanced_editor_open = False
        if self._layout_mode == "compact":
            self._show_active_compact_section()
        focus = self._settings_dialog.get("return_focus")
        try:
            (focus or self.settings_panel.rows["other"]).focus_set()
        except tk.TclError:
            self.root.focus_set()
        return "break"

    def _save_advanced_editor(self) -> str:
        if not self._validate_advanced_draft():
            return "break"
        draft_date = self._settings_draft_render_date_var.get().strip()
        draft_trusted = self._settings_draft_trusted_html_var.get()
        if self.render_date_var.get() != draft_date:
            self.render_date_var.set(draft_date)
        if self.trusted_html_var.get() != draft_trusted:
            self.trusted_html_var.set(draft_trusted)
        self._refresh_accordion_headers()
        return self._close_advanced_editor()

    def _cancel_advanced_editor(self, _event=None) -> str:
        if not getattr(self, "_advanced_editor_open", False):
            return "break"
        self._advanced_editor_open = False
        snapshot = self._settings_dialog.get("snapshot")
        if snapshot is not None:
            self._load_settings_draft(snapshot)
        preview = self._advanced_editor_preview_snapshot
        if preview is not None:
            self._restore_preview_snapshot(preview)
        return self._close_advanced_editor()

    def _on_render_setting_changed(self, *unused) -> None:
        self._refresh_accordion_headers()
        self._on_preview_input_changed()

    def _style_summary(self) -> str:
        if self.css_path:
            return self._t("settings_css_summary", path=self.css_path)
        reference = self.theme_var.get()
        if reference == core.DEFAULT_THEME_ID:
            return self._t("settings_default_theme")
        return getattr(self, "_theme_summaries", {}).get(reference, reference)

    def _header_footer_summary(self) -> str:
        values = {
            key: variable.get()
            for key, variable in self.hf_vars.items()
        }
        items = [
            self._t("{0}_summary".format(key), value=value)
            for key, value in values.items()
            if value
        ]
        if not items:
            return self._t("settings_none")
        return " · ".join(items)

    def _destination_summary(self) -> str:
        if self.output_dir:
            return self.output_dir
        return self._t(
            (
                "source_destination_one"
                if len(self.files) == 1
                else "source_destination_many"
            )
        )

    def _other_options_summary(self) -> str:
        render_date = self.render_date_var.get().strip()
        trusted = self.trusted_html_var.get()
        if render_date and trusted:
            return self._t("other_date_trusted_summary", date=render_date)
        if trusted:
            return self._t("other_trusted_summary")
        if render_date:
            return self._t("other_date_summary", date=render_date)
        return self._t("other_automatic_summary")

    def _settings_summaries(self) -> dict:
        return {
            "style": self._style_summary(),
            "destination": self._destination_summary(),
            "header_footer": self._header_footer_summary(),
            "other": self._other_options_summary(),
        }

    def _settings_summary_labels(self) -> dict:
        return {
            "settings_heading": self._t("settings_heading"),
            "style": self._t("style_heading"),
            "destination": self._t("destination_heading"),
            "header_footer": self._t("header_footer_heading"),
            "other": self._t("advanced_options_heading"),
            "edit": self._t("edit_settings"),
        }

    def _refresh_accordion_headers(self) -> None:
        panel = getattr(self, "settings_panel", None)
        if panel is not None:
            panel.retranslate(
                self._settings_summary_labels(),
                self._settings_summaries(),
            )

    def _settings_snapshot(self) -> dict:
        return {
            "css_path": self.css_path,
            "style_mode": self.style_mode_var.get(),
            "theme": self.theme_var.get(),
            "output_dir": self.output_dir,
            "header_footer": {
                key: variable.get() for key, variable in self.hf_vars.items()
            },
            "render_date": self.render_date_var.get(),
            "trusted_html": self.trusted_html_var.get(),
        }

    def _load_settings_draft(self, settings: dict) -> None:
        """Populate the temporary dialog draft from authoritative settings."""
        self._settings_draft_css_path = settings["css_path"]
        self._settings_draft_output_dir = settings["output_dir"]
        self._settings_draft_style_mode_var.set(settings["style_mode"])
        self._settings_draft_theme_var.set(settings["theme"])
        for key, value in settings["header_footer"].items():
            self._settings_draft_hf_vars[key].set(value)
        self._settings_draft_render_date_var.set(settings["render_date"])
        self._settings_draft_trusted_html_var.set(settings["trusted_html"])
        self._refresh_css_entry()
        self._refresh_output_entry()
        self._render_theme_cards()

    def _open_settings_editor(self) -> str:
        if self.operation != "idle":
            return "break"
        details = self._settings_dialog
        dialog = details["window"]
        if dialog.state() != "withdrawn":
            dialog.lift()
            self._activate_settings_editor()
            return "break"
        details["snapshot"] = self._settings_snapshot()
        self._load_settings_draft(details["snapshot"])
        details["return_focus"] = self.root.focus_get()
        width = max(
            560,
            min(680, self.root.winfo_screenwidth() - 80),
        )
        height = min(
            700,
            max(520, self.root.winfo_screenheight() - 80),
        )
        x = self.root.winfo_rootx() + max(
            0, (self.root.winfo_width() - width) // 2
        )
        y = self.root.winfo_rooty() + max(
            0, (self.root.winfo_height() - height) // 2
        )
        dialog.geometry("{0}x{1}+{2}+{3}".format(width, height, x, y))
        self._layout_settings_dialog(width)
        details["activation_attempts"] = 0
        details["opening"] = True
        dialog.deiconify()
        dialog.lift()
        dialog.update_idletasks()
        self._activate_settings_editor()
        return "break"

    def _activate_settings_editor(self) -> None:
        """Make the dialog visible before it can own keyboard and pointer input."""
        details = self._settings_dialog
        dialog = details["window"]
        if not details.get("opening", False):
            return
        if dialog.state() == "withdrawn":
            dialog.deiconify()
        dialog.lift()
        if not dialog.winfo_viewable():
            attempts = details.get("activation_attempts", 0) + 1
            details["activation_attempts"] = attempts
            if attempts <= 5:
                dialog.after_idle(self._activate_settings_editor)
            return
        dialog.focus_force()
        dialog.grab_set()
        self.theme_mode_radio.focus_set()

    def _close_settings_editor(self) -> str:
        details = self._settings_dialog
        dialog = details["window"]
        details["opening"] = False
        if dialog.grab_current() is dialog:
            dialog.grab_release()
        dialog.withdraw()
        focus = details.get("return_focus")
        if focus is not None:
            try:
                focus.focus_set()
            except tk.TclError:
                self.root.focus_set()
        else:
            self.root.focus_set()
        return "break"

    def _apply_settings_editor(self) -> str:
        details = self._settings_dialog
        draft_trusted = self._settings_draft_trusted_html_var.get()
        if draft_trusted and not self._trusted_html_confirmed:
            confirmed = self.dialogs.ask_trusted_html(
                self._settings_dialog["window"],
                self._t("trusted_html_confirm_title"),
                self._t("trusted_html_confirm"),
                self._t("trusted_html_allow"),
                self._t("cancel_settings"),
            )
            if not confirmed:
                self._settings_draft_trusted_html_var.set(False)
                self.trusted_html_check.focus_set()
                return "break"
            self._trusted_html_confirmed = True

        before = self._settings_snapshot()
        self.css_path = self._settings_draft_css_path
        self.output_dir = self._settings_draft_output_dir
        draft_style_mode = self._settings_draft_style_mode_var.get()
        draft_theme = self._settings_draft_theme_var.get()
        if self.style_mode_var.get() != draft_style_mode:
            self.style_mode_var.set(draft_style_mode)
        if self.theme_var.get() != draft_theme:
            self.theme_var.set(draft_theme)
        for key, variable in self.hf_vars.items():
            draft_value = self._settings_draft_hf_vars[key].get()
            if variable.get() != draft_value:
                variable.set(draft_value)
        draft_date = self._settings_draft_render_date_var.get()
        if self.render_date_var.get() != draft_date:
            self.render_date_var.set(draft_date)
        if self.trusted_html_var.get() != draft_trusted:
            self.trusted_html_var.set(draft_trusted)
        self._refresh_css_entry()
        self._refresh_output_entry()
        self._render_theme_cards()
        self._refresh_accordion_headers()
        after = self._settings_snapshot()
        if any(
            before[key] != after[key]
            for key in (
                "css_path",
                "style_mode",
                "theme",
                "header_footer",
                "render_date",
                "trusted_html",
            )
        ):
            self._schedule_preview()
        return self._close_settings_editor()

    def _cancel_settings_editor(self, _event=None) -> str:
        return self._close_settings_editor()

    def _reset_header_footer(self) -> None:
        for key, value in self._header_footer_defaults().items():
            self._settings_draft_hf_vars[key].set(value)

    def _on_trusted_html_changed(self) -> None:
        if not self.trusted_html_var.get():
            self._refresh_accordion_headers()
            return
        if not self._trusted_html_confirmed:
            confirmed = self.dialogs.ask_trusted_html(
                self._settings_dialog["window"],
                self._t("trusted_html_confirm_title"),
                self._t("trusted_html_confirm"),
                self._t("trusted_html_allow"),
                self._t("cancel_settings"),
            )
            if not confirmed:
                self.trusted_html_var.set(False)
                self.trusted_html_check.focus_set()
                self._refresh_accordion_headers()
                return
            self._trusted_html_confirmed = True
        self._refresh_accordion_headers()

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
