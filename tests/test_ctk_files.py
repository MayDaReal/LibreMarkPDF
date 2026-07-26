"""Public-behavior tests for the modern file-list components."""

import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import i18n
from libremark_pdf.desktop.ctk.assets import UiAssetRegistry
from libremark_pdf.desktop.ctk.theme import SystemFontResolver
from libremark_pdf.desktop.ctk.widgets import file_row
from libremark_pdf.desktop.ctk.widgets.file_panel import FilesPanel
from libremark_pdf.desktop.ctk.widgets.file_row import middle_elide


class TestModernFilesPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Tk is unavailable: {0}".format(exc))
        cls.fonts = SystemFontResolver(cls.root)
        cls.assets = UiAssetRegistry(cls.root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            for identifier in cls.root.tk.call("after", "info"):
                cls.root.after_cancel(identifier)
            cls.root.destroy()

    def setUp(self):
        self.added = []
        self.selected = []
        self.shown = []
        self.copied = []
        self.removed = []
        self.cleared = []
        self.panel = FilesPanel(
            self.root,
            labels=i18n.STRINGS["en"],
            fonts=self.fonts,
            assets=self.assets,
            has_drag_and_drop=False,
            on_add=lambda: self.added.append(True),
            on_select=self.selected.append,
            on_show_source=self.shown.append,
            on_copy_path=self.copied.append,
            on_remove=self.removed.append,
            on_clear=lambda: self.cleared.append(True),
        )
        self.panel.pack(fill="both", expand=True)
        self.root.update()

    def tearDown(self):
        self.panel.destroy()
        self.root.update()

    def test_empty_state_matches_dnd_capability_and_is_keyboard_invokable(self):
        self.assertEqual(
            self.panel.empty_state.cget("text"),
            "Select Markdown files",
        )
        self.assertEqual(self.panel.empty_state.cget("width"), 1)
        self.panel.empty_state.invoke()
        self.assertEqual(self.added, [True])

    def test_file_header_uses_compact_spacing_and_add_action(self):
        self.assertEqual(self.panel.title_label.cget("height"), 20)
        self.assertEqual(self.panel.count_label.cget("height"), 18)
        self.assertEqual(self.panel.add_button.cget("height"), 32)
        self.assertLess(self.panel.add_button.cget("width"), 140)
        self.assertEqual(
            self.panel.add_button.cget("font").cget("size"),
            12,
        )
        english_width = self.panel.add_button.cget("width")
        self.panel.retranslate(i18n.STRINGS["fr"])
        self.assertGreater(self.panel.add_button.cget("width"), english_width)

    def test_file_header_clear_is_a_direct_localized_trash_action(self):
        path = Path("one.md")
        self.panel.set_files([path], active=path)
        self.root.update()
        self.assertEqual(
            self.panel.clear_button.accessible_name,
            "Remove all",
        )
        self.panel.clear_button.invoke()
        self.assertEqual(self.cleared, [True])
        self.panel.set_interaction_enabled(False, False)
        self.assertEqual(
            self.panel.clear_button.cget("state"), "disabled"
        )

    def test_zero_one_two_eight_and_one_hundred_keep_order_and_row_identity(self):
        for count in (0, 1, 2, 8, 100):
            paths = [Path("folder/file-{0}.md".format(index)) for index in range(count)]
            with self.subTest(count=count):
                self.panel.set_files(
                    paths,
                    active=paths[0] if paths else None,
                )
                self.root.update()
                self.assertEqual(list(self.panel.rows), paths)
                self.assertEqual(len(self.panel.rows), count)
                if len(paths) >= 2:
                    row_heights = {
                        self.panel.rows[path].winfo_height()
                        for path in paths[:2]
                    }
                    self.assertEqual(row_heights, {58})

        paths = list(self.panel.rows)
        identities = {path: id(row) for path, row in self.panel.rows.items()}
        self.panel.set_active(paths[-1])
        self.panel.set_conversion_states({
            paths[0]: "ok",
            paths[1]: "error",
            paths[2]: "running",
        })
        self.root.update()
        self.assertEqual(
            {path: id(row) for path, row in self.panel.rows.items()},
            identities,
        )

    def test_row_keyboard_navigation_selection_and_mutation_lock(self):
        paths = [Path("one.md"), Path("two.md"), Path("three.md")]
        self.panel.set_files(paths, active=paths[0], focus_path=paths[0])
        self.root.update()
        first = self.panel.rows[paths[0]]
        second = self.panel.rows[paths[1]]

        with mock.patch.object(second, "focus_set") as focus_second:
            self.panel.focus_relative(paths[0], 1)
            focus_second.assert_called_once_with()
        second.activate()
        self.assertEqual(self.selected, [paths[1]])

        self.panel.set_interaction_enabled(
            mutation_enabled=False,
            selection_enabled=False,
            reason="Unavailable during conversion.",
        )
        second.remove()
        self.assertEqual(self.removed, [])
        self.assertEqual(self.panel.add_button.cget("state"), "disabled")
        self.assertEqual(self.panel.disabled_reason.winfo_manager(), "grid")

        self.panel.set_interaction_enabled(True, True)
        second.remove()
        self.assertEqual(self.removed, [paths[1]])

    def test_native_row_menu_does_not_activate_the_preview_row(self):
        path = Path("folder/report.md")
        self.panel.set_files([path], active=None)
        row = self.panel.rows[path]
        menu = mock.Mock()
        with mock.patch.object(file_row.tk, "Menu", return_value=menu):
            row.menu_button.invoke()

        self.assertEqual(self.selected, [])
        labels = [
            call.kwargs["label"]
            for call in menu.add_command.call_args_list
        ]
        self.assertEqual(
            labels,
            [
                "Show in source folder",
                "Copy path",
                "Remove from list",
            ],
        )

    def test_long_unicode_parent_path_is_elided_in_the_middle(self):
        value = "C:/Utilisateurs/Élodie/projets/très-long/dossier/source"
        shortened = middle_elide(value, 24)
        self.assertEqual(len(shortened), 24)
        self.assertTrue(shortened.startswith("C:/Utilisat"))
        self.assertTrue(shortened.endswith("ssier/source"))
        self.assertIn("…", shortened)

    def test_rendered_long_path_keeps_visible_middle_ellipsis(self):
        path = Path(
            "C:/Utilisateurs/Elodie/projets/tres-long/dossier/source/"
            "archives/2026/juillet/documents/client/final/"
            "report.md"
        )
        self.root.geometry("420x300")
        self.panel.set_files([path], active=None)
        self.root.update()

        self.assertIn("…", self.panel.rows[path].path_label.cget("text"))

    def test_hover_and_visual_state_changes_do_not_touch_the_filesystem(self):
        path = Path("folder/report.md")
        self.panel.set_files([path], active=None)
        row = self.panel.rows[path]
        with mock.patch.object(
            Path, "stat", side_effect=AssertionError("unexpected disk access")
        ), mock.patch.object(
            Path,
            "read_text",
            side_effect=AssertionError("unexpected disk access"),
        ):
            row.set_selected(True)
            row.name_tooltip.schedule()
            row.name_tooltip.hide()
            self.panel.set_conversion_states({path: "running"})

    def test_inactive_row_releases_badge_space_for_the_full_filename(self):
        paths = [
            Path("folder/active.md"),
            Path("folder/CODE_OF_CONDUCT.md"),
        ]
        self.root.geometry("600x400")
        self.panel.set_files(paths, active=paths[0])
        self.root.update()
        inactive = self.panel.rows[paths[1]]

        self.assertEqual(inactive.badges.winfo_manager(), "")
        self.assertGreaterEqual(
            inactive.name_label.winfo_width(),
            inactive.name_label.cget("font").measure(paths[1].name),
        )

    def test_selected_row_stacks_active_and_conversion_badges(self):
        path = Path("folder/MarketAtlas_bootstrapV3.md")
        self.root.geometry("420x300")
        self.panel.set_files([path], active=path)
        self.panel.set_conversion_states({path: "cancelled"})
        self.root.update()
        row = self.panel.rows[path]

        self.assertEqual(row.name_label.cget("text"), path.name)
        self.assertEqual(row.active_badge.winfo_manager(), "grid")
        self.assertEqual(row.conversion_badge.winfo_manager(), "grid")
        self.assertEqual(row.active_badge.grid_info()["column"], 0)
        self.assertEqual(row.conversion_badge.grid_info()["column"], 0)
        self.assertNotEqual(
            row.active_badge.grid_info()["row"],
            row.conversion_badge.grid_info()["row"],
        )

        self.panel.set_conversion_states({path: "kept"})
        self.assertEqual(row.conversion_badge.cget("text"), "Kept")


if __name__ == "__main__":
    unittest.main()
