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
            i18n.t("status_done", "en", count=2),
            "Done: 2 PDF(s) created.",
        )

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
