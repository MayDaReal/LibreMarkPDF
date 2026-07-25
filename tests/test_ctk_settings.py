"""Public-behavior tests for the modern settings-summary panel."""

import tkinter as tk
import unittest
from unittest import mock

import customtkinter as ctk

from libremark_pdf import i18n
from libremark_pdf.desktop.ctk.assets import UiAssetRegistry
from libremark_pdf.desktop.ctk.theme import COLORS, SystemFontResolver
from libremark_pdf.desktop.ctk.widgets.advanced_editor import AdvancedEditorPanel
from libremark_pdf.desktop.ctk.widgets.destination_editor import (
    DestinationEditorPanel,
)
from libremark_pdf.desktop.ctk.widgets.header_footer_editor import (
    HeaderFooterEditorPanel,
)
from libremark_pdf.desktop.ctk.widgets.settings_summary import (
    SettingsSummaryPanel,
)
from libremark_pdf.desktop.ctk.widgets.style_editor import StyleEditorPanel


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
            on_edit_style=lambda: self.opened.append("style"),
            on_edit_destination=lambda: self.opened.append("destination"),
            on_edit_header_footer=lambda: self.opened.append("header_footer"),
            on_edit_other=lambda: self.opened.append("other"),
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

    def test_style_row_is_keyboard_invokable_without_rebuilding_other_rows(self):
        opened = []
        self.panel.destroy()
        self.panel = SettingsSummaryPanel(
            self.root,
            labels={
                "settings_heading": "Settings",
                "style": "PDF style",
                "destination": "Destination",
                "header_footer": "Headers and footers",
                "other": "Advanced options",
                "edit": "Edit",
            },
            summaries=self.summaries,
            fonts=self.fonts,
            assets=self.assets,
            on_edit=lambda: None,
            on_edit_style=lambda: opened.append("style"),
        )
        self.panel.pack()
        identities = {name: id(row) for name, row in self.panel.rows.items()}

        self.panel.rows["style"].invoke()
        self.root.update()

        self.assertEqual(opened, ["style"])
        self.assertTrue(
            tk.Frame.cget(self.panel.rows["style"], "takefocus")
        )
        self.assertEqual(
            {name: id(row) for name, row in self.panel.rows.items()},
            identities,
        )

    def test_destination_row_has_its_own_keyboard_action(self):
        opened = []
        self.panel.destroy()
        self.panel = SettingsSummaryPanel(
            self.root,
            labels={
                "settings_heading": "Settings",
                "style": "PDF style",
                "destination": "Destination",
                "header_footer": "Headers and footers",
                "other": "Advanced options",
                "edit": "Edit",
            },
            summaries=self.summaries,
            fonts=self.fonts,
            assets=self.assets,
            on_edit=lambda: None,
            on_edit_destination=lambda: opened.append("destination"),
        )
        self.panel.pack()

        self.panel.rows["destination"].invoke()

        self.assertEqual(opened, ["destination"])
        self.assertTrue(
            tk.Frame.cget(self.panel.rows["destination"], "takefocus")
        )

    def test_migrated_rows_show_pointer_hover_and_keyboard_focus(self):
        for name in ("style", "destination", "header_footer", "other"):
            row = self.panel.rows[name]
            row.set_interaction_state("hover")
            self.assertEqual(tk.Widget.cget(self.root, "cursor"), "hand2")
            self.assertEqual(row.cget("fg_color"), COLORS["surface_hover"])
            row.set_focus_visible(True)
            self.assertEqual(row.cget("border_color"), COLORS["primary"])
            self.assertEqual(row.cget("border_width"), 2)
            row.set_focus_visible(False)
            self.assertEqual(row.cget("border_color"), COLORS["border"])
            self.assertEqual(row.cget("border_width"), 1)

    def test_header_footer_row_has_its_own_keyboard_action(self):
        self.panel.rows["header_footer"].invoke()
        self.assertEqual(self.opened, ["header_footer"])

    def test_advanced_row_has_its_own_keyboard_action(self):
        self.panel.rows["other"].invoke()
        self.assertEqual(self.opened, ["other"])


class TestStyleEditorPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Tk is unavailable: {0}".format(exc))
        cls.fonts = SystemFontResolver(cls.root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            cls.root.destroy()

    def test_editor_projects_human_theme_copy_actions_error_and_focus(self):
        calls = []
        mode = tk.StringVar(master=self.root, value="theme")
        theme_display = tk.StringVar(master=self.root)
        css_display = tk.StringVar(master=self.root, value="No CSS file selected")
        error = tk.StringVar(master=self.root)
        editor = StyleEditorPanel(
            self.root,
            fonts=self.fonts,
            style_mode_var=mode,
            theme_display_var=theme_display,
            css_display_var=css_display,
            error_var=error,
            on_mode_changed=lambda: calls.append("mode"),
            on_theme_changed=lambda reference: calls.append(reference),
            on_choose_css=lambda: calls.append("choose"),
            on_save=lambda: calls.append("save"),
            on_cancel=lambda: calls.append("cancel"),
            show_back=True,
        )
        editor.pack(fill="both", expand=True)
        editor.retranslate({
            "title": "PDF style",
            "description": "Choose a local style.",
            "back": "Back",
            "local_theme": "Local theme",
            "custom_css": "Custom CSS",
            "choose_css": "Choose CSS",
            "cancel": "Cancel",
            "save": "Save",
        })
        editor.set_themes(
            (("default@1", "Default theme"), ("office@1", "Office")),
            "default@1",
            "Theme identifier: default@1",
        )
        editor.set_mode("theme")
        editor.theme_radio.focus_set = mock.Mock()
        editor.focus_initial("theme")
        self.root.update()

        self.assertEqual(editor.theme_combo.get(), "Default theme")
        self.assertNotIn("default@1", editor.theme_combo.get())
        self.assertIn("default@1", editor.theme_technical_label.cget("text"))
        editor.theme_radio.focus_set.assert_called_once_with()
        self.assertEqual(editor.back_button.cget("text"), "Back")
        error.set("CSS error")
        self.root.update()
        self.assertEqual(error.get(), "CSS error")
        editor.save_button.invoke()
        self.assertEqual(calls, ["save"])
        editor.destroy()


class TestDestinationEditorPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Tk is unavailable: {0}".format(exc))
        cls.fonts = SystemFontResolver(cls.root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            cls.root.destroy()

    def test_editor_disables_source_path_and_exposes_copyable_custom_path(self):
        calls = []
        mode = tk.StringVar(master=self.root, value="source")
        path = tk.StringVar(master=self.root, value="No folder selected")
        error = tk.StringVar(master=self.root)
        editor = DestinationEditorPanel(
            self.root,
            fonts=self.fonts,
            mode_var=mode,
            path_var=path,
            error_var=error,
            on_mode_changed=lambda: calls.append("mode"),
            on_choose_folder=lambda: calls.append("choose"),
            on_save=lambda: calls.append("save"),
            on_cancel=lambda: calls.append("cancel"),
            show_back=True,
        )
        editor.pack(fill="both", expand=True)
        editor.retranslate({
            "title": "Destination",
            "description": "Choose where PDFs are saved.",
            "back": "Back",
            "source": "Same folder as each source file",
            "custom": "Single folder",
            "choose": "Browse",
            "cancel": "Cancel",
            "save": "Save",
        })
        editor.set_mode("source")
        self.assertEqual(str(editor.path_entry.cget("state")), "disabled")
        self.assertEqual(editor.choose_button.cget("state"), "disabled")

        path.set("C:/Données Ω/Exports PDF")
        editor.set_mode("custom")
        editor.custom_radio.focus_set = mock.Mock()
        editor.focus_initial("custom")
        self.root.update()

        self.assertEqual(str(editor.path_entry.cget("state")), "readonly")
        self.assertEqual(path.get(), "C:/Données Ω/Exports PDF")
        editor.custom_radio.focus_set.assert_called_once_with()
        editor.save_button.invoke()
        self.assertEqual(calls, ["save"])
        editor.destroy()


class TestHeaderFooterEditorPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Tk is unavailable: {0}".format(exc))
        cls.fonts = SystemFontResolver(cls.root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            cls.root.destroy()

    def test_six_labelled_fields_insert_tokens_at_the_cursor(self):
        field_vars = {
            key: tk.StringVar(master=self.root)
            for key in (
                "header_left", "header_center", "header_right",
                "footer_left", "footer_center", "footer_right",
            )
        }
        calls = []
        editor = HeaderFooterEditorPanel(
            self.root,
            fonts=self.fonts,
            field_vars=field_vars,
            on_restore_defaults=lambda: calls.append("restore"),
            on_save=lambda: calls.append("save"),
            on_cancel=lambda: calls.append("cancel"),
            show_back=True,
        )
        editor.pack(fill="both", expand=True)
        editor.retranslate({
            "title": "Headers and footers",
            "description": "Empty fields display nothing.",
            "back": "Back",
            "header": "Header",
            "footer": "Footer",
            "left": "Left",
            "center": "Center",
            "right": "Right",
            "tokens": "Insert a variable",
            "token_help": "{page}: current page",
            "restore": "Restore defaults",
            "cancel": "Cancel",
            "save": "Save",
        })
        self.root.update()
        self.assertEqual(len(editor.entries), 6)
        self.assertTrue(
            all(label.cget("text") for label in editor.field_labels.values())
        )

        field_vars["footer_center"].set("Page  / total")
        editor.entries["footer_center"].event_generate("<FocusIn>")
        editor.entries["footer_center"].icursor(5)
        editor.insert_token("{page}")

        self.assertEqual(field_vars["footer_center"].get(), "Page {page} / total")
        self.assertEqual(tuple(editor.token_buttons), (
            "{titre}", "{title}", "{date}", "{page}", "{total}",
        ))
        editor.restore_button.invoke()
        editor.save_button.invoke()
        self.assertEqual(calls, ["restore", "save"])
        editor.destroy()


class TestAdvancedEditorPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Tk is unavailable: {0}".format(exc))
        cls.fonts = SystemFontResolver(cls.root)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "root"):
            cls.root.destroy()

    def test_editor_exposes_date_help_inline_error_security_switch_and_actions(self):
        calls = []
        render_date = tk.StringVar(master=self.root)
        trusted_html = tk.BooleanVar(master=self.root, value=False)
        error = tk.StringVar(master=self.root)
        editor = AdvancedEditorPanel(
            self.root,
            fonts=self.fonts,
            render_date_var=render_date,
            trusted_html_var=trusted_html,
            error_var=error,
            on_trusted_html_changed=lambda: calls.append("trusted"),
            on_save=lambda: calls.append("save"),
            on_cancel=lambda: calls.append("cancel"),
            show_back=True,
        )
        editor.pack(fill="both", expand=True)
        editor.retranslate({
            "title": "Advanced options",
            "description": "Choose render options.",
            "back": "Back",
            "date": "Render date (YYYY-MM-DD)",
            "date_help": "Leave empty to use today's date automatically.",
            "trusted_html": "Allow trusted static HTML",
            "security": (
                "Scripts, remote resources and active content remain blocked."
            ),
            "cancel": "Cancel",
            "save": "Save",
        })
        editor.date_entry.focus_set = mock.Mock()
        editor.focus_initial()
        error.set("Invalid date")
        self.root.update()

        self.assertIsInstance(editor.trusted_html_switch, ctk.CTkSwitch)
        self.assertIn("YYYY-MM-DD", editor.date_label.cget("text"))
        self.assertIn("automatically", editor.date_help_label.cget("text"))
        self.assertIn("remote", editor.security_label.cget("text"))
        self.assertEqual(error.get(), "Invalid date")
        editor.date_entry.focus_set.assert_called_once_with()
        editor.save_button.invoke()
        self.assertEqual(calls, ["save"])
        editor.destroy()


if __name__ == "__main__":
    unittest.main()
