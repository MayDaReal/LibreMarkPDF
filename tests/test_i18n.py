"""Pure tests for translation-table contracts."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
