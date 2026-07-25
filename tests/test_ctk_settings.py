"""Public-behavior tests for the modern settings-summary panel."""

import tkinter as tk
import unittest

from libremark_pdf import i18n
from libremark_pdf.desktop.ctk.assets import UiAssetRegistry
from libremark_pdf.desktop.ctk.theme import SystemFontResolver
from libremark_pdf.desktop.ctk.widgets.settings_summary import (
    SettingsSummaryPanel,
)


class TestSettingsSummaryPanel(unittest.TestCase):
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
        self.opened = []
        self.summaries = {
            "style": "Default theme",
            "destination": "Next to each source file",
            "header_footer": "Default",
            "other": "Automatic date · Safe HTML",
        }
        self.panel = SettingsSummaryPanel(
            self.root,
            labels={
                "settings_heading": i18n.t("settings_heading", "en"),
                "style": i18n.t("style_heading", "en"),
                "destination": i18n.t("destination_heading", "en"),
                "header_footer": i18n.t("header_footer_heading", "en"),
                "other": i18n.t("advanced_options_heading", "en"),
                "edit": i18n.t("edit_settings", "en"),
            },
            summaries=self.summaries,
            fonts=self.fonts,
            assets=self.assets,
            on_edit=lambda: self.opened.append(True),
        )
        self.panel.configure(width=390)
        self.panel.pack()
        self.root.update()

    def tearDown(self):
        self.panel.destroy()
        self.root.update()

    def test_panel_has_exactly_four_stable_rows_and_one_header_action(self):
        self.assertEqual(
            tuple(self.panel.rows),
            ("style", "destination", "header_footer", "other"),
        )
        identities = {
            name: id(row) for name, row in self.panel.rows.items()
        }
        self.panel.edit_button.invoke()
        self.assertEqual(self.opened, [True])
        for row in self.panel.rows.values():
            self.assertFalse(hasattr(row, "edit_button"))
            self.assertEqual(row.summary_label.cget("anchor"), "w")
            self.assertIsNotNone(row.icon_label.cget("image"))
            self.assertEqual(row.icon_label.grid_info()["column"], 0)
            self.assertEqual(row.title_label.grid_info()["column"], 1)
            self.assertEqual(row.summary_label.grid_info()["column"], 2)
            self.assertEqual(row.summary_label.grid_info()["row"], 0)
            for widget in (
                row.icon_label,
                row.title_label,
                row.summary_label,
            ):
                self.assertEqual(widget.grid_info()["pady"], 0)
            self.assertEqual(row.grid_rowconfigure(0)["weight"], 1)
        description_positions = {
            row.summary_label.winfo_rootx()
            for row in self.panel.rows.values()
        }
        self.assertEqual(len(description_positions), 1)
        self.assertEqual(self.panel.edit_button.grid_info()["pady"], 12)

        french = {
            "settings_heading": i18n.t("settings_heading", "fr"),
            "style": i18n.t("style_heading", "fr"),
            "destination": i18n.t("destination_heading", "fr"),
            "header_footer": i18n.t("header_footer_heading", "fr"),
            "other": i18n.t("advanced_options_heading", "fr"),
            "edit": i18n.t("edit_settings", "fr"),
        }
        self.panel.retranslate(french, self.summaries)
        self.assertEqual(
            {name: id(row) for name, row in self.panel.rows.items()},
            identities,
        )
        self.assertEqual(
            self.panel.edit_button.cget("text"),
            "Modifier",
        )

    def test_long_unicode_summary_is_one_line_elided_and_complete_in_tooltip(self):
        complete = (
            "CSS personnalisé · C:/Utilisateurs/Élodie/Projet avec espaces/"
            "styles/impression très détaillée.css"
        )
        summaries = dict(self.summaries)
        summaries["style"] = complete
        labels = {
            "settings_heading": "Réglages",
            "style": "Style PDF",
            "destination": "Destination",
            "header_footer": "En-têtes et pieds de page",
            "other": "Options avancées",
            "edit": "Modifier",
        }
        self.panel.retranslate(labels, summaries)
        self.root.update()
        row = self.panel.rows["style"]

        self.assertNotIn("\n", row.summary_label.cget("text"))
        self.assertIn("…", row.summary_label.cget("text"))
        self.assertEqual(row.summary_tooltip.text, complete)

    def test_disabled_panel_blocks_row_and_button_activation(self):
        self.panel.set_enabled(False)
        self.panel.edit_button.invoke()
        self.assertEqual(self.opened, [])


if __name__ == "__main__":
    unittest.main()
