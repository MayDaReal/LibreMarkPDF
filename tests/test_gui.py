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

from libremark_pdf import desktop_services, gui
from libremark_pdf.desktop import services
from libremark_pdf.desktop.tk import app as tk_app
from libremark_pdf.desktop.tk import conversion as tk_conversion
from libremark_pdf.desktop.tk import dialogs as tk_dialogs
from libremark_pdf.desktop.tk import layout as tk_layout
from libremark_pdf.desktop.tk import preview as tk_preview


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
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
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
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
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
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
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
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
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
        with mock.patch.object(services.core, "PreviewSession", Session):
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
        with mock.patch.object(services.core, "PreviewSession", return_value=session):
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

        with mock.patch.object(services.core, "convert_batch", side_effect=convert):
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


class TestGuiAutomationContract(unittest.TestCase):
    def test_semantic_actions_cover_primary_desktop_workflow(self):
        expected = {
            "files.add", "advanced.toggle", "preview.refresh", "output.choose",
            "convert.start", "convert.cancel", "language.en", "language.fr",
        }
        self.assertTrue(expected.issubset(tk_layout.AUTOMATION_ACTIONS))

    def test_automation_lookup_uses_semantic_actions(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        widget = object()
        app._automation_widgets = {"convert.start": widget}
        self.assertIs(app.automation_widget("convert.start"), widget)
        with self.assertRaisesRegex(ValueError, "Unknown desktop automation action"):
            app.automation_widget("missing")


class TestGuiStateAndPlatformAdapters(unittest.TestCase):
    def test_render_options_preserve_all_desktop_input_values(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.css_path = "custom.css"
        app.theme_var = mock.Mock()
        app.theme_var.get.return_value = "ignored@1"
        app.render_date_var = mock.Mock()
        app.render_date_var.get.return_value = " 2026-07-20 "
        app.trusted_html_var = mock.Mock()
        app.trusted_html_var.get.return_value = True
        values = {
            "header_left": "{title}",
            "header_center": "{date}",
            "header_right": "right",
            "footer_left": "left",
            "footer_center": "Page {page} / {total}",
            "footer_right": "{titre}",
        }
        app.hf_vars = {}
        for key, value in values.items():
            variable = mock.Mock()
            variable.get.return_value = value
            app.hf_vars[key] = variable

        options = app._render_options()

        self.assertEqual(options["css_path"], "custom.css")
        self.assertIsNone(options["theme"])
        self.assertEqual(options["render_date"], "2026-07-20")
        self.assertIs(options["trusted_html"], True)
        self.assertEqual(
            options["header_footer"],
            services.core.HeaderFooterConfig(
                top_left="{title}",
                top_center="{date}",
                top_right="right",
                bottom_left="left",
                bottom_center="Page {page} / {total}",
                bottom_right="{titre}",
            ),
        )

    def test_render_options_use_selected_theme_without_custom_css(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.css_path = None
        app.theme_var = mock.Mock()
        app.theme_var.get.return_value = "default@1"
        app.render_date_var = mock.Mock()
        app.render_date_var.get.return_value = " "
        app.trusted_html_var = mock.Mock()
        app.trusted_html_var.get.return_value = False
        app._current_header_footer = mock.Mock(
            return_value=services.core.HeaderFooterConfig.none()
        )

        self.assertEqual(
            app._render_options(),
            {
                "css_path": None,
                "header_footer": services.core.HeaderFooterConfig.none(),
                "render_date": None,
                "trusted_html": False,
                "theme": "default@1",
            },
        )

    def test_generation_passes_a_snapshot_of_files_and_options_to_service(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_running = False
        app.files = [Path("one.md"), Path("two.md")]
        app.output_dir = "exports"
        app._overwrite_choice = mock.Mock(return_value=True)
        app._invalidate_preview = mock.Mock()
        app._render_options = mock.Mock(
            return_value={"theme": "default@1", "render_date": None}
        )
        app.progress = mock.Mock()
        app.progress_var = mock.Mock()
        app._clear_results = mock.Mock()
        app._begin_operation = mock.Mock()
        app._set_status = mock.Mock()
        app.services = mock.Mock()
        app._result_queue = queue.Queue()
        app._schedule_queue_poll = mock.Mock()
        profile = mock.Mock(render_date="2026-07-20")
        worker = mock.Mock()

        with mock.patch.object(
            services.core, "render_profile_for_options", return_value=profile
        ) as render_profile:
            with mock.patch.object(
                tk_conversion.threading, "Thread", return_value=worker
            ) as thread:
                app._on_generate_clicked()

        render_profile.assert_called_once_with(
            theme="default@1", render_date=None
        )
        thread.assert_called_once()
        call = thread.call_args
        self.assertIs(call.kwargs["target"], app.services.run_conversion_job)
        self.assertTrue(call.kwargs["daemon"])
        result_queue, files, options, cancel_event = call.kwargs["args"]
        self.assertIs(result_queue, app._result_queue)
        self.assertEqual(files, [Path("one.md"), Path("two.md")])
        self.assertIsNot(files, app.files)
        self.assertEqual(
            options,
            {
                "theme": "default@1",
                "render_date": "2026-07-20",
                "output_dir": "exports",
                "overwrite": True,
            },
        )
        self.assertIs(cancel_event, app._cancel_event)
        self.assertFalse(cancel_event.is_set())
        worker.start.assert_called_once_with()

    def test_cancel_requests_stop_once_after_the_active_file(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app._cancel_event = threading.Event()
        app.cancel_button = mock.Mock()
        app._set_status = mock.Mock()

        app._cancel_conversion()
        app._cancel_conversion()

        self.assertTrue(app._cancel_event.is_set())
        app.cancel_button.config.assert_called_once_with(state="disabled")
        app._set_status.assert_called_once_with("status_cancelling")

    def test_preview_request_uses_the_first_file_without_reordering_batch(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_generation = 8
        app._preview_after = "scheduled"
        app.files = [Path("first.md"), Path("second.md")]
        app._render_options = mock.Mock(return_value={"theme": "default@1"})
        app._refresh_generate_button = mock.Mock()
        app._set_status = mock.Mock()
        app._preview_requests = queue.Queue()
        app._schedule_queue_poll = mock.Mock()
        profile = mock.Mock(render_date="2026-07-20")

        with mock.patch.object(
            services.core, "render_profile_for_options", return_value=profile
        ):
            app._start_preview(8)

        generation, source, markdown, options = app._preview_requests.get_nowait()
        self.assertEqual(generation, 8)
        self.assertEqual(source, Path("first.md"))
        self.assertIsNone(markdown)
        self.assertEqual(
            options,
            {
                "theme": "default@1",
                "render_date": "2026-07-20",
                "resource_root": Path("first.md").resolve().parent,
                "dpi": tk_preview.PREVIEW_DPI,
            },
        )
        self.assertEqual(app.files, [Path("first.md"), Path("second.md")])

    def test_zoom_follows_supported_levels_and_stops_at_bounds(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.zoom_percent = mock.Mock()
        current = [100]
        app.zoom_percent.get.side_effect = lambda: current[0]
        app.zoom_percent.set.side_effect = lambda value: current.__setitem__(0, value)
        app._redraw_preview = mock.Mock()

        expected = (125, 150, 200, 200, 150, 125, 100, 75, 50, 50)
        directions = (1, 1, 1, 1, -1, -1, -1, -1, -1, -1)
        observed = []
        for direction in directions:
            app._change_zoom(direction)
            observed.append(current[0])

        self.assertEqual(tuple(observed), expected)
        self.assertEqual(app._redraw_preview.call_count, len(directions))

    def test_initial_focus_is_given_to_browse_files(self):
        root = mock.Mock()
        services_boundary = mock.Mock()
        dialogs = mock.Mock()
        browse_button = mock.Mock()

        def build_ui(instance):
            instance.browse_button = browse_button

        variable = mock.Mock()
        variable.trace_add = mock.Mock()
        with mock.patch.object(tk_app.tk, "IntVar", return_value=variable):
            with mock.patch.object(tk_app.tk, "BooleanVar", return_value=variable):
                with mock.patch.object(tk_app.tk, "StringVar", return_value=variable):
                    with mock.patch.object(
                        gui.LibreMarkPdfApp, "_build_ui", autospec=True,
                        side_effect=build_ui,
                    ):
                        with mock.patch.object(
                            gui.LibreMarkPdfApp, "_bind_accessibility"
                        ):
                            with mock.patch.object(gui.LibreMarkPdfApp, "_retranslate"):
                                gui.LibreMarkPdfApp(
                                    root,
                                    services=services_boundary,
                                    dialogs=dialogs,
                                )

        browse_button.focus_set.assert_called_once_with()
        root.protocol.assert_called_once_with("WM_DELETE_WINDOW", mock.ANY)

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
        app.dialogs = mock.Mock()
        plans = [
            services.core.BatchPlan(
                Path("one.md"), Path("same.pdf"),
                "DUPLICATE_OUTPUT: duplicate destination",
            ),
            services.core.BatchPlan(
                Path("two.md"), Path("two.pdf"),
                "OUTPUT_EXISTS: refusing overwrite",
            ),
        ]
        app.dialogs.ask_collision_continue.return_value = True
        app.dialogs.ask_overwrite.return_value = False
        with mock.patch.object(services.core, "plan_batch_outputs", return_value=plans):
            choice = app._overwrite_choice()
        self.assertFalse(choice)
        app.dialogs.ask_collision_continue.assert_called_once()
        app.dialogs.ask_overwrite.assert_called_once()

    def test_result_actions_receive_successes_only(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._render_results = mock.Mock()
        app._set_status = mock.Mock()
        app._t = lambda key, **kwargs: key
        app.dialogs = mock.Mock()
        results = [
            {
                "input": "ok.md", "output": "ok.pdf", "status": "ok",
                "error": None, "error_code": None,
            },
            {
                "input": "bad.md", "output": None, "status": "error",
                "error": "failed", "error_code": "RENDER_FAILED",
            },
            {
                "input": "later.md", "output": None, "status": "cancelled",
                "error": "cancelled", "error_code": "CANCELLED",
            },
        ]
        app._handle_generate_done(results)
        app._render_results.assert_called_once_with([results[0]])
        app._set_status.assert_called_once_with(
            "status_done_summary", ok=1, failed=1, cancelled=1
        )
        app.dialogs.show_error.assert_called_once_with(
            "error_title", "bad.md: [RENDER_FAILED] failed"
        )

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
        output = Path("report.pdf")
        platform_os = mock.Mock()
        platform_os.name = "posix"
        with mock.patch.object(services, "os", platform_os):
            with mock.patch.object(services.sys, "platform", "linux"):
                with mock.patch.object(
                    services.subprocess, "Popen"
                ) as popen:
                    desktop_services.open_path(output)
        popen.assert_called_once_with(["xdg-open", str(output)])

    def test_source_contains_scroll_zoom_keyboard_and_focus_contracts(self):
        source = "\n".join(
            Path(module.__file__).read_text(encoding="utf-8")
            for module in (tk_app, tk_layout, tk_preview)
        )
        for marker in (
            "body_canvas", "file_canvas", "preview_canvas",
            "ZOOM_LEVELS", "<Control-o>", "<Control-r>", "focus_set()",
        ):
            self.assertIn(marker, source)

    def test_tk_adapter_uses_an_injected_toolkit_neutral_service_boundary(self):
        signature = inspect.signature(gui.LibreMarkPdfApp.__init__)
        self.assertIn("services", signature.parameters)
        service_source = Path(desktop_services.__file__).read_text(encoding="utf-8")
        self.assertNotIn("tkinter", service_source)
        self.assertNotIn("ImageTk", service_source)

    def test_root_gui_is_a_toolkit_free_launch_facade(self):
        source = Path(gui.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import tkinter", source)
        self.assertNotIn("ImageTk", source)
        self.assertIs(gui.LibreMarkPdfApp, tk_app.LibreMarkPdfApp)

    def test_obsolete_root_tk_compatibility_facades_are_absent(self):
        for name in (
            "gui_layout.py",
            "gui_inputs.py",
            "gui_preview.py",
            "gui_conversion.py",
        ):
            self.assertFalse((ROOT / "libremark_pdf" / name).exists())

    def test_result_open_uses_the_injected_desktop_service(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.services = mock.Mock()
        app.dialogs = mock.Mock()
        app._t = lambda key, **kwargs: key
        output = Path("/tmp/report.pdf")
        app._open_result(output)
        app.services.open_path.assert_called_once_with(output)

    def test_open_path_error_uses_the_injected_dialog(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.services = mock.Mock()
        app.services.open_path.side_effect = RuntimeError("unavailable")
        app.dialogs = mock.Mock()
        app._t = lambda key, **kwargs: key
        app._open_result(Path("/tmp/report.pdf"))
        app.dialogs.show_error.assert_called_once_with(
            "error_title", "open_error"
        )

    def test_dialog_boundary_keeps_native_return_values_and_arguments(self):
        dialogs = tk_dialogs.TkDialogs()
        with mock.patch.object(tk_dialogs.filedialog, "askopenfilenames", return_value=("one.md",)) as files:
            self.assertEqual(
                dialogs.choose_markdown_files("Choose", [("Markdown", "*.md")]),
                ("one.md",),
            )
        files.assert_called_once_with(
            title="Choose", filetypes=[("Markdown", "*.md")]
        )
        with mock.patch.object(tk_dialogs.messagebox, "askyesnocancel", return_value=None) as overwrite:
            self.assertIsNone(dialogs.ask_overwrite("Existing", "Replace?"))
        overwrite.assert_called_once_with("Existing", "Replace?")

    def test_native_dialog_calls_are_confined_to_the_dialog_boundary(self):
        for module in (tk_app, tk_layout, tk_preview):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("messagebox", source)
            self.assertNotIn("filedialog", source)
        for module_name in ("inputs", "conversion"):
            source = (
                ROOT / "libremark_pdf" / "desktop" / "tk" / (module_name + ".py")
            ).read_text(encoding="utf-8")
            self.assertNotIn("messagebox", source)
            self.assertNotIn("filedialog", source)

    def test_no_files_and_invalid_options_use_injected_dialogs(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_running = False
        app.files = []
        app._t = lambda key, **kwargs: key
        app.dialogs = mock.Mock()
        app._on_generate_clicked()
        app.dialogs.show_error.assert_called_once_with("error_title", "error_no_files")

        app.files = [Path("one.md")]
        app._overwrite_choice = mock.Mock(return_value=False)
        app._invalidate_preview = mock.Mock()
        app._render_options = mock.Mock(return_value={})
        app._set_status = mock.Mock()
        with mock.patch.object(
            services.core, "render_profile_for_options", side_effect=RuntimeError("invalid")
        ):
            app._on_generate_clicked()
        app.dialogs.show_error.assert_called_with("error_title", "invalid")
        app._set_status.assert_called_once_with("status_generation_error", error="invalid")


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
