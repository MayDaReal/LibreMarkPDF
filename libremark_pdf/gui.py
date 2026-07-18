"""Responsive Tk desktop adapter for the shared conversion engine."""

from __future__ import annotations

import io
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageTk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _HAS_DND = True
except ImportError:  # Browsing and launch remain available without optional DnD.
    DND_FILES = None
    TkinterDnD = None
    _HAS_DND = False

from . import core, i18n


LOGO_ICON_CACHE: dict[int, tk.PhotoImage] = {}
PREVIEW_DPI = 90
PREVIEW_DEBOUNCE_MS = 450
ZOOM_LEVELS = (50, 75, 100, 125, 150, 200)

SAMPLE_MARKDOWN = """# {title}

{body}

| Status | Description |
|---|---|
| Done | Everything works |
| Pending | Waiting on review |
"""


def _load_logo(size: int) -> tk.PhotoImage:
    if size not in LOGO_ICON_CACHE:
        path = core.resource_path("assets/libremark-pdf-logo-{0}.png".format(size))
        LOGO_ICON_CACHE[size] = tk.PhotoImage(file=str(path))
    return LOGO_ICON_CACHE[size]


def _open_path(path: Path) -> None:
    """Open a successful output or directory through the native shell."""
    resolved = str(path)
    if os.name == "nt":
        os.startfile(resolved)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", resolved])
    else:
        subprocess.Popen(["xdg-open", resolved])


def _run_preview_job(
    result_queue: "queue.Queue",
    generation: int,
    source_path: Optional[Path],
    markdown_text: Optional[str],
    options: dict,
) -> None:
    """Worker boundary: perform file I/O/rendering and communicate only by queue."""
    try:
        if source_path is not None:
            markdown_text = source_path.read_text(encoding="utf-8")
        png = core.render_preview_png(markdown_text or "", **options)
        result_queue.put(("preview_ok", generation, png))
    except Exception as exc:
        result_queue.put(("preview_error", generation, str(exc)))


def _run_conversion_job(
    result_queue: "queue.Queue",
    files: list,
    options: dict,
    cancel_event: threading.Event,
) -> None:
    """Worker boundary for batch conversion and progress messages."""
    def progress(index: int, total: int, result: dict) -> None:
        result_queue.put(("progress", index, total, result))

    try:
        results = core.convert_batch(
            files,
            cancel_event=cancel_event,
            progress_callback=progress,
            **options
        )
        result_queue.put(("generate_done", results))
    except Exception as exc:
        result_queue.put(("generate_failed", str(exc)))


