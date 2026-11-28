"""
tests/test_core.py — automated tests for the LibreMark PDF conversion engine.

Run with:  python -m unittest discover -s tests
"""

import base64
import hashlib
import inspect
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libremark_pdf import core
from libremark_pdf.engine import chromium, contracts, document, jobs, preview, resources


class TestCoreFacadeCharacterization(unittest.TestCase):
    """Freeze the public core boundary before its implementation moves."""

    _PUBLIC_NAMES = (
        "ConversionError", "HeaderFooterConfig", "RenderProfile", "RenderDocument",
        "BatchPlan", "DEFAULT_PROFILE_VERSION", "DEFAULT_THEME_ID", "DEFAULT_CSS_PATH",
        "FONTS_DIR", "ICONS_DIR", "BROWSERS_DIR", "resource_path",
        "renderer_identity", "error_code", "markdown_to_html",
        "embed_local_resources", "extract_title", "build_header_template",
        "build_footer_template", "build_full_html", "resolve_render_date",
        "prepare_render_document", "render_profile_for_options",
        "convert_markdown_text_to_pdf", "convert_markdown_to_pdf",
        "plan_batch_outputs", "convert_batch", "PreviewSession", "PreviewPage",
        "render_preview_png", "ThemeInfo", "validate_theme_package",
        "list_themes", "show_theme", "install_theme", "remove_theme",
        "resolve_theme_css",
    )

    def test_public_inventory_and_key_signatures_are_stable(self):
        for name in self._PUBLIC_NAMES:
            self.assertTrue(hasattr(core, name), name)
        expected_parameters = {
            "prepare_render_document": (
                "markdown_text", "css_path", "render_date", "trusted_html",
                "resource_root", "header_footer", "theme", "theme_root",
                "_include_profile_fingerprint",
            ),
            "convert_markdown_text_to_pdf": (
                "markdown_text", "output_path", "css_path", "header_footer",
                "render_date", "trusted_html", "overwrite", "resource_root",
                "theme", "theme_root", "_renderer", "_cancel_event",
            ),
            "convert_markdown_to_pdf": (
                "input_path", "output_path", "css_path", "header_footer",
                "render_date", "trusted_html", "overwrite", "theme",
                "theme_root", "_renderer", "_cancel_event",
            ),
            "convert_batch": (
                "input_paths", "output_dir", "css_path", "header_footer",
                "render_date", "trusted_html", "overwrite", "theme",
                "theme_root", "cancel_event", "progress_callback",
                "cancel_current_event", "stage_callback", "overwrite_targets",
            ),
            "render_preview_png": (
                "markdown_text", "css_path", "header_footer", "dpi", "render_date",
                "trusted_html", "resource_root", "theme", "theme_root",
            ),
        }
        for name, parameters in expected_parameters.items():
            self.assertEqual(tuple(inspect.signature(getattr(core, name)).parameters), parameters)

    def test_fixed_document_has_exact_html_and_profile_fingerprints(self):
        document = core.prepare_render_document(
            "# Canonical\n\nBody with **bold**.",
            render_date="2026-07-14",
            header_footer=core.HeaderFooterConfig(
                top_left="Fixed {title}", bottom_center="Page {page} / {total}"
            ),
        )
        self.assertEqual(
            document.profile.fingerprint,
            "5552d4415fad58535d226f5c901ad9d060bfadc0abe62265e354cce84175dcd4",
        )
        self.assertEqual(
            hashlib.sha256(document.full_html.encode("utf-8")).hexdigest(),
            "a4bfd28eb2319dee66ce754ec96854ee977d6d857df662170058240cdccac04c",
        )

    def test_default_theme_alias_is_exact(self):
        self.assertEqual(
            core.resolve_theme_css(None).as_dict(),
            core.resolve_theme_css("default@1").as_dict(),
        )

    def test_extracted_contracts_keep_one_public_identity(self):
        for name in (
            "ConversionError",
            "HeaderFooterConfig",
            "RenderProfile",
            "RenderDocument",
            "BatchPlan",
            "ThemeInfo",
        ):
            self.assertIs(getattr(core, name), getattr(contracts, name), name)
        self.assertNotIn("libremark_pdf.core", Path(contracts.__file__).read_text(encoding="utf-8"))

    def test_engine_and_adapters_keep_the_one_way_facade_boundary(self):
        root = Path(__file__).resolve().parent.parent
        for module in ("cli.py", "gui.py", "desktop_services.py"):
            source = (root / "libremark_pdf" / module).read_text(encoding="utf-8")
            self.assertNotIn(".engine", source, module)

        forbidden = (
            "libremark_pdf.core",
            "libremark_pdf.cli",
            "libremark_pdf.gui",
            "libremark_pdf.desktop",
            "tkinter",
            "ImageTk",
        )
        for path in (root / "libremark_pdf" / "engine").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            for name in forbidden:
                self.assertNotIn(name, source, "{0}: {1}".format(path.name, name))

    def test_obsolete_private_implementation_aliases_are_not_facade_api(self):
        for name in (
            "_sha256_file",
            "_renderer_resource_hashes",
            "_icon_data_uri",
            "_font_face_css",
            "_preview_template_font_css",
            "_is_within",
            "_validate_image_bytes",
            "_css_has_forbidden_resources",
            "_default_theme_info",
            "_manifest_relative_path",
            "_theme_file",
            "_theme_root",
            "_theme_error",
            "_build_preview_template",
            "_read_css",
            "_resolve_style_profile",
            "_validate_markdown_text",
            "_BrowserRenderer",
            "_render_pdf",
            "_atomic_render_pdf",
            "_first_page_png",
        ):
            self.assertFalse(hasattr(core, name), name)

    def test_contract_defaults_mutability_and_error_codes_are_stable(self):
        defaults = core.HeaderFooterConfig()
        self.assertEqual(defaults.bottom_center, "Page {page} / {total}")
        self.assertFalse(defaults.is_empty())
        disabled = core.HeaderFooterConfig.none()
        self.assertTrue(disabled.is_empty())
        disabled.top_left = "Mutable"
        self.assertEqual(disabled.top_left, "Mutable")
        plan = core.BatchPlan(Path("input.md"), Path("output.pdf"), "INPUT_NOT_FOUND: absent")
        self.assertEqual(plan.error_code, "INPUT_NOT_FOUND")
        self.assertEqual(core.BatchPlan(Path("input.md"), Path("output.pdf")).error_code, None)


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

    def test_preview_latin_template_omits_unselected_large_families(self):
        css = resources._preview_template_font_css("Page 1 / 2")
        self.assertIn("G1 Noto Sans", css)
        self.assertNotIn("G1 Noto Sans Arabic", css)
        self.assertNotIn("G1 Noto Sans CJK SC", css)

    def test_preview_template_includes_fonts_required_by_its_text(self):
        arabic = resources._preview_template_font_css("العربية")
        cjk = resources._preview_template_font_css("中文")
        self.assertIn("G1 Noto Sans Arabic", arabic)
        self.assertIn("G1 Noto Sans CJK SC", cjk)

    def test_empty_preview_template_has_no_font_payload(self):
        self.assertEqual(
            document._build_preview_template("", "", "", None, ""),
            "<div></div>",
        )


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

    def test_trusted_static_mode_rejects_inline_css_and_fetch_attributes(self):
        for value in (
            '<div style="background:url(https://example.invalid/a.png)">x</div>',
            '<video poster="https://example.invalid/a.png">x</video>',
        ):
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_"):
                core.markdown_to_html(value, trusted_html=True)

    def test_emoji_in_code_stays_literal(self):
        html = core.markdown_to_html("`✅`")
        self.assertIn("<code>✅</code>", html)

    def test_emoji_in_alternative_text_stays_literal(self):
        html = core.markdown_to_html("Visible ✅\n\n![Status ✅](icon.png)")
        self.assertIn('alt="Status ✅"', html)
        self.assertEqual(html.count('class="emoji"'), 1)


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

    def test_browser_resource_path_prefers_the_configured_platform_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                "os.environ", {"PLAYWRIGHT_BROWSERS_PATH": tmp}
            ):
                self.assertEqual(
                    resources.browser_resource_path(core.__file__),
                    Path(tmp).resolve(),
                )

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
                document._read_css(css)

    def test_css_data_resources_are_rejected_until_embedded_support_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            css = Path(tmp) / "unsafe.css"
            css.write_text("p { background: url(data:image/png;base64,AA==) }", encoding="utf-8")
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_CSS_URL"):
                document._read_css(css)

    def test_invalid_css_is_rejected_with_a_stable_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            css = Path(tmp) / "invalid.css"
            css.write_bytes(b"body { color: black; }\x00")
            with self.assertRaisesRegex(core.ConversionError, "INVALID_CSS"):
                document._read_css(css)

    def test_empty_and_limit_exceeding_markdown_have_defined_behavior(self):
        self.assertIn("<body>", core.prepare_render_document("").full_html)
        with mock.patch.object(document, "MAX_MARKDOWN_BYTES", 4):
            with self.assertRaisesRegex(core.ConversionError, "INPUT_TOO_LARGE"):
                core.prepare_render_document("12345")

    def test_file_input_rejects_malformed_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.md"
            source.write_bytes(b"# heading\n\xff")
            with self.assertRaisesRegex(core.ConversionError, "INVALID_UTF8"):
                core.convert_markdown_to_pdf(source, Path(tmp) / "out.pdf")

    def test_unavailable_destination_has_a_stable_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            with mock.patch.object(Path, "mkdir", side_effect=PermissionError("denied")):
                with self.assertRaisesRegex(core.ConversionError, "OUTPUT_UNAVAILABLE"):
                    core.convert_markdown_text_to_pdf("# body", output)

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
            with mock.patch.object(chromium, "render_pdf", side_effect=RuntimeError("renderer failed")):
                with self.assertRaisesRegex(RuntimeError, "renderer failed"):
                    core.convert_markdown_text_to_pdf("# New", output, overwrite=True)
            self.assertEqual(output.read_bytes(), b"old")
            self.assertEqual(list(Path(tmp).glob(".libremark-*.pdf")), [])

    def test_temporary_creation_failure_has_stable_code_and_preserves_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            output.write_bytes(b"old")
            with mock.patch.object(
                chromium.os,
                "open",
                side_effect=PermissionError("denied"),
            ) as open_file:
                with self.assertRaisesRegex(core.ConversionError, "OUTPUT_UNAVAILABLE"):
                    core.convert_markdown_text_to_pdf("# New", output, overwrite=True)
            open_file.assert_called_once()
            self.assertEqual(output.read_bytes(), b"old")
            self.assertEqual(list(Path(tmp).glob(".libremark-*.pdf")), [])

    def test_atomic_replacement_failure_has_stable_code_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            output.write_bytes(b"old")

            def write_pdf(_html, temporary, _header_footer, _render_date):
                temporary.write_bytes(b"new")

            with mock.patch.object(chromium, "render_pdf", side_effect=write_pdf):
                with mock.patch.object(chromium.os, "replace", side_effect=PermissionError("denied")):
                    with self.assertRaisesRegex(core.ConversionError, "OUTPUT_REPLACE_FAILED"):
                        core.convert_markdown_text_to_pdf("# New", output, overwrite=True)
            self.assertEqual(output.read_bytes(), b"old")
            self.assertEqual(list(Path(tmp).glob(".libremark-*.pdf")), [])

    def test_renderer_failure_has_stable_error_code_and_keeps_message(self):
        class Page:
            def route(self, pattern, callback):
                return None

            def set_content(self, *args, **kwargs):
                raise RuntimeError("engine diagnostic")

        class Context:
            closed = False

            def new_page(self):
                return Page()

            def close(self):
                type(self).closed = True

        class Browser:
            def new_context(self, **kwargs):
                return Context()

        renderer = chromium.BrowserRenderer()
        renderer._browser = Browser()
        with self.assertRaisesRegex(core.ConversionError, "RENDER_FAILED: engine diagnostic") as raised:
            renderer.render("<p>x</p>", Path("ignored.pdf"), core.HeaderFooterConfig.none(), None)
        self.assertEqual(core.error_code(raised.exception), "RENDER_FAILED")
        self.assertTrue(Context.closed)

    def test_browser_launch_uses_the_locked_render_timeout(self):
        playwright = mock.Mock()
        playwright.chromium.launch.return_value.version = core.CHROMIUM_VERSION
        manager = mock.Mock()
        manager.start.return_value = playwright
        with mock.patch(
            "playwright.sync_api.sync_playwright", return_value=manager
        ):
            renderer = chromium.BrowserRenderer()
            renderer.__enter__()
            renderer.__exit__(None, None, None)
        playwright.chromium.launch.assert_called_once_with(
            args=["--disable-font-subpixel-positioning"],
            timeout=core.RENDER_TIMEOUT_MS,
        )

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
            with mock.patch.object(jobs.chromium, "BrowserRenderer", FakeRenderer):
                results = core.convert_batch([first, second], output_dir=root)
            self.assertEqual([item["status"] for item in results], ["ok", "ok"])
            self.assertEqual(FakeRenderer.entered, 1)
            self.assertEqual(FakeRenderer.exited, 1)

    def test_batch_plan_exposes_collisions_and_existing_outputs_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "one" / "same.md"
            second = root / "two" / "same.md"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("# One", encoding="utf-8")
            second.write_text("# Two", encoding="utf-8")
            duplicate = core.plan_batch_outputs([first, second], root / "out")
            self.assertEqual(
                [item.error_code for item in duplicate],
                ["DUPLICATE_OUTPUT", "DUPLICATE_OUTPUT"],
            )

            existing = root / "existing.md"
            existing.write_text("# Existing", encoding="utf-8")
            existing.with_suffix(".pdf").write_bytes(b"old")
            plan = core.plan_batch_outputs([existing])
            self.assertEqual(plan[0].error_code, "OUTPUT_EXISTS")
            self.assertEqual(existing.with_suffix(".pdf").read_bytes(), b"old")

    def test_batch_overwrites_only_selected_existing_targets(self):
        class FakeRenderer:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def render(self, full_html, output_path, header_footer, render_date):
                output_path.write_bytes(b"%PDF-1.4\nnew")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "one.md"
            second = root / "two.md"
            first.write_text("# One", encoding="utf-8")
            second.write_text("# Two", encoding="utf-8")
            first_output = first.with_suffix(".pdf")
            second_output = second.with_suffix(".pdf")
            first_output.write_bytes(b"old-one")
            second_output.write_bytes(b"old-two")

            with mock.patch.object(jobs.chromium, "BrowserRenderer", FakeRenderer):
                results = core.convert_batch(
                    [first, second], overwrite_targets=[first_output]
                )

            self.assertEqual(
                [item["status"] for item in results], ["ok", "error"]
            )
            self.assertEqual(first_output.read_bytes(), b"%PDF-1.4\nnew")
            self.assertEqual(second_output.read_bytes(), b"old-two")
            self.assertEqual(results[1]["error_code"], "OUTPUT_EXISTS")

    def test_batch_cancellation_returns_one_result_per_input_and_reports_progress(self):
        class FakeRenderer:
            entered = 0

            def __enter__(self):
                type(self).entered += 1
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def render(self, full_html, output_path, header_footer, render_date):
                output_path.write_bytes(b"%PDF-1.4\nmock")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = [root / "one.md", root / "two.md", root / "three.md"]
            for path in files:
                path.write_text("# " + path.stem, encoding="utf-8")
            cancel = threading.Event()
            progress = []

            def on_progress(index, total, result):
                progress.append((index, total, result["status"]))
                if index == 1:
                    cancel.set()

            with mock.patch.object(jobs.chromium, "BrowserRenderer", FakeRenderer):
                results = core.convert_batch(
                    files,
                    cancel_event=cancel,
                    progress_callback=on_progress,
                )
            self.assertEqual(
                [item["status"] for item in results],
                ["ok", "cancelled", "cancelled"],
            )
            self.assertEqual(progress, [
                (1, 3, "ok"), (2, 3, "cancelled"), (3, 3, "cancelled"),
            ])
            self.assertEqual(FakeRenderer.entered, 1)

    def test_already_cancelled_batch_does_not_launch_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "one.md"
            source.write_text("# One", encoding="utf-8")
            cancel = threading.Event()
            cancel.set()
            with mock.patch.object(jobs.chromium, "BrowserRenderer") as renderer:
                results = core.convert_batch([source], cancel_event=cancel)
            renderer.assert_not_called()
            self.assertEqual(results[0]["status"], "cancelled")

    def test_cancelled_batch_ignores_presentation_callback_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "one.md"
            source.write_text("# One", encoding="utf-8")
            cancel = threading.Event()
            cancel.set()

            def broken_callback(*unused):
                raise RuntimeError("presentation failed")

            results = core.convert_batch(
                [source],
                cancel_event=cancel,
                progress_callback=broken_callback,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "cancelled")

    def test_batch_reports_exact_engine_stages_and_ignores_callback_failure(self):
        class FakeRenderer:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def render(self, full_html, output_path, header_footer, render_date):
                output_path.write_bytes(b"%PDF-1.4\nmock")

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "one.md"
            source.write_text("# One", encoding="utf-8")
            stages = []

            def on_stage(index, total, input_path, stage):
                stages.append((index, total, input_path.name, stage))

            with mock.patch.object(jobs.chromium, "BrowserRenderer", FakeRenderer):
                results = core.convert_batch([source], stage_callback=on_stage)
                resilient = core.convert_batch(
                    [source], overwrite=True,
                    stage_callback=lambda *unused: (_ for _ in ()).throw(
                        RuntimeError("presentation failed")
                    ),
                )

        self.assertEqual(results[0]["status"], "ok")
        self.assertEqual(resilient[0]["status"], "ok")
        self.assertEqual(
            stages,
            [
                (1, 1, "one.md", "preparing"),
                (1, 1, "one.md", "rendering"),
                (1, 1, "one.md", "finalizing"),
                (1, 1, "one.md", "publishing"),
            ],
        )

    def test_current_item_cancellation_preserves_existing_output(self):
        class CancellingRenderer:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def render(self, full_html, output_path, header_footer, render_date):
                output_path.write_bytes(b"new")
                cancel_current.set()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "one.md"
            output = root / "one.pdf"
            source.write_text("# One", encoding="utf-8")
            output.write_bytes(b"old")
            cancel_current = threading.Event()
            with mock.patch.object(
                jobs.chromium, "BrowserRenderer", CancellingRenderer
            ):
                results = core.convert_batch(
                    [source],
                    overwrite=True,
                    cancel_current_event=cancel_current,
                )
            self.assertEqual(results[0]["status"], "cancelled")
            self.assertEqual(results[0]["error_code"], "CANCELLED")
            self.assertEqual(output.read_bytes(), b"old")
            self.assertEqual(list(root.glob(".libremark-*.pdf")), [])

    def test_current_item_cancellation_cancels_remaining_items(self):
        class CancellingRenderer:
            rendered = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def render(self, full_html, output_path, header_footer, render_date):
                type(self).rendered += 1
                output_path.write_bytes(b"new")
                cancel_current.set()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = [root / "one.md", root / "two.md"]
            for path in files:
                path.write_text("# " + path.stem, encoding="utf-8")
            cancel_current = threading.Event()
            with mock.patch.object(
                jobs.chromium, "BrowserRenderer", CancellingRenderer
            ):
                results = core.convert_batch(
                    files, cancel_current_event=cancel_current
                )
            self.assertEqual(
                [item["status"] for item in results],
                ["cancelled", "cancelled"],
            )
            self.assertEqual(CancellingRenderer.rendered, 1)
            self.assertFalse(any(path.with_suffix(".pdf").exists() for path in files))


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
        encoded = base64.b64encode(payload).decode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(core.ConversionError, "FORBIDDEN_RESOURCE"):
                core.embed_local_resources(
                    '<img src="data:image/svg+xml;base64,{0}">'.format(encoded), tmp
                )

    def test_svg_extension_requires_svg_content(self):
        payload = base64.b64encode(b"not an SVG").decode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(core.ConversionError, "SVG signature"):
                core.embed_local_resources(
                    '<img src="data:image/svg+xml;base64,{0}">'.format(payload), tmp
                )

    def test_standard_static_svg_is_embedded_but_external_href_is_rejected(self):
        safe = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
        unsafe = (b'<svg xmlns="http://www.w3.org/2000/svg" '
                  b'href="https://example.invalid/image.png"/>')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "safe.svg").write_bytes(safe)
            self.assertIn("data:image/svg+xml;base64,", core.embed_local_resources(
                '<img src="safe.svg">', root
            ))
            (root / "unsafe.svg").write_bytes(unsafe)
            with self.assertRaisesRegex(core.ConversionError, "active or network-capable"):
                core.embed_local_resources('<img src="unsafe.svg">', root)

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
    def test_standard_static_svg_renders_offline(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8"/></svg>'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "document.md"
            source.write_text("![Static SVG](image.svg)", encoding="utf-8")
            (root / "image.svg").write_bytes(svg)
            output = root / "document.pdf"
            with chromium.BrowserRenderer() as renderer:
                core.convert_markdown_to_pdf(source, output, _renderer=renderer)
                self.assertEqual(renderer.last_observed_requests, [])
            self.assertGreater(output.stat().st_size, 0)

    def test_safe_and_trusted_static_rendering_observe_zero_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_output = root / "safe.pdf"
            trusted_output = root / "trusted.pdf"
            with chromium.BrowserRenderer() as renderer:
                core.convert_markdown_text_to_pdf(
                    "# Safe\n\nLiteral <b>markup</b>", safe_output, _renderer=renderer
                )
                self.assertEqual(renderer.last_observed_requests, [])
                core.convert_markdown_text_to_pdf(
                    "# Trusted\n\n<div class=\"note\">static content</div>",
                    trusted_output,
                    trusted_html=True,
                    _renderer=renderer,
                )
                self.assertEqual(renderer.last_observed_requests, [])

    def test_convert_markdown_text_to_pdf_creates_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.pdf"
            result = core.convert_markdown_text_to_pdf("# Hello\n\nWorld.", output)
            self.assertEqual(result, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)

    def test_locked_engine_emits_tagged_pdf_and_outline(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "accessible.pdf"
            core.convert_markdown_text_to_pdf("# Heading\n\nBody.", output)
            pdf = output.read_bytes()
            self.assertIn(b"/StructTreeRoot", pdf)
            self.assertIn(b"/Outlines", pdf)

    def test_convert_batch_reports_per_file_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.md"
            good.write_text("# Good\n\nfine.", encoding="utf-8")
            missing = Path(tmp) / "missing.md"

            results = core.convert_batch([good, missing], output_dir=tmp)
            statuses = {Path(r["input"]).name: r["status"] for r in results}
            self.assertEqual(statuses["good.md"], "ok")
            self.assertEqual(statuses["missing.md"], "error")

    def test_preview_session_reuses_loaded_page_for_header_footer_changes(self):
        renderer = mock.MagicMock()
        renderer.__enter__.return_value = renderer
        context = mock.MagicMock()
        page = mock.MagicMock()
        renderer._open_page.return_value = (context, page)
        document = core.RenderDocument(
            "<html>same visual content</html>",
            mock.MagicMock(),
            "2026-07-18",
        )
        first = core.HeaderFooterConfig(top_left="First")
        second = core.HeaderFooterConfig(top_left="Second")
        with mock.patch.object(preview.chromium, "BrowserRenderer", return_value=renderer):
            with mock.patch.object(
                preview.document, "prepare_render_document", return_value=document
            ) as prepare:
                with mock.patch.object(
                    preview, "rasterize_pdf_page",
                    return_value=preview.PreviewPage(1, 1, b"png"),
                ):
                    with core.PreviewSession() as session:
                        session.render_png("# Same", header_footer=first)
                        session.render_png("# Same", header_footer=second)
        self.assertEqual(page.set_content.call_count, 1)
        self.assertEqual(renderer._render_loaded_page.call_count, 2)
        self.assertIs(
            renderer._render_loaded_page.call_args_list[0].args[2], first
        )
        self.assertIs(
            renderer._render_loaded_page.call_args_list[1].args[2], second
        )
        self.assertTrue(
            prepare.call_args_list[0].kwargs["_include_profile_fingerprint"]
            is False
        )

    def test_preview_session_reloads_page_when_visual_content_changes(self):
        renderer = mock.MagicMock()
        renderer.__enter__.return_value = renderer
        page = mock.MagicMock()
        renderer._open_page.return_value = (mock.MagicMock(), page)
        documents = [
            core.RenderDocument("<html>one</html>", mock.MagicMock(), "2026-07-18"),
            core.RenderDocument("<html>two</html>", mock.MagicMock(), "2026-07-18"),
        ]
        with mock.patch.object(preview.chromium, "BrowserRenderer", return_value=renderer):
            with mock.patch.object(
                preview.document, "prepare_render_document", side_effect=documents
            ):
                with mock.patch.object(
                    preview, "rasterize_pdf_page",
                    return_value=preview.PreviewPage(1, 1, b"png"),
                ):
                    with core.PreviewSession() as session:
                        session.render_png("# One")
                        session.render_png("# Two")
        self.assertEqual(page.set_content.call_count, 2)

    def test_render_preview_png_returns_valid_png_bytes(self):
        png_bytes = core.render_preview_png("# Hello\n\nWorld.", dpi=60)
        self.assertIsInstance(png_bytes, bytes)
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(png_bytes), 100)

    def test_preview_session_rasterizes_first_middle_and_last_from_one_pdf(self):
        markdown = "# Multipage\n\n" + "\n\n".join(
            "## Section {0}\n\n{1}".format(
                index,
                "Local preview content. " * 12,
            )
            for index in range(1, 121)
        )
        with core.PreviewSession() as session:
            first = session.render_document(markdown, dpi=45)
            self.assertGreaterEqual(first.total, 3)
            middle_number = (first.total + 1) // 2
            middle = session.render_page(middle_number, dpi=45)
            last = session.render_page(first.total, dpi=45)
            pdf_path = session._preview_pdf_path
            self.assertTrue(pdf_path.exists())
        self.assertFalse(pdf_path.exists())
        for rendered, expected_page in (
            (first, 1),
            (middle, middle_number),
            (last, first.total),
        ):
            self.assertEqual(rendered.page, expected_page)
            self.assertEqual(rendered.total, first.total)
            self.assertTrue(rendered.png.startswith(b"\x89PNG\r\n\x1a\n"))


if __name__ == "__main__":
    unittest.main()
