"""Tk widget construction for the LibreMark PDF desktop adapter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from ... import __version__, core
from ..ctk.app_shell import AppShell
from ..ctk.assets import UiAssetRegistry, product_logo
from ..ctk.components import CardFrame, PrimaryButton, SecondaryButton
from ..ctk.responsive import (
    DebouncedLayoutController,
    resolve_layout_mode,
)
from ..ctk.theme import (
    COLORS,
    SIZES,
    SPACING,
    SystemFontResolver,
    install_light_theme,
)
from ..ctk.widgets.action_bar import ActionBar
from ..ctk.widgets.app_header import AppHeader
from ..ctk.widgets.file_panel import FilesPanel
from ..ctk.widgets.settings_summary import SettingsSummaryPanel
from .components import configure_symbol_button
from .styles import (
    ICON_BUTTON_STYLE,
    OUTER_PADDING,
    PREVIEW_HEIGHT,
    SECTION_GAP,
    SECTION_PADDING,
    SPACE_SM,
    SPACE_XS,
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
    "style.toggle", "destination.toggle", "header_footer.toggle",
    "other.toggle", "advanced.toggle", "preview.refresh",
    "preview.zoom_out", "preview.zoom_in", "preview.retry",
    "preview.copy_details",
    "preview.previous_page", "preview.next_page",
    "output.choose", "output.reset",
    "convert.start", "convert.cancel",
    "about.open",
))

INITIAL_WINDOW_WIDTH = 1180
INITIAL_WINDOW_HEIGHT = 760
MINIMUM_WINDOW_WIDTH = 560
MINIMUM_WINDOW_HEIGHT = 520
LEFT_PANEL_TARGET_WIDTH = 390
LEFT_PANEL_MIN_WIDTH = 360
LEFT_PANEL_MAX_WIDTH = 440
PREVIEW_MIN_WIDTH = 560


def initial_window_size(root: tk.Misc) -> tuple[int, int]:
    """Return the target size capped to the available Tk screen."""
    available_width = int(root.winfo_screenwidth())
    available_height = int(root.winfo_screenheight())
    return (
        max(
            MINIMUM_WINDOW_WIDTH,
            min(INITIAL_WINDOW_WIDTH, int(available_width * 0.92)),
        ),
        max(
            MINIMUM_WINDOW_HEIGHT,
            min(INITIAL_WINDOW_HEIGHT, int(available_height * 0.90)),
        ),
    )


def responsive_mode(width: int) -> str:
    """Return the responsive mode for a window width."""
    return resolve_layout_mode(width)


def drop_zone_text_key(has_dnd: bool) -> str:
    """Return copy that accurately reflects drag-and-drop availability."""
    return "drop_or_browse" if has_dnd else "browse_without_dnd"


def load_logo(size: int) -> tk.PhotoImage:
    if size not in LOGO_ICON_CACHE:
        path = core.resource_path("assets/libremark-pdf-logo-{0}.png".format(size))
        LOGO_ICON_CACHE[size] = tk.PhotoImage(file=str(path))
    return LOGO_ICON_CACHE[size]


class AutoHideVerticalScrollbar(ttk.Scrollbar):
    """Show the legacy body scrollbar only when its content overflows."""

    def set(self, first, last) -> None:
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.pack_forget()
        elif not self.winfo_manager():
            self.pack(side="right", fill="y")
        super().set(first, last)


class TkLayoutMixin:
    """Build and bind widgets without owning application state transitions."""

    def _build_ui(self) -> None:
        install_light_theme()
        initial_width, initial_height = initial_window_size(self.root)
        self.root.geometry("{0}x{1}".format(initial_width, initial_height))
        self.root.minsize(MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT)
        self._layout_mode = None
        self._dnd_files_type = DND_FILES
        self.ui_fonts = SystemFontResolver(self.root)
        self.ui_assets = UiAssetRegistry(self.root)
        # CTk frames proxy their master's configure method. Calling Tk's base
        # implementation avoids retaining a destroyed frame's proxy when a
        # root is deliberately reused by GUI characterization tests.
        tk.Misc.configure(self.root, background=COLORS["app_bg"])
        self.app_shell = AppShell(self.root)
        resize_border = SIZES["window_resize_border"]
        self.app_shell.pack(
            fill="both",
            expand=True,
            padx=resize_border,
            pady=resize_border,
        )
        self.app_header = AppHeader(
            self.app_shell,
            root=self.root,
            logo=product_logo(32),
            version=__version__,
            language=self.lang,
            fonts=self.ui_fonts,
            on_shortcuts=self._show_keyboard_shortcuts,
            on_manual=self._show_user_manual,
            on_report=self._show_problem_report,
            on_about=self._show_about,
            on_language=self._set_lang,
        )
        self.app_shell.attach_header(self.app_header)
        self.logo_label = self.app_header.logo_label
        try:
            self.root.iconphoto(True, load_logo(64))
        except Exception:
            pass
        self.title_label = self.app_header.product_label
        self.version_button = self.app_header.version_button
        self.help_button = self.app_header.help_button
        self.help_menu_widget = self.app_header.help_menu
        self.language_menu_widget = self.app_header.language_menu
        self.btn_en = self.app_header.language_actions["en"]
        self.btn_fr = self.app_header.language_actions["fr"]
        self._register_automation_widget("about.open", self.version_button)
        self._register_automation_widget("language.en", self.btn_en)
        self._register_automation_widget("language.fr", self.btn_fr)
        self.action_bar = ActionBar(
            self.app_shell,
            fonts=self.ui_fonts,
            on_generate=self._on_generate_clicked,
            on_cancel=self._cancel_conversion,
            progress_variable=self.progress_var,
            generate_icon=self.ui_assets.image(
                "file-earmark-text",
                size=20,
                color="on-primary",
            ),
        )
        self.app_shell.attach_action_bar(self.action_bar)
        self.generate_button = self.action_bar.generate_button
        self.cancel_button = self.action_bar.cancel_button
        self.status_label = self.action_bar.status_label
        self.progress = self.action_bar.progress
        self._register_automation_widget("convert.start", self.generate_button)
        self._register_automation_widget("convert.cancel", self.cancel_button)

        container = ttk.Frame(self.app_shell.content)
        container.pack(fill="both", expand=True)
        self.body_canvas = tk.Canvas(container, highlightthickness=0, takefocus=True)
        self.body_scroll = AutoHideVerticalScrollbar(
            container, orient="vertical", command=self.body_canvas.yview
        )
        self.body_canvas.configure(yscrollcommand=self.body_scroll.set)
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

        self.workspace = ttk.Frame(self.body)
        self.workspace.pack(fill="both", expand=True)
        self._left_panel_width = LEFT_PANEL_TARGET_WIDTH
        self._left_resize_origin = None
        self.workspace_splitter = ttk.Frame(
            self.workspace,
            width=SECTION_GAP,
            cursor="size_we",
            takefocus=True,
        )
        self.workspace_splitter.grid_propagate(False)
        splitter_line = ttk.Separator(
            self.workspace_splitter,
            orient="vertical",
        )
        splitter_line.place(relx=0.5, rely=0, relheight=1, anchor="n")
        for splitter_widget in (self.workspace_splitter, splitter_line):
            splitter_widget.bind(
                "<ButtonPress-1>",
                self._start_left_panel_resize,
                add="+",
            )
            splitter_widget.bind(
                "<B1-Motion>",
                self._resize_left_panel,
                add="+",
            )
        self.workspace_splitter.bind(
            "<Left>",
            lambda _event: self._adjust_left_panel_width(-10),
            add="+",
        )
        self.workspace_splitter.bind(
            "<Right>",
            lambda _event: self._adjust_left_panel_width(10),
            add="+",
        )
        self.workspace_splitter.bind(
            "<Home>",
            lambda _event: self._set_left_panel_width(
                LEFT_PANEL_MIN_WIDTH
            ),
            add="+",
        )
        self.workspace_splitter.bind(
            "<End>",
            lambda _event: self._set_left_panel_width(
                LEFT_PANEL_MAX_WIDTH
            ),
            add="+",
        )

        self.files_panel = FilesPanel(
            self.workspace,
            labels=self._file_panel_labels(),
            fonts=self.ui_fonts,
            assets=self.ui_assets,
            has_drag_and_drop=HAS_DND,
            on_add=self._browse_files,
            on_select=self._select_file,
            on_show_source=self._show_source_file,
            on_copy_path=self._copy_source_path,
            on_remove=self._remove_file,
            on_clear=self._clear_files,
        )
        self.source_group = self.files_panel
        self.browse_button = self.files_panel.add_button
        self.file_count_label = self.files_panel.count_label
        self.clear_files_button = self.files_panel.panel_menu_button
        self.drop_canvas = self.files_panel.empty_state
        self.file_canvas = self.files_panel.list_view
        self._register_automation_widget("files.add", self.browse_button)
        self._register_automation_widget("files.clear", self.clear_files_button)
        if HAS_DND:
            for drop_target in self.files_panel.drop_targets:
                self._register_drop_target(drop_target)

        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.withdraw()
        settings_dialog.transient(self.root)
        settings_dialog.configure(background=COLORS["app_bg"])
        settings_dialog.resizable(True, True)
        settings_dialog.minsize(560, 520)
        settings_dialog.maxsize(
            720,
            max(520, self.root.winfo_screenheight()),
        )
        settings_dialog.protocol(
            "WM_DELETE_WINDOW",
            self._cancel_settings_editor,
        )
        settings_dialog.bind("<Escape>", self._cancel_settings_editor)
        settings_dialog.bind(
            "<Configure>",
            self._on_settings_dialog_configure,
            add="+",
        )

        dialog_shell = ctk.CTkFrame(
            settings_dialog,
            fg_color=COLORS["app_bg"],
            corner_radius=0,
        )
        dialog_shell.pack(fill="both", expand=True)
        dialog_header = ctk.CTkFrame(dialog_shell, fg_color="transparent")
        dialog_header.pack(
            fill="x",
            padx=SPACING["lg"],
            pady=(SPACING["lg"], SPACING["md"]),
        )
        settings_dialog_title = ctk.CTkLabel(
            dialog_header,
            text="",
            anchor="w",
            text_color=COLORS["text"],
            font=self.ui_fonts.font("dialog_title"),
        )
        settings_dialog_title.pack(fill="x")
        settings_dialog_description = ctk.CTkLabel(
            dialog_header,
            text="",
            anchor="w",
            justify="left",
            wraplength=640,
            text_color=COLORS["text_secondary"],
            font=self.ui_fonts.font("secondary"),
        )
        settings_dialog_description.pack(fill="x", pady=(SPACING["xs"], 0))
        settings_scroll = ctk.CTkScrollableFrame(
            dialog_shell,
            fg_color="transparent",
            corner_radius=0,
        )
        settings_scroll.pack(
            fill="both",
            expand=True,
            padx=SPACING["lg"],
        )
        settings_section_titles = {}

        def build_settings_section(name: str) -> tuple:
            card = CardFrame(settings_scroll)
            card.pack(fill="x", pady=(0, SPACING["md"]))
            title = ctk.CTkLabel(
                card,
                text="",
                anchor="w",
                text_color=COLORS["text"],
                font=self.ui_fonts.font("panel_title"),
            )
            title.pack(
                fill="x",
                padx=SPACING["md"],
                pady=(SPACING["md"], SPACING["xs"]),
            )
            content = ttk.Frame(card, padding=SECTION_PADDING)
            content.pack(
                fill="x",
                padx=SPACING["xs"],
                pady=(0, SPACING["md"]),
            )
            settings_section_titles[name] = title
            return card, content

        self.theme_group, style_content = build_settings_section("style")
        self.theme_mode_radio = ttk.Radiobutton(
            style_content,
            variable=self._settings_draft_style_mode_var,
            value="theme",
            command=self._reset_css,
        )
        self.theme_mode_radio.pack(anchor="w")
        self.theme_cards = ttk.Frame(style_content)
        self.theme_cards.pack(fill="x", pady=(SPACE_XS, 0))
        self.css_mode_radio = ttk.Radiobutton(
            style_content,
            variable=self._settings_draft_style_mode_var,
            value="css",
            command=self._activate_css_mode,
        )
        self.css_mode_radio.pack(anchor="w", pady=(SPACE_SM, 0))
        self.css_row = ttk.Frame(style_content)
        self.css_row.pack(fill="x", pady=(SPACE_SM, 0))
        self.css_label = ttk.Label(self.css_row)
        self.css_label.pack(side="left")
        self.css_entry = ttk.Entry(self.css_row, state="readonly")
        self.css_entry.pack(side="left", fill="x", expand=True, padx=SPACE_SM)
        self.css_button = ttk.Button(self.css_row, command=self._choose_css)
        self.css_button.pack(side="left")
        self.css_reset_button = ttk.Button(
            self.css_row,
            command=self._reset_css,
        )
        self.css_reset_button.pack(side="left", padx=(SPACE_SM, 0))

        self.output_group, destination_content = build_settings_section(
            "destination"
        )
        self.output_row = ttk.Frame(destination_content)
        self.output_row.pack(fill="x")
        self.output_entry = ttk.Entry(self.output_row, state="readonly")
        self.output_entry.pack(side="left", fill="x", expand=True)
        self.output_button = ttk.Button(
            self.output_row,
            command=self._choose_output_dir,
        )
        self.output_button.pack(side="left", padx=(SPACE_SM, 0))
        self.output_reset_button = ttk.Button(
            self.output_row,
            command=self._reset_output_dir,
        )
        self.output_reset_button.pack(side="left", padx=(SPACE_SM, 0))
        self._register_automation_widget("output.choose", self.output_button)
        self._register_automation_widget("output.reset", self.output_reset_button)

        self.advanced_group, self.advanced_content = build_settings_section(
            "header_footer"
        )
        self.tokens_hint_label = ttk.Label(self.advanced_content)
        self.tokens_hint_label.pack(anchor="w", pady=(0, SPACE_XS))
        self.header_footer_entry_rows = []
        self.header_footer_field_rows = []
        self.hf_position_labels = {
            "position_left": [],
            "position_center": [],
            "position_right": [],
        }
        for group_name, keys in (
            ("header_group_label", ("header_left", "header_center", "header_right")),
            ("footer_group_label", ("footer_left", "footer_center", "footer_right")),
        ):
            label = ttk.Label(self.advanced_content)
            setattr(self, group_name, label)
            label.pack(anchor="w", pady=(SPACE_XS, 0))
            row = ttk.Frame(self.advanced_content)
            row.pack(fill="x")
            entries = []
            fields = []
            for key, position_key in zip(
                keys,
                ("position_left", "position_center", "position_right"),
            ):
                field = ttk.Frame(row)
                position_label = ttk.Label(field)
                position_label.pack(anchor="w")
                entry = ttk.Entry(
                    field,
                    textvariable=self._settings_draft_hf_vars[key],
                )
                entry.pack(fill="x", expand=True)
                entries.append(entry)
                fields.append(field)
                self.hf_position_labels[position_key].append(position_label)
                self._operation_controls.append(entry)
            self.header_footer_entry_rows.append(entries)
            self.header_footer_field_rows.append(fields)
        self.reset_header_footer_button = ttk.Button(
            self.advanced_content,
            command=self._reset_header_footer,
        )
        self.reset_header_footer_button.pack(anchor="e", pady=(SPACE_SM, 0))

        self.other_group, other_content = build_settings_section("other")
        date_row = ttk.Frame(other_content)
        date_row.pack(fill="x")
        self.render_date_label = ttk.Label(date_row)
        self.render_date_label.pack(side="left")
        self.render_date_entry = ttk.Entry(
            date_row,
            textvariable=self._settings_draft_render_date_var,
            width=12,
        )
        self.render_date_entry.pack(side="left", padx=(SPACE_SM, 0))
        self.trusted_html_check = ttk.Checkbutton(
            other_content,
            variable=self._settings_draft_trusted_html_var,
        )
        self.trusted_html_check.pack(anchor="w", pady=(SPACE_SM, 0))
        self.trusted_html_help_label = ttk.Label(
            other_content,
            wraplength=420,
            justify="left",
        )
        self.trusted_html_help_label.pack(fill="x", pady=(SPACE_XS, 0))

        dialog_actions = ctk.CTkFrame(
            dialog_shell,
            fg_color=COLORS["surface"],
            corner_radius=0,
            border_width=1,
            border_color=COLORS["border"],
        )
        dialog_actions.pack(fill="x", side="bottom")
        settings_cancel_button = SecondaryButton(
            dialog_actions,
            text="",
            command=self._cancel_settings_editor,
            width=104,
        )
        settings_cancel_button.pack(
            side="right",
            padx=(SPACING["sm"], SPACING["lg"]),
            pady=SPACING["md"],
        )
        settings_apply_button = PrimaryButton(
            dialog_actions,
            text="",
            command=self._apply_settings_editor,
            width=104,
        )
        settings_apply_button.pack(
            side="right",
            pady=SPACING["md"],
        )
        self._settings_dialog = {
            "window": settings_dialog,
            "title": settings_dialog_title,
            "description": settings_dialog_description,
            "section_titles": settings_section_titles,
            "apply": settings_apply_button,
            "cancel": settings_cancel_button,
        }
        self._settings_dialog_layout_narrow = None
        self._layout_settings_dialog(680)

        self.settings_panel = SettingsSummaryPanel(
            self.workspace,
            labels=self._settings_summary_labels(),
            summaries=self._settings_summaries(),
            fonts=self.ui_fonts,
            assets=self.ui_assets,
            on_edit=self._open_settings_editor,
        )
        for action in (
            "style.toggle",
            "destination.toggle",
            "header_footer.toggle",
            "other.toggle",
            "advanced.toggle",
        ):
            self._register_automation_widget(
                action,
                self.settings_panel.edit_button,
            )

        self.preview_group = ttk.LabelFrame(self.workspace, padding=SECTION_PADDING)
        self.preview_header = ttk.Frame(self.preview_group)
        self.preview_header.pack(fill="x")
        self.active_preview_label = ttk.Label(
            self.preview_header,
            font=self.ui_styles.emphasis_font,
            anchor="w",
        )
        self.active_preview_label.pack(side="left", fill="x", expand=True)
        self.preview_controls = ttk.Frame(self.preview_header)
        self.preview_controls.pack(side="right")
        self.refresh_preview_button = ttk.Button(
            self.preview_controls,
            command=self._refresh_preview,
            style=ICON_BUTTON_STYLE,
        )
        self.refresh_preview_button.pack(side="left")
        self._register_automation_widget("preview.refresh", self.refresh_preview_button)
        self.previous_page_button = ttk.Button(
            self.preview_controls,
            command=lambda: self._change_preview_page(-1),
            style=ICON_BUTTON_STYLE,
        )
        self.previous_page_button.pack(side="left", padx=(SPACE_SM, 0))
        self._register_automation_widget(
            "preview.previous_page", self.previous_page_button
        )
        self.preview_page_label = ttk.Label(
            self.preview_controls, anchor="center", width=16
        )
        self.preview_page_label.pack(side="left", padx=SPACE_XS)
        self.next_page_button = ttk.Button(
            self.preview_controls,
            command=lambda: self._change_preview_page(1),
            style=ICON_BUTTON_STYLE,
        )
        self.next_page_button.pack(side="left")
        self._register_automation_widget(
            "preview.next_page", self.next_page_button
        )
        self.zoom_out_button = ttk.Button(
            self.preview_controls,
            command=lambda: self._change_zoom(-1),
            style=ICON_BUTTON_STYLE,
        )
        self.zoom_out_button.pack(side="left", padx=(SPACE_SM, 0))
        self._register_automation_widget("preview.zoom_out", self.zoom_out_button)
        self.zoom_label = ttk.Label(
            self.preview_controls,
            anchor="center",
            width=7,
        )
        self.zoom_label.pack(side="left", padx=SPACE_XS)
        self.zoom_in_button = ttk.Button(
            self.preview_controls,
            command=lambda: self._change_zoom(1),
            style=ICON_BUTTON_STYLE,
        )
        self.zoom_in_button.pack(side="left")
        self._register_automation_widget("preview.zoom_in", self.zoom_in_button)
        configure_symbol_button(
            self.refresh_preview_button,
            "↻",
            self._t("refresh_preview_a11y"),
        )
        configure_symbol_button(
            self.previous_page_button,
            "‹",
            self._t("previous_page_a11y"),
        )
        configure_symbol_button(
            self.next_page_button,
            "›",
            self._t("next_page_a11y"),
        )
        configure_symbol_button(
            self.zoom_out_button,
            "−",
            self._t("zoom_out_a11y"),
        )
        configure_symbol_button(
            self.zoom_in_button,
            "+",
            self._t("zoom_in_a11y"),
        )

        self.preview_message_frame = ttk.Frame(self.preview_group)
        self.preview_message_label = ttk.Label(
            self.preview_message_frame,
            wraplength=480,
            justify="left",
        )
        self.preview_message_label.pack(side="left", fill="x", expand=True)
        self.preview_retry_button = ttk.Button(
            self.preview_message_frame,
            command=self._retry_preview,
        )
        self.preview_retry_button.pack(side="right", padx=(SPACE_SM, 0))
        self._register_automation_widget("preview.retry", self.preview_retry_button)
        self.preview_copy_button = ttk.Button(
            self.preview_message_frame,
            command=self._copy_preview_details,
        )
        self.preview_copy_button.pack(side="right", padx=(SPACE_SM, 0))
        self._register_automation_widget(
            "preview.copy_details", self.preview_copy_button
        )
        preview_box = ttk.Frame(self.preview_group)
        preview_box.pack(fill="both", expand=True, pady=(SPACE_SM, 0))
        preview_box.rowconfigure(0, weight=1)
        preview_box.columnconfigure(0, weight=1)
        self.preview_canvas = tk.Canvas(
            preview_box,
            height=PREVIEW_HEIGHT,
            bg=self.ui_styles.preview_background,
            highlightbackground=self.ui_styles.drop_border,
            highlightcolor=self.ui_styles.drop_border,
            highlightthickness=1,
            takefocus=True,
        )
        self.preview_vertical = ttk.Scrollbar(
            preview_box, orient="vertical", command=self.preview_canvas.yview
        )
        self.preview_horizontal = ttk.Scrollbar(
            preview_box, orient="horizontal", command=self.preview_canvas.xview
        )
        self.preview_canvas.configure(
            yscrollcommand=self.preview_vertical.set,
            xscrollcommand=self.preview_horizontal.set,
        )
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        self.preview_canvas.bind("<Configure>", self._on_preview_canvas_configure)
        self.preview_canvas.bind("<Button-1>", self._focus_preview)
        self.preview_canvas.bind("<MouseWheel>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Control-MouseWheel>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Button-4>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Button-5>", self._on_preview_mousewheel)
        self.preview_canvas.bind("<Button-2>", self._start_preview_pan)
        self.preview_canvas.bind("<B2-Motion>", self._drag_preview_pan)
        self.preview_canvas.bind(
            "<Left>", lambda event: self._change_preview_page(-1)
        )
        self.preview_canvas.bind(
            "<Right>", lambda event: self._change_preview_page(1)
        )

        self.results_frame = ttk.LabelFrame(
            self.workspace,
            padding=SECTION_PADDING,
        )
        self.results_summary_label = ttk.Label(
            self.results_frame,
            anchor="w",
            takefocus=True,
            font=self.ui_styles.emphasis_font,
        )
        self.results_summary_label.pack(fill="x")
        self.results_error_label = ttk.Label(
            self.results_frame,
            justify="left",
            wraplength=480,
        )
        self.result_rows_frame = ttk.Frame(self.results_frame)
        self.result_rows_frame.pack(fill="x", pady=(SPACE_SM, 0))

        self._operation_controls.extend([
            self.browse_button, self.clear_files_button, self.css_button,
            self.css_reset_button, self.theme_mode_radio, self.css_mode_radio,
            self.settings_panel.edit_button,
            self.reset_header_footer_button,
            self.render_date_entry, self.trusted_html_check,
            self.refresh_preview_button, self.zoom_out_button,
            self.zoom_in_button, self.preview_retry_button,
            self.preview_copy_button,
            self.previous_page_button, self.next_page_button,
            self.output_button, self.output_reset_button,
        ])
        self._responsive_controller = DebouncedLayoutController(
            self.root,
            self._apply_responsive_layout,
        )
        self.root.bind("<Configure>", self._on_root_configure, add="+")
        self._apply_responsive_layout(initial_width, initial_height)

    def _on_root_configure(self, event) -> None:
        if event.widget is self.root:
            self._responsive_controller.schedule(event.width, event.height)

    def _apply_responsive_layout(self, width: int, height: int) -> None:
        """Adapt existing panes without rebuilding widgets or changing focus."""
        self._viewport_height = height
        mode = responsive_mode(width)
        layout_changed = mode != self._layout_mode
        if layout_changed:
            sections = (
                self.source_group,
                self.preview_group,
                self.settings_panel,
                self.results_frame,
            )
            for section in sections:
                section.grid_forget()
            for row in range(len(sections)):
                self.workspace.rowconfigure(row, weight=0)
            if mode == "compact":
                self.workspace.columnconfigure(0, weight=1, minsize=0)
                self.workspace.columnconfigure(1, weight=0, minsize=0)
                self.workspace.columnconfigure(2, weight=0, minsize=0)
                self.workspace_splitter.grid_remove()
                for row, section in enumerate(sections):
                    section.grid(
                        row=row,
                        column=0,
                        sticky="nsew",
                        pady=(0, SECTION_GAP),
                    )
            else:
                left_minimum = (
                    self._left_panel_width if mode == "large" else 340
                )
                right_minimum = (
                    PREVIEW_MIN_WIDTH if mode == "large" else 320
                )
                self.workspace.columnconfigure(
                    0, weight=0, minsize=left_minimum
                )
                self.workspace.columnconfigure(
                    1,
                    weight=0,
                    minsize=SECTION_GAP if mode == "large" else 0,
                )
                self.workspace.columnconfigure(
                    2, weight=1, minsize=right_minimum
                )
                left_sections = (
                    self.source_group,
                    self.settings_panel,
                    self.results_frame,
                )
                for row, section in enumerate(left_sections):
                    section.grid(
                        row=row,
                        column=0,
                        sticky="nsew",
                        padx=(0, 0 if mode == "large" else SECTION_GAP),
                        pady=(0, SECTION_GAP),
                    )
                self.workspace.rowconfigure(len(left_sections) - 1, weight=1)
                if mode == "large":
                    self.workspace_splitter.grid(
                        row=0,
                        column=1,
                        rowspan=len(left_sections),
                        sticky="ns",
                    )
                else:
                    self.workspace_splitter.grid_remove()
                self.preview_group.grid(
                    row=0,
                    column=2,
                    rowspan=len(left_sections),
                    sticky="nsew",
                )
            self._layout_legacy_setting_rows()
            self._layout_preview_header()
            self._layout_mode = mode

        if layout_changed:
            outer_padding = SPACE_SM
            preview_height = {
                "compact": 240,
                "medium": 280,
                "large": 320,
            }[mode]
            legacy_panel_width = {
                "compact": 1,
                "medium": 300,
                "large": 340,
            }[mode]
            self.body.configure(
                padding=(outer_padding, SPACE_SM, outer_padding, SPACE_XS)
            )
            files_panel = getattr(self, "files_panel", None)
            if files_panel is not None:
                files_panel.configure(width=legacy_panel_width)
            else:
                self.drop_canvas.configure(width=legacy_panel_width)
                self.file_canvas.configure(width=legacy_panel_width)
            self.preview_canvas.configure(height=preview_height)
            self.app_header.set_layout_mode(mode)
        self.status_label.configure(
            wraplength=max(160, width // 2),
        )

    def _start_left_panel_resize(self, event) -> str:
        if self._layout_mode != "large":
            return "break"
        self.workspace_splitter.focus_set()
        self._left_resize_origin = (event.x_root, self._left_panel_width)
        return "break"

    def _resize_left_panel(self, event) -> str:
        if self._left_resize_origin is None or self._layout_mode != "large":
            return "break"
        pointer_x, initial_width = self._left_resize_origin
        self._set_left_panel_width(
            initial_width + event.x_root - pointer_x
        )
        return "break"

    def _adjust_left_panel_width(self, delta: int) -> str:
        if self._layout_mode == "large":
            self._set_left_panel_width(self._left_panel_width + delta)
        return "break"

    def _set_left_panel_width(self, width: int) -> str:
        width = max(
            LEFT_PANEL_MIN_WIDTH,
            min(LEFT_PANEL_MAX_WIDTH, int(width)),
        )
        self._left_panel_width = width
        if self._layout_mode == "large":
            self.workspace.columnconfigure(0, minsize=width)
        return "break"

    def _layout_legacy_setting_rows(self) -> None:
        """Keep temporary legacy editors usable inside their modal adapters."""
        for widget in (
            self.css_label,
            self.css_entry,
            self.css_button,
            self.css_reset_button,
        ):
            widget.pack_forget()
        self.css_label.pack(anchor="w")
        self.css_entry.pack(fill="x", pady=(SPACE_XS, SPACE_SM))
        self.css_button.pack(side="left")
        self.css_reset_button.pack(side="left", padx=(SPACE_SM, 0))

        for widget in (
            self.output_entry,
            self.output_button,
            self.output_reset_button,
        ):
            widget.pack_forget()
        self.output_entry.pack(fill="x", pady=(0, SPACE_SM))
        self.output_button.pack(side="left")
        self.output_reset_button.pack(side="left", padx=(SPACE_SM, 0))

    def _on_settings_dialog_configure(self, event) -> None:
        if (
            hasattr(self, "_settings_dialog")
            and event.widget is self._settings_dialog["window"]
        ):
            self._layout_settings_dialog(event.width)

    def _layout_settings_dialog(self, width: int) -> None:
        """Keep the unified legacy adapter readable across its width range."""
        narrow = width < 640
        if narrow == getattr(self, "_settings_dialog_layout_narrow", None):
            return
        self._settings_dialog_layout_narrow = narrow
        self._settings_dialog["description"].configure(
            wraplength=max(480, width - 64)
        )
        for fields in self.header_footer_field_rows:
            for field in fields:
                field.pack_forget()
                if narrow:
                    field.pack(fill="x", pady=(0, SPACE_XS))
                else:
                    field.pack(
                        side="left",
                        fill="x",
                        expand=True,
                        padx=SPACE_XS,
                    )

    def _layout_preview_header(self) -> None:
        """Keep the active file and legacy toolbar visible without clipping."""
        self.active_preview_label.pack_forget()
        self.preview_controls.pack_forget()
        self.active_preview_label.pack(fill="x")
        self.preview_controls.pack(anchor="e", pady=(SPACE_XS, 0))

    def _register_automation_widget(self, action: str, widget: tk.Misc) -> None:
        """Expose a stable semantic control for automated desktop checks."""
        if action not in AUTOMATION_ACTIONS:
            raise ValueError("Unknown desktop automation action: {0}".format(action))
        self._automation_widgets[action] = widget

    def _register_drop_target(self, widget: tk.Misc) -> None:
        """Bind a source-area widget to the optional local DnD adapter."""
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        widget.dnd_bind("<<DropLeave>>", self._on_drop_leave)
        widget.dnd_bind("<<Drop>>", self._on_drop)

    def _bind_accessibility(self) -> None:
        self.root.bind_all("<Control-o>", lambda event: self._browse_files())
        self.root.bind_all("<Control-r>", lambda event: self._refresh_preview())
        self.root.bind_all("<Control-g>", lambda event: self._on_generate_clicked())
        self.root.bind_all("<Escape>", lambda event: self._cancel_conversion())
        self.root.bind_all("<Control-plus>", lambda event: self._change_zoom(1))
        self.root.bind_all("<Control-equal>", lambda event: self._change_zoom(1))
        self.root.bind_all("<Control-minus>", lambda event: self._change_zoom(-1))
        self.root.bind_all("<Control-Key-0>", lambda event: self._reset_zoom())
        self.root.bind_all("<F1>", lambda event: self._show_keyboard_shortcuts())
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event) -> None:
        if self.root.focus_get() is self.preview_canvas:
            return self._on_preview_mousewheel(event)
        target = self.body_canvas
        target.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _show_keyboard_shortcuts(self) -> str:
        self.dialogs.show_info(
            self._t("keyboard_shortcuts_action"),
            self._t("keyboard_shortcuts_body"),
        )
        return "break"