class LibreMarkPdfApp:
    """Coordinate Tk widgets while workers use only immutable values and queues."""

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.lang = i18n.load_language()
        self.files = []  # type: list[Path]
        self.css_path = None  # type: Optional[str]
        self.output_dir = None  # type: Optional[str]
        self.operation = "idle"
        self._status_key = "status_ready"
        self._status_kwargs = {}  # type: dict
        self._close_requested = False
        self._preview_generation = 0
        self._preview_after = None
        self._preview_running = False
        self._preview_pending_generation = None
        self._poll_after = None
        self._cancel_event = threading.Event()
        self._result_queue = queue.Queue()  # type: queue.Queue
        self._preview_png = None  # type: Optional[bytes]
        self.preview_photo = None
        self.zoom_percent = tk.IntVar(value=100)
        self.advanced_open = tk.BooleanVar(value=False)
        self.trusted_html_var = tk.BooleanVar(value=False)
        self.render_date_var = tk.StringVar()
        self.theme_var = tk.StringVar(value=core.DEFAULT_THEME_ID)
        self.progress_var = tk.IntVar(value=0)
        self.hf_vars = {
            "header_left": tk.StringVar(),
            "header_center": tk.StringVar(),
            "header_right": tk.StringVar(),
            "footer_left": tk.StringVar(),
            "footer_center": tk.StringVar(value="Page {page} / {total}"),
            "footer_right": tk.StringVar(),
        }
        self._operation_controls = []  # type: list
        self._theme_buttons = []  # type: list

        self._build_ui()
        self._bind_accessibility()
        self._retranslate()
        for variable in list(self.hf_vars.values()) + [
            self.render_date_var, self.trusted_html_var
        ]:
            variable.trace_add("write", self._on_preview_input_changed)
        self.root.protocol("WM_DELETE_WINDOW", self._request_close)
        self.browse_button.focus_set()

    def _build_ui(self) -> None:
        self.root.geometry("820x780")
        self.root.minsize(560, 520)

        top = ttk.Frame(self.root, padding=(14, 10))
        top.pack(fill="x")
        logo = _load_logo(32)
        self.logo_label = ttk.Label(top, image=logo)
        self.logo_label.image = logo
        self.logo_label.pack(side="left")
        try:
            self.root.iconphoto(True, _load_logo(64))
        except Exception:
            pass
        self.title_label = ttk.Label(top, font=("TkDefaultFont", 12, "bold"))
        self.title_label.pack(side="left", padx=10)
        language = ttk.Frame(top)
        language.pack(side="right")
        self.btn_en = ttk.Button(
            language, text="EN", width=4, command=lambda: self._set_lang("en")
        )
        self.btn_fr = ttk.Button(
            language, text="FR", width=4, command=lambda: self._set_lang("fr")
        )
        self.btn_en.pack(side="left")
        self.btn_fr.pack(side="left")

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        self.body_canvas = tk.Canvas(container, highlightthickness=0, takefocus=True)
        body_scroll = ttk.Scrollbar(
            container, orient="vertical", command=self.body_canvas.yview
        )
        self.body_canvas.configure(yscrollcommand=body_scroll.set)
        body_scroll.pack(side="right", fill="y")
        self.body_canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(self.body_canvas, padding=(14, 6, 14, 14))
        self._body_window = self.body_canvas.create_window(
            (0, 0), window=self.body, anchor="nw"
        )
        self.body.bind(
            "<Configure>",
            lambda event: self.body_canvas.configure(
                scrollregion=self.body_canvas.bbox("all")
            ),
        )
        self.body_canvas.bind(
            "<Configure>",
            lambda event: self.body_canvas.itemconfigure(
                self._body_window, width=event.width
            ),
        )

        source_group = ttk.LabelFrame(self.body, padding=8)
        source_group.pack(fill="x", pady=(0, 10))
        self.source_group = source_group
        self.drop_canvas = tk.Canvas(
            source_group,
            height=76,
            bg="#f6f8fa",
            highlightbackground="#8c959f",
            highlightthickness=1,
            takefocus=True,
        )
        self.drop_canvas.pack(fill="x")
        self.drop_canvas.bind("<Configure>", self._redraw_drop_zone)
        self.drop_canvas.bind("<Button-1>", lambda event: self._browse_files())
        self.drop_canvas.bind("<Return>", lambda event: self._browse_files())
        self.drop_canvas.bind("<space>", lambda event: self._browse_files())
        if _HAS_DND:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self._on_drop)
        source_actions = ttk.Frame(source_group)
        source_actions.pack(fill="x", pady=(6, 4))
        self.browse_button = ttk.Button(source_actions, command=self._browse_files)
        self.browse_button.pack(side="left")
        self.clear_files_button = ttk.Button(
            source_actions, command=self._clear_files
        )
        self.clear_files_button.pack(side="left", padx=6)

        file_box = ttk.Frame(source_group)
        file_box.pack(fill="x")
        self.file_canvas = tk.Canvas(
            file_box, height=96, highlightthickness=0, takefocus=True
        )
        file_scroll = ttk.Scrollbar(
            file_box, orient="vertical", command=self.file_canvas.yview
        )
        self.file_canvas.configure(yscrollcommand=file_scroll.set)
        file_scroll.pack(side="right", fill="y")
        self.file_canvas.pack(side="left", fill="x", expand=True)
        self.file_list_frame = ttk.Frame(self.file_canvas)
        self._file_window = self.file_canvas.create_window(
            (0, 0), window=self.file_list_frame, anchor="nw"
        )
        self.file_list_frame.bind(
            "<Configure>",
            lambda event: self.file_canvas.configure(
                scrollregion=self.file_canvas.bbox("all")
            ),
        )
        self.file_canvas.bind(
            "<Configure>",
            lambda event: self.file_canvas.itemconfigure(
                self._file_window, width=event.width
            ),
        )

        self.theme_group = ttk.LabelFrame(self.body, padding=8)
        self.theme_group.pack(fill="x", pady=(0, 10))
        self.theme_cards = ttk.Frame(self.theme_group)
        self.theme_cards.pack(fill="x")
        css_row = ttk.Frame(self.theme_group)
        css_row.pack(fill="x", pady=(8, 0))
        self.css_label = ttk.Label(css_row)
        self.css_label.pack(side="left")
        self.css_entry = ttk.Entry(css_row, state="readonly")
        self.css_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.css_button = ttk.Button(css_row, command=self._choose_css)
        self.css_button.pack(side="left")
        self.css_reset_button = ttk.Button(css_row, command=self._reset_css)
        self.css_reset_button.pack(side="left", padx=(6, 0))

        self.advanced_group = ttk.LabelFrame(self.body, padding=8)
        self.advanced_group.pack(fill="x", pady=(0, 10))
        self.advanced_toggle = ttk.Button(
            self.advanced_group, command=self._toggle_advanced
        )
        self.advanced_toggle.pack(fill="x")
        self.advanced_content = ttk.Frame(self.advanced_group)
        self.tokens_hint_label = ttk.Label(self.advanced_content)
        self.tokens_hint_label.pack(anchor="w", pady=(6, 4))
        for group_name, keys in (
            ("header_group_label", ("header_left", "header_center", "header_right")),
            ("footer_group_label", ("footer_left", "footer_center", "footer_right")),
        ):
            label = ttk.Label(self.advanced_content)
            setattr(self, group_name, label)
            label.pack(anchor="w", pady=(4, 0))
            row = ttk.Frame(self.advanced_content)
            row.pack(fill="x")
            for key in keys:
                entry = ttk.Entry(row, textvariable=self.hf_vars[key])
                entry.pack(side="left", fill="x", expand=True, padx=2)
                self._operation_controls.append(entry)
        options = ttk.Frame(self.advanced_content)
        options.pack(fill="x", pady=(8, 0))
        self.render_date_label = ttk.Label(options)
        self.render_date_label.pack(side="left")
        self.render_date_entry = ttk.Entry(
            options, textvariable=self.render_date_var, width=12
        )
        self.render_date_entry.pack(side="left", padx=(6, 14))
        self.trusted_html_check = ttk.Checkbutton(
            options, variable=self.trusted_html_var
        )
        self.trusted_html_check.pack(side="left")

        preview_group = ttk.LabelFrame(self.body, padding=8)
        preview_group.pack(fill="both", expand=True, pady=(0, 10))
        self.preview_group = preview_group
        preview_header = ttk.Frame(preview_group)
        preview_header.pack(fill="x")
        self.refresh_preview_button = ttk.Button(
            preview_header, command=self._refresh_preview
        )
        self.refresh_preview_button.pack(side="left")
        self.zoom_out_button = ttk.Button(
            preview_header, width=3, text="−", command=lambda: self._change_zoom(-1)
        )
        self.zoom_out_button.pack(side="right")
        self.zoom_in_button = ttk.Button(
            preview_header, width=3, text="+", command=lambda: self._change_zoom(1)
        )
        self.zoom_in_button.pack(side="right", padx=4)
        self.zoom_label = ttk.Label(preview_header)
        self.zoom_label.pack(side="right")
        preview_box = ttk.Frame(preview_group)
        preview_box.pack(fill="both", expand=True, pady=(8, 0))
        self.preview_canvas = tk.Canvas(
            preview_box,
            height=330,
            bg="#78828c",
            highlightthickness=0,
            takefocus=True,
        )
        preview_vertical = ttk.Scrollbar(
            preview_box, orient="vertical", command=self.preview_canvas.yview
        )
        preview_horizontal = ttk.Scrollbar(
            preview_box, orient="horizontal", command=self.preview_canvas.xview
        )
        self.preview_canvas.configure(
            yscrollcommand=preview_vertical.set,
            xscrollcommand=preview_horizontal.set,
        )
        preview_vertical.pack(side="right", fill="y")
        preview_horizontal.pack(side="bottom", fill="x")
        self.preview_canvas.pack(side="left", fill="both", expand=True)

        output_group = ttk.LabelFrame(self.body, padding=8)
        output_group.pack(fill="x", pady=(0, 10))
        self.output_group = output_group
        output_row = ttk.Frame(output_group)
        output_row.pack(fill="x")
        self.output_entry = ttk.Entry(output_row, state="readonly")
        self.output_entry.pack(side="left", fill="x", expand=True)
        self.output_button = ttk.Button(
            output_row, command=self._choose_output_dir
        )
        self.output_button.pack(side="left", padx=(6, 0))
        self.output_reset_button = ttk.Button(
            output_row, command=self._reset_output_dir
        )
        self.output_reset_button.pack(side="left", padx=(6, 0))

        action_row = ttk.Frame(self.body)
        action_row.pack(fill="x")
        self.generate_button = ttk.Button(
            action_row, command=self._on_generate_clicked
        )
        self.generate_button.pack(side="left", fill="x", expand=True)
        self.cancel_button = ttk.Button(
            action_row, command=self._cancel_conversion, state="disabled"
        )
        self.cancel_button.pack(side="left", padx=(6, 0))
        self.progress = ttk.Progressbar(
            self.body, variable=self.progress_var, maximum=1
        )
        self.progress.pack(fill="x", pady=(8, 2))
        self.status_label = ttk.Label(self.body, wraplength=720)
        self.status_label.pack(anchor="w")
        self.results_frame = ttk.Frame(self.body)
        self.results_frame.pack(fill="x", pady=(8, 0))

        self._operation_controls.extend([
            self.browse_button, self.clear_files_button, self.css_button,
            self.css_reset_button, self.advanced_toggle, self.render_date_entry,
            self.trusted_html_check, self.refresh_preview_button,
            self.output_button, self.output_reset_button,
        ])

    def _bind_accessibility(self) -> None:
        self.root.bind_all("<Control-o>", lambda event: self._browse_files())
        self.root.bind_all("<Control-r>", lambda event: self._refresh_preview())
        self.root.bind_all("<Control-g>", lambda event: self._on_generate_clicked())
        self.root.bind_all("<Escape>", lambda event: self._cancel_conversion())
        self.root.bind_all("<Control-plus>", lambda event: self._change_zoom(1))
        self.root.bind_all("<Control-minus>", lambda event: self._change_zoom(-1))
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event) -> None:
        target = self.preview_canvas if self.preview_canvas.focus_get() else self.body_canvas
        target.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _set_lang(self, lang: str) -> None:
        self.lang = lang
        i18n.save_language(lang)
        self._retranslate()

    def _t(self, key: str, **kwargs) -> str:
        return i18n.t(key, self.lang, **kwargs)

    def _set_status(self, key: str, **kwargs) -> None:
        self._status_key = key
        self._status_kwargs = kwargs
        self.status_label.config(text=self._t(key, **kwargs))

    def _retranslate(self) -> None:
        self.root.title(self._t("app_title"))
        self.title_label.config(text=self._t("app_title"))
        self.source_group.config(text=self._t("source_files_label"))
        self._drop_zone_text = self._t("drop_hint")
        self._redraw_drop_zone()
        self.browse_button.config(text=self._t("browse_files"))
        self.clear_files_button.config(text=self._t("clear_files"))
        self.theme_group.config(text=self._t("themes_label"))
        self.css_label.config(text=self._t("custom_css_label"))
        self.css_button.config(text=self._t("change"))
        self.css_reset_button.config(text=self._t("use_theme"))
        self.advanced_group.config(text=self._t("advanced_header_footer"))
        self.advanced_toggle.config(
            text=("\u25be " if self.advanced_open.get() else "\u25b8 ")
            + self._t("advanced_toggle")
        )
        self.tokens_hint_label.config(text=self._t("tokens_hint"))
        self.header_group_label.config(text=self._t("header_label"))
        self.footer_group_label.config(text=self._t("footer_label"))
        self.render_date_label.config(text=self._t("render_date_label"))
        self.trusted_html_check.config(text=self._t("trusted_html_label"))
        self.preview_group.config(text=self._t("preview_label"))
        self.refresh_preview_button.config(text=self._t("refresh_preview"))
        self.output_group.config(text=self._t("output_label"))
        self.output_button.config(text=self._t("choose_folder"))
        self.output_reset_button.config(text=self._t("use_source_folder"))
        self.cancel_button.config(text=self._t("cancel_button"))
        self._refresh_generate_button()
        self._refresh_css_entry()
        self._refresh_output_entry()
        self._render_theme_cards()
        self._render_file_list()
        self.zoom_label.config(text="{0}%".format(self.zoom_percent.get()))
        self.status_label.config(
            text=self._t(self._status_key, **self._status_kwargs)
        )

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

    def _on_preview_input_changed(self, *unused) -> None:
        self._schedule_preview()

    def _invalidate_preview(self, clear_image: bool = False) -> None:
        self._preview_generation += 1
        self._preview_pending_generation = None
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
            self._preview_after = None
        if clear_image:
            self._preview_png = None
            self.preview_photo = None
            self.preview_canvas.delete("all")
            self._set_status("status_ready")

    def _schedule_preview(self) -> None:
        if self.operation != "idle" or not hasattr(self, "refresh_preview_button"):
            return
        self._preview_generation += 1
        generation = self._preview_generation
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
        self._preview_after = self.root.after(
            PREVIEW_DEBOUNCE_MS, lambda: self._start_preview(generation)
        )

    def _refresh_preview(self) -> None:
        if self.operation != "idle":
            return
        if self._preview_after is not None:
            self.root.after_cancel(self._preview_after)
            self._preview_after = None
        self._preview_generation += 1
        self._start_preview(self._preview_generation)

    def _start_preview(self, generation: int) -> None:
        self._preview_after = None
        if generation != self._preview_generation or self.operation != "idle":
            return
        if self._preview_running:
            self._preview_pending_generation = generation
            return
        options = self._render_options()
        try:
            profile = core.render_profile_for_options(**options)
        except Exception as exc:
            self._set_status("status_preview_error", error=str(exc))
            return
        options["render_date"] = profile.render_date
        source_path = self.files[0] if self.files else None
        markdown_text = None
        if source_path is None:
            markdown_text = SAMPLE_MARKDOWN.format(
                title=self._t("sample_preview_title"),
                body=self._t("sample_preview_body"),
            )
            options["resource_root"] = Path.cwd()
        else:
            options["resource_root"] = source_path.resolve().parent
        options["dpi"] = PREVIEW_DPI
        self._preview_running = True
        self.refresh_preview_button.config(state="disabled")
        self._refresh_generate_button()
        self._set_status("status_rendering_preview")
        threading.Thread(
            target=_run_preview_job,
            args=(
                self._result_queue, generation, source_path, markdown_text, options
            ),
            daemon=True,
        ).start()
        self._schedule_queue_poll()

    def _apply_preview_image(self, png_bytes: bytes) -> None:
        self._preview_png = png_bytes
        self._redraw_preview()

    def _redraw_preview(self) -> None:
        if self._preview_png is None:
            return
        image = Image.open(io.BytesIO(self._preview_png)).convert("RGB")
        scale = self.zoom_percent.get() / 100.0
        size = (
            max(1, int(image.width * scale)),
            max(1, int(image.height * scale)),
        )
        image = image.resize(size, Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(12, 12, image=self.preview_photo, anchor="nw")
        self.preview_canvas.configure(
            scrollregion=(0, 0, image.width + 24, image.height + 24)
        )
        self.zoom_label.config(text="{0}%".format(self.zoom_percent.get()))

    def _change_zoom(self, direction: int) -> None:
        current = self.zoom_percent.get()
        index = min(range(len(ZOOM_LEVELS)), key=lambda item: abs(
            ZOOM_LEVELS[item] - current
        ))
        index = max(0, min(len(ZOOM_LEVELS) - 1, index + direction))
        self.zoom_percent.set(ZOOM_LEVELS[index])
        self._redraw_preview()

    def _refresh_generate_button(self) -> None:
        self.generate_button.config(
            text=self._t("generate_button", count=len(self.files)),
            state=(
                "normal"
                if self.files
                and self.operation == "idle"
                and not self._preview_running
                else "disabled"
            ),
        )

    def _overwrite_choice(self) -> Optional[bool]:
        plans = core.plan_batch_outputs(self.files, self.output_dir, overwrite=False)
        collisions = [
            plan for plan in plans
            if plan.error and not plan.error.startswith("OUTPUT_EXISTS:")
        ]
        if collisions:
            details = "\n".join(
                "{0}: {1}".format(plan.input_path.name, plan.error)
                for plan in collisions
            )
            if not messagebox.askokcancel(
                self._t("collision_title"),
                self._t("collision_continue", details=details),
            ):
                return None
        existing = [plan for plan in plans if plan.error_code == "OUTPUT_EXISTS"]
        if not existing:
            return False
        return messagebox.askyesnocancel(
            self._t("overwrite_title"),
            self._t("overwrite_question", count=len(existing)),
        )

    def _on_generate_clicked(self) -> None:
        if self.operation != "idle" or self._preview_running:
            return
        if not self.files:
            messagebox.showerror(self._t("error_title"), self._t("error_no_files"))
            return
        overwrite = self._overwrite_choice()
        if overwrite is None:
            self._set_status("status_cancelled")
            return
        self._invalidate_preview()
        options = self._render_options()
        try:
            profile = core.render_profile_for_options(**options)
        except Exception as exc:
            messagebox.showerror(self._t("error_title"), str(exc))
            self._set_status("status_generation_error", error=str(exc))
            return
        options["render_date"] = profile.render_date
        options["output_dir"] = self.output_dir
        options["overwrite"] = overwrite
        files = list(self.files)
        self._cancel_event = threading.Event()
        self.progress.configure(maximum=max(1, len(files)))
        self.progress_var.set(0)
        self._clear_results()
        self._begin_operation("generate")
        self._set_status("status_generating_progress", current=0, total=len(files))
        threading.Thread(
            target=_run_conversion_job,
            args=(self._result_queue, files, options, self._cancel_event),
            daemon=True,
        ).start()
        self._schedule_queue_poll()

    def _cancel_conversion(self) -> None:
        if self.operation == "generate" and not self._cancel_event.is_set():
            self._cancel_event.set()
            self.cancel_button.config(state="disabled")
            self._set_status("status_cancelling")

    def _begin_operation(self, operation: str) -> None:
        self.operation = operation
        for widget in self._operation_controls:
            try:
                widget.config(state="disabled")
            except tk.TclError:
                pass
        for card in self._theme_buttons:
            card.config(state="disabled")
        self.generate_button.config(state="disabled")
        self.cancel_button.config(
            state="normal" if operation == "generate" else "disabled"
        )

    def _finish_operation(self) -> None:
        self.operation = "idle"
        if self._close_requested:
            self.root.destroy()
            return
        for widget in self._operation_controls:
            try:
                widget.config(state="normal")
            except tk.TclError:
                pass
        self.css_entry.config(state="readonly")
        self.output_entry.config(state="readonly")
        self.cancel_button.config(state="disabled")
        self._render_theme_cards()
        self._refresh_generate_button()

    def _schedule_queue_poll(self) -> None:
        if self._poll_after is None:
            self._poll_after = self.root.after(75, self._poll_queue)

    def _poll_queue(self) -> None:
        self._poll_after = None
        while True:
            try:
                message = self._result_queue.get_nowait()
            except queue.Empty:
                break
            kind = message[0]
            if kind in ("preview_ok", "preview_error"):
                generation = message[1]
                self._preview_running = False
                self.refresh_preview_button.config(state="normal")
                if generation == self._preview_generation:
                    if kind == "preview_ok":
                        self._apply_preview_image(message[2])
                        self._set_status("status_ready")
                    else:
                        self._set_status("status_preview_error", error=message[2])
                pending = self._preview_pending_generation
                self._preview_pending_generation = None
                self._refresh_generate_button()
                if (
                    pending is not None
                    and pending == self._preview_generation
                    and self.operation == "idle"
                    and not self._close_requested
                ):
                    self.root.after(0, lambda: self._start_preview(pending))
            elif kind == "progress":
                _kind, index, total, _result = message
                self.progress_var.set(index)
                self._set_status(
                    "status_generating_progress", current=index, total=total
                )
            elif kind == "generate_done":
                if not self._close_requested:
                    self._handle_generate_done(message[1])
                self._finish_operation()
            elif kind == "generate_failed":
                if not self._close_requested:
                    self._set_status("status_generation_error", error=message[1])
                    messagebox.showerror(self._t("error_title"), message[1])
                self._finish_operation()
        if self.operation != "idle" or self._preview_running:
            self._schedule_queue_poll()

    def _handle_generate_done(self, results: list) -> None:
        ok = [item for item in results if item["status"] == "ok"]
        failed = [item for item in results if item["status"] == "error"]
        cancelled = [item for item in results if item["status"] == "cancelled"]
        self._render_results(ok)
        self._set_status(
            "status_done_summary",
            ok=len(ok),
            failed=len(failed),
            cancelled=len(cancelled),
        )
        if failed:
            details = "\n".join(
                "{0}: [{1}] {2}".format(
                    item["input"], item["error_code"], item["error"]
                )
                for item in failed
            )
            messagebox.showerror(self._t("error_title"), details)

    def _clear_results(self) -> None:
        for child in self.results_frame.winfo_children():
            child.destroy()

    def _render_results(self, successful: list) -> None:
        self._clear_results()
        for result in successful:
            output = Path(result["output"])
            row = ttk.Frame(self.results_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=str(output), anchor="w").pack(
                side="left", fill="x", expand=True
            )
            ttk.Button(
                row,
                text=self._t("open_pdf"),
                command=lambda path=output: self._open_result(path),
            ).pack(side="right")
            ttk.Button(
                row,
                text=self._t("open_folder"),
                command=lambda path=output.parent: self._open_result(path),
            ).pack(side="right", padx=4)

    def _open_result(self, path: Path) -> None:
        try:
            _open_path(path)
        except Exception as exc:
            messagebox.showerror(
                self._t("error_title"),
                self._t("open_error", error=str(exc)),
            )

    def _request_close(self) -> None:
        if self.operation == "idle":
            self._close_requested = True
            self._invalidate_preview()
            if self._poll_after is not None:
                self.root.after_cancel(self._poll_after)
                self._poll_after = None
            self.root.destroy()
            return
        self._close_requested = True
        self._preview_generation += 1
        if self.operation == "generate":
            self._cancel_event.set()
        self._set_status("status_closing")


def launch() -> None:
    """Create the best available root and run the desktop event loop."""
    root = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    LibreMarkPdfApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
