"""Headless checks for GUI orchestration and optional integration boundaries."""

import inspect
import os
import queue
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import gui


ROOT = Path(__file__).resolve().parent.parent


class TestGuiWorkerBoundaries(unittest.TestCase):
    def test_preview_worker_reuses_session_and_never_calls_tk(self):
        request_queue = queue.Queue()
        result_queue = queue.Queue()
        options = {"dpi": 90}
        worker_thread = []

        session = mock.MagicMock()
        session.render_png.side_effect = lambda markdown, **kwargs: (
            worker_thread.append(threading.get_ident())
            or b"\x89PNG\r\n\x1a\nmock"
        )
        request_queue.put((7, None, "# Preview", options))
        with mock.patch.object(gui.core, "PreviewSession", return_value=session):
            thread = threading.Thread(
                target=gui._run_preview_worker,
                args=(request_queue, result_queue),
            )
            thread.start()
            message = result_queue.get(timeout=2)
            request_queue.put(None)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertNotEqual(worker_thread[0], threading.get_ident())
        self.assertEqual(
            message,
            ("preview_ok", 7, b"\x89PNG\r\n\x1a\nmock"),
        )
        session.__enter__.assert_called_once_with()
        session.__exit__.assert_called_once_with(None, None, None)
        source = inspect.getsource(gui._run_preview_worker)
        self.assertNotIn("tk.", source)
        self.assertNotIn("messagebox", source)

    def test_preview_worker_coalesces_queued_requests_to_latest(self):
        request_queue = queue.Queue()
        result_queue = queue.Queue()
        rendered = []

        def render(markdown, **kwargs):
            rendered.append(markdown)
            return b"png"

        session = mock.MagicMock()
        session.render_png.side_effect = render
        request_queue.put((1, None, "old", {}))
        request_queue.put((2, None, "new", {}))
        with mock.patch.object(gui.core, "PreviewSession", return_value=session):
            thread = threading.Thread(
                target=gui._run_preview_worker,
                args=(request_queue, result_queue),
            )
            thread.start()
            message = result_queue.get(timeout=2)
            request_queue.put(None)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(rendered, ["new"])
        self.assertEqual(message, ("preview_ok", 2, b"png"))

    def test_preview_worker_reads_source_off_the_main_thread(self):
        request_queue = queue.Queue()
        result_queue = queue.Queue()
        source = mock.MagicMock(spec=Path)

        def read_text(encoding):
            self.assertNotEqual(threading.get_ident(), main_thread)
            return "# File"

        source.read_text.side_effect = read_text
        session = mock.MagicMock()
        session.render_png.return_value = b"png"
        main_thread = threading.get_ident()
        request_queue.put((3, source, None, {}))
        with mock.patch.object(gui.core, "PreviewSession", return_value=session):
            thread = threading.Thread(
                target=gui._run_preview_worker,
                args=(request_queue, result_queue),
            )
            thread.start()
            result_queue.get(timeout=2)
            request_queue.put(None)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        source.read_text.assert_called_once_with(encoding="utf-8")
        session.render_png.assert_called_once_with("# File")

    def test_preview_worker_reports_actionable_error(self):
        request_queue = queue.Queue()
        result_queue = queue.Queue()
        session = mock.MagicMock()
        session.render_png.side_effect = RuntimeError("preview failed")
        request_queue.put((4, None, "# Broken", {}))
        with mock.patch.object(gui.core, "PreviewSession", return_value=session):
            thread = threading.Thread(
                target=gui._run_preview_worker,
                args=(request_queue, result_queue),
            )
            thread.start()
            message = result_queue.get(timeout=2)
            request_queue.put(None)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(
            message,
            ("preview_error", 4, "preview failed"),
        )

    def test_preview_session_is_created_on_the_worker_thread(self):
        request_queue = queue.Queue()
        result_queue = queue.Queue()
        created_on = []
        main_thread = threading.get_ident()

        class Session:
            def __init__(self):
                created_on.append(threading.get_ident())

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def render_png(self, markdown, **kwargs):
                return b"png"

        request_queue.put((5, None, "# Thread", {}))
        with mock.patch.object(gui.core, "PreviewSession", Session):
            thread = threading.Thread(
                target=gui._run_preview_worker,
                args=(request_queue, result_queue),
            )
            thread.start()
            result_queue.get(timeout=2)
            request_queue.put(None)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertNotEqual(created_on[0], main_thread)

    def test_preview_refresh_remains_available_while_rendering(self):
        source = inspect.getsource(gui.LibreMarkPdfApp._start_preview)
        self.assertNotIn('refresh_preview_button.config(state="disabled")', source)

    def test_preview_worker_uses_render_options(self):
        request_queue = queue.Queue()
        result_queue = queue.Queue()
        options = {"dpi": 90}
        session = mock.MagicMock()
        session.render_png.return_value = b"png"
        request_queue.put((6, None, "# Preview", options))
        with mock.patch.object(gui.core, "PreviewSession", return_value=session):
            thread = threading.Thread(
                target=gui._run_preview_worker,
                args=(request_queue, result_queue),
            )
            thread.start()
            result_queue.get(timeout=2)
            request_queue.put(None)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        session.render_png.assert_called_once_with("# Preview", dpi=90)

    def test_conversion_worker_reports_progress_then_completion_by_queue(self):
        result_queue = queue.Queue()
        cancel = threading.Event()

        def convert(files, progress_callback, **kwargs):
            result = {
                "input": "one.md", "output": "one.pdf", "status": "ok",
                "error": None, "error_code": None,
            }
            progress_callback(1, 1, result)
            return [result]

        with mock.patch.object(gui.core, "convert_batch", side_effect=convert):
            gui._run_conversion_job(result_queue, [Path("one.md")], {}, cancel)
        self.assertEqual(result_queue.get_nowait()[0:3], ("progress", 1, 1))
        self.assertEqual(result_queue.get_nowait()[0], "generate_done")
        source = inspect.getsource(gui._run_conversion_job)
        self.assertNotIn("tk.", source)
        self.assertNotIn("messagebox", source)

    def test_stale_preview_generation_is_explicitly_checked(self):
        source = inspect.getsource(gui.LibreMarkPdfApp._poll_queue)
        self.assertIn("generation == self._preview_generation", source)

    def test_queue_completion_suppresses_dialogs_after_close_request(self):
        source = inspect.getsource(gui.LibreMarkPdfApp._poll_queue)
        self.assertGreaterEqual(source.count("if not self._close_requested"), 2)

    def test_preview_does_not_enter_the_global_blocking_operation(self):
        source = inspect.getsource(gui.LibreMarkPdfApp._start_preview)
        self.assertNotIn('_begin_operation("preview")', source)
        self.assertIn("self._preview_running = True", source)


