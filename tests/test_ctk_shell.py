"""Public-behavior tests for the modern desktop shell."""

import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

import customtkinter as ctk

from libremark_pdf import __version__
from libremark_pdf.desktop.ctk.app_shell import AppShell
from libremark_pdf.desktop.ctk.assets import product_logo
from libremark_pdf.desktop.ctk.responsive import (
    DebouncedLayoutController,
    resolve_layout_mode,
)
from libremark_pdf.desktop.ctk.theme import COLORS, SystemFontResolver
from libremark_pdf.desktop.ctk.widgets.action_bar import ActionBar
from libremark_pdf.desktop.ctk.widgets.app_header import AppHeader, WindowChrome
from libremark_pdf.desktop.ctk.widgets.preview_panel import PreviewPanel
from libremark_pdf.desktop.ctk.widgets import results_view as ctk_results
from libremark_pdf.desktop.tk import app as tk_app
from libremark_pdf.desktop.tk import layout as tk_layout


class ScheduledRoot:
    def __init__(self):
        self.callbacks = {}
        self.cancelled = []
        self.next_id = 0

    def after(self, delay, callback):
        self.next_id += 1
        identifier = "after-{0}".format(self.next_id)
        self.callbacks[identifier] = (delay, callback)
        return identifier

    def after_cancel(self, identifier):
        self.cancelled.append(identifier)
        self.callbacks.pop(identifier, None)


class TestResponsiveShellContract(unittest.TestCase):
    def test_breakpoints_and_resize_debounce_apply_only_the_latest_size(self):
        self.assertEqual(resolve_layout_mode(759), "compact")
        self.assertEqual(resolve_layout_mode(760), "medium")
        self.assertEqual(resolve_layout_mode(1099), "medium")
        self.assertEqual(resolve_layout_mode(1100), "large")

        root = ScheduledRoot()
        applied = []
        controller = DebouncedLayoutController(
            root,
            lambda width, height: applied.append((width, height)),
        )
        controller.schedule(1099, 700)
        first = "after-1"
        controller.schedule(1100, 701)

        self.assertEqual(root.cancelled, [first])
        self.assertEqual(applied, [])
        delay, callback = root.callbacks["after-2"]
        self.assertEqual(delay, 100)
        callback()
        self.assertEqual(applied, [(1100, 701)])
        self.assertFalse(controller.pending)

    def test_cancelled_resize_never_applies_layout(self):
        root = ScheduledRoot()
        applied = mock.Mock()
        controller = DebouncedLayoutController(root, applied)
        controller.schedule(820, 780)
        controller.cancel()
        self.assertEqual(root.callbacks, {})
        applied.assert_not_called()

    def test_unchanged_window_size_does_not_repeat_layout_after_a_move(self):
        root = ScheduledRoot()
        applied = mock.Mock()
        controller = DebouncedLayoutController(root, applied)
        controller.schedule(820, 780)
        _delay, callback = root.callbacks.pop("after-1")
        callback()

        controller.schedule(820, 780)

        applied.assert_called_once_with(820, 780)
        self.assertEqual(root.callbacks, {})


