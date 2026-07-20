"""Tk widget construction for the LibreMark PDF desktop adapter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import core
from .styles import (
    DROP_ZONE_HEIGHT,
    FILE_LIST_HEIGHT,
    OUTER_PADDING,
    PREVIEW_HEIGHT,
    PRIMARY_BUTTON_STYLE,
    SECTION_GAP,
    SECTION_PADDING,
    SPACE_SM,
    SPACE_XS,
    STATUS_LABEL_STYLE,
    STATUS_WRAP_LENGTH,
    TITLE_LABEL_STYLE,
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:  # Browsing and launch remain available without optional DnD.
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False


LOGO_ICON_CACHE: dict[int, tk.PhotoImage] = {}

AUTOMATION_ACTIONS = frozenset((
    "files.add", "files.clear", "language.en", "language.fr",
    "advanced.toggle", "preview.refresh", "output.choose", "output.reset",
    "convert.start", "convert.cancel",
))


def load_logo(size: int) -> tk.PhotoImage:
    if size not in LOGO_ICON_CACHE:
        path = core.resource_path("assets/libremark-pdf-logo-{0}.png".format(size))
        LOGO_ICON_CACHE[size] = tk.PhotoImage(file=str(path))
    return LOGO_ICON_CACHE[size]


class TkLayoutMixin:
    """Build and bind widgets without owning application state transitions."""

    def _build_ui(self) -> None:
        self.root.geometry("820x780")
        self.root.minsize(560, 520)

        top = ttk.Frame(
            self.root,
            padding=(OUTER_PADDING, SECTION_GAP),
        )
        top.pack(fill="x")
        logo = load_logo(32)
        self.logo_label = ttk.Label(top, image=logo)
        self.logo_label.image = logo
        self.logo_label.pack(side="left")
        try:
            self.root.iconphoto(True, load_logo(64))
        except Exception:
            pass
        self.title_label = ttk.Label(top, style=TITLE_LABEL_STYLE)
        self.title_label.pack(side="left", padx=SECTION_GAP)
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
        self._register_automation_widget("language.en", self.btn_en)
        self._register_automation_widget("language.fr", self.btn_fr)

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        self.body_canvas = tk.Canvas(container, highlightthickness=0, takefocus=True)
        body_scroll = ttk.Scrollbar(
            container, orient="vertical", command=self.body_canvas.yview
        )
        self.body_canvas.configure(yscrollcommand=body_scroll.set)
        body_scroll.pack(side="right", fill="y")
        self.body_canvas.pack(side="left", fill="both", expand=True)
        self.body = ttk.Frame(
            self.body_canvas,
            padding=(OUTER_PADDING, SPACE_XS, OUTER_PADDING, OUTER_PADDING),
        )
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

        self.source_group = ttk.LabelFrame(self.body, padding=SECTION_PADDING)
        self.source_group.pack(fill="x", pady=(0, SECTION_GAP))
        self.drop_canvas = tk.Canvas(
            self.source_group,
            height=DROP_ZONE_HEIGHT,
            bg=self.ui_styles.drop_background,
            highlightbackground=self.ui_styles.drop_border,
            highlightthickness=1,
            takefocus=True,
        )
        self.drop_canvas.pack(fill="x")
        self.drop_canvas.bind("<Configure>", self._redraw_drop_zone)
        self.drop_canvas.bind("<Button-1>", lambda event: self._browse_files())
        self.drop_canvas.bind("<Return>", lambda event: self._browse_files())
        self.drop_canvas.bind("<space>", lambda event: self._browse_files())
        if HAS_DND:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self._on_drop)
        source_actions = ttk.Frame(self.source_group)
        source_actions.pack(fill="x", pady=(SPACE_SM, SPACE_XS))
        self.browse_button = ttk.Button(source_actions, command=self._browse_files)
        self.browse_button.pack(side="left")
        self.clear_files_button = ttk.Button(
            source_actions, command=self._clear_files
        )
        self.clear_files_button.pack(side="left", padx=SPACE_SM)
        self._register_automation_widget("files.add", self.browse_button)
        self._register_automation_widget("files.clear", self.clear_files_button)

        file_box = ttk.Frame(self.source_group)
        file_box.pack(fill="x")
        self.file_canvas = tk.Canvas(
            file_box, height=FILE_LIST_HEIGHT, highlightthickness=0, takefocus=True
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

        self.theme_group = ttk.LabelFrame(self.body, padding=SECTION_PADDING)
        self.theme_group.pack(fill="x", pady=(0, SECTION_GAP))
        self.theme_cards = ttk.Frame(self.theme_group)
        self.theme_cards.pack(fill="x")
        css_row = ttk.Frame(self.theme_group)
        css_row.pack(fill="x", pady=(SPACE_SM, 0))
        self.css_label = ttk.Label(css_row)
        self.css_label.pack(side="left")
        self.css_entry = ttk.Entry(css_row, state="readonly")
        self.css_entry.pack(side="left", fill="x", expand=True, padx=SPACE_SM)
        self.css_button = ttk.Button(css_row, command=self._choose_css)
        self.css_button.pack(side="left")
        self.css_reset_button = ttk.Button(css_row, command=self._reset_css)
        self.css_reset_button.pack(side="left", padx=(SPACE_SM, 0))

        self.advanced_group = ttk.LabelFrame(self.body, padding=SECTION_PADDING)
        self.advanced_group.pack(fill="x", pady=(0, SECTION_GAP))
        self.advanced_toggle = ttk.Button(
            self.advanced_group, command=self._toggle_advanced
        )
        self.advanced_toggle.pack(fill="x")
        self._register_automation_widget("advanced.toggle", self.advanced_toggle)
        self.advanced_content = ttk.Frame(self.advanced_group)
        self.tokens_hint_label = ttk.Label(self.advanced_content)
        self.tokens_hint_label.pack(anchor="w", pady=(SPACE_SM, SPACE_XS))
        for group_name, keys in (
            ("header_group_label", ("header_left", "header_center", "header_right")),
            ("footer_group_label", ("footer_left", "footer_center", "footer_right")),
        ):
            label = ttk.Label(self.advanced_content)
            setattr(self, group_name, label)
            label.pack(anchor="w", pady=(SPACE_XS, 0))
            row = ttk.Frame(self.advanced_content)
            row.pack(fill="x")
            for key in keys:
                entry = ttk.Entry(row, textvariable=self.hf_vars[key])
                entry.pack(side="left", fill="x", expand=True, padx=SPACE_XS)
                self._operation_controls.append(entry)
        options = ttk.Frame(self.advanced_content)
        options.pack(fill="x", pady=(SPACE_SM, 0))
        self.render_date_label = ttk.Label(options)
        self.render_date_label.pack(side="left")
        self.render_date_entry = ttk.Entry(
            options, textvariable=self.render_date_var, width=12
        )
        self.render_date_entry.pack(
            side="left",
            padx=(SPACE_SM, OUTER_PADDING),
        )
        self.trusted_html_check = ttk.Checkbutton(
            options, variable=self.trusted_html_var
        )
        self.trusted_html_check.pack(side="left")

        self.preview_group = ttk.LabelFrame(self.body, padding=SECTION_PADDING)
        self.preview_group.pack(fill="both", expand=True, pady=(0, SECTION_GAP))
        preview_header = ttk.Frame(self.preview_group)
        preview_header.pack(fill="x")
        self.refresh_preview_button = ttk.Button(
            preview_header, command=self._refresh_preview
        )
        self.refresh_preview_button.pack(side="left")
        self._register_automation_widget("preview.refresh", self.refresh_preview_button)
        self.zoom_out_button = ttk.Button(
            preview_header, width=3, text="−", command=lambda: self._change_zoom(-1)
        )
        self.zoom_out_button.pack(side="right")
        self.zoom_in_button = ttk.Button(
            preview_header, width=3, text="+", command=lambda: self._change_zoom(1)
        )
        self.zoom_in_button.pack(side="right", padx=SPACE_XS)
        self.zoom_label = ttk.Label(preview_header)
        self.zoom_label.pack(side="right")
        preview_box = ttk.Frame(self.preview_group)
        preview_box.pack(fill="both", expand=True, pady=(SPACE_SM, 0))
        self.preview_canvas = tk.Canvas(
            preview_box,
            height=PREVIEW_HEIGHT,
            bg=self.ui_styles.preview_background,
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

        self.output_group = ttk.LabelFrame(self.body, padding=SECTION_PADDING)
        self.output_group.pack(fill="x", pady=(0, SECTION_GAP))
        output_row = ttk.Frame(self.output_group)
        output_row.pack(fill="x")
        self.output_entry = ttk.Entry(output_row, state="readonly")
        self.output_entry.pack(side="left", fill="x", expand=True)
        self.output_button = ttk.Button(output_row, command=self._choose_output_dir)
        self.output_button.pack(side="left", padx=(SPACE_SM, 0))
        self.output_reset_button = ttk.Button(
            output_row, command=self._reset_output_dir
        )
        self.output_reset_button.pack(side="left", padx=(SPACE_SM, 0))
        self._register_automation_widget("output.choose", self.output_button)
        self._register_automation_widget("output.reset", self.output_reset_button)

        action_row = ttk.Frame(self.body)
        action_row.pack(fill="x")
        self.generate_button = ttk.Button(
            action_row,
            command=self._on_generate_clicked,
            style=PRIMARY_BUTTON_STYLE,
        )
        self.generate_button.pack(side="left", fill="x", expand=True)
        self.cancel_button = ttk.Button(
            action_row, command=self._cancel_conversion, state="disabled"
        )
        self.cancel_button.pack(side="left", padx=(SPACE_SM, 0))
        self._register_automation_widget("convert.start", self.generate_button)
        self._register_automation_widget("convert.cancel", self.cancel_button)
        self.progress = ttk.Progressbar(
            self.body, variable=self.progress_var, maximum=1
        )
        self.progress.pack(fill="x", pady=(SPACE_SM, SPACE_XS))
        self.status_label = ttk.Label(
            self.body,
            wraplength=STATUS_WRAP_LENGTH,
            style=STATUS_LABEL_STYLE,
        )
        self.status_label.pack(anchor="w")
        self.results_frame = ttk.Frame(self.body)
        self.results_frame.pack(fill="x", pady=(SPACE_SM, 0))

        self._operation_controls.extend([
            self.browse_button, self.clear_files_button, self.css_button,
            self.css_reset_button, self.advanced_toggle, self.render_date_entry,
            self.trusted_html_check, self.refresh_preview_button,
            self.output_button, self.output_reset_button,
        ])

    def _register_automation_widget(self, action: str, widget: tk.Misc) -> None:
        """Expose a stable semantic control for automated desktop checks."""
        if action not in AUTOMATION_ACTIONS:
            raise ValueError("Unknown desktop automation action: {0}".format(action))
        self._automation_widgets[action] = widget

    def _bind_accessibility(self) -> None:
        self.root.bind_all("<Control-o>", lambda event: self._browse_files())
        self.root.bind_all("<Control-r>", lambda event: self._refresh_preview())
        self.root.bind_all("<Control-g>", lambda event: self._on_generate_clicked())
        self.root.bind_all("<Escape>", lambda event: self._cancel_conversion())
        self.root.bind_all("<Control-plus>", lambda event: self._change_zoom(1))
        self.root.bind_all("<Control-minus>", lambda event: self._change_zoom(-1))
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event) -> None:
        target = (
            self.preview_canvas
            if self.preview_canvas.focus_get()
            else self.body_canvas
        )
        target.yview_scroll(-1 if event.delta > 0 else 1, "units")
