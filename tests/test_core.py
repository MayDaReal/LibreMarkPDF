"""
tests/test_core.py — automated tests for the LibreMark PDF conversion engine.

Run with:  python -m unittest discover -s tests
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libremark_pdf import core


class TestTitleExtraction(unittest.TestCase):
    def test_simple_title(self):
        html = "<h1>Hello World</h1><p>text</p>"
        self.assertEqual(core.extract_title(html), "Hello World")

    def test_no_title_returns_default(self):
        html = "<p>no heading here</p>"
        self.assertEqual(core.extract_title(html), "Document")

    def test_multiline_title_is_collapsed(self):
        html = "<h1>Hello\nWorld   —   Test</h1>"
        self.assertEqual(core.extract_title(html), "Hello World — Test")

    def test_html_tags_inside_title_are_stripped(self):
        html = "<h1>Hello <em>World</em></h1>"
        self.assertEqual(core.extract_title(html), "Hello World")


class TestHeaderFooterConfig(unittest.TestCase):
    def test_default_is_not_empty(self):
        cfg = core.HeaderFooterConfig()
        self.assertFalse(cfg.is_empty())  # footer_center has a default

    def test_none_is_empty(self):
        cfg = core.HeaderFooterConfig.none()
        self.assertTrue(cfg.is_empty())

    def test_any_field_set_is_not_empty(self):
        cfg = core.HeaderFooterConfig.none()
        cfg.top_left = "hello"
        self.assertFalse(cfg.is_empty())


class TestTemplateBuilding(unittest.TestCase):
    def test_page_and_total_tokens_map_to_playwright_classes(self):
        cfg = core.HeaderFooterConfig(bottom_center="Page {page} / {total}")
        html = core.build_footer_template(cfg)
        self.assertIn('<span class="pageNumber"></span>', html)
        self.assertIn('<span class="totalPages"></span>', html)

    def test_title_token_maps_to_playwright_class(self):
        cfg = core.HeaderFooterConfig(top_center="{titre}")
        html = core.build_header_template(cfg)
        self.assertIn('<span class="title"></span>', html)

    def test_date_token_is_a_real_date_not_a_placeholder_class(self):
        cfg = core.HeaderFooterConfig(bottom_left="{date}")
        html = core.build_footer_template(cfg)
        self.assertNotIn('class="date"', html)
        # Should contain an ISO-like date string (YYYY-MM-DD)
        import re
        self.assertRegex(html, r"\d{4}-\d{2}-\d{2}")

    def test_literal_text_is_html_escaped(self):
        cfg = core.HeaderFooterConfig(bottom_left="A & B < C")
        html = core.build_footer_template(cfg)
        self.assertIn("A &amp; B &lt; C", html)

    def test_empty_field_produces_empty_span(self):
        cfg = core.HeaderFooterConfig.none()
        html = core.build_header_template(cfg)
        self.assertIn("<span></span><span></span><span></span>", html)


class TestMarkdownConversion(unittest.TestCase):
    def test_basic_markdown_to_html(self):
        html = core.markdown_to_html("# Title\n\nSome **bold** text.")
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<strong>bold</strong>", html)

    def test_table_extension_enabled(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        html = core.markdown_to_html(md)
        self.assertIn("<table>", html)

    def test_emoji_substitution(self):
        html = core.markdown_to_html("Status: \u2705 done")
        self.assertIn('<img class="emoji"', html)
        self.assertIn("data:image/png;base64,", html)
        self.assertNotIn("\u2705", html)

    def test_full_document_escapes_title(self):
        html = core.build_full_html("<p>Body</p>", "A & B < C", "")
        self.assertIn("<title>A &amp; B &lt; C</title>", html)


class TestEndToEndConversion(unittest.TestCase):
    def test_convert_markdown_text_to_pdf_creates_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            result = core.convert_markdown_text_to_pdf("# Hello\n\nWorld.", output)
            self.assertEqual(result, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)

    def test_convert_batch_reports_per_file_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.md"
            good.write_text("# Good\n\nfine.", encoding="utf-8")
            missing = Path(tmp) / "missing.md"

            results = core.convert_batch([good, missing], output_dir=tmp)
            statuses = {Path(r["input"]).name: r["status"] for r in results}
            self.assertEqual(statuses["good.md"], "ok")
            self.assertEqual(statuses["missing.md"], "error")

    def test_render_preview_png_returns_valid_png_bytes(self):
        png_bytes = core.render_preview_png("# Hello\n\nWorld.", dpi=60)
        self.assertIsInstance(png_bytes, bytes)
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(png_bytes), 100)


if __name__ == "__main__":
    unittest.main()
