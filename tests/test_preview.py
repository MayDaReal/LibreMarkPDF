"""Regression coverage for the preview engine boundary."""

import builtins
import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import core
from libremark_pdf.engine import preview


class TestPreviewBoundary(unittest.TestCase):
    def test_core_reexports_the_canonical_preview_types(self):
        self.assertIs(core.PreviewSession, preview.PreviewSession)
        self.assertIs(core.PreviewPage, preview.PreviewPage)
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
                with mock.patch.object(
                    preview,
                    "rasterize_pdf_page",
                    return_value=preview.PreviewPage(1, 1, b"png"),
                ):
                    with preview.PreviewSession() as session:
                        with self.assertRaises(core.ConversionError):
                            session.render_png("# Same")
                        self.assertEqual(session.render_png("# Same"), b"png")
        self.assertEqual(page.set_content.call_count, 2)
        context.close.assert_called_once_with()
        renderer.__exit__.assert_called_once_with(None, None, None)

    def test_rasterizer_returns_requested_page_and_total_then_closes_pdfium(self):
        original_import = builtins.__import__
        image = mock.Mock()
        image.save.side_effect = lambda buffer, format: buffer.write(b"png")
        bitmap = mock.Mock()
        bitmap.to_pil.return_value = image
        page = mock.Mock()
        page.render.return_value = bitmap

        class Pdf:
            def __init__(self, path):
                self.path = path
                self.closed = False

            def __len__(self):
                return 3

            def __getitem__(self, index):
                self.index = index
                return page

            def close(self):
                self.closed = True

        pdf = Pdf("preview.pdf")
        pdfium = mock.Mock()
        pdfium.PdfDocument.return_value = pdf

        def import_pdfium(name, *args, **kwargs):
            if name == "pypdfium2":
                return pdfium
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=import_pdfium):
            rendered = preview.rasterize_pdf_page(Path("preview.pdf"), 2, 90)

        self.assertEqual(rendered, preview.PreviewPage(2, 3, b"png"))
        self.assertEqual(pdf.index, 1)
        page.render.assert_called_once_with(scale=90 / 72)
        bitmap.close.assert_called_once_with()
        page.close.assert_called_once_with()
        self.assertTrue(pdf.closed)

    def test_session_keeps_one_pdf_and_caches_pages_until_close(self):
        renderer = mock.MagicMock()
        renderer.__enter__.return_value = renderer
        renderer._open_page.return_value = (mock.MagicMock(), mock.MagicMock())
        renderer._render_loaded_page.side_effect = (
            lambda page, path, *args, **kwargs: path.write_bytes(b"%PDF-mock")
        )
        rendered_document = core.RenderDocument(
            "<html>document</html>", mock.MagicMock(), "2026-07-21"
        )
        paths = []

        def rasterize(path, page, dpi):
            self.assertTrue(path.exists())
            paths.append(path)
            return preview.PreviewPage(page, 3, "page-{0}".format(page).encode())

        with mock.patch.object(preview.chromium, "BrowserRenderer", return_value=renderer):
            with mock.patch.object(
                preview.document,
                "prepare_render_document",
                return_value=rendered_document,
            ):
                with mock.patch.object(
                    preview, "rasterize_pdf_page", side_effect=rasterize
                ) as raster:
                    with preview.PreviewSession() as session:
                        first = session.render_document("# Document", dpi=90)
                        pdf_path = session._preview_pdf_path
                        second = session.render_page(2, dpi=90)
                        cached = session.render_page(2, dpi=90)
                        self.assertTrue(pdf_path.exists())
                    self.assertFalse(pdf_path.exists())

        self.assertEqual(first, preview.PreviewPage(1, 3, b"page-1"))
        self.assertEqual(second, preview.PreviewPage(2, 3, b"page-2"))
        self.assertEqual(cached, second)
        self.assertEqual(raster.call_count, 2)
        renderer._render_loaded_page.assert_called_once()

    def test_new_document_replaces_pdf_and_invalidates_page_cache(self):
        renderer = mock.MagicMock()
        renderer.__enter__.return_value = renderer
        renderer._open_page.return_value = (mock.MagicMock(), mock.MagicMock())
        documents = [
            core.RenderDocument("<html>one</html>", mock.MagicMock(), "2026-07-21"),
            core.RenderDocument("<html>two</html>", mock.MagicMock(), "2026-07-21"),
        ]
        with mock.patch.object(preview.chromium, "BrowserRenderer", return_value=renderer):
            with mock.patch.object(
                preview.document,
                "prepare_render_document",
                side_effect=documents,
            ):
                with mock.patch.object(
                    preview,
                    "rasterize_pdf_page",
                    side_effect=lambda path, page, dpi: preview.PreviewPage(
                        page, 2, path.read_bytes()
                    ),
                ):
                    renderer._render_loaded_page.side_effect = (
                        lambda page, path, *args, **kwargs: path.write_bytes(
                            str(renderer._render_loaded_page.call_count).encode()
                        )
                    )
                    with preview.PreviewSession() as session:
                        session.render_document("# One")
                        first_path = session._preview_pdf_path
                        session.render_document("# Two")
                        second_path = session._preview_pdf_path
                        self.assertNotEqual(first_path, second_path)
                        self.assertFalse(first_path.exists())
                        self.assertTrue(second_path.exists())
                    self.assertFalse(second_path.exists())

    def test_page_failure_preserves_cached_pages_and_bounds(self):
        session = preview.PreviewSession()
        session._preview_pdf_path = Path("preview.pdf")
        session._page_count = 3
        session._page_cache = {(1, 90): b"page-1"}
        with mock.patch.object(
            preview,
            "rasterize_pdf_page",
            side_effect=core.ConversionError("RENDER_FAILED: page 2"),
        ) as raster:
            with self.assertRaisesRegex(core.ConversionError, "page 2"):
                session.render_page(2, dpi=90)
            self.assertEqual(
                session.render_page(1, dpi=90),
                preview.PreviewPage(1, 3, b"page-1"),
            )
            with self.assertRaisesRegex(
                core.ConversionError, "PREVIEW_PAGE_OUT_OF_RANGE"
            ):
                session.render_page(4, dpi=90)
        raster.assert_called_once_with(Path("preview.pdf"), 2, 90)
