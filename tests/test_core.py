"""
tests/test_core.py — automated tests for the LibreMark PDF conversion engine.

Run with:  python -m unittest discover -s tests
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_title_entities_are_decoded(self):
        self.assertEqual(core.extract_title("<h1>A &amp; B</h1>"), "A & B")


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
        self.assertEqual(html.count('style="text-align:'), 3)

    def test_center_slot_uses_geometric_grid_centering(self):
        cfg = core.HeaderFooterConfig(top_left="long left", top_center="middle")
        html = core.build_header_template(cfg)
        self.assertIn("grid-template-columns:1fr auto 1fr", html)
        self.assertIn('style="text-align:center">middle</span>', html)


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

    def test_safe_mode_neutralizes_raw_html(self):
        html = core.markdown_to_html("<script>alert(1)</script>")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_trusted_static_mode_rejects_active_html(self):
        with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_HTML"):
            core.markdown_to_html("<img src=x onerror=alert(1)>", trusted_html=True)

    def test_trusted_static_mode_rejects_network_resource(self):
        with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_HTML_URL"):
            core.markdown_to_html("<img src=https://example.invalid/x.png>", trusted_html=True)

    def test_trusted_static_mode_rejects_active_css_and_refresh(self):
        for value in (
            "<style>p { background: url(data:image/png;base64,AA==) }</style>",
            '<meta http-equiv="refresh" content="0;url=https://example.invalid">',
        ):
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_"):
                core.markdown_to_html(value, trusted_html=True)

    def test_emoji_in_code_stays_literal(self):
        html = core.markdown_to_html("`✅`")
        self.assertIn("<code>✅</code>", html)


class TestDeterministicCoreContract(unittest.TestCase):
    def test_prepare_render_document_is_renderer_free_and_canonical(self):
        document = core.prepare_render_document(
            "# Canonical\n\nBody", render_date="2026-07-14"
        )
        self.assertEqual(document.render_date, "2026-07-14")
        self.assertIn("<h1>Canonical</h1>", document.full_html)
        self.assertIn(document.profile.fingerprint, document.full_html)

    def test_prepare_render_document_rejects_non_iso_date(self):
        with self.assertRaisesRegex(core.ConversionError, "INVALID_DATE"):
            core.prepare_render_document("# Date", render_date="20260714")

    def test_resource_path_supports_source_and_pyinstaller_layouts(self):
        self.assertTrue(core.resource_path("style.css").is_file())
        with tempfile.TemporaryDirectory() as tmp:
            frozen = Path(tmp)
            (frozen / "style.css").write_text("body{}", encoding="utf-8")
            with mock.patch.object(sys, "_MEIPASS", str(frozen), create=True):
                self.assertEqual(core.resource_path("style.css"), frozen / "style.css")

    def test_resource_path_supports_installed_wheel_data_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefix = Path(tmp)
            target = prefix / "libremark_pdf" / "style.css"
            target.parent.mkdir()
            target.write_text("body{}", encoding="utf-8")
            with mock.patch.object(core, "__file__", str(prefix / "missing" / "core.py")):
                with mock.patch.object(sys, "prefix", str(prefix)):
                    self.assertEqual(core.resource_path("style.css"), target)

    def test_render_profile_has_stable_canonical_fingerprint(self):
        first = core.RenderProfile("2026-07-14")
        second = core.RenderProfile("2026-07-14")
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_render_profile_theme_hash_changes_fingerprint(self):
        first = core.RenderProfile("2026-07-14", theme_hash="a")
        second = core.RenderProfile("2026-07-14", theme_hash="b")
        self.assertNotEqual(first.fingerprint, second.fingerprint)

    def test_css_network_references_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            css = Path(tmp) / "unsafe.css"
            css.write_text("@import url(https://example.invalid/x.css);", encoding="utf-8")
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_CSS_URL"):
                core._read_css(css)

    def test_css_data_resources_are_rejected_until_embedded_support_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            css = Path(tmp) / "unsafe.css"
            css.write_text("p { background: url(data:image/png;base64,AA==) }", encoding="utf-8")
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_CSS_URL"):
                core._read_css(css)

    def test_existing_output_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            output.write_bytes(b"old")
            with self.assertRaisesRegex(core.ConversionError, "OUTPUT_EXISTS"):
                core.convert_markdown_text_to_pdf("# New", output)
            self.assertEqual(output.read_bytes(), b"old")

    def test_atomic_failure_preserves_previous_output_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            output.write_bytes(b"old")
            with mock.patch.object(core, "_render_pdf", side_effect=RuntimeError("renderer failed")):
                with self.assertRaisesRegex(RuntimeError, "renderer failed"):
                    core.convert_markdown_text_to_pdf("# New", output, overwrite=True)
            self.assertEqual(output.read_bytes(), b"old")
            self.assertEqual(list(Path(tmp).glob(".libremark-*.pdf")), [])

    def test_batch_duplicate_destinations_are_rejected_per_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "one" / "same.md"
            second = Path(tmp) / "two" / "same.md"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("# One", encoding="utf-8")
            second.write_text("# Two", encoding="utf-8")
            results = core.convert_batch([first, second], output_dir=tmp)
            self.assertEqual([item["status"] for item in results], ["error", "error"])
            self.assertTrue(all("DUPLICATE_OUTPUT" in item["error"] for item in results))

    def test_batch_reuses_one_browser_and_closes_it(self):
        class FakeRenderer:
            entered = 0
            exited = 0

            def __enter__(self):
                type(self).entered += 1
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                type(self).exited += 1

            def render(self, full_html, output_path, header_footer, render_date):
                output_path.write_bytes(b"%PDF-1.4\nmock")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "one.md"
            second = root / "two.md"
            first.write_text("# One", encoding="utf-8")
            second.write_text("# Two", encoding="utf-8")
            with mock.patch.object(core, "_BrowserRenderer", FakeRenderer):
                results = core.convert_batch([first, second], output_dir=root)
            self.assertEqual([item["status"] for item in results], ["ok", "ok"])
            self.assertEqual(FakeRenderer.entered, 1)
            self.assertEqual(FakeRenderer.exited, 1)


class TestResourcePolicy(unittest.TestCase):
    _PNG = b"\x89PNG\r\n\x1a\nsmall-png"

    def test_local_png_is_embedded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "image.png").write_bytes(self._PNG)
            html = core.embed_local_resources('<img src="image.png">', root)
            self.assertIn("data:image/png;base64,", html)
            self.assertNotIn('src="image.png"', html)

    def test_traversal_and_external_urls_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in ("../outside.png", "https://example.invalid/x.png", "file:///tmp/x.png", "//example.invalid/x.png"):
                with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_RESOURCE"):
                    core.embed_local_resources('<img src="{0}">'.format(value), tmp)

    def test_malformed_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "wrong.png").write_bytes(b"not-a-png")
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_RESOURCE"):
                core.embed_local_resources('<img src="wrong.png">', root)

    def test_data_svg_with_active_content_is_rejected(self):
        payload = b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>'
        encoded = core.base64.b64encode(payload).decode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_RESOURCE"):
                core.embed_local_resources(
                    '<img src="data:image/svg+xml;base64,{0}">'.format(encoded), tmp
                )

    def test_symbolic_link_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            outside = Path(tmp) / "outside.png"
            outside.write_bytes(self._PNG)
            link = root / "escaped.png"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest("symbolic links are unavailable: {0}".format(exc))
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_RESOURCE"):
                core.embed_local_resources('<img src="escaped.png">', root)


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
