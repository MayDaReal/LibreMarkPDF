"""Tk widget construction for the LibreMark PDF desktop adapter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from ... import __version__, core
from ..ctk.app_shell import AppShell
from ..ctk.assets import UiAssetRegistry, product_logo
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
from ..ctk.widgets.advanced_editor import AdvancedEditorPanel
from ..ctk.widgets.app_header import AppHeader
from ..ctk.widgets.compact_tabs import CompactTabBar
from ..ctk.widgets.destination_editor import DestinationEditorPanel
from ..ctk.widgets.file_panel import FilesPanel
from ..ctk.widgets.header_footer_editor import HeaderFooterEditorPanel
from ..ctk.widgets.preview_panel import PreviewPanel
from ..ctk.widgets.results_view import ResultsView
from ..ctk.widgets.settings_summary import SettingsSummaryPanel
from ..ctk.widgets.style_editor import StyleEditorPanel
from .styles import (
    OUTER_PADDING,
    SECTION_GAP,
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
    "preview.copy_details", "preview.report", "preview.fit_page",
    "preview.fit_width",
    "preview.previous_page", "preview.next_page",
    "output.choose", "output.reset",
    "convert.start", "convert.cancel", "convert.cancel_now", "menu.compact",
    "tab.files", "tab.preview", "tab.settings", "tab.results",
    "results.clear", "results.toggle",
    "about.open",
))

INITIAL_WINDOW_WIDTH = 1180
INITIAL_WINDOW_HEIGHT = 760
MINIMUM_WINDOW_WIDTH = 560
MINIMUM_WINDOW_HEIGHT = 520
LEFT_PANEL_TARGET_WIDTH = 390
LEFT_PANEL_MIN_WIDTH = 360
PREVIEW_MIN_WIDTH = 560
PREVIEW_MEDIUM_MIN_WIDTH = 320
LEFT_SECTION_MIN_HEIGHT = 148
LEFT_SETTINGS_TARGET_HEIGHT = 226
RESULTS_PANEL_TARGET_HEIGHT = 232
RESULTS_PANEL_MIN_HEIGHT = 160
RESULTS_PANEL_MAX_HEIGHT = 360
RESULTS_PANEL_COLLAPSED_HEIGHT = 52
RESULTS_PANEL_VERTICAL_RESERVE = 542


def splitter_cursors(windowing_system: str) -> dict[str, str]:
    """Return resize cursors accepted by the active Tk window system."""
    if windowing_system == "win32":
        return {"horizontal": "size_we", "vertical": "size_ns"}
    return {
        "horizontal": "sb_h_double_arrow",
        "vertical": "sb_v_double_arrow",
    }


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


class ScalingCompatibleToplevel(tk.Toplevel):
    """Host CTk children without interrupting their Windows DPI transition."""

    def block_update_dimensions_event(self) -> None:
        """Satisfy the CTk scaling-window contract for a plain Tk host."""

    def unblock_update_dimensions_event(self) -> None:
        """Satisfy the CTk scaling-window contract for a plain Tk host."""


class TkLayoutMixin:
    """Build and bind widgets without owning application state transitions."""

    def _build_ui(self) -> None:
        install_light_theme()
        initial_width, initial_height = initial_window_size(self.root)
        self.root.geometry("{0}x{1}".format(initial_width, initial_height))
        self.root.minsize(MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT)
        self._layout_mode = None
        self._compact_vertical_padding = None
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
            compact_menu_icon=self.ui_assets.image(
                "three-dots-vertical", size=20, color="neutral"
            ),
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
        self.compact_menu_widget = self.app_header.compact_menu
        self.btn_en = self.app_header.language_actions["en"]
        self.btn_fr = self.app_header.language_actions["fr"]
        self._register_automation_widget("about.open", self.version_button)
        self._register_automation_widget("language.en", self.btn_en)
        self._register_automation_widget("language.fr", self.btn_fr)
        self._register_automation_widget(
            "menu.compact", self.app_header.compact_menu_button
        )
        self.action_bar = ActionBar(
            self.app_shell,
            fonts=self.ui_fonts,
            on_generate=self._on_generate_clicked,
            on_cancel=self._cancel_conversion,
            on_cancel_now=self._cancel_conversion_now,
            on_decision_continue=self._continue_generation_decision,
            on_decision_back=self._cancel_generation_decision,
            on_scroll_outside=self._on_mousewheel,
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
        self.cancel_now_button = self.action_bar.cancel_now_button
        self.status_label = self.action_bar.status_label
        self.progress = self.action_bar.progress
        self._register_automation_widget("convert.start", self.generate_button)
        self._register_automation_widget("convert.cancel", self.cancel_button)
        self._register_automation_widget(
            "convert.cancel_now", self.cancel_now_button
        )

        self.compact_tabs = CompactTabBar(
            self.app_shell.content,
            labels=self._compact_tab_labels(),
            fonts=self.ui_fonts,
            on_select=self._select_compact_tab,
        )
        self.compact_tabs.set_active(self._active_compact_tab)
        for name, button in self.compact_tabs.buttons.items():
            self._register_automation_widget("tab.{0}".format(name), button)
        self.content_container = ttk.Frame(self.app_shell.content)
        self.content_container.pack(fill="both", expand=True)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.body_container = ttk.Frame(self.content_container)
        self.body_container.grid(row=0, column=0, sticky="nsew")
        container = self.body_container
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
        self.body_canvas.bind("<Configure>", self._on_body_canvas_configure)

        self.workspace = ttk.Frame(self.body)
        self.workspace.pack(fill="both", expand=True)
        self._left_panel_width = LEFT_PANEL_TARGET_WIDTH
        self._left_resize_origin = None
        self._results_panel_height = RESULTS_PANEL_TARGET_HEIGHT
        self._results_resize_origin = None
        cursors = splitter_cursors(
            str(self.root.tk.call("tk", "windowingsystem"))
        )
        self.workspace_splitter = ttk.Frame(
            self.workspace,
            width=SECTION_GAP,
            cursor=cursors["horizontal"],
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
                self._left_panel_max_width()
            ),
            add="+",
        )
        self.results_splitter = ttk.Frame(
            self.content_container,
            height=SECTION_GAP,
            cursor=cursors["vertical"],
            takefocus=True,
        )
        self.results_splitter.grid_propagate(False)
        results_splitter_line = ttk.Separator(
            self.results_splitter,
            orient="horizontal",
        )
        results_splitter_line.place(
            relx=0,
            rely=0.5,
            relwidth=1,
            anchor="w",
        )
        for splitter_widget in (
            self.results_splitter,
            results_splitter_line,
        ):
            splitter_widget.bind(
                "<ButtonPress-1>",
                self._start_results_panel_resize,
                add="+",
            )
            splitter_widget.bind(
                "<B1-Motion>",
                self._resize_results_panel,
                add="+",
            )
        self.results_splitter.bind(
            "<Up>",
            lambda _event: self._adjust_results_panel_height(10),
            add="+",
        )
        self.results_splitter.bind(
            "<Down>",
            lambda _event: self._adjust_results_panel_height(-10),
            add="+",
        )
        self.results_splitter.bind(
            "<Home>",
            lambda _event: self._set_results_panel_height(
                RESULTS_PANEL_MIN_HEIGHT
            ),
            add="+",
        )
        self.results_splitter.bind(
            "<End>",
            lambda _event: self._set_results_panel_height(
                RESULTS_PANEL_MAX_HEIGHT
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
        self.clear_files_button = self.files_panel.clear_button
        self.drop_canvas = self.files_panel.empty_state
        self.file_canvas = self.files_panel.list_view
        self._register_automation_widget("files.add", self.browse_button)
        self._register_automation_widget("files.clear", self.clear_files_button)
        if HAS_DND:
            for drop_target in self.files_panel.drop_targets:
                self._register_drop_target(drop_target)

        self.settings_panel = SettingsSummaryPanel(
            self.workspace,
            labels=self._settings_summary_labels(),
            summaries=self._settings_summaries(),
            fonts=self.ui_fonts,
            assets=self.ui_assets,
            on_edit_style=self._open_style_editor,
            on_edit_destination=self._open_destination_editor,
            on_edit_header_footer=self._open_header_footer_editor,
            on_edit_other=self._open_advanced_editor,
        )
        style_dialog = ScalingCompatibleToplevel(self.root)
        style_dialog.withdraw()
        style_dialog.transient(self.root)
        style_dialog.configure(background=COLORS["app_bg"])
        style_dialog.resizable(True, True)
        style_dialog.minsize(560, 520)
        style_dialog.maxsize(720, max(520, self.root.winfo_screenheight()))
        style_dialog.protocol("WM_DELETE_WINDOW", self._cancel_style_editor)
        style_dialog.bind("<Escape>", self._cancel_style_editor)
        self.style_dialog_editor = self._build_style_editor(
            style_dialog, show_back=False
        )
        self.style_dialog_editor.pack(fill="both", expand=True)
        self.compact_style_editor = self._build_style_editor(
            self.workspace, show_back=True
        )
        self._style_dialog = style_dialog
        destination_dialog = ScalingCompatibleToplevel(self.root)
        destination_dialog.withdraw()
        destination_dialog.transient(self.root)
        destination_dialog.configure(background=COLORS["app_bg"])
        destination_dialog.resizable(True, True)
        destination_dialog.minsize(560, 520)
        destination_dialog.maxsize(
            720, max(520, self.root.winfo_screenheight())
        )
        destination_dialog.protocol(
            "WM_DELETE_WINDOW", self._cancel_destination_editor
        )
        destination_dialog.bind("<Escape>", self._cancel_destination_editor)
        self.destination_dialog_editor = self._build_destination_editor(
            destination_dialog, show_back=False
        )
        self.destination_dialog_editor.pack(fill="both", expand=True)
        self.compact_destination_editor = self._build_destination_editor(
            self.workspace, show_back=True
        )
        self._destination_dialog = destination_dialog
        self._register_automation_widget(
            "output.choose", self.destination_dialog_editor.choose_button
        )
        self._register_automation_widget(
            "output.reset", self.destination_dialog_editor.source_radio
        )
        header_footer_dialog = ScalingCompatibleToplevel(self.root)
        header_footer_dialog.withdraw()
        header_footer_dialog.transient(self.root)
        header_footer_dialog.configure(background=COLORS["app_bg"])
        header_footer_dialog.resizable(True, True)
        header_footer_dialog.minsize(560, 520)
        header_footer_dialog.maxsize(
            720, max(520, self.root.winfo_screenheight())
        )
        header_footer_dialog.protocol(
            "WM_DELETE_WINDOW", self._cancel_header_footer_editor
        )
        header_footer_dialog.bind(
            "<Escape>", self._cancel_header_footer_editor
        )
        self.header_footer_dialog_editor = self._build_header_footer_editor(
            header_footer_dialog, show_back=False
        )
        self.header_footer_dialog_editor.pack(fill="both", expand=True)
        self.compact_header_footer_editor = self._build_header_footer_editor(
            self.workspace, show_back=True
        )
        self._header_footer_dialog = header_footer_dialog
        advanced_dialog = ScalingCompatibleToplevel(self.root)
        advanced_dialog.withdraw()
        advanced_dialog.transient(self.root)
        advanced_dialog.configure(background=COLORS["app_bg"])
        advanced_dialog.resizable(True, True)
        advanced_dialog.minsize(560, 520)
        advanced_dialog.maxsize(
            720, max(520, self.root.winfo_screenheight())
        )
        advanced_dialog.protocol(
            "WM_DELETE_WINDOW", self._cancel_advanced_editor
        )
        advanced_dialog.bind("<Escape>", self._cancel_advanced_editor)
        self.advanced_dialog_editor = self._build_advanced_editor(
            advanced_dialog, show_back=False
        )
        self.advanced_dialog_editor.pack(fill="both", expand=True)
        self.compact_advanced_editor = self._build_advanced_editor(
            self.workspace, show_back=True
        )
        self._advanced_dialog = advanced_dialog
        for action in (
            "style.toggle",
            "destination.toggle",
            "header_footer.toggle",
            "other.toggle",
            "advanced.toggle",
        ):
            self._register_automation_widget(
                action,
                (
                    self.settings_panel.rows["style"]
                    if action == "style.toggle"
                    else self.settings_panel.rows["destination"]
                    if action == "destination.toggle"
                    else self.settings_panel.rows["header_footer"]
                    if action == "header_footer.toggle"
                    else self.settings_panel.rows["other"]
                ),
            )

        self.preview_group = PreviewPanel(
            self.workspace,
            labels=self._preview_labels(),
            fonts=self.ui_fonts,
            assets=self.ui_assets,
            on_add_files=self._browse_files,
            on_refresh=self._reset_preview,
            on_previous=lambda: self._change_preview_page(-1),
            on_next=lambda: self._change_preview_page(1),
            on_zoom_out=lambda: self._change_zoom(-1),
            on_zoom_in=lambda: self._change_zoom(1),
            on_fit_page=lambda: self._set_preview_fit("page"),
            on_fit_width=lambda: self._set_preview_fit("width"),
            on_retry=self._retry_preview,
            on_copy_details=self._copy_preview_details,
            on_report=self._report_preview_error,
        )
        toolbar = self.preview_group.toolbar
        self.preview_header = self.preview_group.header
        self.active_preview_label = self.preview_group.filename_label
        self.preview_controls = toolbar
        self.refresh_preview_button = toolbar.refresh_button
        self.previous_page_button = toolbar.previous_button
        self.preview_page_label = toolbar.page_label
        self.next_page_button = toolbar.next_button
        self.zoom_out_button = toolbar.zoom_out_button
        self.zoom_label = toolbar.zoom_label
        self.zoom_in_button = toolbar.zoom_in_button
        self.fit_page_button = toolbar.fit_page_button
        self.fit_width_button = toolbar.fit_width_button
        self.preview_overflow_button = toolbar.overflow_button
        self.preview_message_frame = self.preview_group.message_frame
        self.preview_message_label = self.preview_group.message_label
        self.preview_retry_button = self.preview_group.retry_button
        self.preview_copy_button = self.preview_group.copy_button
        self.preview_report_button = self.preview_group.report_button
        self.preview_canvas = self.preview_group.canvas
        self.preview_vertical = self.preview_group.vertical_scrollbar
        self.preview_horizontal = self.preview_group.horizontal_scrollbar
        for action, widget in (
            ("preview.refresh", self.refresh_preview_button),
            ("preview.previous_page", self.previous_page_button),
            ("preview.next_page", self.next_page_button),
            ("preview.zoom_out", self.zoom_out_button),
            ("preview.zoom_in", self.zoom_in_button),
            ("preview.fit_page", self.fit_page_button),
            ("preview.fit_width", self.fit_width_button),
            ("preview.retry", self.preview_retry_button),
            ("preview.copy_details", self.preview_copy_button),
            ("preview.report", self.preview_report_button),
        ):
            self._register_automation_widget(action, widget)
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

        self.results_view = ResultsView(
            self.content_container,
            labels=self._results_labels(),
            fonts=self.ui_fonts,
            assets=self.ui_assets,
            on_clear=self._clear_results_from_ui,
            on_open=self._open_result,
            on_copy=self._copy_result_details,
            on_report=self._show_problem_report,
            on_collapsed_changed=self._on_results_collapsed_changed,
            on_details_changed=self._refresh_results_projection,
        )
        self.results_frame = self.results_view
        self._register_automation_widget(
            "results.clear", self.results_view.clear_button
        )
        self._register_automation_widget(
            "results.toggle", self.results_view.collapse_button
        )

        self._operation_controls.extend([
            self.browse_button,
            self.clear_files_button,
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

    def _on_body_canvas_configure(self, event) -> None:
        self._sync_body_window_size(event.width, event.height)

    def _sync_body_window_size(self, width: int, height: int) -> None:
        window_height = 0
        fills_viewport = self._active_compact_tab in ("files", "preview") or (
            self._active_compact_tab == "settings"
            and (
                getattr(self, "_style_editor_open", False)
                or getattr(self, "_destination_editor_open", False)
                or getattr(self, "_header_footer_editor_open", False)
                or getattr(self, "_advanced_editor_open", False)
            )
        )
        if self._layout_mode == "compact" and fills_viewport:
            window_height = max(1, height)
        elif self._layout_mode != "compact":
            window_height = max(1, height)
        self.body_canvas.itemconfigure(
            self._body_window,
            width=width,
            height=window_height,
        )

    def _sync_body_window_to_canvas(self) -> None:
        """Refresh the compact viewport after Tk settles remapped content."""
        self._sync_body_window_size(
            self.body_canvas.winfo_width(),
            self.body_canvas.winfo_height(),
        )

    def _refresh_compact_viewport(self) -> None:
        """Force Tk to project a remapped tab into an unchanged viewport."""
        viewport_width = self.body_canvas.winfo_width()
        refresh_width = viewport_width - 1 if viewport_width > 1 else 2
        self.body_canvas.itemconfigure(
            self._body_window,
            width=refresh_width,
        )
        self.body_canvas.after_idle(self._sync_body_window_to_canvas)

    def _compact_sections(self) -> dict:
        return {
            "files": self.source_group,
            "preview": self.preview_group,
            "settings": (
                getattr(self, "compact_style_editor", self.settings_panel)
                if getattr(self, "_style_editor_open", False)
                else getattr(
                    self, "compact_destination_editor", self.settings_panel
                )
                if getattr(self, "_destination_editor_open", False)
                else getattr(
                    self, "compact_header_footer_editor", self.settings_panel
                )
                if getattr(self, "_header_footer_editor_open", False)
                else getattr(
                    self, "compact_advanced_editor", self.settings_panel
                )
                if getattr(self, "_advanced_editor_open", False)
                else self.settings_panel
            ),
            "results": self.results_frame,
        }

    def _all_compact_sections(self) -> tuple:
        """Return every reusable compact panel, including inactive editors."""
        sections = [
            self.source_group,
            self.preview_group,
            self.settings_panel,
            self.results_frame,
        ]
        for name in (
            "compact_style_editor",
            "compact_destination_editor",
            "compact_header_footer_editor",
            "compact_advanced_editor",
        ):
            editor = getattr(self, name, None)
            if editor is not None:
                sections.append(editor)
        return tuple(sections)

    def _select_compact_tab(self, name: str) -> str:
        """Remember and display one compact tab without changing business state."""
        if name not in self._compact_sections():
            raise ValueError("Unknown compact tab: {0}".format(name))
        self._active_compact_tab = name
        self.compact_tabs.set_active(name)
        if self._layout_mode == "compact":
            self._show_active_compact_section(move_focus=True)
        return "break"

    def _show_active_compact_section(self, move_focus: bool = False) -> None:
        sections = self._compact_sections()
        focus = self.root.focus_get()
        all_sections = self._all_compact_sections()
        for section in all_sections:
            section.grid_forget()
        active = sections[self._active_compact_tab]
        if active is self.results_view:
            self.body_container.grid_remove()
            active.grid(row=0, column=0, sticky="nsew")
        else:
            self.results_view.grid_forget()
            self.body_container.grid(row=0, column=0, sticky="nsew")
            active.grid(row=0, column=0, sticky="nsew")
            self.workspace.rowconfigure(0, weight=1)
        self.compact_tabs.set_active(self._active_compact_tab)
        if active is not self.results_view:
            self.body_canvas.yview_moveto(0)
            self._sync_body_window_to_canvas()
        # Tk can leave a remapped grid child hidden when the canvas window
        # keeps exactly the same dimensions. Two idle stages let grid settle,
        # then make it project the new tab without resizing the root.
        if active is not self.results_view:
            self.body_canvas.after_idle(self._refresh_compact_viewport)
        focus_was_in_hidden_section = any(
            section is not active and self._is_descendant(focus, section)
            for section in all_sections
        )
        if move_focus or focus_was_in_hidden_section:
            self.compact_tabs.focus_active()

    @staticmethod
    def _is_descendant(widget, ancestor) -> bool:
        current = widget
        while current is not None:
            if current is ancestor:
                return True
            current = getattr(current, "master", None)
        return False

    def _apply_responsive_layout(self, width: int, height: int) -> None:
        """Adapt existing panes without rebuilding widgets or changing focus."""
        self._viewport_width = width
        self._viewport_height = height
        mode = responsive_mode(width)
        layout_changed = mode != self._layout_mode
        if layout_changed:
            sections = self._all_compact_sections()
            for section in sections:
                section.grid_forget()
            self.workspace_splitter.grid_remove()
            self.results_splitter.grid_remove()
            for row in range(5):
                self.workspace.rowconfigure(row, weight=0)
                self.workspace.rowconfigure(row, minsize=0)
            self.results_view.set_layout_mode(mode)
            if mode == "compact":
                self.results_view.grid_propagate(True)
                self.source_group.grid_propagate(True)
                self.settings_panel.grid_propagate(True)
                self.content_container.rowconfigure(2, minsize=0)
                self.compact_tabs.pack(
                    fill="x",
                    before=self.content_container,
                )
                self.workspace.columnconfigure(0, weight=1, minsize=0)
                self.workspace.columnconfigure(1, weight=0, minsize=0)
                self.workspace.columnconfigure(2, weight=0, minsize=0)
                self._show_active_compact_section()
            else:
                self.results_view.grid_propagate(False)
                self.source_group.grid_propagate(False)
                self.settings_panel.grid_propagate(False)
                self.source_group.configure(height=LEFT_SECTION_MIN_HEIGHT)
                self.settings_panel.configure(height=LEFT_SETTINGS_TARGET_HEIGHT)
                self.compact_tabs.pack_forget()
                self.body_container.grid(row=0, column=0, sticky="nsew")
                self.body_canvas.itemconfigure(self._body_window, height=0)
                right_minimum = self._preview_min_width(mode)
                left_minimum = min(
                    self._left_panel_width,
                    self._left_panel_max_width(mode),
                )
                self._left_panel_width = max(
                    LEFT_PANEL_MIN_WIDTH,
                    left_minimum,
                )
                self.workspace.columnconfigure(
                    0, weight=0, minsize=self._left_panel_width
                )
                self.workspace.columnconfigure(
                    1,
                    weight=0,
                    minsize=SECTION_GAP,
                )
                self.workspace.columnconfigure(
                    2, weight=1, minsize=right_minimum
                )
                self.source_group.grid(
                    row=0,
                    column=0,
                    sticky="nsew",
                )
                self.settings_panel.grid(
                    row=1,
                    column=0,
                    sticky="nsew",
                )
                self.workspace.rowconfigure(
                    0,
                    weight=1,
                    minsize=LEFT_SECTION_MIN_HEIGHT,
                )
                self.workspace.rowconfigure(
                    1,
                    weight=0,
                    minsize=LEFT_SETTINGS_TARGET_HEIGHT,
                )
                self.workspace_splitter.grid(
                    row=0,
                    column=1,
                    rowspan=2,
                    sticky="ns",
                )
                self.preview_group.grid(
                    row=0,
                    column=2,
                    rowspan=2,
                    sticky="nsew",
                )
                self.results_frame.grid(
                    row=2,
                    column=0,
                    sticky="nsew",
                )
                self._apply_results_panel_geometry(mode)
            self._layout_preview_header(mode)
            self._layout_mode = mode
            self._refresh_results_projection()
            if getattr(self, "_style_editor_open", False):
                self._show_style_editor_host()
            elif getattr(self, "_destination_editor_open", False):
                self._show_destination_editor_host()
            elif getattr(self, "_header_footer_editor_open", False):
                self._show_header_footer_editor_host()
            elif getattr(self, "_advanced_editor_open", False):
                self._show_advanced_editor_host()
            self._sync_body_window_size(
                self.body_canvas.winfo_width(),
                self.body_canvas.winfo_height(),
            )

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
                files_panel.set_layout_mode(mode)
            else:
                self.drop_canvas.configure(width=legacy_panel_width)
                self.file_canvas.configure(width=legacy_panel_width)
            self.preview_canvas.configure(height=preview_height)
            self.app_header.set_layout_mode(mode)
            self.action_bar.set_layout_mode(mode)
        if mode == "compact":
            vertical_padding = 12 if height < 640 else SPACING["lg"]
            if vertical_padding != self._compact_vertical_padding:
                self.body.configure(
                    padding=(
                        SPACING["md"],
                        vertical_padding,
                        SPACING["md"],
                        vertical_padding,
                    )
                )
                self._compact_vertical_padding = vertical_padding
        else:
            self._compact_vertical_padding = None
            self._set_left_panel_width(self._left_panel_width)
            self._set_results_panel_height(self._results_panel_height)
        self.status_label.configure(
            wraplength=max(160, width // 2),
        )

    def _start_left_panel_resize(self, event) -> str:
        if self._layout_mode == "compact":
            return "break"
        self.workspace_splitter.focus_set()
        self._left_resize_origin = (event.x_root, self._left_panel_width)
        return "break"

    def _resize_left_panel(self, event) -> str:
        if self._left_resize_origin is None or self._layout_mode == "compact":
            return "break"
        pointer_x, initial_width = self._left_resize_origin
        self._set_left_panel_width(
            initial_width + event.x_root - pointer_x
        )
        return "break"

    def _adjust_left_panel_width(self, delta: int) -> str:
        if self._layout_mode != "compact":
            self._set_left_panel_width(self._left_panel_width + delta)
        return "break"

    def _set_left_panel_width(self, width: int) -> str:
        width = max(
            LEFT_PANEL_MIN_WIDTH,
            min(self._left_panel_max_width(), int(width)),
        )
        self._left_panel_width = width
        if self._layout_mode != "compact":
            self.workspace.columnconfigure(0, minsize=width)
        return "break"

    def _preview_min_width(self, mode=None) -> int:
        current_mode = mode or self._layout_mode
        return (
            PREVIEW_MIN_WIDTH
            if current_mode == "large"
            else PREVIEW_MEDIUM_MIN_WIDTH
        )

    def _left_panel_max_width(self, mode=None) -> int:
        available = max(
            1,
            int(getattr(self, "_viewport_width", INITIAL_WINDOW_WIDTH))
            - (2 * OUTER_PADDING),
        )
        return max(
            LEFT_PANEL_MIN_WIDTH,
            available - SECTION_GAP - self._preview_min_width(mode),
        )

    def _start_results_panel_resize(self, event) -> str:
        if (
            self._layout_mode == "compact"
            or self.results_view.collapsed
        ):
            return "break"
        self.results_splitter.focus_set()
        self._results_resize_origin = (
            event.y_root,
            self._results_panel_height,
        )
        return "break"

    def _resize_results_panel(self, event) -> str:
        if (
            self._results_resize_origin is None
            or self._layout_mode == "compact"
            or self.results_view.collapsed
        ):
            return "break"
        pointer_y, initial_height = self._results_resize_origin
        self._set_results_panel_height(
            initial_height + pointer_y - event.y_root
        )
        return "break"

    def _adjust_results_panel_height(self, delta: int) -> str:
        if self._layout_mode != "compact" and not self.results_view.collapsed:
            self._set_results_panel_height(
                self._results_panel_height + delta
            )
        return "break"

    def _set_results_panel_height(self, height: int) -> str:
        available_height = max(
            RESULTS_PANEL_MIN_HEIGHT,
            int(getattr(self, "_viewport_height", 760))
            - RESULTS_PANEL_VERTICAL_RESERVE,
        )
        maximum = min(RESULTS_PANEL_MAX_HEIGHT, available_height)
        self._results_panel_height = max(
            RESULTS_PANEL_MIN_HEIGHT,
            min(maximum, int(height)),
        )
        self._apply_results_panel_geometry()
        return "break"

    def _on_results_collapsed_changed(self, _collapsed: bool) -> None:
        self._apply_results_panel_geometry()

    def _apply_results_panel_geometry(self, mode=None) -> None:
        current_mode = mode or self._layout_mode
        if current_mode == "compact":
            self.results_splitter.grid_remove()
            return
        collapsed = self.results_view.collapsed
        height = (
            RESULTS_PANEL_COLLAPSED_HEIGHT
            if collapsed
            else self._results_panel_height
        )
        self.content_container.rowconfigure(2, minsize=height, weight=0)
        self.results_view.configure(height=height)
        if collapsed:
            self.results_splitter.grid_remove()
        else:
            self.results_splitter.grid(
                row=1,
                column=0,
                sticky="ew",
            )

    def _layout_preview_header(self, mode=None) -> None:
        """Adapt the modern preview toolbar without rebuilding its widgets."""
        self.preview_group.set_layout_mode(mode or self._layout_mode or "large")

    def _build_style_editor(self, master, show_back: bool) -> StyleEditorPanel:
        return StyleEditorPanel(
            master,
            fonts=self.ui_fonts,
            style_mode_var=self._settings_draft_style_mode_var,
            theme_display_var=self._style_theme_display_var,
            css_display_var=self._style_css_display_var,
            error_var=self._style_error_var,
            on_mode_changed=self._on_style_mode_changed,
            on_theme_changed=self._select_style_theme,
            on_choose_css=self._choose_css,
            on_save=self._save_style_editor,
            on_cancel=self._cancel_style_editor,
            show_back=show_back,
        )

    def _build_destination_editor(
        self, master, show_back: bool
    ) -> DestinationEditorPanel:
        return DestinationEditorPanel(
            master,
            fonts=self.ui_fonts,
            mode_var=self._destination_mode_var,
            path_var=self._destination_path_var,
            error_var=self._destination_error_var,
            on_mode_changed=self._on_destination_mode_changed,
            on_choose_folder=self._choose_destination_folder,
            on_save=self._save_destination_editor,
            on_cancel=self._cancel_destination_editor,
            show_back=show_back,
        )

    def _build_header_footer_editor(
        self, master, show_back: bool
    ) -> HeaderFooterEditorPanel:
        return HeaderFooterEditorPanel(
            master,
            fonts=self.ui_fonts,
            field_vars=self._settings_draft_hf_vars,
            on_restore_defaults=self._restore_header_footer_defaults,
            on_save=self._save_header_footer_editor,
            on_cancel=self._cancel_header_footer_editor,
            show_back=show_back,
        )

    def _build_advanced_editor(
        self, master, show_back: bool
    ) -> AdvancedEditorPanel:
        return AdvancedEditorPanel(
            master,
            fonts=self.ui_fonts,
            render_date_var=self._settings_draft_render_date_var,
            trusted_html_var=self._settings_draft_trusted_html_var,
            error_var=self._advanced_error_var,
            on_trusted_html_changed=self._on_advanced_trusted_html_changed,
            on_save=self._save_advanced_editor,
            on_cancel=self._cancel_advanced_editor,
            show_back=show_back,
        )

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
        self.root.bind_all("<Control-r>", lambda event: self._reset_preview())
        self.root.bind_all("<Control-g>", lambda event: self._on_generate_clicked())
        self.root.bind_all("<Escape>", self._handle_escape)
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
        shortcut_keys = (
            ("shortcut_add_files", "Ctrl+O"),
            ("shortcut_refresh_preview", "Ctrl+R"),
            ("shortcut_generate", "Ctrl+G"),
            ("shortcut_zoom_in", "Ctrl++"),
            ("shortcut_zoom_out", "Ctrl+-"),
            ("shortcut_reset_zoom", "Ctrl+0"),
            ("shortcut_previous_page", "←"),
            ("shortcut_next_page", "→"),
            ("shortcut_cancel_batch", "Esc"),
        )
        self.dialogs.show_shortcuts(
            self.root,
            self._t("keyboard_shortcuts_action"),
            tuple((self._t(key), value) for key, value in shortcut_keys),
            self._t("close_action"),
        )
        return "break"

    def _handle_escape(self, _event=None) -> str:
        if getattr(self, "_style_editor_open", False):
            return self._cancel_style_editor()
        if getattr(self, "_destination_editor_open", False):
            return self._cancel_destination_editor()
        if getattr(self, "_header_footer_editor_open", False):
            return self._cancel_header_footer_editor()
        if getattr(self, "_advanced_editor_open", False):
            return self._cancel_advanced_editor()
        if self.operation == "decision":
            self._cancel_generation_decision()
            return "break"
        self._cancel_conversion()
        return "break"
