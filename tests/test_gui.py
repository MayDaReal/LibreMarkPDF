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
from libremark_pdf.desktop.tk import components as tk_components
from libremark_pdf.desktop.tk import conversion as tk_conversion
from libremark_pdf.desktop.tk import dialogs as tk_dialogs
from libremark_pdf.desktop.tk import layout as tk_layout
from libremark_pdf.desktop.tk import preview as tk_preview
from libremark_pdf.desktop.tk import styles as tk_styles


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

    def test_stale_preview_response_does_not_replace_current_state(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._poll_after = None
        app._result_queue = queue.Queue()
        app._result_queue.put(("preview_ok", 2, b"stale"))
        app._preview_generation = 3
        app._preview_last_submitted = 2
        app._preview_running = True
        app.operation = "idle"
        app._apply_preview_image = mock.Mock()
        app._set_preview_error = mock.Mock()
        app._refresh_generate_button = mock.Mock()

        app._poll_queue()

        self.assertFalse(app._preview_running)
        app._apply_preview_image.assert_not_called()
        app._set_preview_error.assert_not_called()
        app._refresh_generate_button.assert_called_once_with()

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
            "style.toggle", "destination.toggle", "header_footer.toggle",
            "other.toggle",
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
    def test_initial_window_size_targets_1060_by_720_and_respects_limits(self):
        root = mock.Mock()
        root.winfo_screenwidth.return_value = 1920
        root.winfo_screenheight.return_value = 1080
        self.assertEqual(tk_layout.initial_window_size(root), (1060, 720))

        root.winfo_screenwidth.return_value = 800
        root.winfo_screenheight.return_value = 600
        self.assertEqual(tk_layout.initial_window_size(root), (800, 600))

        root.winfo_screenwidth.return_value = 500
        root.winfo_screenheight.return_value = 400
        self.assertEqual(tk_layout.initial_window_size(root), (560, 520))

    def test_reference_widths_select_large_medium_and_narrow_modes(self):
        expected = {
            1440: "large",
            1280: "large",
            1100: "large",
            1024: "medium",
            820: "medium",
            720: "narrow",
            560: "narrow",
        }
        self.assertEqual(
            {
                width: tk_layout.responsive_mode(width)
                for width in expected
            },
            expected,
        )
        self.assertEqual(tk_layout.responsive_mode(759), "narrow")
        self.assertEqual(tk_layout.responsive_mode(760), "medium")
        self.assertEqual(tk_layout.responsive_mode(1099), "medium")
        self.assertEqual(tk_layout.responsive_mode(1100), "large")

    def test_responsive_transitions_reuse_widgets_without_moving_focus(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._layout_mode = None
        app.workspace = mock.Mock()
        app.source_group = mock.Mock()
        app.preview_group = mock.Mock()
        app.theme_group = mock.Mock()
        app.output_group = mock.Mock()
        app.advanced_group = mock.Mock()
        app.other_group = mock.Mock()
        app.results_frame = mock.Mock()
        app.header_footer_entry_rows = [
            [mock.Mock(), mock.Mock(), mock.Mock()],
            [mock.Mock(), mock.Mock(), mock.Mock()],
        ]
        app.header_footer_field_rows = [
            [mock.Mock(), mock.Mock(), mock.Mock()],
            [mock.Mock(), mock.Mock(), mock.Mock()],
        ]
        app._enforce_compact_accordions = mock.Mock()
        app.body = mock.Mock()
        app.action_bar = mock.Mock()
        app.preview_canvas = mock.Mock()
        app.status_label = mock.Mock()
        app.root = mock.Mock()
        widgets = (
            app.source_group,
            app.preview_group,
            app.advanced_group,
            app.preview_canvas,
            app.status_label,
        )

        app._apply_responsive_layout(560, 520)
        app.preview_group.grid.assert_called_with(
            row=1,
            column=0,
            sticky="nsew",
            pady=(0, tk_styles.SECTION_GAP),
        )
        for fields in app.header_footer_field_rows:
            for field in fields:
                field.pack.assert_called_with(
                    fill="x",
                    pady=(0, tk_styles.SPACE_XS),
                )
        app._apply_responsive_layout(1100, 700)

        self.assertEqual(
            widgets,
            (
                app.source_group,
                app.preview_group,
                app.advanced_group,
                app.preview_canvas,
                app.status_label,
            ),
        )
        app.root.focus_get.assert_not_called()
        app.root.focus_set.assert_not_called()
        self.assertEqual(app._layout_mode, "large")
        app.source_group.grid.assert_called_with(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, tk_styles.SECTION_GAP),
            pady=(0, tk_styles.SECTION_GAP),
        )
        app.preview_group.grid.assert_called_with(
            row=0,
            column=1,
            rowspan=6,
            sticky="nsew",
        )

    def test_primary_action_and_progress_are_outside_scrolling_content(self):
        source = inspect.getsource(tk_layout.TkLayoutMixin._build_ui)
        self.assertIn("self.action_bar = ttk.Frame(\n            self.root", source)
        self.assertIn(
            "self.progress = ttk.Progressbar(\n"
            "            self.action_bar",
            source,
        )
        self.assertLess(
            source.index("self.action_bar.pack"),
            source.index("container.pack"),
        )
        self.assertIn(
            "self.root.minsize(MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT)",
            source,
        )

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

    def test_css_selection_and_theme_restore_remain_exclusive(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.dialogs = mock.Mock()
        app.dialogs.choose_css_file.return_value = "styles/print.css"
        app._t = lambda key, **kwargs: key
        app.css_path = None
        app.style_mode_var = mock.Mock()
        app._refresh_css_entry = mock.Mock()
        app._render_theme_cards = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._choose_css()

        self.assertEqual(app.css_path, "styles/print.css")
        app.style_mode_var.set.assert_called_with("css")

        app._reset_css()

        self.assertIsNone(app.css_path)
        app.style_mode_var.set.assert_called_with("theme")
        self.assertEqual(app._schedule_preview.call_count, 2)

    def test_header_footer_reset_changes_only_the_six_fields(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.hf_vars = {
            key: mock.Mock()
            for key in (
                "header_left", "header_center", "header_right",
                "footer_left", "footer_center", "footer_right",
            )
        }
        app.render_date_var = mock.Mock()
        app.trusted_html_var = mock.Mock()
        app._refresh_accordion_headers = mock.Mock()

        app._reset_header_footer()

        expected = {
            "header_left": "",
            "header_center": "",
            "header_right": "",
            "footer_left": "",
            "footer_center": "Page {page} / {total}",
            "footer_right": "",
        }
        for key, value in expected.items():
            app.hf_vars[key].set.assert_called_once_with(value)
        app.render_date_var.set.assert_not_called()
        app.trusted_html_var.set.assert_not_called()

    def test_destination_choose_and_reset_preserve_global_batch_value(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.dialogs = mock.Mock()
        app.dialogs.choose_output_folder.return_value = "exports"
        app._t = lambda key, **kwargs: key
        app.output_dir = None
        app._refresh_output_entry = mock.Mock()

        app._choose_output_dir()
        self.assertEqual(app.output_dir, "exports")
        app._reset_output_dir()
        self.assertIsNone(app.output_dir)
        self.assertEqual(app._refresh_output_entry.call_count, 2)

    def test_destination_summary_handles_one_many_and_custom_folder(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._t = lambda key, **kwargs: key
        app.output_dir = None
        app.files = [Path("one.md")]
        self.assertEqual(app._destination_summary(), "source_destination_one")
        app.files.append(Path("two.md"))
        self.assertEqual(app._destination_summary(), "source_destination_many")
        app.output_dir = str(Path("C:/exports/private/project"))
        self.assertEqual(app._destination_summary(), "project")

    def test_trusted_html_decline_restores_value_and_keyboard_focus(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._trusted_html_confirmed = False
        app.trusted_html_var = mock.Mock()
        app.trusted_html_var.get.return_value = True
        app.trusted_html_check = mock.Mock()
        app.dialogs = mock.Mock()
        app.dialogs.ask_trusted_html.return_value = False
        app._t = lambda key, **kwargs: key
        app._refresh_accordion_headers = mock.Mock()

        app._on_trusted_html_changed()

        app.trusted_html_var.set.assert_called_once_with(False)
        app.trusted_html_check.focus_set.assert_called_once_with()
        self.assertFalse(app._trusted_html_confirmed)

    def test_trusted_html_confirmation_is_once_per_session(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._trusted_html_confirmed = False
        app.trusted_html_var = mock.Mock()
        app.trusted_html_var.get.return_value = True
        app.trusted_html_check = mock.Mock()
        app.dialogs = mock.Mock()
        app.dialogs.ask_trusted_html.return_value = True
        app._t = lambda key, **kwargs: key
        app._refresh_accordion_headers = mock.Mock()

        app._on_trusted_html_changed()
        app._on_trusted_html_changed()

        app.dialogs.ask_trusted_html.assert_called_once_with(
            "trusted_html_confirm_title",
            "trusted_html_confirm",
        )
        self.assertTrue(app._trusted_html_confirmed)

    def test_compact_accordion_opening_closes_the_previous_section(self):
        class State:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._viewport_height = 520
        app.accordion_open = {
            "style": State(True),
            "destination": State(False),
            "header_footer": State(False),
            "other": State(False),
        }
        app._accordion_sections = {
            name: (mock.Mock(), mock.Mock())
            for name in app.accordion_open
        }
        app._refresh_accordion_headers = mock.Mock()

        app._toggle_accordion("destination")

        self.assertFalse(app.accordion_open["style"].get())
        self.assertTrue(app.accordion_open["destination"].get())
        app._accordion_sections["style"][1].pack_forget.assert_called_once_with()
        app._accordion_sections["destination"][1].pack.assert_called_once_with(
            fill="x",
            pady=(tk_styles.SPACE_SM, 0),
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

    def test_preview_request_uses_active_file_without_reordering_batch(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_generation = 9
        app._preview_after = "scheduled"
        app.files = [Path("first.md"), Path("second.md")]
        app.active_file = Path("second.md")
        app._render_options = mock.Mock(return_value={"theme": "default@1"})
        app._refresh_generate_button = mock.Mock()
        app._set_status = mock.Mock()
        app._preview_requests = queue.Queue()
        app._schedule_queue_poll = mock.Mock()
        profile = mock.Mock(render_date="2026-07-20")

        with mock.patch.object(
            services.core, "render_profile_for_options", return_value=profile
        ):
            app._start_preview(9)

        _generation, source, _markdown, options = (
            app._preview_requests.get_nowait()
        )
        self.assertEqual(source, Path("second.md"))
        self.assertEqual(
            options["resource_root"],
            Path("second.md").resolve().parent,
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

    def test_preview_schedule_uses_450_ms_and_replaces_pending_request(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("one.md")]
        app.refresh_preview_button = mock.Mock()
        app._preview_generation = 4
        app._preview_after = "older"
        app.root = mock.Mock()
        app.root.after.return_value = "newer"
        app._set_preview_state = mock.Mock()

        app._schedule_preview()

        app.root.after_cancel.assert_called_once_with("older")
        self.assertEqual(app.root.after.call_args.args[0], 450)
        self.assertEqual(app._preview_after, "newer")
        app._set_preview_state.assert_called_once_with("loading")

    def test_refresh_without_files_keeps_explicit_empty_state(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = []
        app._preview_after = None
        app._preview_generation = 2
        app._set_preview_state = mock.Mock()
        app._start_preview = mock.Mock()

        app._refresh_preview()

        app._set_preview_state.assert_called_once_with("empty")
        app._start_preview.assert_not_called()

    def test_preview_error_is_inline_and_preserves_the_previous_image(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.files = [Path("one.md")]
        app.active_file = Path("one.md")
        app._preview_png = b"previous"
        app._t = lambda key, **kwargs: key
        app.active_preview_label = mock.Mock()
        app.preview_message_label = mock.Mock()
        app.preview_message_frame = mock.Mock()
        app.preview_retry_button = mock.Mock()
        app.preview_copy_button = mock.Mock()
        app.zoom_label = mock.Mock()
        app.zoom_percent = mock.Mock()
        app.zoom_percent.get.return_value = 100
        app.zoom_out_button = mock.Mock()
        app.zoom_in_button = mock.Mock()
        app.operation = "idle"
        app.preview_canvas = mock.Mock()
        app.preview_canvas.master = object()

        app._set_preview_error("pypdfium2 is required")

        self.assertEqual(app._preview_png, b"previous")
        app.preview_message_label.config.assert_called_once_with(
            text=(
                "preview_unavailable: pypdfium2 is required "
                "preview_conversion_possible"
            )
        )
        app.preview_retry_button.pack.assert_called()
        app.preview_copy_button.pack.assert_called()
        app.preview_canvas.delete.assert_not_called()

    def test_loading_state_keeps_the_previous_preview_bytes(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_png = b"previous"
        app._refresh_preview_ui = mock.Mock()
        app._draw_preview_state = mock.Mock()

        app._set_preview_state("loading")

        self.assertEqual(app._preview_png, b"previous")
        app._refresh_preview_ui.assert_called_once_with()
        app._draw_preview_state.assert_not_called()

    def test_generation_remains_available_during_preview_rendering(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.files = [Path("one.md")]
        app.operation = "idle"
        app._preview_running = True
        app.generate_button = mock.Mock()
        app._t = lambda key, **kwargs: key

        app._refresh_generate_button()

        app.generate_button.config.assert_called_once_with(
            text="generate_button",
            state="normal",
        )
        app._overwrite_choice = mock.Mock(return_value=None)
        app._set_status = mock.Mock()
        app._on_generate_clicked()
        app._overwrite_choice.assert_called_once_with()

    def test_pointer_centered_zoom_preserves_the_document_point(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_png = b"png"
        app.zoom_percent = mock.Mock()
        app.zoom_percent.get.return_value = 100
        app.preview_canvas = mock.Mock()
        app.preview_canvas.canvasx.return_value = 112
        app.preview_canvas.canvasy.return_value = 212
        app.preview_canvas.cget.return_value = "0 0 1000 2000"
        app._redraw_preview = mock.Mock()
        app._update_zoom_controls = mock.Mock()

        app._set_zoom(200, (10, 20))

        app.zoom_percent.set.assert_called_once_with(200)
        app.preview_canvas.xview_moveto.assert_called_once_with(0.202)
        app.preview_canvas.yview_moveto.assert_called_once_with(0.196)

    def test_preview_mouse_gestures_scroll_zoom_and_pan(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.preview_canvas = mock.Mock()
        app._change_zoom = mock.Mock()
        zoom_event = mock.Mock(delta=120, num=0, state=4, x=30, y=40)
        scroll_event = mock.Mock(delta=-120, num=0, state=0, x=30, y=40)
        pan_event = mock.Mock(x=12, y=18)

        self.assertEqual(app._on_preview_mousewheel(zoom_event), "break")
        app._change_zoom.assert_called_once_with(1, (30, 40))
        self.assertEqual(app._on_preview_mousewheel(scroll_event), "break")
        app.preview_canvas.yview_scroll.assert_called_once_with(1, "units")
        self.assertEqual(app._start_preview_pan(pan_event), "break")
        self.assertEqual(app._drag_preview_pan(pan_event), "break")
        app.preview_canvas.scan_mark.assert_called_once_with(12, 18)
        app.preview_canvas.scan_dragto.assert_called_once_with(12, 18, gain=1)

    def test_zoom_bounds_disable_only_the_unavailable_direction(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.zoom_percent = mock.Mock()
        app.zoom_label = mock.Mock()
        app.zoom_out_button = mock.Mock()
        app.zoom_in_button = mock.Mock()
        app._t = lambda key, **kwargs: "{0}%".format(kwargs["percent"])

        app.zoom_percent.get.return_value = 50
        app._update_zoom_controls()
        app.zoom_out_button.config.assert_called_with(state="disabled")
        app.zoom_in_button.config.assert_called_with(state="normal")

        app.zoom_percent.get.return_value = 200
        app._update_zoom_controls()
        app.zoom_out_button.config.assert_called_with(state="normal")
        app.zoom_in_button.config.assert_called_with(state="disabled")

    def test_preview_scrollbars_are_visible_only_when_needed(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.preview_canvas = mock.Mock()
        app.preview_canvas.winfo_width.return_value = 400
        app.preview_canvas.winfo_height.return_value = 300
        app.preview_vertical = mock.Mock()
        app.preview_horizontal = mock.Mock()

        app.preview_canvas.bbox.return_value = (0, 0, 800, 200)
        app._update_preview_scrollbars()
        app.preview_horizontal.grid.assert_called_once_with(
            row=1, column=0, sticky="ew"
        )
        app.preview_vertical.grid_remove.assert_called_once_with()

        app.preview_canvas.bbox.return_value = (0, 0, 200, 200)
        app._update_preview_scrollbars()
        self.assertEqual(app.preview_horizontal.grid_remove.call_count, 1)
        self.assertEqual(app.preview_vertical.grid_remove.call_count, 2)

    def test_ctrl_zero_and_f1_handlers_are_non_destructive(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._set_zoom = mock.Mock()
        app.dialogs = mock.Mock()
        app._t = lambda key, **kwargs: key

        self.assertEqual(app._reset_zoom(), "break")
        app._set_zoom.assert_called_once_with(100)
        self.assertEqual(app._show_keyboard_shortcuts(), "break")
        app.dialogs.show_info.assert_called_once_with(
            "keyboard_shortcuts_action",
            "keyboard_shortcuts_body",
        )

    def test_preview_error_details_copy_only_the_worker_message(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_error = "preview failed"
        app.root = mock.Mock()

        app._copy_preview_details()

        app.root.clipboard_clear.assert_called_once_with()
        app.root.clipboard_append.assert_called_once_with("preview failed")

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
                        with mock.patch.object(tk_app, "install_ui_styles"):
                            with mock.patch.object(
                                gui.LibreMarkPdfApp, "_bind_accessibility"
                            ):
                                with mock.patch.object(
                                    gui.LibreMarkPdfApp, "_retranslate"
                                ):
                                    gui.LibreMarkPdfApp(
                                        root,
                                        services=services_boundary,
                                        dialogs=dialogs,
                                    )

        browse_button.focus_set.assert_called_once_with()
        root.protocol.assert_called_once_with("WM_DELETE_WINDOW", mock.ANY)

    def test_ui_styles_use_native_theme_colors_and_named_variants(self):
        root = mock.Mock()
        style = mock.Mock()
        native_colors = {
            ("TFrame", "background"): "native-background",
            ("TEntry", "fieldbackground"): "native-field",
            ("TEntry", "bordercolor"): "native-border",
        }
        style.lookup.side_effect = (
            lambda style_name, option: native_colors.get((style_name, option))
        )
        default_font = mock.Mock()
        default_font.cget.return_value = 10
        title_font = mock.Mock()
        emphasis_font = mock.Mock()
        default_font.copy.side_effect = [title_font, emphasis_font]

        with mock.patch.object(tk_styles.ttk, "Style", return_value=style):
            with mock.patch.object(
                tk_styles.tkfont,
                "Font",
                return_value=default_font,
            ) as font:
                resources = tk_styles.install_ui_styles(root)

        font.assert_called_once_with(
            root=root,
            name="TkDefaultFont",
            exists=True,
        )
        title_font.configure.assert_called_once_with(size=12, weight="bold")
        emphasis_font.configure.assert_called_once_with(weight="bold")
        configured_names = [call.args[0] for call in style.configure.call_args_list]
        self.assertEqual(
            configured_names,
            [
                tk_styles.TITLE_LABEL_STYLE,
                tk_styles.PRIMARY_BUTTON_STYLE,
                tk_styles.ACTIVE_FILE_ROW_STYLE,
                tk_styles.ICON_BUTTON_STYLE,
                tk_styles.STATUS_LABEL_STYLE,
                tk_styles.ERROR_STATUS_LABEL_STYLE,
                tk_styles.SUCCESS_STATUS_LABEL_STYLE,
            ],
        )
        self.assertEqual(resources.drop_background, "native-field")
        self.assertEqual(resources.drop_border, "native-border")
        self.assertEqual(resources.preview_background, "native-background")
        self.assertTrue(tk_styles.PRIMARY_BUTTON_STYLE.endswith(".TButton"))

    def test_drop_zone_copy_matches_optional_dnd_capability(self):
        self.assertEqual(
            tk_layout.drop_zone_text_key(True),
            "drop_or_browse",
        )
        self.assertEqual(
            tk_layout.drop_zone_text_key(False),
            "browse_without_dnd",
        )
        self.assertNotIn(
            "drop",
            tk_app.i18n.STRINGS["en"][tk_layout.drop_zone_text_key(False)].lower(),
        )

    def test_mixed_file_add_reports_exact_counts_and_preserves_order(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("existing.md")]
        app.active_file = Path("existing.md")
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_preview = mock.Mock()
        app._set_status = mock.Mock()

        app._add_files([
            "new.md",
            "notes.txt",
            "existing.md",
            "second.markdown",
            "new.md",
        ])

        self.assertEqual(
            app.files,
            [
                Path("existing.md"),
                Path("new.md"),
                Path("second.markdown"),
            ],
        )
        self.assertEqual(app.active_file, Path("existing.md"))
        app._render_file_list.assert_called_once_with(focus_path=Path("new.md"))
        app._schedule_preview.assert_called_once_with()
        app._set_status.assert_called_once_with(
            "files_add_summary",
            added=2,
            duplicates=2,
            unsupported=1,
        )

    def test_first_valid_file_becomes_active_and_invalid_add_does_not_preview(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = []
        app.active_file = None
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_preview = mock.Mock()
        app._set_status = mock.Mock()

        app._add_files(["unsupported.txt"])
        self.assertIsNone(app.active_file)
        app._schedule_preview.assert_not_called()
        app._set_status.assert_called_once_with(
            "files_add_summary",
            added=0,
            duplicates=0,
            unsupported=1,
        )

        app._set_status.reset_mock()
        app._add_files(["first.md", "second.md"])
        self.assertEqual(app.active_file, Path("first.md"))
        app._set_status.assert_called_once_with("files_added_many", count=2)

    def test_selecting_preview_file_does_not_reorder_batch(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("first.md"), Path("second.md")]
        app.active_file = Path("first.md")
        app._render_file_list = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._select_file(Path("second.md"))

        self.assertEqual(app.active_file, Path("second.md"))
        self.assertEqual(app.files, [Path("first.md"), Path("second.md")])
        app._render_file_list.assert_called_once_with(
            focus_path=Path("second.md")
        )
        app._schedule_preview.assert_called_once_with()

    def test_removing_active_file_selects_next_then_previous(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("one.md"), Path("two.md"), Path("three.md")]
        app.active_file = Path("two.md")
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_preview = mock.Mock()
        app._invalidate_preview = mock.Mock()

        app._remove_file(Path("two.md"))
        self.assertEqual(app.files, [Path("one.md"), Path("three.md")])
        self.assertEqual(app.active_file, Path("three.md"))

        app._remove_file(Path("three.md"))
        self.assertEqual(app.files, [Path("one.md")])
        self.assertEqual(app.active_file, Path("one.md"))
        self.assertEqual(
            app._render_file_list.call_args_list,
            [
                mock.call(focus_path=Path("three.md")),
                mock.call(focus_path=Path("one.md")),
            ],
        )

    def test_drop_hover_distinguishes_supported_and_unsupported_inputs(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.root = mock.Mock()
        app.root.tk.splitlist.side_effect = lambda data: data
        app._dnd_files_type = "DND_Files"
        app._redraw_drop_zone = mock.Mock()

        supported = mock.Mock(data="", types=("DND_Files",))
        self.assertEqual(app._on_drop_enter(supported), "copy")
        self.assertEqual(app._drop_zone_state, "active")

        unsupported = mock.Mock(data="", types=("DND_Text",))
        self.assertEqual(app._on_drop_enter(unsupported), "copy")
        self.assertEqual(app._drop_zone_state, "unsupported")
        self.assertEqual(app._redraw_drop_zone.call_count, 2)

        app.operation = "generate"
        self.assertEqual(app._on_drop_enter(supported), "refuse_drop")

    def test_icon_button_retains_localized_name_tooltip_and_focus(self):
        button = mock.Mock()
        image = object()
        tooltip = mock.Mock()
        with mock.patch.object(
            tk_components,
            "Tooltip",
            return_value=tooltip,
        ) as tooltip_type:
            result = tk_components.configure_icon_button(
                button,
                image,
                "Remove report.md",
            )

        button.configure.assert_called_once_with(
            text="Remove report.md",
            image=image,
            compound="none",
            takefocus=True,
            width=2,
        )
        self.assertEqual(button.accessible_name, "Remove report.md")
        tooltip_type.assert_called_once_with(button, "Remove report.md")
        self.assertIs(result, tooltip)

    def test_symbol_button_retains_visible_symbol_and_localized_name(self):
        button = mock.Mock()
        tooltip = mock.Mock()
        with mock.patch.object(
            tk_components,
            "Tooltip",
            return_value=tooltip,
        ) as tooltip_type:
            result = tk_components.configure_symbol_button(
                button,
                "↻",
                "Refresh preview",
            )

        button.configure.assert_called_once_with(
            text="↻", takefocus=True, width=3
        )
        self.assertEqual(button.accessible_name, "Refresh preview")
        tooltip_type.assert_called_once_with(button, "Refresh preview")
        self.assertIs(result, tooltip)

    def test_primary_generate_action_keeps_gear_and_text_in_both_languages(self):
        for language, word in (("en", "Generate"), ("fr", "Générer")):
            text = tk_app.i18n.t("generate_button", language, count=2)
            self.assertTrue(text.startswith("⚙ "))
            self.assertIn(word, text)

    def test_status_styles_preserve_semantics_across_retranslation(self):
        self.assertEqual(
            tk_styles.status_label_style("status_generation_error"),
            tk_styles.ERROR_STATUS_LABEL_STYLE,
        )
        self.assertEqual(
            tk_styles.status_label_style("status_done_summary"),
            tk_styles.SUCCESS_STATUS_LABEL_STYLE,
        )
        self.assertEqual(
            tk_styles.status_label_style("status_generating_progress"),
            tk_styles.STATUS_LABEL_STYLE,
        )

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.status_label = mock.Mock()
        app._t = lambda key, **kwargs: key
        app._set_status("status_preview_error", error="failure")
        app.status_label.config.assert_called_once_with(
            text="status_preview_error",
            style=tk_styles.ERROR_STATUS_LABEL_STYLE,
        )

    def test_layout_has_no_scattered_literal_color_palette(self):
        source = Path(tk_layout.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"#[0-9a-fA-F]{3,8}")

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
        with mock.patch.object(
            tk_dialogs.messagebox, "askyesno", return_value=False
        ) as trusted:
            self.assertFalse(dialogs.ask_trusted_html("Trusted", "Continue?"))
        trusted.assert_called_once_with(
            "Trusted",
            "Continue?",
            default=tk_dialogs.messagebox.NO,
        )
        with mock.patch.object(tk_dialogs.messagebox, "showinfo") as info:
            dialogs.show_info("Shortcuts", "Ctrl+O")
        info.assert_called_once_with("Shortcuts", "Ctrl+O")

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
