"""Pure tests for translation-table contracts."""

import unittest
from string import Formatter

from libremark_pdf import i18n


class TestTranslations(unittest.TestCase):
    def test_english_and_french_have_identical_keys(self):
        self.assertEqual(set(i18n.STRINGS["en"]), set(i18n.STRINGS["fr"]))

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(
            i18n.t("status_ready", "unknown"),
            i18n.STRINGS["en"]["status_ready"],
        )

    def test_format_arguments_are_applied(self):
        self.assertEqual(
            i18n.t("generate_many", "en", count=2),
            "⚙ Generate 2 PDFs",
        )

    def test_count_forms_use_singular_only_for_one(self):
        self.assertEqual(i18n.plural_key("one", "many", 0), "many")
        self.assertEqual(i18n.plural_key("one", "many", 1), "one")
        self.assertEqual(i18n.plural_key("one", "many", 2), "many")

    def test_target_count_copy_is_natural_in_english_and_french(self):
        expected = {
            ("en", 1): "⚙ Generate PDF",
            ("en", 3): "⚙ Generate 3 PDFs",
            ("fr", 1): "⚙ Générer le PDF",
            ("fr", 3): "⚙ Générer 3 PDF",
        }
        for (lang, count), text in expected.items():
            with self.subTest(lang=lang, count=count):
                key = i18n.plural_key("generate_one", "generate_many", count)
                self.assertEqual(i18n.t(key, lang, count=count), text)

    def test_translation_tables_contain_no_pseudo_plurals(self):
        for lang, table in i18n.STRINGS.items():
            with self.subTest(lang=lang):
                self.assertNotIn("(s)", "\n".join(table.values()))

    def test_unknown_key_falls_back_to_key_name(self):
        self.assertEqual(i18n.t("missing_key", "fr"), "missing_key")

    def test_english_and_french_placeholders_match_for_every_key(self):
        for key in i18n.STRINGS["en"]:
            with self.subTest(key=key):
                english = {
                    field for _literal, field, _spec, _conversion
                    in Formatter().parse(i18n.STRINGS["en"][key])
                    if field is not None
                }
                french = {
                    field for _literal, field, _spec, _conversion
                    in Formatter().parse(i18n.STRINGS["fr"][key])
                    if field is not None
                }
                self.assertEqual(english, french)

    def test_setting_copy_lists_every_supported_header_footer_token(self):
        expected = ("{titre}", "{title}", "{date}", "{page}", "{total}")
        for lang in i18n.LANGUAGES:
            with self.subTest(lang=lang):
                text = i18n.STRINGS[lang]["tokens_help"]
                self.assertTrue(all(token in text for token in expected))


if __name__ == "__main__":
    unittest.main()
