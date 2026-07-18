"""File, theme, output, and render-option controls for the Tk adapter."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, ttk

from . import core


class TkInputMixin:
    """Translate Tk input state into shared-core options."""

    def _redraw_drop_zone(self, event=None) -> None:
        self.drop_canvas.delete("all")
        width = self.drop_canvas.winfo_width() or 500
        self.drop_canvas.create_text(
            width // 2,
            38,
            text=self._drop_zone_text,
            fill="#24292f",
            font=("TkDefaultFont", 10),
        )

    def _on_drop(self, event) -> None:
        self._add_files(self.root.tk.splitlist(event.data))

    def _browse_files(self) -> None:
        if self.operation != "idle":
            return
        paths = filedialog.askopenfilenames(
            title=self._t("choose_markdown_title"),
            filetypes=[(self._t("markdown_filter_name"), "*.md *.markdown")],
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths) -> None:
        for raw_path in paths:
            path = Path(raw_path)
            if path.suffix.lower() in (".md", ".markdown") and path not in self.files:
                self.files.append(path)
        self._render_file_list()
        self._refresh_generate_button()
        self._schedule_preview()

    def _remove_file(self, path: Path) -> None:
        if self.operation != "idle":
            return
        self.files = [item for item in self.files if item != path]
        self._render_file_list()
        self._refresh_generate_button()
        if self.files:
            self._schedule_preview()
        else:
            self._invalidate_preview(clear_image=True)

    def _clear_files(self) -> None:
        if self.operation == "idle":
            self.files = []
            self._render_file_list()
            self._refresh_generate_button()
            self._invalidate_preview(clear_image=True)

    def _render_file_list(self) -> None:
        for child in self.file_list_frame.winfo_children():
            child.destroy()
        for path in self.files:
            row = ttk.Frame(self.file_list_frame, padding=(4, 2))
            row.pack(fill="x")
            ttk.Label(row, text=path.name, anchor="w").pack(
                side="left", fill="x", expand=True
            )
            button = ttk.Button(
                row,
                text=self._t("remove_file"),
                command=lambda selected=path: self._remove_file(selected),
            )
            button.pack(side="right")
            self._operation_controls.append(button)

    def _choose_css(self) -> None:
        path = filedialog.askopenfilename(
            title=self._t("choose_css_title"),
            filetypes=[(self._t("css_filter_name"), "*.css")],
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
        path = filedialog.askdirectory(title=self._t("choose_output_folder_title"))
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
