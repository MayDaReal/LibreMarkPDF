"""Characterization tests for toolkit-independent desktop services."""

import inspect
import queue
import threading
import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import desktop_services
from libremark_pdf.desktop import contracts, services


class TestDesktopServiceBoundary(unittest.TestCase):
    def test_root_module_reexports_the_canonical_services(self):
        for name in (
            "DEFAULT_DESKTOP_SERVICES",
            "DesktopServices",
            "open_path",
            "run_conversion_job",
            "run_preview_worker",
        ):
            self.assertIs(getattr(desktop_services, name), getattr(services, name))

    def test_services_are_toolkit_free_and_use_only_core(self):
        source = Path(services.__file__).read_text(encoding="utf-8")
        self.assertNotIn("tkinter", source)
        self.assertNotIn("ImageTk", source)
        self.assertIn("from .. import core", source)
        self.assertNotIn(".engine", source)

    def test_typed_preview_messages_preserve_tuple_compatibility(self):
        request = contracts.PreviewRequest(3, None, "# Preview", {"dpi": 90})
        self.assertEqual(request, (3, None, "# Preview", {"dpi": 90}))
        self.assertEqual(
            contracts.PreviewRequest.from_queue_item((3, None, "# Preview", {})),
            contracts.PreviewRequest(3, None, "# Preview", {}),
        )
        event = contracts.PreviewEvent("preview_ok", 3, b"png")
        self.assertEqual(event, ("preview_ok", 3, b"png"))
        document_request = contracts.PreviewDocumentRequest(
            4, Path("one.md"), None, {"dpi": 90}
        )
        self.assertEqual(
            document_request,
            (4, Path("one.md"), None, {"dpi": 90}),
        )
        self.assertEqual(
            contracts.PreviewPageRequest(4, 2, 90),
            (4, 2, 90),
        )

    def test_preview_worker_coalesces_typed_requests_and_isolates_errors(self):
        requests = queue.Queue()
        results = queue.Queue()
        session = mock.MagicMock()
        session.render_png.side_effect = RuntimeError("preview failed")
        requests.put(contracts.PreviewRequest(1, None, "old", {}))
        requests.put(contracts.PreviewRequest(2, None, "new", {}))
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
            worker = threading.Thread(
                target=services.run_preview_worker, args=(requests, results)
            )
            worker.start()
            event = results.get(timeout=2)
            requests.put(None)
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(event, ("preview_error", 2, "preview failed"))
        session.render_png.assert_called_once_with("new")

    def test_multipage_worker_renders_document_then_pages_in_one_session(self):
        requests = queue.Queue()
        results = queue.Queue()
        session = mock.MagicMock()
        session.render_document.return_value = services.core.PreviewPage(
            1, 3, b"page-1"
        )
        session.render_page.return_value = services.core.PreviewPage(
            2, 3, b"page-2"
        )
        requests.put(contracts.PreviewDocumentRequest(7, None, "# Pages", {"dpi": 90}))
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
            worker = threading.Thread(
                target=services.run_preview_worker, args=(requests, results)
            )
            worker.start()
            document_event = results.get(timeout=2)
            requests.put(contracts.PreviewPageRequest(7, 2, 90))
            page_event = results.get(timeout=2)
            requests.put(None)
            worker.join(2)

        self.assertFalse(worker.is_alive())
        self.assertEqual(
            document_event,
            ("preview_document_ok", 7, 1, 3, b"page-1"),
        )
        self.assertEqual(
            page_event,
            ("preview_page_ok", 7, 2, 3, b"page-2"),
        )
        session.render_document.assert_called_once_with("# Pages", dpi=90)
        session.render_page.assert_called_once_with(2, dpi=90)
        session.__enter__.assert_called_once_with()
        session.__exit__.assert_called_once_with(None, None, None)

    def test_page_error_retains_worker_session_for_another_request(self):
        requests = queue.Queue()
        results = queue.Queue()
        session = mock.MagicMock()
        session.render_document.return_value = services.core.PreviewPage(
            1, 2, b"page-1"
        )
        session.render_page.side_effect = [
            RuntimeError("page failed"),
            services.core.PreviewPage(2, 2, b"page-2"),
        ]
        requests.put(contracts.PreviewDocumentRequest(8, None, "# Pages", {}))
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
            worker = threading.Thread(
                target=services.run_preview_worker, args=(requests, results)
            )
            worker.start()
            results.get(timeout=2)
            requests.put(contracts.PreviewPageRequest(8, 2, 90))
            failed = results.get(timeout=2)
            requests.put(contracts.PreviewPageRequest(8, 2, 90))
            recovered = results.get(timeout=2)
            requests.put(None)
            worker.join(2)

        self.assertEqual(failed, ("preview_page_error", 8, 2, "page failed"))
        self.assertEqual(recovered, ("preview_page_ok", 8, 2, 2, b"page-2"))
        session.__exit__.assert_called_once_with(None, None, None)

    def test_conversion_worker_emits_typed_progress_and_terminal_events(self):
        results = queue.Queue()
        cancel_event = threading.Event()
        cancel_current_event = threading.Event()
        conversion = {"input": "one.md", "status": "ok"}

        def convert(files, progress_callback, stage_callback, **kwargs):
            self.assertEqual(files, [Path("one.md")])
            self.assertIs(kwargs["cancel_event"], cancel_event)
            self.assertIs(kwargs["cancel_current_event"], cancel_current_event)
            stage_callback(1, 1, Path("one.md"), "rendering")
            progress_callback(1, 1, conversion)
            return [conversion]

        with mock.patch.object(services.core, "convert_batch", side_effect=convert):
            services.run_conversion_job(
                results,
                [Path("one.md")],
                {},
                cancel_event,
                cancel_current_event,
            )
        self.assertEqual(
            results.get_nowait(),
            ("conversion_stage", 1, 1, Path("one.md"), "rendering"),
        )
        self.assertEqual(results.get_nowait(), ("progress", 1, 1, conversion))
        self.assertEqual(results.get_nowait(), ("generate_done", [conversion]))

    def test_worker_source_does_not_call_tk(self):
        for worker in (services.run_preview_worker, services.run_conversion_job):
            source = inspect.getsource(worker)
            self.assertNotIn("tk.", source)
            self.assertNotIn("messagebox", source)


if __name__ == "__main__":
    unittest.main()
