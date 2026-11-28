"""Characterization tests for the locked Chromium implementation."""

import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import core
from libremark_pdf.engine import chromium


class TestChromiumDomain(unittest.TestCase):
    def test_browser_version_mismatch_closes_renderer_and_driver(self):
        driver = mock.Mock()
        browser = driver.chromium.launch.return_value
        browser.version = "0.0.0.0"
        with mock.patch("playwright.sync_api.sync_playwright") as start:
            start.return_value.start.return_value = driver
            with self.assertRaisesRegex(core.ConversionError, "BROWSER_MISMATCH"):
                with chromium.BrowserRenderer():
                    self.fail("An unexpected browser started a rendering session")
        browser.close.assert_called_once_with()
        driver.stop.assert_called_once_with()

    def test_chromium_implementation_does_not_import_the_public_facade(self):
        self.assertNotIn(
            "libremark_pdf.core", Path(chromium.__file__).read_text(encoding="utf-8")
        )

    def test_page_context_and_pdf_options_remain_locked(self):
        renderer = chromium.BrowserRenderer()
        browser = mock.Mock()
        context = mock.Mock()
        page = mock.Mock()
        browser.new_context.return_value = context
        context.new_page.return_value = page
        renderer._browser = browser

        opened_context, opened_page = renderer._open_page()

        self.assertIs(opened_context, context)
        self.assertIs(opened_page, page)
        browser.new_context.assert_called_once_with(
            locale="en-US",
            timezone_id="UTC",
            color_scheme="light",
            java_script_enabled=False,
            service_workers="block",
        )
        page.route.assert_called_once()
        self.assertEqual(page.route.call_args.args[0], "**/*")

        renderer._render_loaded_page(
            page, Path("output.pdf"), core.HeaderFooterConfig.none(), None
        )

        page.emulate_media.assert_called_once_with(media="print")
        self.assertEqual(
            page.pdf.call_args.kwargs,
            {
                "path": "output.pdf",
                "format": "A4",
                "margin": core.MARGIN_NO_HEADER_FOOTER,
                "display_header_footer": False,
                "header_template": "<div></div>",
                "footer_template": "<div></div>",
                "print_background": True,
                "tagged": True,
                "outline": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