class TestWindowChromeContract(unittest.TestCase):
    def test_compact_menu_is_clamped_to_the_current_monitor_work_area(self):
        header = AppHeader.__new__(AppHeader)
        header.window_chrome = mock.Mock()
        header.window_chrome._work_area.return_value = (-1920, 0, 1920, 1040)
        button = mock.Mock()
        button.winfo_rootx.return_value = -100
        button.winfo_rooty.return_value = 40
        button.winfo_height.return_value = 36
        button.tooltip = mock.Mock()
        menu = mock.Mock()
        menu.winfo_reqwidth.return_value = 300
        menu.winfo_reqheight.return_value = 180

        header._post_menu(button, menu)

        menu.tk_popup.assert_called_once_with(-300, 76)
        menu.grab_release.assert_called_once_with()
        button.tooltip.hide.assert_called_once_with()

    def test_taskbar_registration_refreshes_the_borderless_window_once(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome._taskbar_registered = False

        chrome._schedule_windows_taskbar_refresh()
        chrome._schedule_windows_taskbar_refresh()

        chrome.root.withdraw.assert_called_once_with()
        chrome.root.after.assert_called_once_with(
            10,
            chrome._restore_windows_taskbar_window,
        )

    def test_taskbar_style_is_reapplied_after_the_native_window_is_restored(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome._raise_resize_surfaces = mock.Mock()
        chrome._configure_windows_taskbar = mock.Mock()

        chrome._restore_windows_taskbar_window()

        chrome.root.deiconify.assert_called_once_with()
        chrome.root.after_idle.assert_called_once_with(
            chrome._configure_windows_taskbar
        )

    def test_resize_updates_are_frame_limited_and_rebased(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome.root.minsize.return_value = (560, 520)
        chrome.root.after.return_value = "resize-after"
        chrome._resize_origin = ("e", 100, 100, 700, 600, 20, 30)
        chrome._pending_resize_geometry = None
        chrome._resize_after_id = None
        first = mock.Mock(x_root=110, y_root=100)
        second = mock.Mock(x_root=114, y_root=100)

        chrome._resize(first)
        chrome._resize(second)

        self.assertEqual(
            chrome._pending_resize_geometry,
            (714, 600, 20, 30),
        )
        chrome.root.after.assert_called_once_with(
            16,
            chrome._apply_pending_resize,
        )

    def test_maximize_uses_the_work_area_for_the_current_monitor(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome.root.winfo_width.return_value = 900
        chrome.root.winfo_height.return_value = 700
        chrome.root.winfo_x.return_value = 2100
        chrome.root.winfo_y.return_value = 80
        chrome._work_area = mock.Mock(return_value=(1920, 0, 1920, 1040))
        chrome._update_maximize_glyph = mock.Mock()

        chrome.maximize()

        chrome.root.geometry.assert_called_once_with("1920x1040+1920+0")
        self.assertEqual(chrome._normal_geometry, (900, 700, 2100, 80))
        self.assertTrue(chrome._maximized)

    def test_absolute_window_rectangle_preserves_negative_monitor_coordinates(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome._move_window_on_windows = mock.Mock(return_value=True)

        chrome._set_window_rectangle(900, 700, -1920, 40)

        chrome._move_window_on_windows.assert_called_once_with(
            900,
            700,
            -1920,
            40,
        )
        chrome.root.geometry.assert_not_called()

    def test_double_click_restore_does_not_start_a_maximized_drag(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome.root.winfo_x.return_value = 1920
        chrome.root.winfo_width.return_value = 1920
        chrome._maximized = True
        chrome._maximized_drag_ratio = None
        chrome._drag_origin = None
        chrome.restore = mock.Mock()
        event = mock.Mock(x_root=2500, y_root=20)

        chrome._start_drag(event)

        chrome.restore.assert_not_called()
        self.assertAlmostEqual(
            chrome._maximized_drag_ratio,
            (2500 - 1920) / 1920,
        )
        chrome.toggle_maximize()
        chrome.restore.assert_called_once_with()

    def test_drag_from_maximized_uses_coordinates_local_to_current_monitor(self):
        chrome = WindowChrome.__new__(WindowChrome)
        chrome.root = mock.Mock()
        chrome.root.winfo_x.return_value = 1920
        chrome.root.winfo_width.return_value = 1920
        chrome._maximized = True
        chrome._normal_geometry = (900, 700, 2100, 80)
        chrome._maximized_drag_ratio = None
        chrome._drag_origin = None
        chrome._work_area = mock.Mock(return_value=(1920, 0, 1920, 1040))
        chrome._set_window_rectangle = mock.Mock()
        chrome._update_maximize_glyph = mock.Mock()

        chrome._start_drag(mock.Mock(x_root=2500, y_root=20))
        chrome._drag(mock.Mock(x_root=2520, y_root=40))

        self.assertFalse(chrome._maximized)
        self.assertEqual(
            chrome._set_window_rectangle.call_args_list,
            [
                mock.call(900, 700, 2100, 80),
                mock.call(900, 700, 2248, 12),
            ],
        )


class TestModernShellWidgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Tk is unavailable: {0}".format(exc))

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            for identifier in cls.root.tk.call("after", "info"):
                cls.root.after_cancel(identifier)
            cls.root.destroy()

    def setUp(self):
        self.root.geometry("1180x760+0+0")
        self.fonts = SystemFontResolver(self.root)

    def tearDown(self):
        for identifier in self.root.tk.call("after", "info"):
            self.root.after_cancel(identifier)
        self.root.unbind("<Configure>")
        for child in self.root.winfo_children():
            child.destroy()
        for identifier in self.root.tk.call("after", "info"):
            self.root.after_cancel(identifier)

    def test_action_bar_is_fixed_and_primary_button_is_geometrically_centered(self):
        shell = AppShell(self.root)
        shell.pack(fill="both", expand=True)
        action_bar = ActionBar(
            shell,
            fonts=self.fonts,
            on_generate=lambda: None,
            on_cancel=lambda: None,
            progress_variable=tk.IntVar(master=self.root, value=0),
            generate_icon=None,
        )
        shell.attach_action_bar(action_bar)

        for width in (1100, 1280, 1440, 1600):
            with self.subTest(width=width):
                self.root.geometry("{0}x760+0+0".format(width))
                self.root.update()
                self.assertLessEqual(abs(action_bar.button_center_error()), 16)
        self.assertIs(action_bar.master, shell)
        self.assertEqual(action_bar.cancel_button.winfo_manager(), "")

    def test_action_bar_presents_running_details_and_inline_decision(self):
        shell = AppShell(self.root)
        shell.pack(fill="both", expand=True)
        progress = tk.IntVar(master=self.root, value=0)
        action_bar = ActionBar(
            shell,
            fonts=self.fonts,
            on_generate=lambda: None,
            on_cancel=lambda: None,
            progress_variable=progress,
            generate_icon=None,
        )
        shell.attach_action_bar(action_bar)
        action_bar.set_state(
            "running",
            status_text="Converting 2 of 4 — two.md",
            generate_text="Generate 4 PDFs",
            generate_enabled=False,
            progress_current=1,
            progress_total=4,
            progress_text="25%",
            cancel_text="Stop after this file",
            cancel_enabled=True,
            cancel_now_text="Cancel now",
            cancel_now_enabled=True,
            batch_text="4 files in progress · Destination: sources",
            active_text="Converting 2 of 4 — two.md",
            options_text="Applied options ⓘ",
            options_summary="Style: Default\nDestination: sources",
        )
        self.root.update()
        self.assertEqual(action_bar.batch_label.winfo_manager(), "grid")
        self.assertEqual(action_bar.active_label.winfo_manager(), "grid")
        self.assertEqual(action_bar.cancel_now_button.winfo_manager(), "grid")
        self.assertEqual(action_bar.options_tooltip.text, "Style: Default\nDestination: sources")
        self.assertIsInstance(action_bar.options_button, ctk.CTkLabel)
        self.assertEqual(action_bar._toggle_options_popover(), "break")
        self.root.update()
        self.assertIsNotNone(action_bar._options_popover)
        self.assertEqual(action_bar._toggle_options_popover(), "break")
        self.assertIsNone(action_bar._options_popover)

        action_bar.set_state(
            "decision_required",
            status_text="",
            generate_text="Generate 4 PDFs",
            generate_enabled=False,
            decision_title="A decision is required",
            decision_message="Existing outputs were found.",
            decision_rows=(
                ("folder/one.md", "output/one.pdf", "Existing PDF", True),
                ("other/two.md", "output/two.pdf", "Conflict", False),
            ),
            decision_has_existing=True,
            decision_instruction="Check PDFs to replace. Others will be kept.",
            decision_source_heading="Source",
            decision_destination_heading="Destination",
            decision_issue_heading="Issue",
            decision_replace_heading="Replace?",
            decision_blocked_text="Blocked",
            decision_replace_help="Checked replaces; unchecked keeps.",
            decision_blocked_help="This destination is blocked.",
            decision_replaced_one="{count} will be replaced",
            decision_replaced_many="{count} will be replaced",
            decision_kept_one="{count} kept",
            decision_kept_many="{count} kept",
            continue_text="Continue",
            back_text="Back",
        )
        self.root.update()
        self.assertEqual(action_bar.decision_title.winfo_manager(), "grid")
        self.assertEqual(action_bar.decision_header_frame.winfo_manager(), "grid")
        self.assertEqual(action_bar.decision_back_button.winfo_manager(), "grid")
        self.assertEqual(action_bar.decision_table.winfo_manager(), "grid")
        item = action_bar.decision_table.get_children()[0]
        replace_box = action_bar.decision_table.bbox(item, "replace")
        self.assertTrue(replace_box)
        self.assertLessEqual(
            replace_box[0] + replace_box[2],
            action_bar.decision_table.winfo_width(),
        )
        header_event = mock.Mock(
            x=replace_box[0] + replace_box[2] // 2,
            y=2,
        )
        with mock.patch.object(action_bar, "_toggle_decision_item") as toggle:
            self.assertIsNone(action_bar._on_decision_click(header_event))
        toggle.assert_not_called()
        self.assertEqual(
            action_bar.decision_table.item(item, "values"),
            ("folder / one.md", "output / one.pdf", "Existing PDF", "☐"),
        )
        self.assertEqual(action_bar.decision_continue_button.cget("text"), "Continue")
        action_bar.decision_table.focus(item)
        self.assertEqual(action_bar._toggle_focused_decision(), "break")
        self.assertEqual(action_bar.selected_overwrite_targets(), ("output/one.pdf",))
        self.assertEqual(action_bar.decision_table.item(item, "values")[3], "☑")
        self.assertEqual(
            action_bar.decision_selection_summary.cget("text"),
            "1 will be replaced · 0 kept",
        )
        blocked = action_bar.decision_table.get_children()[1]
        self.assertEqual(
            action_bar.decision_table.item(blocked, "values")[3], "Blocked"
        )
        self.assertEqual(action_bar._toggle_all_decisions(), "break")
        self.assertEqual(action_bar.selected_overwrite_targets(), ())
        self.assertTrue(
            action_bar.decision_table.heading("replace", "text").startswith("☐")
        )
        self.assertEqual(action_bar.generate_button.winfo_manager(), "")
        self.assertEqual(action_bar.progress.winfo_manager(), "")
        action_bar.set_conversion_active(True)
        self.assertEqual(action_bar.generate_button.winfo_manager(), "")
        self.assertEqual(action_bar.cancel_button.winfo_manager(), "grid")
        self.assertEqual(action_bar.progress.winfo_manager(), "grid")

    def test_decision_table_scrolls_itself_only_with_focus(self):
        shell = AppShell(self.root)
        shell.pack(fill="both", expand=True)
        outside_scroll = mock.Mock()
        action_bar = ActionBar(
            shell,
            fonts=self.fonts,
            on_generate=lambda: None,
            on_cancel=lambda: None,
            progress_variable=tk.IntVar(master=self.root, value=0),
            generate_icon=None,
            on_scroll_outside=outside_scroll,
        )
        shell.attach_action_bar(action_bar)
        rows = tuple(
            (
                "source/{0}.md".format(index),
                "output/{0}.pdf".format(index),
                "Conflict",
                False,
            )
            for index in range(7)
        )
        action_bar.set_state(
            "decision_required",
            status_text="",
            generate_text="Generate",
            generate_enabled=False,
            decision_rows=rows,
            decision_source_heading="Source",
            decision_destination_heading="Destination",
            decision_issue_heading="Issue",
            decision_replace_heading="Replace?",
            decision_blocked_text="Blocked",
        )
        action_bar.decision_table.configure(height=2)
        action_bar.decision_table_frame.configure(height=80)
        action_bar.decision_table_frame.grid_propagate(False)
        self.root.update()
        wheel = mock.Mock(delta=-120, num=0)
        action_bar.status_label.focus_force()
        self.root.update()
        self.assertEqual(action_bar._on_decision_mousewheel(wheel), "break")
        outside_scroll.assert_called_once_with(wheel)

        action_bar.decision_table.focus_force()
        self.root.update()
        before = action_bar.decision_table.yview()
        self.assertEqual(action_bar._on_decision_mousewheel(wheel), "break")
        self.assertNotEqual(action_bar.decision_table.yview(), before)
        outside_scroll.assert_called_once_with(wheel)

    def test_action_bar_projects_validation_progress_cancel_and_terminal_states(self):
        shell = AppShell(self.root)
        shell.pack(fill="both", expand=True)
        progress = tk.IntVar(master=self.root, value=0)
        action_bar = ActionBar(
            shell,
            fonts=self.fonts,
            on_generate=lambda: None,
            on_cancel=lambda: None,
            progress_variable=progress,
            generate_icon=None,
        )
        shell.attach_action_bar(action_bar)

        action_bar.set_state(
            "validating",
            status_text="… Validating outputs…",
            generate_text="Generate 2 PDFs",
            generate_enabled=False,
            disabled_reason="Outputs are being checked.",
        )
        self.root.update()
        self.assertEqual(action_bar.state, "validating")
        self.assertEqual(action_bar.progress.winfo_manager(), "grid")
        self.assertEqual(str(action_bar.progress.cget("mode")), "indeterminate")
        self.assertEqual(action_bar.generate_button.cget("state"), "disabled")

        action_bar.set_state(
            "running",
            status_text="→ Converting 2 of 4 — two.md",
            generate_text="Generate 4 PDFs",
            generate_enabled=False,
            progress_current=1,
            progress_total=4,
            progress_text="25%",
            cancel_text="Stop after this file",
            cancel_enabled=True,
        )
        self.root.update()
        self.assertEqual(progress.get(), 25)
        self.assertEqual(action_bar.progress_percent, 25)
        self.assertEqual(action_bar.cancel_button.winfo_manager(), "grid")
        self.assertEqual(action_bar.generate_button.winfo_manager(), "")

        action_bar.set_state(
            "cancel_requested",
            status_text="! Stop requested — two.md may finish.",
            generate_text="Generate 4 PDFs",
            generate_enabled=False,
            progress_current=1,
            progress_total=4,
            progress_text="25%",
            cancel_text="Stop after this file",
            cancel_enabled=False,
        )
        self.assertEqual(progress.get(), 25)
        self.assertEqual(action_bar.cancel_button.cget("state"), "disabled")
        self.assertIn("may finish", action_bar.status_label.accessible_name)

        action_bar.set_state(
            "complete",
            status_text="✓ 4 succeeded",
            generate_text="Generate 4 PDFs",
            generate_enabled=True,
        )
        self.assertEqual(action_bar.progress.winfo_manager(), "")
        self.assertEqual(action_bar.cancel_button.winfo_manager(), "")

    def test_header_uses_real_version_native_menus_and_immediate_language(self):
        calls = []
        shell = AppShell(self.root)
        shell.pack(fill="both", expand=True)
        header = AppHeader(
            shell,
            root=self.root,
            logo=product_logo(32),
            version=__version__,
            language="en",
            fonts=self.fonts,
            on_shortcuts=lambda: calls.append("shortcuts"),
            on_manual=lambda: calls.append("manual"),
            on_report=lambda: calls.append("report"),
            on_about=lambda: calls.append("about"),
            on_language=lambda language: calls.append(language),
        )
        shell.attach_header(header)
        labels = {
            "app_title": "LibreMark PDF",
            "app_version_compact": "v{version}",
            "help_menu": "Help",
            "keyboard_shortcuts_action": "Keyboard shortcuts",
            "manual_action": "User manual",
            "report_issue_action": "Report a problem",
            "about_action": "About LibreMark PDF",
            "language_menu": "Language",
            "compact_menu_a11y": "Application menu",
            "language_english_name": "English",
            "language_french_name": "French",
            "window_minimize_a11y": "Minimize window",
            "window_maximize_a11y": "Maximize window",
            "window_restore_a11y": "Restore window",
            "window_close_a11y": "Close window",
        }
        header.retranslate(labels, __version__, "en")
        self.root.update()

        self.assertEqual(
            header.version_button.cget("text"),
            "v{0}".format(__version__),
        )
        self.assertIsInstance(header.help_menu, tk.Menu)
        self.assertIsInstance(header.language_menu, tk.Menu)
        self.assertEqual(
            str(header.help_menu.cget("background")), COLORS["surface"]
        )
        self.assertEqual(
            str(header.help_menu.cget("activebackground")),
            COLORS["primary_subtle"],
        )
        self.assertEqual(header.language_menu.entrycget(0, "label"), "French")
        self.assertEqual(header.minimize_button.tooltip.text, "Minimize window")
        self.assertEqual(header.maximize_button.tooltip.text, "Maximize window")
        self.assertEqual(header.close_button.tooltip.text, "Close window")
        header.window_chrome._maximized = True
        header.window_chrome._update_maximize_glyph()
        self.assertEqual(header.maximize_button.tooltip.text, "Restore window")
        header.help_menu.invoke(0)
        header.help_menu.invoke(1)
        header.help_menu.invoke(2)
        header.help_menu.invoke(4)
        header.language_menu.invoke(0)
        self.assertEqual(
            calls,
            ["shortcuts", "manual", "report", "about", "fr"],
        )
        self.assertEqual(
            tk.Frame.cget(header.help_button, "takefocus"),
            "1",
        )
        header.set_layout_mode("compact")
        self.assertEqual(header.help_button.winfo_manager(), "")
        self.assertEqual(header.language_button.winfo_manager(), "")
        self.assertEqual(header.version_button.winfo_manager(), "")
        self.assertEqual(header.compact_menu_button.winfo_manager(), "grid")
        self.assertEqual(
            int(header.compact_menu_button.grid_info()["column"]),
            int(header.minimize_button.grid_info()["column"]) - 1,
        )
        self.assertEqual(header.compact_menu.type(0), "command")
        self.assertEqual(header.compact_menu.type(2), "cascade")
        self.assertEqual(header.compact_menu.type(4), "separator")
        self.assertEqual(header.compact_menu.index("end"), 5)
        header.compact_menu.invoke(0)
        header.compact_menu.invoke(1)
        header.compact_menu.invoke(3)
        header.compact_menu.invoke(5)
        self.assertEqual(calls[-4:], ["manual", "shortcuts", "report", "about"])

        french = dict(labels)
        french.update({
            "help_menu": "Aide",
            "keyboard_shortcuts_action": "Raccourcis clavier",
            "manual_action": "Manuel utilisateur",
            "report_issue_action": "Signaler un problème",
            "about_action": "À propos de LibreMark PDF",
            "language_english_name": "Anglais",
            "language_french_name": "Français",
            "window_minimize_a11y": "Réduire la fenêtre",
            "window_maximize_a11y": "Agrandir la fenêtre",
            "window_restore_a11y": "Restaurer la fenêtre",
            "window_close_a11y": "Fermer la fenêtre",
        })
        header.retranslate(french, __version__, "fr")
        self.assertEqual(header.active_language, "fr")
        self.assertEqual(header.help_menu.entrycget(1, "label"), "Manuel utilisateur")
        self.assertEqual(header.language_button.cget("text"), "Français ▾")
        self.assertEqual(
            header.language_menu.entrycget(1, "label"), "Anglais"
        )
        self.assertEqual(header.maximize_button.tooltip.text, "Restaurer la fenêtre")

    def test_layout_only_resize_preserves_state_and_calls_no_business_service(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        services.reset_mock()
        application.files = [Path("one.md"), Path("two.md")]
        application.active_file = application.files[1]
        application.css_path = "print.css"
        application.output_dir = "exports"

        self.root.geometry("820x780+0+0")
        application._responsive_controller.schedule(820, 780)
        application._responsive_controller.flush()
        self.root.update()
        self.assertEqual(
            application.workspace.grid_bbox(0, 0)[2],
            application._left_panel_width,
        )
        application._responsive_controller.schedule(560, 520)
        application._responsive_controller.flush()
        self.root.geometry("560x520+0+0")
        self.root.update()
        self.assertEqual(application.body_scroll.winfo_manager(), "")
        application._responsive_controller.schedule(1440, 900)
        application._responsive_controller.flush()
        self.root.geometry("1440x900+0+0")
        self.root.update()

        self.assertEqual(application.files, [Path("one.md"), Path("two.md")])
        self.assertEqual(application.active_file, Path("two.md"))
        self.assertEqual(application.css_path, "print.css")
        self.assertEqual(application.output_dir, "exports")
        self.assertEqual(application._layout_mode, "large")
        self.assertEqual(application.workspace.grid_bbox(0, 0)[2], 390)
        self.assertEqual(application.body_scroll.winfo_manager(), "")
        self.assertEqual(
            application.workspace_splitter.winfo_manager(),
            "grid",
        )
        application._set_left_panel_width(440)
        self.root.update()
        self.assertEqual(application.workspace.grid_bbox(0, 0)[2], 440)
        application._set_left_panel_width(999)
        self.assertEqual(
            application._left_panel_width,
            application._left_panel_max_width(),
        )
        self.assertGreater(application._left_panel_width, 440)
        application._set_left_panel_width(1)
        self.assertEqual(application._left_panel_width, 360)
        application._render_file_list()
        self.root.update()
        populated_width = application.workspace.grid_bbox(0, 0)[2]
        application._clear_files()
        self.root.update()
        empty_width = application.workspace.grid_bbox(0, 0)[2]
        self.assertEqual((populated_width, empty_width), (360, 360))
        services.run_preview_worker.assert_not_called()
        services.run_conversion_job.assert_not_called()
        services.open_path.assert_not_called()

    def test_compact_tabs_reuse_panels_retranslate_and_keep_action_visible(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        panels = {
            "files": application.source_group,
            "preview": application.preview_group,
            "settings": application.settings_panel,
            "results": application.results_frame,
        }
        identities = {name: id(panel) for name, panel in panels.items()}
        application._preview_page = 3
        application.zoom_percent.set(150)
        application.files = [Path("one.md"), Path("two.md")]
        application.active_file = Path("two.md")
        application._render_file_list()

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()

        self.assertEqual(application.compact_tabs.winfo_manager(), "pack")
        self.assertEqual(application.compact_tabs.active, "files")
        self.assertEqual(
            [name for name, panel in panels.items() if panel.winfo_manager()],
            ["files"],
        )
        self.assertGreaterEqual(
            application.generate_button.winfo_width(),
            application.action_bar.winfo_width() - 40,
        )
        application.compact_tabs.buttons["preview"].invoke()
        self.root.update()
        self.assertEqual(application._active_compact_tab, "preview")
        self.assertEqual(
            [name for name, panel in panels.items() if panel.winfo_manager()],
            ["preview"],
        )
        self.assertEqual(application._preview_page, 3)
        self.assertEqual(application.zoom_percent.get(), 150)
        self.assertGreaterEqual(application.preview_canvas.winfo_height(), 180)
        self.assertEqual(application.body_scroll.winfo_manager(), "")

        application.operation = "generate"
        application._apply_responsive_layout(720, 640)
        self.assertEqual(application._active_compact_tab, "preview")
        application.lang = "fr"
        application._retranslate()
        self.assertEqual(
            [
                application.compact_tabs.buttons[name].cget("text")
                for name in application.compact_tabs.TAB_NAMES
            ],
            ["Fichiers", "Aperçu", "Réglages", "Résultats"],
        )

        self.root.geometry("1180x760+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        self.assertEqual(application.compact_tabs.winfo_manager(), "")
        self.assertEqual(
            {name: id(panel) for name, panel in panels.items()},
            identities,
        )
        self.assertEqual(application._active_compact_tab, "preview")
        self.assertEqual(application._preview_page, 3)
        self.assertEqual(application.zoom_percent.get(), 150)

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        application.compact_tabs.buttons["files"].invoke()
        self.root.update()
        self.root.after(20, self.root.quit)
        self.root.mainloop()

        self.assertEqual(application._active_compact_tab, "files")
        self.assertEqual(application.source_group.winfo_manager(), "grid")
        self.assertTrue(application.source_group.winfo_ismapped())
        self.assertGreater(application.source_group.winfo_height(), 100)
        self.assertEqual(
            application.files_panel.list_view.winfo_manager(),
            "canvas",
        )
        self.assertTrue(application.files_panel.list_view.winfo_ismapped())
        self.assertGreater(application.files_panel.list_view.winfo_height(), 100)

    def test_running_action_state_survives_resize_and_hot_translation(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        application.files = [Path("one.md"), Path("two.md")]
        application._cancel_event.clear()
        application.operation = "generate"
        application._set_action_state(
            "running",
            progress_current=1,
            progress_total=2,
            active_name="two.md",
        )
        application._set_status(
            "status_generating_file",
            current=2,
            total=2,
            name="two.md",
        )

        for width, height in ((720, 640), (560, 520), (1440, 900)):
            with self.subTest(size=(width, height)):
                self.root.geometry("{0}x{1}+0+0".format(width, height))
                self.root.update()
                application._responsive_controller.flush()
                self.root.update()
                self.assertEqual(application.action_bar.state, "running")
                self.assertEqual(application.action_bar.progress_percent, 50)
                self.assertEqual(
                    application.cancel_button.cget("state"), "normal"
                )

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        application.compact_tabs.buttons["preview"].invoke()
        self.root.update()
        self.assertEqual(application.preview_group.winfo_manager(), "grid")
        self.assertEqual(application.action_bar.winfo_manager(), "grid")

        application.lang = "fr"
        application._retranslate()
        self.root.update()
        self.assertEqual(
            application.cancel_button.cget("text"),
            "Arrêter après ce fichier",
        )
        self.assertIn("Conversion 2 sur 2", application.status_label.cget("text"))
        services.run_conversion_job.assert_not_called()

    def test_preview_panel_toolbar_states_translation_and_compact_overflow(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        self.root.update()
        panel = application.preview_group
        toolbar = panel.toolbar
        self.assertIsInstance(panel, PreviewPanel)
        self.assertEqual(
            toolbar.ordered_controls,
            (
                application.refresh_preview_button,
                application.previous_page_button,
                application.preview_page_label,
                application.next_page_button,
                application.zoom_out_button,
                application.zoom_label,
                application.zoom_in_button,
                application.fit_page_button,
                application.fit_width_button,
            ),
        )
        self.assertEqual(application.fit_page_button.winfo_manager(), "grid")
        self.assertEqual(application.preview_overflow_button.winfo_manager(), "")
        self.assertEqual(
            application.preview_canvas.accessible_name,
            "Document preview",
        )
        self.assertEqual(
            application.refresh_preview_button.accessible_name,
            "Reset preview and fit page",
        )
        self.assertGreaterEqual(
            toolbar.winfo_width(), panel.winfo_width() - 32
        )
        self.assertGreater(
            application.preview_page_label.winfo_width(),
            int(application.preview_page_label.cget("width")),
        )
        self.assertLessEqual(
            application.refresh_preview_button.winfo_rootx()
            - toolbar.winfo_rootx(),
            12,
        )
        self.assertLessEqual(
            toolbar.winfo_rootx()
            + toolbar.winfo_width()
            - application.fit_width_button.winfo_rootx()
            - application.fit_width_button.winfo_width(),
            12,
        )

        for state in ("scheduled", "rendering"):
            with self.subTest(state=state):
                application._set_preview_state(state)
                self.root.update()
                self.assertEqual(panel.state_badge.winfo_manager(), "grid")
                self.assertEqual(panel.message_frame.winfo_manager(), "")
                filename_right = (
                    panel.filename_label.winfo_rootx()
                    + panel.filename_label.winfo_width()
                )
                self.assertLessEqual(
                    panel.state_badge.winfo_rootx() - filename_right,
                    12,
                )
                self.assertLessEqual(
                    abs(
                        panel.state_badge.winfo_rooty()
                        + panel.state_badge.winfo_height() // 2
                        - panel.filename_label.winfo_rooty()
                        - panel.filename_label.winfo_height() // 2
                    ),
                    2,
                )
        application._set_preview_state("ready")
        self.root.update()
        self.assertEqual(panel.state_badge.winfo_manager(), "")
        self.assertEqual(panel.message_frame.winfo_manager(), "")

        application._set_preview_state("error", "preview failed")
        self.root.update()
        self.assertEqual(panel.retry_button.winfo_manager(), "grid")
        self.assertEqual(panel.copy_button.winfo_manager(), "grid")
        self.assertEqual(panel.report_button.winfo_manager(), "grid")
        self.assertIn("preview failed", panel.message_label.cget("text"))
        application._set_preview_state("unavailable", "renderer missing")
        self.root.update()
        self.assertEqual(panel.retry_button.winfo_manager(), "grid")
        application._set_preview_state("empty")
        self.root.update()
        self.assertEqual(panel.add_files_button.winfo_manager(), "")
        self.assertEqual(panel.message_label.cget("text"), "")
        self.assertEqual(panel.message_frame.winfo_manager(), "")

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        application._select_compact_tab("preview")
        self.root.update()
        self.assertEqual(application.fit_page_button.winfo_manager(), "")
        self.assertEqual(
            application.preview_overflow_button.winfo_manager(), "grid"
        )
        self.assertEqual(panel.add_files_button.winfo_manager(), "grid")
        self.assertGreaterEqual(application.preview_canvas.winfo_height(), 180)

        application.lang = "fr"
        application._retranslate()
        self.root.update()
        self.assertEqual(application.fit_page_button.cget("text"), "Ajuster à la page")
        self.assertEqual(
            application.preview_overflow_button.accessible_name,
            "Autres actions d’aperçu",
        )
        self.assertEqual(
            application.refresh_preview_button.accessible_name,
            "Réinitialiser l’aperçu et ajuster à la page",
        )
        services.run_conversion_job.assert_not_called()

    def test_compact_conversion_controls_remain_fixed_at_short_height(self):
        shell = AppShell(self.root)
        shell.pack(fill="both", expand=True)
        action_bar = ActionBar(
            shell,
            fonts=self.fonts,
            on_generate=lambda: None,
            on_cancel=lambda: None,
            progress_variable=tk.IntVar(master=self.root, value=1),
            generate_icon=None,
        )
        shell.attach_action_bar(action_bar)
        action_bar.set_conversion_active(True)
        action_bar.set_layout_mode("compact")
        self.root.geometry("560x520+0+0")
        self.root.update()

        self.assertEqual(action_bar.winfo_manager(), "grid")
        self.assertEqual(action_bar.generate_button.winfo_manager(), "")
        self.assertEqual(action_bar.cancel_button.winfo_manager(), "grid")
        self.assertEqual(action_bar.progress.winfo_manager(), "grid")
        self.assertLessEqual(
            action_bar.winfo_rooty() + action_bar.winfo_height(),
            self.root.winfo_rooty() + self.root.winfo_height(),
        )

    def test_only_dedicated_settings_editors_are_reachable(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        self.root.update()

        self.assertFalse(hasattr(application, "_settings_dialog"))
        self.assertFalse(hasattr(application, "_open_settings_editor"))
        self.assertFalse(hasattr(application.settings_panel, "edit_button"))
        self.assertEqual(
            set(application.settings_panel.rows),
            {"style", "destination", "header_footer", "other"},
        )
        titled_dialogs = (
            (application._style_dialog, "PDF style"),
            (application._destination_dialog, "Destination"),
            (application._header_footer_dialog, "Headers and footers"),
            (application._advanced_dialog, "Advanced options"),
        )
        for dialog, expected_title in titled_dialogs:
            self.assertEqual(dialog.state(), "withdrawn")
            self.assertEqual(dialog.title(), expected_title)
        self.assertEqual(
            application.status_label.cget("text"),
            "Add at least one Markdown file to generate a PDF.",
        )
        self.assertEqual(application.action_bar.reason_label.cget("text"), "")
        application._open_style_editor()
        self.root.update()
        application._cancel_style_editor()
        self.root.update()

    def test_style_editor_retranslates_preserves_draft_and_moves_to_compact(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        original_theme = application.theme_var.get()
        original_preview = application._capture_preview_snapshot()

        application._open_style_editor()
        self.root.update()
        self.assertTrue(application._style_dialog.winfo_viewable())
        self.assertIs(
            application._style_dialog.grab_current(),
            application._style_dialog,
        )
        self.assertTrue(
            application.style_dialog_editor.theme_radio.cget("takefocus")
        )
        application._settings_draft_theme_var.set("remembered@1")
        application.lang = "fr"
        application._retranslate()
        self.root.update()
        self.assertEqual(
            application._settings_draft_theme_var.get(), "remembered@1"
        )
        self.assertEqual(
            application.style_dialog_editor.save_button.cget("text"),
            "Enregistrer",
        )
        self.assertEqual(application.theme_var.get(), original_theme)

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        self.assertFalse(application._style_dialog.winfo_viewable())
        self.assertEqual(application._active_compact_tab, "settings")
        self.assertEqual(
            application.compact_style_editor.winfo_manager(), "grid"
        )
        self.assertLessEqual(
            application.compact_style_editor.winfo_width(),
            application.root.winfo_width(),
        )
        self.assertEqual(
            application.compact_style_editor.save_button.winfo_manager(),
            "grid",
        )
        self.assertEqual(application.body_scroll.winfo_manager(), "")
        self.assertLessEqual(
            application.compact_style_editor.actions.winfo_rooty()
            + application.compact_style_editor.actions.winfo_height(),
            application.action_bar.winfo_rooty(),
        )

        application.compact_style_editor.back_button.invoke()
        self.root.update()
        self.assertFalse(application._style_editor_open)
        self.assertEqual(application.theme_var.get(), original_theme)
        self.assertEqual(
            application._capture_preview_snapshot(), original_preview
        )

    def test_destination_editor_preserves_preview_and_moves_to_compact(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        dialogs.choose_output_folder.return_value = "C:/Données Ω/Exports PDF"
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        preview_generation = application._preview_generation

        application.settings_panel.rows["destination"].invoke()
        self.root.update()
        self.assertTrue(application._destination_dialog.winfo_viewable())
        application._destination_mode_var.set("custom")
        application._on_destination_mode_changed()
        self.assertIsNone(application.output_dir)
        self.assertEqual(
            application._settings_draft_output_dir,
            "C:/Données Ω/Exports PDF",
        )
        self.assertEqual(application._preview_generation, preview_generation)

        application.lang = "fr"
        application._retranslate()
        self.assertEqual(
            application.destination_dialog_editor.save_button.cget("text"),
            "Enregistrer",
        )
        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        self.assertFalse(application._destination_dialog.winfo_viewable())
        self.assertEqual(
            application.compact_destination_editor.winfo_manager(), "grid"
        )
        self.assertLessEqual(
            application.compact_destination_editor.actions.winfo_rooty()
            + application.compact_destination_editor.actions.winfo_height(),
            application.action_bar.winfo_rooty(),
        )

        application.compact_destination_editor.save_button.invoke()
        self.root.update()
        self.assertEqual(
            application.output_dir, "C:/Données Ω/Exports PDF"
        )
        self.assertEqual(application._preview_generation, preview_generation)
        self.assertFalse(application._destination_editor_open)

    def test_header_footer_editor_retranslates_resets_and_moves_to_compact(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        dialogs.ask_restore_header_footer.return_value = True
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        original = application._settings_snapshot()
        original_preview = application._capture_preview_snapshot()

        application.settings_panel.rows["header_footer"].invoke()
        self.root.update()
        self.assertTrue(application._header_footer_dialog.winfo_viewable())
        self.assertFalse(
            application.header_footer_dialog_editor.scrollbar_visible
        )
        application._settings_draft_hf_vars["header_left"].set(
            "Report {title}"
        )
        application._restore_header_footer_defaults()
        dialogs.ask_restore_header_footer.assert_called_once()
        self.assertEqual(
            application._settings_draft_hf_vars["footer_center"].get(),
            "Page {page} / {total}",
        )

        application._settings_draft_hf_vars["header_left"].set(
            "Résumé Ω {page}"
        )
        application.lang = "fr"
        application._retranslate()
        self.assertEqual(
            application.header_footer_dialog_editor.save_button.cget("text"),
            "Enregistrer",
        )
        self.assertEqual(
            application._settings_draft_hf_vars["header_left"].get(),
            "Résumé Ω {page}",
        )

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        self.assertFalse(application._header_footer_dialog.winfo_viewable())
        self.assertEqual(
            application.compact_header_footer_editor.winfo_manager(), "grid"
        )
        self.assertTrue(
            application.compact_header_footer_editor.scrollbar_visible
        )
        compact_entries = application.compact_header_footer_editor.entries
        self.assertEqual(
            [
                int(compact_entries[key].master.grid_info()["column"])
                for key in (
                    "header_left", "header_center", "header_right",
                    "footer_left", "footer_center", "footer_right",
                )
            ],
            [0, 1, 2, 0, 1, 2],
        )
        self.assertLessEqual(
            application.compact_header_footer_editor.actions.winfo_rooty()
            + application.compact_header_footer_editor.actions.winfo_height(),
            application.action_bar.winfo_rooty(),
        )
        application.compact_header_footer_editor.content_surface.canvas.yview_moveto(1)
        self.root.update()
        self.assertGreater(
            application.compact_header_footer_editor.restore_button.winfo_rooty(),
            application.compact_header_footer_editor.content_surface.winfo_rooty(),
        )

        application.compact_header_footer_editor.back_button.invoke()
        self.root.update()
        self.assertFalse(application._header_footer_editor_open)
        self.assertEqual(application._settings_snapshot(), original)
        self.assertEqual(
            application._capture_preview_snapshot(), original_preview
        )

    def test_advanced_editor_retranslates_validates_confirms_and_moves_to_compact(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        dialogs.ask_trusted_html.return_value = True
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        original = application._settings_snapshot()
        original_preview = application._capture_preview_snapshot()

        application.settings_panel.rows["other"].invoke()
        self.root.update()
        self.assertTrue(application._advanced_dialog.winfo_viewable())
        self.assertIs(
            application._advanced_dialog.grab_current(),
            application._advanced_dialog,
        )
        self.assertEqual(
            application.advanced_dialog_editor.date_label.cget("text"),
            "Render date (YYYY-MM-DD)",
        )

        application._settings_draft_render_date_var.set("2026-02-31")
        self.root.update()
        self.assertTrue(application._advanced_error_var.get())
        application._settings_draft_render_date_var.set("2026-07-25")
        application._settings_draft_trusted_html_var.set(True)
        application._on_advanced_trusted_html_changed()
        self.assertTrue(application._trusted_html_confirmed)
        dialogs.ask_trusted_html.assert_called_once_with(
            application._advanced_dialog,
            tk_app.i18n.t("trusted_html_confirm_title", "en"),
            tk_app.i18n.t("trusted_html_confirm", "en"),
            tk_app.i18n.t("trusted_html_allow", "en"),
            tk_app.i18n.t("cancel_settings", "en"),
        )

        application.lang = "fr"
        application._retranslate()
        self.root.update()
        self.assertEqual(
            application.advanced_dialog_editor.title_label.cget("text"),
            "Options avancées",
        )
        self.assertEqual(application._advanced_dialog.title(), "Options avancées")
        self.assertEqual(
            application._settings_draft_render_date_var.get(), "2026-07-25"
        )

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        self.assertEqual(application._layout_mode, "compact")
        self.assertEqual(
            application.compact_advanced_editor.winfo_manager(), "grid"
        )
        self.assertLessEqual(
            application.compact_advanced_editor.actions.winfo_rooty()
            + application.compact_advanced_editor.actions.winfo_height(),
            application.action_bar.winfo_rooty(),
        )

        application.compact_advanced_editor.back_button.invoke()
        self.root.update()
        self.assertFalse(application._advanced_editor_open)
        self.assertEqual(application._settings_snapshot(), original)
        self.assertEqual(
            application._capture_preview_snapshot(), original_preview
        )

    def test_compact_tabs_hide_open_setting_editors_without_closing_drafts(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()

        scenarios = (
            (
                "style",
                application.compact_style_editor,
                application._cancel_style_editor,
            ),
            (
                "destination",
                application.compact_destination_editor,
                application._cancel_destination_editor,
            ),
            (
                "header_footer",
                application.compact_header_footer_editor,
                application._cancel_header_footer_editor,
            ),
            (
                "other",
                application.compact_advanced_editor,
                application._cancel_advanced_editor,
            ),
        )
        for row_name, editor, cancel in scenarios:
            application.settings_panel.rows[row_name].invoke()
            self.root.update()
            self.assertEqual(editor.winfo_manager(), "grid")
            self.assertEqual(application.settings_panel.winfo_manager(), "")

            application.compact_tabs.select("files")
            self.root.update()
            self.assertEqual(application.source_group.winfo_manager(), "grid")
            self.assertEqual(editor.winfo_manager(), "")
            self.assertEqual(application.settings_panel.winfo_manager(), "")

            application.compact_tabs.select("settings")
            self.root.update()
            self.assertEqual(editor.winfo_manager(), "grid")
            self.assertEqual(application.source_group.winfo_manager(), "")
            cancel()
            self.root.update()

    def test_results_view_projects_ordered_mixed_batch_in_large_and_compact_modes(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        long_source = (
            "C:/Données Ω/Projet avec espaces/"
            "rapport-très-long-avec-unicode-東京.md"
        )
        results = [
            {
                "input": long_source,
                "output": "C:/Exports/rapport-très-long-avec-unicode-東京.pdf",
                "status": "ok",
                "error": None,
                "error_code": None,
            },
            {
                "input": "C:/Données Ω/erreur.md",
                "output": None,
                "status": "error",
                "error": "Markdown could not be rendered\nparser context",
                "error_code": "MD_PARSE_ERROR",
            },
            {
                "input": "C:/Données Ω/annulé.md",
                "output": None,
                "status": "cancelled",
                "error": "Cancelled before rendering",
                "error_code": "CANCELLED",
            },
            {
                "input": "C:/Données Ω/conservé.md",
                "output": "C:/Exports/conservé.pdf",
                "status": "kept",
                "error": None,
                "error_code": None,
            },
        ]

        application.results_view.set_collapsed(False)
        application._render_results(results)
        self.root.update()

        view = application.results_view
        self.assertEqual(view.mode, "large")
        self.assertEqual(list(view.rows), [item["input"] for item in results])
        self.assertEqual(
            [
                button.accessible_name
                for button in view.rows[long_source].action_buttons
            ],
            ["Open PDF", "Open folder"],
        )
        self.assertEqual(
            [
                button.accessible_name
                for button in view.rows[results[1]["input"]].action_buttons
            ],
            [
                "Copy details",
                "Report a problem",
                "Show details",
            ],
        )
        self.assertEqual(
            [
                button.accessible_name
                for button in view.rows[results[2]["input"]].action_buttons
            ],
            ["Show details"],
        )
        self.assertEqual(
            view.rows[long_source].source_label.tooltip.text,
            str(Path(long_source)),
        )
        kept_source = results[3]["input"]
        self.assertEqual(view.rows[kept_source].action_buttons, [])
        self.assertLess(view.rows[kept_source].winfo_reqheight(), 80)
        self.assertEqual(
            view.rows[kept_source].output_label.tooltip.text,
            str(Path(results[3]["output"])),
        )

        error_source = results[1]["input"]
        self.assertEqual(
            view.rows[error_source].output_label.cget("text"),
            "Markdown could not be rendered",
        )
        view.rows[error_source].details_button.invoke()
        self.root.update()
        self.assertIn(error_source, view._expanded_sources)
        self.assertEqual(
            view.rows[error_source].details_frame.winfo_manager(), "grid"
        )
        detail_text = "\n".join(
            str(child.cget("text"))
            for child in view.rows[error_source].details_frame.winfo_children()
            if hasattr(child, "cget")
        )
        self.assertNotIn("Markdown could not be rendered", detail_text)
        self.assertIn("parser context", detail_text)
        application.lang = "fr"
        application._retranslate()
        self.root.update()
        self.assertIn(error_source, view._expanded_sources)
        self.assertEqual(
            view.rows[error_source].details_button.accessible_name,
            "Masquer les détails",
        )

        first_source = results[0]["input"]
        # Native focus_set() requires the shared test toplevel to be active.
        self.root.focus_force()
        self.root.update()
        view.focus_result(first_source)
        self.root.update()
        view.rows[first_source]._move_focus(1)
        self.root.update()
        self.assertIs(self.root.focus_get(), view.rows[error_source])

        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        application._select_compact_tab("results")
        self.root.update()
        self.assertEqual(view.mode, "compact")
        self.assertFalse(view.has_horizontal_scroll)
        self.assertEqual(view.column_header.winfo_manager(), "")
        self.assertEqual(list(view.rows), [item["input"] for item in results])
        for row in view.rows.values():
            self.assertTrue(all(
                int(button.grid_info()["column"]) <= 2
                for button in row.action_buttons
            ))

    def test_terminal_error_selects_results_but_success_keeps_compact_tab(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        self.root.geometry("560x520+0+0")
        self.root.update()
        application._responsive_controller.flush()
        application.files = [Path("ok.md"), Path("bad.md")]
        application._render_file_list()
        application._select_compact_tab("files")
        mixed = [
            {
                "input": "ok.md", "output": "ok.pdf", "status": "ok",
                "error": None, "error_code": None,
            },
            {
                "input": "bad.md", "output": None, "status": "error",
                "error": "failed", "error_code": "RENDER_FAILED",
            },
        ]

        application._handle_generate_done(mixed)
        self.root.update()
        self.assertEqual(application._active_compact_tab, "results")
        self.assertEqual(application.results_view._selected_source, "bad.md")

        application._select_compact_tab("files")
        application._handle_generate_done(mixed[:1])
        self.root.update()
        self.assertEqual(application._active_compact_tab, "files")

    def test_results_panel_is_full_width_bounded_resizable_and_clear_is_safe(self):
        services = mock.Mock()
        dialogs = mock.Mock()
        with mock.patch.object(tk_layout, "HAS_DND", False), mock.patch.object(
            tk_app.i18n,
            "load_language",
            return_value="en",
        ):
            application = tk_app.LibreMarkPdfApp(
                self.root,
                services=services,
                dialogs=dialogs,
            )
        application.files = [Path("one.md")]
        result = {
            "input": "one.md", "output": "one.pdf", "status": "ok",
            "error": None, "error_code": None,
        }
        application._render_results([result])
        application.results_view.set_collapsed(False)
        self.root.update()

        grid = application.results_view.grid_info()
        self.assertEqual(int(grid["row"]), 2)
        self.assertGreaterEqual(
            application.results_view.winfo_width(),
            application.content_container.winfo_width() - 2,
        )
        self.assertEqual(application.results_splitter.winfo_manager(), "grid")
        application._set_results_panel_height(999)
        self.assertEqual(
            application._results_panel_height,
            min(
                tk_layout.RESULTS_PANEL_MAX_HEIGHT,
                760 - tk_layout.RESULTS_PANEL_VERTICAL_RESERVE,
            ),
        )
        application._set_results_panel_height(1)
        self.assertEqual(
            application._results_panel_height,
            tk_layout.RESULTS_PANEL_MIN_HEIGHT,
        )

        application.results_view.set_conversion_active(True)
        self.assertEqual(
            application.results_view.clear_button.winfo_manager(), ""
        )
        application.results_view.set_conversion_active(False)
        self.assertEqual(
            application.results_view.clear_button.winfo_manager(), "grid"
        )
        self.assertEqual(
            application.results_view.clear_button.accessible_name,
            "Clear results",
        )
        application.results_view.clear_button.invoke()
        self.root.update()
        self.assertEqual(application._conversion_results, [])
        self.assertEqual(application.results_view.rows, {})
        self.assertEqual(application._action_state, "ready")
        services.open_path.assert_not_called()

        application.results_view.set_collapsed(True)
        self.root.update()
        self.assertEqual(application.results_splitter.winfo_manager(), "")
        self.assertEqual(
            int(application.content_container.grid_rowconfigure(2)["minsize"]),
            tk_layout.RESULTS_PANEL_COLLAPSED_HEIGHT,
        )

        application.results_view.set_collapsed(False)
        application._set_left_panel_width(9999)
        self.assertEqual(
            application._left_panel_width,
            application._left_panel_max_width(),
        )
        self.assertGreater(application._left_panel_width, 440)
        self.assertEqual(
            int(application.workspace.grid_rowconfigure(0)["weight"]), 1
        )
        self.assertEqual(
            int(application.workspace.grid_rowconfigure(1)["minsize"]),
            tk_layout.LEFT_SETTINGS_TARGET_HEIGHT,
        )
        last_setting = application.settings_panel.rows["other"]
        self.assertLessEqual(
            last_setting.winfo_y() + last_setting.winfo_height(),
            application.settings_panel.winfo_height(),
        )
        self.assertLessEqual(
            application.settings_panel.winfo_y()
            + application.settings_panel.winfo_height(),
            application.workspace.winfo_height(),
        )

        self.root.geometry("900x700+0+0")
        self.root.update()
        application._responsive_controller.flush()
        self.root.update()
        self.assertEqual(application._layout_mode, "medium")
        self.assertEqual(application.workspace_splitter.winfo_manager(), "grid")


if __name__ == "__main__":
    unittest.main()
