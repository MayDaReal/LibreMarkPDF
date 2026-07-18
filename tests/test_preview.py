"""Regression coverage for the preview engine boundary."""

import builtins
import unittest
from unittest import mock

from libremark_pdf import core
from libremark_pdf.engine import preview


class TestPreviewBoundary(unittest.TestCase):
    def test_core_reexports_the_canonical_preview_types(self):
        self.assertIs(core.PreviewSession, preview.PreviewSession)
        self.assertIs(core.render_preview_png, preview.render_preview_png)

    def test_preview_does_not_import_the_public_facade(self):
        with open(preview.__file__, encoding="utf-8") as source:
            self.assertNotIn("libremark_pdf.core", source.read())

    def test_missing_pdfium_has_an_actionable_error(self):
        original_import = builtins.__import__

        def without_pdfium(name, *args, **kwargs):
            if name == "pypdfium2":
                raise ImportError("not installed")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=without_pdfium):
            with self.assertRaisesRegex(core.ConversionError, "pypdfium2.*pip install"):
                preview.first_page_png(None, 72)

    def test_failed_page_is_not_reused_and_the_session_is_cleaned_up(self):
        renderer = mock.MagicMock()
        renderer.__enter__.return_value = renderer
        context = mock.MagicMock()
        page = mock.MagicMock()
        renderer._open_page.return_value = (context, page)
        rendered_document = core.RenderDocument("<html>same</html>", mock.MagicMock(), "2026-07-18")
        renderer._render_loaded_page.side_effect = [
            core.ConversionError("RENDER_FAILED: simulated"), None,
        ]
        with mock.patch.object(preview.chromium, "BrowserRenderer", return_value=renderer):
            with mock.patch.object(preview.document, "prepare_render_document", return_value=rendered_document):
                with mock.patch.object(preview, "first_page_png", return_value=b"png"):
                    with preview.PreviewSession() as session:
                        with self.assertRaises(core.ConversionError):
                            session.render_png("# Same")
                        self.assertEqual(session.render_png("# Same"), b"png")
        self.assertEqual(page.set_content.call_count, 2)
        context.close.assert_called_once_with()
        renderer.__exit__.assert_called_once_with(None, None, None)
