"""Public-behavior tests for the modern desktop shell."""

import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import __version__
from libremark_pdf.desktop.ctk.app_shell import AppShell
from libremark_pdf.desktop.ctk.assets import product_logo
from libremark_pdf.desktop.ctk.responsive import (
    DebouncedLayoutController,
    resolve_layout_mode,
)
from libremark_pdf.desktop.ctk.theme import SystemFontResolver
from libremark_pdf.desktop.ctk.widgets.action_bar import ActionBar
from libremark_pdf.desktop.ctk.widgets.app_header import AppHeader
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
            cls.root.destroy()

    def setUp(self):
        self.root.geometry("1180x760+0+0")
        self.fonts = SystemFontResolver(self.root)

    def tearDown(self):
        for child in self.root.winfo_children():
            child.destroy()

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
        self.assertEqual(action_bar.progress.winfo_manager(), "")
        action_bar.set_conversion_active(True)
        self.assertEqual(action_bar.cancel_button.winfo_manager(), "grid")
        self.assertEqual(action_bar.progress.winfo_manager(), "grid")

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
        }
        header.retranslate(labels, __version__, "en")
        self.root.update()

        self.assertEqual(
            header.version_button.cget("text"),
            "v{0}".format(__version__),
        )
        self.assertIsInstance(header.help_menu, tk.Menu)
        self.assertIsInstance(header.language_menu, tk.Menu)
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

        french = dict(labels)
        french.update({
            "help_menu": "Aide",
            "keyboard_shortcuts_action": "Raccourcis clavier",
            "manual_action": "Manuel utilisateur",
            "report_issue_action": "Signaler un problème",
            "about_action": "À propos de LibreMark PDF",
        })
        header.retranslate(french, __version__, "fr")
        self.assertEqual(header.active_language, "fr")
        self.assertEqual(header.help_menu.entrycget(1, "label"), "Manuel utilisateur")
        self.assertEqual(header.language_button.cget("text"), "Français ▾")

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
        self.assertEqual(application.workspace.grid_bbox(0, 0)[2], 340)
        application._responsive_controller.schedule(560, 520)
        application._responsive_controller.flush()
        self.root.geometry("560x520+0+0")
        self.root.update()
        self.assertEqual(application.body_scroll.winfo_manager(), "pack")
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
        services.run_preview_worker.assert_not_called()
        services.run_conversion_job.assert_not_called()
        services.open_path.assert_not_called()


if __name__ == "__main__":
    unittest.main()