class TestGuiStateAndPlatformAdapters(unittest.TestCase):
    def test_declined_collision_stops_before_render_options_or_worker(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_running = False
        app.files = [Path("one.md")]
        app._overwrite_choice = mock.Mock(return_value=None)
        app._render_options = mock.Mock()
        app._set_status = mock.Mock()
        app._on_generate_clicked()
        app._render_options.assert_not_called()
        app._set_status.assert_called_once_with("status_cancelled")

    def test_preflight_presents_collision_before_existing_output_choice(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.files = [Path("one.md"), Path("two.md")]
        app.output_dir = None
        app._t = lambda key, **kwargs: key
        plans = [
            gui.core.BatchPlan(
                Path("one.md"), Path("same.pdf"),
                "DUPLICATE_OUTPUT: duplicate destination",
            ),
            gui.core.BatchPlan(
                Path("two.md"), Path("two.pdf"),
                "OUTPUT_EXISTS: refusing overwrite",
            ),
        ]
        with mock.patch.object(gui.core, "plan_batch_outputs", return_value=plans):
            with mock.patch.object(
                gui.messagebox, "askokcancel", return_value=True
            ) as collision:
                with mock.patch.object(
                    gui.messagebox, "askyesnocancel", return_value=False
                ) as overwrite:
                    choice = app._overwrite_choice()
        self.assertFalse(choice)
        collision.assert_called_once()
        overwrite.assert_called_once()

    def test_result_actions_receive_successes_only(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._render_results = mock.Mock()
        app._set_status = mock.Mock()
        app._t = lambda key, **kwargs: key
        results = [
            {
                "input": "ok.md", "output": "ok.pdf", "status": "ok",
                "error": None, "error_code": None,
            },
            {
                "input": "bad.md", "output": None, "status": "error",
                "error": "failed", "error_code": "RENDER_FAILED",
            },
        ]
        with mock.patch.object(gui.messagebox, "showerror"):
            app._handle_generate_done(results)
        app._render_results.assert_called_once_with([results[0]])

    def test_close_during_generation_requests_cancel_before_destroy(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app.root = mock.Mock()
        app._cancel_event = threading.Event()
        app._preview_generation = 3
        app._set_status = mock.Mock()
        app._close_requested = False
        app._request_close()
        self.assertTrue(app._close_requested)
        self.assertTrue(app._cancel_event.is_set())
        self.assertEqual(app._preview_generation, 4)
        app.root.destroy.assert_not_called()
        app._set_status.assert_called_once_with("status_closing")

    def test_idle_close_is_immediate(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.root = mock.Mock()
        app._close_requested = False
        app._preview_after = "preview-after"
        app._poll_after = "poll-after"
        app._preview_generation = 2
        app._request_close()
        self.assertTrue(app._close_requested)
        self.assertEqual(app._preview_generation, 3)
        self.assertIsNone(app._preview_after)
        self.assertIsNone(app._poll_after)
        self.assertEqual(
            app.root.after_cancel.call_args_list,
            [mock.call("preview-after"), mock.call("poll-after")],
        )
        app.root.destroy.assert_called_once_with()

    def test_clear_files_does_not_start_a_sample_preview(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("one.md")]
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._invalidate_preview = mock.Mock()
        app._schedule_preview = mock.Mock()
        app._clear_files()
        self.assertEqual(app.files, [])
        app._invalidate_preview.assert_called_once_with(clear_image=True)
        app._schedule_preview.assert_not_called()

    def test_open_path_uses_argument_list_without_shell(self):
        with mock.patch.object(gui.os, "name", "posix"):
            with mock.patch.object(gui.sys, "platform", "linux"):
                with mock.patch.object(gui.subprocess, "Popen") as popen:
                    gui._open_path(Path("/tmp/report.pdf"))
        popen.assert_called_once_with(["xdg-open", "/tmp/report.pdf"])

    def test_source_contains_scroll_zoom_keyboard_and_focus_contracts(self):
        source = Path(gui.__file__).read_text(encoding="utf-8")
        for marker in (
            "body_canvas", "file_canvas", "preview_canvas",
            "ZOOM_LEVELS", "<Control-o>", "<Control-r>", "focus_set()",
        ):
            self.assertIn(marker, source)


class TestOptionalDragAndDrop(unittest.TestCase):
    def _run_import(self, block_dnd):
        blocker = (
            "import builtins\n"
            "original = builtins.__import__\n"
            "def guarded(name, *args, **kwargs):\n"
            "    if name == 'tkinterdnd2': raise ImportError('blocked for test')\n"
            "    return original(name, *args, **kwargs)\n"
            "builtins.__import__ = guarded\n"
            if block_dnd else ""
        )
        script = blocker + (
            "import libremark_pdf.gui as gui\n"
            "print('imported', gui._HAS_DND)\n"
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(ROOT),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_imports_with_installed_optional_drag_and_drop(self):
        completed = self._run_import(False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("imported ", completed.stdout)

    def test_imports_when_optional_drag_and_drop_is_unavailable(self):
        completed = self._run_import(True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "imported False")


if __name__ == "__main__":
    unittest.main()
