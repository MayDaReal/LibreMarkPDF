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

from libremark_pdf import __version__, core, desktop_services, gui, i18n
from libremark_pdf.desktop import services
from libremark_pdf.desktop.ctk.widgets import results_view as ctk_results
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

    def test_stale_page_response_does_not_replace_current_document(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._poll_after = None
        app._result_queue = queue.Queue()
        app._result_queue.put(("preview_page_ok", 2, 2, 4, b"stale-page"))
        app._preview_generation = 3
        app._preview_active_request = ("page", 3, 2)
        app._preview_page_pending = 2
        app._preview_running = True
        app.operation = "idle"
        app._apply_preview_page = mock.Mock()
        app._set_preview_page_error = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_queue_poll = mock.Mock()

        app._poll_queue()

        self.assertTrue(app._preview_running)
        app._apply_preview_page.assert_not_called()
        app._set_preview_page_error.assert_not_called()
        app._schedule_queue_poll.assert_called_once_with()

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
            "about.open",
            "menu.compact", "tab.files", "tab.preview", "tab.settings",
            "tab.results",
            "results.clear", "results.toggle",
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
    def test_initial_window_size_targets_1180_by_760_and_respects_limits(self):
        root = mock.Mock()
        root.winfo_screenwidth.return_value = 1920
        root.winfo_screenheight.return_value = 1080
        self.assertEqual(tk_layout.initial_window_size(root), (1180, 760))

        root.winfo_screenwidth.return_value = 800
        root.winfo_screenheight.return_value = 600
        self.assertEqual(tk_layout.initial_window_size(root), (736, 540))

        root.winfo_screenwidth.return_value = 500
        root.winfo_screenheight.return_value = 400
        self.assertEqual(tk_layout.initial_window_size(root), (560, 520))

    def test_reference_widths_select_large_medium_and_compact_modes(self):
        expected = {
            1440: "large",
            1280: "large",
            1100: "large",
            1024: "medium",
            820: "medium",
            720: "compact",
            560: "compact",
        }
        self.assertEqual(
            {
                width: tk_layout.responsive_mode(width)
                for width in expected
            },
            expected,
        )
        self.assertEqual(tk_layout.responsive_mode(759), "compact")
        self.assertEqual(tk_layout.responsive_mode(760), "medium")
        self.assertEqual(tk_layout.responsive_mode(1099), "medium")
        self.assertEqual(tk_layout.responsive_mode(1100), "large")

    def test_responsive_transitions_reuse_widgets_without_moving_focus(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._layout_mode = None
        app._compact_vertical_padding = None
        app._active_compact_tab = "files"
        app.workspace = mock.Mock()
        app.workspace.winfo_width.return_value = 1100
        app.workspace.winfo_height.return_value = 500
        app.workspace_splitter = mock.Mock()
        app.results_splitter = mock.Mock()
        app._left_panel_width = tk_layout.LEFT_PANEL_TARGET_WIDTH
        app._results_panel_height = tk_layout.RESULTS_PANEL_TARGET_HEIGHT
        app.source_group = mock.Mock()
        app.preview_group = mock.Mock()
        app.settings_panel = mock.Mock()
        app.results_frame = mock.Mock()
        app.results_view = app.results_frame
        app.results_view.collapsed = True
        app._refresh_results_projection = mock.Mock()
        app._layout_legacy_setting_rows = mock.Mock()
        app._layout_preview_header = mock.Mock()
        app.body = mock.Mock()
        app.action_bar = mock.Mock()
        app.drop_canvas = mock.Mock()
        app.file_canvas = mock.Mock()
        app.preview_canvas = mock.Mock()
        app.status_label = mock.Mock()
        app.app_header = mock.Mock()
        app.compact_tabs = mock.Mock()
        app.content_container = mock.Mock()
        app.body_container = mock.Mock()
        app.body_canvas = mock.Mock()
        app.body_canvas.winfo_width.return_value = 560
        app.body_canvas.winfo_height.return_value = 400
        app._body_window = mock.Mock()
        app.root = mock.Mock()
        app.root.focus_get.return_value = None
        widgets = (
            app.source_group,
            app.preview_group,
            app.settings_panel,
            app.preview_canvas,
            app.status_label,
        )

        app._apply_responsive_layout(560, 520)
        app.body.configure.assert_called_with(
            padding=(
                12,
                12,
                12,
                12,
            )
        )
        app.source_group.grid.assert_called_with(
            row=0, column=0, sticky="nsew"
        )
        app.preview_group.grid.assert_not_called()
        for widget in (
            app.body,
            app.drop_canvas,
            app.file_canvas,
            app.preview_canvas,
            app.app_header,
            app.workspace_splitter,
        ):
            widget.reset_mock()
        app._apply_responsive_layout(600, 520)
        app.body.configure.assert_not_called()
        app.drop_canvas.configure.assert_not_called()
        app.file_canvas.configure.assert_not_called()
        app.preview_canvas.configure.assert_not_called()
        app.app_header.set_layout_mode.assert_not_called()
        app.workspace_splitter.grid.assert_not_called()
        app._apply_responsive_layout(1100, 700)

        self.assertEqual(
            widgets,
            (
                app.source_group,
                app.preview_group,
                app.settings_panel,
                app.preview_canvas,
                app.status_label,
            ),
        )
        self.assertGreaterEqual(app.root.focus_get.call_count, 1)
        app.root.focus_set.assert_not_called()
        self.assertEqual(app._layout_mode, "large")
        app.source_group.grid.assert_called_with(
            row=0,
            column=0,
            sticky="nsew",
        )
        app.settings_panel.grid.assert_called_with(
            row=1, column=0, sticky="nsew"
        )
        app.preview_group.grid.assert_called_with(
            row=0,
            column=2,
            rowspan=2,
            sticky="nsew",
        )
        app.results_frame.grid.assert_called_with(
            row=2,
            column=0,
            sticky="nsew",
        )

    def test_primary_action_and_progress_are_outside_scrolling_content(self):
        source = inspect.getsource(tk_layout.TkLayoutMixin._build_ui)
        self.assertIn("self.app_shell = AppShell(self.root)", source)
        self.assertIn("self.action_bar = ActionBar(\n            self.app_shell", source)
        self.assertIn(
            "self.app_shell.attach_action_bar(self.action_bar)",
            source,
        )
        self.assertLess(
            source.index("self.app_shell.attach_action_bar"),
            source.index("container.pack"),
        )
        self.assertIn(
            "self.content_container = ttk.Frame(self.app_shell.content)",
            source,
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
        app._settings_draft_css_path = None
        app._settings_draft_style_mode_var = mock.Mock()
        app._refresh_css_entry = mock.Mock()
        app._render_theme_cards = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._choose_css()

        self.assertIsNone(app.css_path)
        self.assertEqual(
            app._settings_draft_css_path,
            "styles/print.css",
        )
        app._settings_draft_style_mode_var.set.assert_called_with("css")

        app._reset_css()

        self.assertIsNone(app._settings_draft_css_path)
        app._settings_draft_style_mode_var.set.assert_called_with("theme")
        app._schedule_preview.assert_not_called()

    def test_style_draft_options_are_isolated_and_match_render_boundary(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.css_path = None
        app.theme_var = Value("default@1")
        app.style_mode_var = Value("theme")
        app.render_date_var = Value("2026-07-25")
        app.trusted_html_var = Value(False)
        app.hf_vars = {
            key: Value(value) for key, value in {
                "header_left": "{title}",
                "header_center": "",
                "header_right": "",
                "footer_left": "",
                "footer_center": "Page {page} / {total}",
                "footer_right": "",
            }.items()
        }
        app._settings_draft_style_mode_var = Value("css")
        app._settings_draft_theme_var = Value("office@1")
        app._settings_draft_css_path = "print.css"

        draft = app._draft_style_render_options()

        self.assertIsNone(app.css_path)
        self.assertEqual(app.theme_var.get(), "default@1")
        self.assertEqual(draft["css_path"], "print.css")
        self.assertIsNone(draft["theme"])
        self.assertEqual(draft["render_date"], "2026-07-25")
        self.assertEqual(draft["header_footer"].top_left, "{title}")

        app._validate_style_draft = mock.Mock(return_value=True)
        app._refresh_accordion_headers = mock.Mock()
        app._close_style_editor = mock.Mock(return_value="break")
        app._save_style_editor()
        self.assertEqual(app.css_path, "print.css")
        self.assertEqual(
            app._render_options(),
            draft,
        )

    def test_invalid_style_draft_is_inline_and_does_not_schedule_preview(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._style_editor_open = True
        app._settings_draft_style_mode_var = mock.Mock()
        app._settings_draft_style_mode_var.get.return_value = "css"
        app._settings_draft_css_path = None
        app._style_error_var = mock.Mock()
        app._t = lambda key, **kwargs: i18n.t(key, "fr", **kwargs)
        app._invalidate_preview = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._schedule_style_draft_preview()

        app._style_error_var.set.assert_called_once_with(
            "Choisissez un fichier CSS pour utiliser le CSS personnalisé."
        )
        app._invalidate_preview.assert_called_once_with()
        app._schedule_preview.assert_not_called()

    def test_style_draft_preview_reuses_450_ms_coalescing(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._style_editor_open = True
        app._validate_style_draft = mock.Mock(return_value=True)
        app.operation = "idle"
        app.files = [Path("one.md")]
        app.refresh_preview_button = mock.Mock()
        app._preview_generation = 4
        app._preview_after = None
        app._preview_page_pending = None
        app._preview_failed_page = None
        app.root = mock.Mock()
        app.root.after.side_effect = ("first", "second")
        app._set_preview_state = mock.Mock()

        app._schedule_style_draft_preview()
        app._schedule_style_draft_preview()

        self.assertEqual(
            [call.args[0] for call in app.root.after.call_args_list],
            [450, 450],
        )
        app.root.after_cancel.assert_called_once_with("first")
        self.assertEqual(app._preview_after, "second")

    def test_style_cancel_restores_exact_previous_preview_and_invalidates_stale(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.root = mock.Mock()
        app._preview_generation = 7
        app._preview_after = "draft-after"
        app._preview_state = "loading"
        app._preview_png = b"draft"
        app._preview_error = "draft error"
        app._preview_page = 1
        app._preview_total_pages = 1
        app._preview_pages = {1: b"draft"}
        app._preview_page_pending = None
        app._preview_failed_page = None
        app._preview_running = True
        app._preview_active_request = ("document", 7, 1)
        app._status_key = "status_rendering_preview"
        app._status_kwargs = {}
        app._redraw_preview = mock.Mock()
        app._draw_preview_state = mock.Mock()
        app._refresh_preview_ui = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._set_status = mock.Mock()
        previous = {
            "png": b"previous",
            "state": "ready",
            "error": None,
            "page": 3,
            "total_pages": 5,
            "pages": {3: b"previous"},
            "page_pending": None,
            "failed_page": None,
            "status_key": "status_ready",
            "status_kwargs": {},
        }

        app._restore_preview_snapshot(previous)

        self.assertEqual(app._preview_generation, 8)
        app.root.after_cancel.assert_called_once_with("draft-after")
        self.assertEqual(app._preview_png, b"previous")
        self.assertEqual(app._preview_state, "ready")
        self.assertEqual((app._preview_page, app._preview_total_pages), (3, 5))
        self.assertEqual(app._preview_pages, {3: b"previous"})
        self.assertFalse(app._preview_running)
        self.assertIsNone(app._preview_active_request)
        app._redraw_preview.assert_called_once_with()
        app._set_status.assert_called_once_with("status_ready")

    def test_header_footer_reset_changes_only_the_six_fields(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._settings_draft_hf_vars = {
            key: mock.Mock()
            for key in (
                "header_left", "header_center", "header_right",
                "footer_left", "footer_center", "footer_right",
            )
        }
        app._settings_draft_render_date_var = mock.Mock()
        app._settings_draft_trusted_html_var = mock.Mock()
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
            app._settings_draft_hf_vars[key].set.assert_called_once_with(value)
        app._settings_draft_render_date_var.set.assert_not_called()
        app._settings_draft_trusted_html_var.set.assert_not_called()

    def test_header_footer_draft_matches_render_boundary_and_saves_only_six_fields(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        keys = tuple(app._header_footer_defaults())
        app._settings_draft_hf_vars = {
            key: Value("Draft {page}" if key == "header_left" else "")
            for key in keys
        }
        app.hf_vars = {key: Value("authoritative") for key in keys}
        app._render_options = mock.Mock(return_value={
            "css_path": None,
            "theme": "default@1",
            "header_footer": core.HeaderFooterConfig.none(),
            "render_date": None,
            "trusted_html": False,
        })
        app._validate_header_footer_draft = mock.Mock(return_value=True)
        app._refresh_accordion_headers = mock.Mock()
        app._close_header_footer_editor = mock.Mock(return_value="break")

        draft = app._draft_header_footer_render_options()
        self.assertEqual(draft["header_footer"].top_left, "Draft {page}")
        self.assertEqual(app.hf_vars["header_left"].get(), "authoritative")

        app._save_header_footer_editor()
        self.assertEqual(app.hf_vars["header_left"].get(), "Draft {page}")
        self.assertEqual(app.hf_vars["footer_right"].get(), "")

    def test_header_footer_restore_confirms_only_customized_values(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        defaults = app._header_footer_defaults()
        app._settings_draft_hf_vars = {
            key: Value(value) for key, value in defaults.items()
        }
        app.dialogs = mock.Mock()
        app._t = lambda key, **kwargs: key

        app._restore_header_footer_defaults()
        app.dialogs.ask_restore_header_footer.assert_not_called()

        app._settings_draft_hf_vars["header_right"].set("Custom")
        app.dialogs.ask_restore_header_footer.return_value = False
        app._restore_header_footer_defaults()
        self.assertEqual(
            app._settings_draft_hf_vars["header_right"].get(), "Custom"
        )
        app.dialogs.ask_restore_header_footer.return_value = True
        app._restore_header_footer_defaults()
        self.assertEqual(
            {key: value.get() for key, value in app._settings_draft_hf_vars.items()},
            defaults,
        )

    def test_header_footer_draft_preview_uses_existing_debounce(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._header_footer_editor_open = True
        app._validate_header_footer_draft = mock.Mock(return_value=True)
        app._schedule_preview = mock.Mock()

        app._on_header_footer_draft_changed()

        app._schedule_preview.assert_called_once_with()

    def test_destination_choose_and_reset_preserve_global_batch_value(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.dialogs = mock.Mock()
        app.dialogs.choose_output_folder.return_value = "exports"
        app._t = lambda key, **kwargs: key
        app.output_dir = None
        app._settings_draft_output_dir = None
        app._refresh_output_entry = mock.Mock()

        app._choose_output_dir()
        self.assertIsNone(app.output_dir)
        self.assertEqual(app._settings_draft_output_dir, "exports")
        app._reset_output_dir()
        self.assertIsNone(app.output_dir)
        self.assertIsNone(app._settings_draft_output_dir)
        self.assertEqual(app._refresh_output_entry.call_count, 2)

    def test_destination_draft_save_cancel_and_preview_isolation(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.output_dir = "C:/Original"
        app._settings_draft_output_dir = "C:/Données Ω/Exports PDF"
        app._destination_mode_var = mock.Mock()
        app._destination_mode_var.get.return_value = "custom"
        app._destination_error_var = mock.Mock()
        app._refresh_output_entry = mock.Mock()
        app._refresh_accordion_headers = mock.Mock()
        app._close_destination_editor = mock.Mock(return_value="break")
        app._schedule_preview = mock.Mock()
        app._validate_destination_draft = mock.Mock(return_value=True)

        app._save_destination_editor()

        self.assertEqual(app.output_dir, "C:/Données Ω/Exports PDF")
        app._schedule_preview.assert_not_called()

        app._destination_editor_open = True
        app._settings_dialog = {
            "snapshot": {
                "output_dir": "C:/Données Ω/Exports PDF",
            }
        }
        app._load_settings_draft = mock.Mock()
        app._cancel_destination_editor()
        app._load_settings_draft.assert_called_once_with(
            app._settings_dialog["snapshot"]
        )
        app._schedule_preview.assert_not_called()

    def test_destination_custom_mode_requires_a_selected_folder_inline(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._settings_draft_output_dir = None
        app._destination_mode_var = mock.Mock()
        app._destination_mode_var.get.return_value = "custom"
        app._destination_error_var = mock.Mock()
        app._t = lambda key, **kwargs: i18n.t(key, "fr", **kwargs)

        self.assertFalse(app._validate_destination_draft())
        app._destination_error_var.set.assert_called_once_with(
            "Choisissez un dossier pour utiliser une destination unique."
        )

    def test_destination_summary_handles_one_many_and_custom_folder(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._t = lambda key, **kwargs: key
        app.output_dir = None
        app.files = [Path("one.md")]
        self.assertEqual(app._destination_summary(), "source_destination_one")
        app.files.append(Path("two.md"))
        self.assertEqual(app._destination_summary(), "source_destination_many")
        app.output_dir = str(Path("C:/exports/private/project"))
        self.assertEqual(
            app._destination_summary(),
            str(Path("C:/exports/private/project")),
        )

    def test_settings_summaries_cover_default_none_custom_date_and_html(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.lang = "en"
        app._t = lambda key, **kwargs: i18n.t(key, "en", **kwargs)
        app.css_path = None
        app.theme_var = Value("default@1")
        app.output_dir = None
        app.files = []
        defaults = {
            "header_left": "",
            "header_center": "",
            "header_right": "",
            "footer_left": "",
            "footer_center": "Page {page} / {total}",
            "footer_right": "",
        }
        app.hf_vars = {
            key: Value(value) for key, value in defaults.items()
        }
        app.render_date_var = Value("")
        app.trusted_html_var = Value(False)

        self.assertEqual(app._style_summary(), "Default theme")
        self.assertNotIn("default@1", app._style_summary())
        self.assertEqual(
            app._header_footer_summary(),
            "Center footer: Page {page} / {total}",
        )
        self.assertEqual(
            app._other_options_summary(),
            "Automatic date · Safe HTML",
        )

        for variable in app.hf_vars.values():
            variable.value = ""
        self.assertEqual(app._header_footer_summary(), "None")
        app.hf_vars["header_left"].value = "{title}"
        self.assertEqual(
            app._header_footer_summary(),
            "Left header: {title}",
        )
        app.render_date_var.value = "2026-07-25"
        app.trusted_html_var.value = True
        self.assertEqual(
            app._other_options_summary(),
            "Date: 2026-07-25 · Trusted HTML enabled",
        )
        app.css_path = "C:/Projet avec espaces/élégant.css"
        self.assertEqual(
            app._style_summary(),
            "Custom CSS · C:/Projet avec espaces/élégant.css",
        )

    def test_trusted_html_decline_restores_value_and_keyboard_focus(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._trusted_html_confirmed = False
        app.trusted_html_var = mock.Mock()
        app.trusted_html_var.get.return_value = True
        app.trusted_html_check = mock.Mock()
        app._settings_dialog = {"window": mock.sentinel.settings_window}
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
        app._settings_dialog = {"window": mock.sentinel.settings_window}
        app.dialogs = mock.Mock()
        app.dialogs.ask_trusted_html.return_value = True
        app._t = lambda key, **kwargs: key
        app._refresh_accordion_headers = mock.Mock()

        app._on_trusted_html_changed()
        app._on_trusted_html_changed()

        app.dialogs.ask_trusted_html.assert_called_once_with(
            mock.sentinel.settings_window,
            "trusted_html_confirm_title",
            "trusted_html_confirm",
            "trusted_html_allow",
            "cancel_settings",
        )
        self.assertTrue(app._trusted_html_confirmed)

    def test_generation_passes_a_snapshot_of_files_and_options_to_service(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_running = False
        app.files = [Path("one.md"), Path("two.md")]
        app.output_dir = "exports"
        app._preflight_decisions = mock.Mock(return_value=([], [], []))
        app._invalidate_preview = mock.Mock()
        app._render_options = mock.Mock(
            return_value={"theme": "default@1", "render_date": None}
        )
        app._applied_options_summary = mock.Mock(return_value="snapshot")
        app.progress = mock.Mock()
        app.progress_var = mock.Mock()
        app._cancel_event = threading.Event()
        app._clear_results = mock.Mock()
        app._begin_operation = mock.Mock()
        app._set_status = mock.Mock()
        app.services = mock.Mock()
        app._result_queue = queue.Queue()
        app._schedule_queue_poll = mock.Mock()
        app.root = mock.Mock()
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
        result_queue, files, options, cancel_event, cancel_current = call.kwargs["args"]
        self.assertIs(result_queue, app._result_queue)
        self.assertEqual(files, [Path("one.md"), Path("two.md")])
        self.assertIsNot(files, app.files)
        self.assertEqual(
            options,
            {
                "theme": "default@1",
                "render_date": "2026-07-20",
                "output_dir": "exports",
                "overwrite": False,
                "overwrite_targets": (),
            },
        )
        self.assertIs(cancel_event, app._cancel_event)
        self.assertFalse(cancel_event.is_set())
        self.assertIs(cancel_current, app._cancel_current_event)
        self.assertFalse(cancel_current.is_set())
        worker.start.assert_called_once_with()
        self.assertEqual(
            app._begin_operation.call_args_list,
            [mock.call("validate"), mock.call("generate")],
        )

    def test_cancel_requests_stop_once_after_the_active_file(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app._cancel_event = threading.Event()
        app.cancel_button = mock.Mock()
        app._set_status = mock.Mock()
        app._set_action_state = mock.Mock()
        app._action_progress_current = 1
        app._action_progress_total = 3
        app._action_active_name = "two.md"

        app._cancel_conversion()
        app._cancel_conversion()

        self.assertTrue(app._cancel_event.is_set())
        app.cancel_button.config.assert_called_once_with(state="disabled")
        app._set_action_state.assert_called_once_with(
            "cancel_requested",
            progress_current=1,
            progress_total=3,
            active_name="two.md",
        )
        app._set_status.assert_called_once_with(
            "status_cancelling_file", name="two.md"
        )

    def test_cancel_now_requests_current_item_interruption_only_once(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app._cancel_event = threading.Event()
        app._cancel_current_event = threading.Event()
        app.cancel_now_button = mock.Mock()
        app._set_status = mock.Mock()
        app._set_action_state = mock.Mock()
        app._action_progress_current = 1
        app._action_progress_total = 3
        app._action_active_name = "two.md"

        app._cancel_conversion_now()
        app._cancel_conversion_now()

        self.assertTrue(app._cancel_current_event.is_set())
        self.assertFalse(app._cancel_event.is_set())
        app.cancel_now_button.config.assert_called_once_with(state="disabled")
        app._set_status.assert_called_once_with("status_cancelling_now")

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

        expected = (125, 150, 200, 200, 150, 125, 100, 75, 50, 25, 10, 10)
        directions = (1, 1, 1, 1, -1, -1, -1, -1, -1, -1, -1, -1)
        observed = []
        for direction in directions:
            app._change_zoom(direction)
            observed.append(current[0])

        self.assertEqual(tuple(observed), expected)
        self.assertEqual(app._redraw_preview.call_count, len(directions))

    def test_new_preview_document_resets_page_and_cache_to_first_page(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_page = 3
        app._preview_total_pages = 5
        app._preview_pages = {3: b"old"}
        app._preview_page_pending = 4
        app._preview_failed_page = 4
        app._apply_preview_image = mock.Mock()

        app._apply_preview_document(1, 4, b"new-first")

        self.assertEqual(app._preview_page, 1)
        self.assertEqual(app._preview_total_pages, 4)
        self.assertEqual(app._preview_pages, {1: b"new-first"})
        self.assertIsNone(app._preview_page_pending)
        self.assertIsNone(app._preview_failed_page)
        app._apply_preview_image.assert_called_once_with(b"new-first")

    def test_cached_page_navigation_does_not_enqueue_worker_request(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_page = 1
        app._preview_total_pages = 3
        app._preview_pages = {1: b"one", 2: b"two"}
        app._preview_page_pending = None
        app._preview_failed_page = None
        app._preview_requests = queue.Queue()
        app._apply_preview_image = mock.Mock()

        self.assertEqual(app._change_preview_page(1), "break")

        self.assertEqual(app._preview_page, 2)
        self.assertTrue(app._preview_requests.empty())
        app._apply_preview_image.assert_called_once_with(b"two")

    def test_uncached_page_navigation_uses_active_document_generation(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_page = 1
        app._preview_total_pages = 3
        app._preview_pages = {1: b"one"}
        app._preview_generation = 9
        app._preview_requests = queue.Queue()
        app._set_preview_state = mock.Mock()
        app._set_status = mock.Mock()
        app._schedule_queue_poll = mock.Mock()

        app._change_preview_page(1)

        request = app._preview_requests.get_nowait()
        self.assertIsInstance(request, tk_preview.PreviewPageRequest)
        self.assertEqual(request, (9, 2, tk_preview.PREVIEW_DPI))
        self.assertEqual(app._preview_page_pending, 2)
        self.assertEqual(app._preview_active_request, ("page", 9, 2))
        app._set_preview_state.assert_called_once_with("rendering")
        app._schedule_queue_poll.assert_called_once_with()

    def test_page_controls_follow_bounds_and_loading_state(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_state = "ready"
        app._preview_page_pending = None
        app._preview_page = 1
        app._preview_total_pages = 3
        app.preview_page_label = mock.Mock()
        app.previous_page_button = mock.Mock()
        app.next_page_button = mock.Mock()
        app._t = lambda key, **kwargs: "{0}/{1}".format(
            kwargs["current"], kwargs["total"]
        )

        app._update_page_controls()
        app.preview_page_label.configure.assert_called_with(text="1/3")
        app.previous_page_button.config.assert_called_with(state="disabled")
        app.next_page_button.config.assert_called_with(state="normal")

        app._preview_page = 3
        app._update_page_controls()
        app.previous_page_button.config.assert_called_with(state="normal")
        app.next_page_button.config.assert_called_with(state="disabled")

        app._preview_state = "loading"
        app._update_page_controls()
        app.previous_page_button.config.assert_called_with(state="disabled")
        app.next_page_button.config.assert_called_with(state="disabled")

    def test_page_error_preserves_cache_and_retries_only_failed_page(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_page = 2
        app._preview_total_pages = 4
        app._preview_pages = {1: b"one", 2: b"two"}
        app._set_preview_state = mock.Mock()

        app._set_preview_page_error(3, "raster failed")

        self.assertEqual(app._preview_page, 2)
        self.assertEqual(app._preview_pages, {1: b"one", 2: b"two"})
        self.assertEqual(app._preview_failed_page, 3)
        app._set_preview_state.assert_called_once_with(
            "page_error", "raster failed"
        )

        app._request_preview_page = mock.Mock()
        app._retry_preview()
        app._request_preview_page.assert_called_once_with(3)

    def test_zoom_keeps_current_preview_page(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_page = 3
        app._preview_png = None
        app.zoom_percent = mock.Mock()
        app.zoom_percent.get.return_value = 100
        app._redraw_preview = mock.Mock()
        app._update_zoom_controls = mock.Mock()

        app._set_zoom(125)

        self.assertEqual(app._preview_page, 3)

    def test_page_arrow_bindings_are_scoped_to_preview_canvas(self):
        source = inspect.getsource(tk_layout.TkLayoutMixin._build_ui)
        self.assertIn('self.preview_canvas.bind(\n            "<Left>"', source)
        self.assertIn('self.preview_canvas.bind(\n            "<Right>"', source)
        accessibility = inspect.getsource(
            tk_layout.TkLayoutMixin._bind_accessibility
        )
        self.assertNotIn("<Left>", accessibility)
        self.assertNotIn("<Right>", accessibility)

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
        app._set_preview_state.assert_called_once_with("scheduled")

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

    def test_explicit_preview_reset_enables_fit_page_before_refresh(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_png = b"existing-raster"
        app._preview_fit_mode = None
        app._redraw_preview = mock.Mock()
        app._refresh_preview = mock.Mock()

        app._reset_preview()

        self.assertEqual(app._preview_fit_mode, "page")
        app._redraw_preview.assert_called_once_with()
        app._refresh_preview.assert_called_once_with()

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
                "preview_unavailable\npypdfium2 is required\n"
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
            text="generate_one",
            state="normal",
        )
        collision = services.core.BatchPlan(
            Path("one.md"), Path("one.pdf"),
            "DUPLICATE_OUTPUT: duplicate destination",
        )
        app._preflight_decisions = mock.Mock(
            return_value=([collision], [collision], [])
        )
        app._set_status = mock.Mock()
        app._begin_operation = mock.Mock()
        app._finish_operation = mock.Mock()
        app._set_action_state = mock.Mock()
        app.root = mock.Mock()
        app._on_generate_clicked()
        app._preflight_decisions.assert_called_once_with()
        app._set_action_state.assert_called_with("decision_required")

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
        app.preview_canvas.xview_moveto.assert_called_once_with(0.198)
        app.preview_canvas.yview_moveto.assert_called_once_with(0.194)

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

        app.zoom_percent.get.return_value = 10
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

    def test_fit_modes_use_only_the_existing_raster_and_manual_zoom_exits_fit(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app._preview_png = b"existing-raster"
        app._preview_fit_mode = None
        app._preview_requests = queue.Queue()
        app._redraw_preview = mock.Mock()

        self.assertEqual(app._set_preview_fit("page"), "break")
        self.assertEqual(app._preview_fit_mode, "page")
        app._redraw_preview.assert_called_once_with()
        self.assertTrue(app._preview_requests.empty())

        app.zoom_percent = mock.Mock()
        app.zoom_percent.get.return_value = 100
        app._update_zoom_controls = mock.Mock()
        app._set_zoom(125)
        self.assertIsNone(app._preview_fit_mode)
        self.assertTrue(app._preview_requests.empty())

    def test_fit_percent_respects_canvas_margin_zoom_bounds_and_mode(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.preview_canvas = mock.Mock()
        app.preview_canvas.winfo_width.return_value = 432
        app.preview_canvas.winfo_height.return_value = 632

        self.assertEqual(app._fit_zoom_percent(400, 600, "page"), 100)
        self.assertEqual(app._fit_zoom_percent(400, 900, "page"), 66)
        self.assertEqual(app._fit_zoom_percent(400, 900, "width"), 100)
        app.preview_canvas.winfo_width.return_value = 100
        app.preview_canvas.winfo_height.return_value = 100
        self.assertEqual(app._fit_zoom_percent(400, 900, "page"), 10)

    def test_resize_recalculates_active_fit_without_rendering(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_png = b"existing-raster"
        app._preview_fit_mode = "width"
        app._preview_requests = queue.Queue()
        app._redraw_preview = mock.Mock()

        app._on_preview_canvas_configure()

        app._redraw_preview.assert_called_once_with()
        self.assertTrue(app._preview_requests.empty())

    def test_shift_wheel_scrolls_horizontally(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.preview_canvas = mock.Mock()
        event = mock.Mock(delta=-120, num=0, state=1, x=30, y=40)

        self.assertEqual(app._on_preview_mousewheel(event), "break")
        app.preview_canvas.xview_scroll.assert_called_once_with(1, "units")
        app.preview_canvas.yview_scroll.assert_not_called()

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

    def test_about_information_uses_package_and_pinned_identities_without_paths(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.lang = "en"
        with mock.patch.object(tk_app.platform, "system", return_value="Windows"), \
                mock.patch.object(tk_app.platform, "release", return_value="10"), \
                mock.patch.object(tk_app.platform, "machine", return_value="AMD64"), \
                mock.patch.object(
                    tk_app.platform, "python_version", return_value="3.9.13"
                ):
            information = app._technical_information()

        for expected in (
            "LibreMark PDF: {0}".format(__version__),
            "Render profile: {0}".format(core.DEFAULT_PROFILE_VERSION),
            "Playwright: {0}".format(core.PLAYWRIGHT_VERSION),
            "Chromium: {0}".format(core.CHROMIUM_VERSION),
            "Chromium revision: {0}".format(core.CHROMIUM_REVISION),
            "Python: 3.9.13",
            "System: Windows 10",
            "Architecture: AMD64",
        ):
            self.assertIn(expected, information)
        for excluded in (str(Path.home()), "PLAYWRIGHT_BROWSERS_PATH", ".md"):
            self.assertNotIn(excluded, information)

    def test_about_action_passes_localized_copyable_information_to_dialog(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.root = mock.Mock()
        app.dialogs = mock.Mock()
        app.lang = "fr"
        app._technical_information = mock.Mock(return_value="Système : Windows")

        app._show_about()

        app.dialogs.show_about.assert_called_once_with(
            app.root,
            "À propos de LibreMark PDF",
            "LibreMark PDF {0}".format(__version__),
            "Informations techniques",
            "Système : Windows",
            "Copier les informations techniques",
            "Informations techniques copiées.",
            "Fermer",
        )

    def test_user_manual_uses_localized_packaged_document_and_service(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.services = mock.Mock()
        app.dialogs = mock.Mock()
        app.lang = "fr"
        app._t = lambda key, **kwargs: key

        app._show_user_manual()

        app.services.open_path.assert_called_once_with(
            core.resource_path("docs/MANUEL_FR.md")
        )

        app.services.open_path.side_effect = RuntimeError("unavailable")
        app.lang = "en"
        app._show_user_manual()
        app.dialogs.show_error.assert_called_once_with(
            "error_title",
            "manual_open_error",
        )

    def test_user_guides_do_not_reintroduce_the_legacy_generate_gear(self):
        for relative_path in (
            "README.md",
            "docs/MANUAL_EN.md",
            "docs/MANUEL_FR.md",
        ):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("⚙", text, relative_path)
            self.assertNotIn("gear", text.lower(), relative_path)
            self.assertNotIn("engrenage", text.lower(), relative_path)

    def test_problem_report_uses_optional_diagnostics_and_never_passes_paths_to_report(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.root = mock.Mock()
        app.dialogs = mock.Mock()
        app.reporting = mock.Mock()
        app.reporting.has_support_channel = False
        app.reporting.diagnostic_payload.return_value = {"safe": True}
        app.reporting.build_report.return_value = "reviewed report\n"
        app.lang = "en"
        app.files = [Path("C:/Users/Alice/private.md")]
        app.theme_var = mock.Mock()
        app.theme_var.get.return_value = "default@1"

        app._show_problem_report("RENDER_FAILED", "failed private.md")

        call = app.dialogs.show_problem_report.call_args
        self.assertEqual(call.args, (app.root,))
        self.assertEqual(call.kwargs["error_code"], "RENDER_FAILED")
        self.assertFalse(call.kwargs["has_support_channel"])
        build = call.kwargs["build_report"]
        self.assertEqual(
            build("Summary", "Steps", "Expected", False),
            "reviewed report\n",
        )
        app.reporting.diagnostic_payload.assert_not_called()
        app.reporting.build_report.assert_called_with(
            language="en",
            summary="Summary",
            steps="Steps",
            expected="Expected",
            error_code="RENDER_FAILED",
            diagnostics=None,
        )

        build("Summary", "", "", True)
        diagnostic_call = app.reporting.diagnostic_payload.call_args.kwargs
        self.assertEqual(diagnostic_call["file_count"], 1)
        self.assertEqual(
            diagnostic_call["private_paths"],
            (Path("C:/Users/Alice/private.md"),),
        )
        app.reporting.build_report.assert_called_with(
            language="en",
            summary="Summary",
            steps="",
            expected="",
            error_code="RENDER_FAILED",
            diagnostics={"safe": True},
        )

    def test_problem_report_dialog_starts_without_diagnostic_consent(self):
        source = inspect.getsource(tk_dialogs.TkDialogs.show_problem_report)
        self.assertIn("tk.BooleanVar(value=False)", source)
        self.assertIn("summary.focus_set()", source)
        self.assertIn('dialog.bind("<Escape>", close)', source)

    def test_preview_error_details_copy_only_the_worker_message(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_error = "preview failed"
        app.root = mock.Mock()

        app._copy_preview_details()

        app.root.clipboard_clear.assert_called_once_with()
        app.root.clipboard_append.assert_called_once_with("preview failed")

    def test_preview_error_report_uses_local_reporting_dialog(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._preview_error = "preview failed"
        app._preview_state = "error"
        app._show_problem_report = mock.Mock()

        app._report_preview_error()

        app._show_problem_report.assert_called_once_with(
            "PREVIEW_FAILED", "preview failed"
        )

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
                tk_styles.ICON_BUTTON_STYLE,
                tk_styles.LINK_BUTTON_STYLE,
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
        app._preview_fit_mode = "width"
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
        self.assertEqual(app._preview_fit_mode, "width")
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
        app._preview_fit_mode = "width"
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_preview = mock.Mock()
        app._set_status = mock.Mock()

        app._add_files(["unsupported.txt"])
        self.assertIsNone(app.active_file)
        self.assertEqual(app._preview_fit_mode, "width")
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
        self.assertEqual(app._preview_fit_mode, "page")
        app._set_status.assert_called_once_with("files_added_many", count=2)

    def test_advanced_draft_matches_render_boundary_and_saves_only_advanced_values(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.render_date_var = Value("")
        app.trusted_html_var = Value(False)
        app._settings_draft_render_date_var = Value(" 2026-07-25 ")
        app._settings_draft_trusted_html_var = Value(True)
        authoritative = {
            "css_path": None,
            "theme": "default@1",
            "header_footer": core.HeaderFooterConfig.none(),
            "render_date": None,
            "trusted_html": False,
        }
        app._render_options = mock.Mock(return_value=authoritative)
        app._validate_advanced_draft = mock.Mock(return_value=True)
        app._refresh_accordion_headers = mock.Mock()
        app._close_advanced_editor = mock.Mock(return_value="break")

        draft = app._draft_advanced_render_options()

        self.assertEqual(draft["render_date"], "2026-07-25")
        self.assertTrue(draft["trusted_html"])
        self.assertIsNone(authoritative["render_date"])
        self.assertFalse(authoritative["trusted_html"])

        self.assertEqual(app._save_advanced_editor(), "break")
        self.assertEqual(app.render_date_var.get(), "2026-07-25")
        self.assertTrue(app.trusted_html_var.get())
        app._refresh_accordion_headers.assert_called_once_with()

    def test_invalid_advanced_date_is_inline_and_does_not_schedule_preview(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._advanced_editor_open = True
        app._settings_draft_render_date_var = mock.Mock()
        app._settings_draft_render_date_var.get.return_value = "2026-02-31"
        app._settings_draft_trusted_html_var = mock.Mock()
        app._settings_draft_trusted_html_var.get.return_value = False
        app._render_options = mock.Mock(return_value={
            "css_path": None,
            "theme": "default@1",
            "header_footer": core.HeaderFooterConfig.none(),
            "render_date": None,
            "trusted_html": False,
        })
        app._advanced_error_var = mock.Mock()
        app._t = lambda key, **kwargs: i18n.t(key, "fr", **kwargs)
        app._invalidate_preview = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._on_advanced_date_changed()

        app._advanced_error_var.set.assert_called_once_with(
            "Saisissez une date valide au format AAAA-MM-JJ ou laissez le champ vide."
        )
        app._invalidate_preview.assert_called_once_with()
        app._schedule_preview.assert_not_called()

    def test_advanced_trusted_html_confirms_first_activation_and_restores_refusal(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._trusted_html_confirmed = False
        app._settings_draft_trusted_html_var = Value(True)
        app.dialogs = mock.Mock()
        app.dialogs.ask_trusted_html.return_value = False
        app._t = lambda key, **kwargs: key
        app._layout_mode = "compact"
        app.compact_advanced_editor = mock.Mock()
        app.advanced_dialog_editor = mock.Mock()
        app._validate_advanced_draft = mock.Mock(return_value=True)
        app._schedule_preview = mock.Mock()

        app._on_advanced_trusted_html_changed()

        self.assertFalse(app._settings_draft_trusted_html_var.get())
        self.assertFalse(app._trusted_html_confirmed)
        app.compact_advanced_editor.trusted_html_switch.focus_set.assert_called_once_with()
        app._schedule_preview.assert_not_called()

        app._settings_draft_trusted_html_var.set(True)
        app.dialogs.ask_trusted_html.return_value = True
        app._on_advanced_trusted_html_changed()
        app._on_advanced_trusted_html_changed()

        self.assertTrue(app._trusted_html_confirmed)
        self.assertEqual(app.dialogs.ask_trusted_html.call_count, 2)
        app.dialogs.ask_trusted_html.assert_called_with(
            app.compact_advanced_editor,
            "trusted_html_confirm_title",
            "trusted_html_confirm",
            "trusted_html_allow",
            "cancel_settings",
        )
        self.assertEqual(app._schedule_preview.call_count, 2)

    def test_advanced_cancel_restores_authoritative_draft_and_exact_preview(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._advanced_editor_open = True
        app._settings_dialog = {"snapshot": {"render_date": "2026-07-20"}}
        app._advanced_editor_preview_snapshot = {"png": b"previous"}
        app._load_settings_draft = mock.Mock()
        app._restore_preview_snapshot = mock.Mock()
        app._close_advanced_editor = mock.Mock(return_value="break")

        self.assertEqual(app._cancel_advanced_editor(), "break")

        self.assertFalse(app._advanced_editor_open)
        app._load_settings_draft.assert_called_once_with(
            {"render_date": "2026-07-20"}
        )
        app._restore_preview_snapshot.assert_called_once_with(
            {"png": b"previous"}
        )

    def test_mixed_file_feedback_uses_natural_count_forms(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        expected = {
            "en": "2 files added · 1 duplicate · 2 unsupported types",
            "fr": (
                "2 fichiers ajoutés · 1 doublon · "
                "2 types non pris en charge"
            ),
        }
        for language, message in expected.items():
            with self.subTest(language=language):
                app.lang = language
                self.assertEqual(
                    app._format_files_add_summary(2, 1, 2),
                    message,
                )

    def test_selecting_preview_file_does_not_reorder_batch(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("first.md"), Path("second.md")]
        app.active_file = Path("first.md")
        app._preview_fit_mode = "width"
        app._render_file_list = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._select_file(Path("second.md"))

        self.assertEqual(app.active_file, Path("second.md"))
        self.assertEqual(app._preview_fit_mode, "page")
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
        app._preview_fit_mode = "width"
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_preview = mock.Mock()
        app._invalidate_preview = mock.Mock()

        app._remove_file(Path("two.md"))
        self.assertEqual(app.files, [Path("one.md"), Path("three.md")])
        self.assertEqual(app.active_file, Path("three.md"))
        self.assertEqual(app._preview_fit_mode, "page")

        app._preview_fit_mode = "width"
        app._remove_file(Path("three.md"))
        self.assertEqual(app.files, [Path("one.md")])
        self.assertEqual(app.active_file, Path("one.md"))
        self.assertEqual(app._preview_fit_mode, "page")
        self.assertEqual(
            app._render_file_list.call_args_list,
            [
                mock.call(focus_path=Path("three.md")),
                mock.call(focus_path=Path("one.md")),
            ],
        )

    def test_removing_inactive_file_preserves_active_preview_view(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("one.md"), Path("two.md")]
        app.active_file = Path("one.md")
        app._preview_fit_mode = "width"
        app._render_file_list = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._schedule_preview = mock.Mock()

        app._remove_file(Path("two.md"))

        self.assertEqual(app.active_file, Path("one.md"))
        self.assertEqual(app._preview_fit_mode, "width")
        app._schedule_preview.assert_called_once_with()

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

    def test_primary_generate_action_keeps_text_outside_the_icon_in_both_languages(self):
        for language, word in (("en", "Generate"), ("fr", "Générer")):
            text = tk_app.i18n.t("generate_many", language, count=2)
            self.assertNotIn("⚙", text)
            self.assertIn(word, text)

    def test_result_summary_uses_natural_singular_and_plural_forms(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        expected = {
            "en": "1 succeeded · 2 failed · 0 kept · 0 cancelled",
            "fr": "1 réussi · 2 échecs · 0 conservés · 0 annulés",
        }
        for language, summary in expected.items():
            with self.subTest(language=language):
                app.lang = language
                self.assertEqual(app._format_result_summary(1, 2, 0), summary)

    def test_ready_action_summary_uses_file_count_and_destination(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.output_dir = None
        expected = {
            "en": "2 files ready · Destination: Next to each source file",
            "fr": "2 fichiers prêts · Destination : À côté de chaque fichier source",
        }
        for language, summary in expected.items():
            with self.subTest(language=language):
                app.lang = language
                app.files = [Path("one.md"), Path("two.md")]
                self.assertEqual(
                    app._translated_status("status_ready", {}),
                    summary,
                )

    def test_language_change_preserves_files_and_render_settings(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.lang = "en"
        app.files = [Path("one.md"), Path("two.md")]
        app.active_file = app.files[1]
        app.css_path = "print.css"
        app.output_dir = "exports"
        app._retranslate = mock.Mock()
        with mock.patch.object(tk_app.i18n, "save_language") as save:
            app._set_lang("fr")
        self.assertEqual(app.files, [Path("one.md"), Path("two.md")])
        self.assertEqual(app.active_file, Path("two.md"))
        self.assertEqual(app.css_path, "print.css")
        self.assertEqual(app.output_dir, "exports")
        save.assert_called_once_with("fr")
        app._retranslate.assert_called_once_with()

    def test_language_accessible_names_follow_hot_retranslation(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.btn_en = mock.Mock()
        app.btn_fr = mock.Mock()
        app.lang = "fr"

        app._update_language_accessibility()

        self.assertEqual(
            app.btn_en.accessible_name,
            "Passer l’interface en anglais",
        )
        self.assertEqual(
            app.btn_fr.accessible_name,
            "Passer l’interface en français",
        )

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

    def test_back_from_collision_decision_stops_before_worker(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "decision"
        app.files = [Path("one.md")]
        app._decision_plans = [mock.sentinel.plan]
        app._decision_has_collisions = True
        app._decision_has_existing = False
        app._render_options = mock.Mock()
        app._set_status = mock.Mock()
        app._finish_operation = mock.Mock()
        app._set_action_state = mock.Mock()
        app._cancel_generation_decision()
        app._render_options.assert_not_called()
        app._set_status.assert_called_once_with("status_cancelled")
        app._set_action_state.assert_called_once_with("ready")
        app._finish_operation.assert_called_once_with()

    def test_existing_output_decision_passes_individual_overwrite_targets(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "decision"
        app._decision_has_existing = True
        app._decision_plans = [
            services.core.BatchPlan(
                Path("one.md"), Path("exports/one.pdf"),
                "OUTPUT_EXISTS: refusing overwrite",
            ),
            services.core.BatchPlan(
                Path("two.md"), Path("exports/two.pdf"),
                "OUTPUT_EXISTS: refusing overwrite",
            ),
        ]
        app.action_bar = mock.Mock()
        app._start_generation = mock.Mock()

        app.action_bar.selected_overwrite_targets.return_value = (
            "exports/one.pdf", "exports/three.pdf"
        )
        app._continue_generation_decision()
        app._start_generation.assert_called_once_with(
            False,
            overwrite_targets=("exports/one.pdf", "exports/three.pdf"),
        )
        self.assertEqual(
            app._expected_kept_outputs,
            {Path("two.md"): Path("exports/two.pdf")},
        )

    def test_preflight_returns_collisions_before_existing_outputs_without_dialog(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.files = [Path("one.md"), Path("two.md")]
        app.output_dir = None
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
        with mock.patch.object(services.core, "plan_batch_outputs", return_value=plans):
            returned, collisions, existing = app._preflight_decisions()
        self.assertEqual(returned, plans)
        self.assertEqual(collisions, [plans[0]])
        self.assertEqual(existing, [plans[1]])
        app.dialogs.assert_not_called()

    def test_only_explicitly_declined_overwrite_is_projected_as_kept(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._expected_kept_outputs = {
            Path("kept.md"): Path("exports/kept.pdf")
        }
        refusal = {
            "input": "kept.md",
            "output": None,
            "status": "error",
            "error": "OUTPUT_EXISTS: refusing to overwrite",
            "error_code": "OUTPUT_EXISTS",
        }
        projected = app._project_expected_kept_result(refusal)
        self.assertEqual(projected["status"], "kept")
        self.assertEqual(projected["output"], str(Path("exports/kept.pdf")))
        self.assertIsNone(projected["error"])
        unexpected = dict(refusal, input="unexpected.md")
        self.assertIs(app._project_expected_kept_result(unexpected), unexpected)

    def test_mixed_results_keep_one_persistent_row_per_core_result(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app._render_results = mock.Mock()
        app._set_status = mock.Mock()
        app._reveal_terminal_results = mock.Mock()
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
        app._render_results.assert_called_once_with(results)
        app._set_status.assert_called_once_with(
            "status_done_summary", ok=1, failed=1, kept=0, cancelled=1
        )
        app._reveal_terminal_results.assert_called_once_with("bad.md")

    def test_progress_keeps_completed_result_and_names_the_active_item(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.progress_var = mock.Mock()
        app._cancel_event = threading.Event()
        app._conversion_results = []
        app._render_results = mock.Mock()
        app._set_status = mock.Mock()
        app._set_action_state = mock.Mock()
        app.files = [Path("one.md"), Path("two.md"), Path("three.md")]
        result = {
            "input": "folder/one.md", "output": "one.pdf", "status": "ok",
            "error": None, "error_code": None,
        }
        app._handle_conversion_progress(1, 3, result)
        self.assertEqual(app._conversion_results, [result])
        app._render_results.assert_called_once_with([result])
        app._set_status.assert_called_once_with(
            "status_generating_file", current=2, total=3, name="two.md"
        )
        app._set_action_state.assert_called_once_with(
            "running",
            progress_current=1,
            progress_total=3,
            active_name="two.md",
        )

    def test_engine_stage_updates_active_file_without_inventing_completion(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app._cancel_event = threading.Event()
        app._cancel_current_event = threading.Event()
        app._conversion_results = []
        app._set_action_state = mock.Mock()
        app._set_status = mock.Mock()

        app._handle_conversion_stage(
            1, 3, Path("folder/one.md"), "rendering"
        )

        self.assertEqual(app._action_item_index, 1)
        self.assertEqual(app._action_stage, "rendering")
        app._set_action_state.assert_called_once_with(
            "running",
            progress_current=0,
            progress_total=3,
            active_name="one.md",
        )
        app._set_status.assert_called_once_with(
            "status_generating_file", current=1, total=3, name="one.md"
        )

    def test_progress_does_not_hide_a_pending_cancellation(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.progress_var = mock.Mock()
        app._cancel_event = threading.Event()
        app._cancel_event.set()
        app._conversion_results = []
        app._render_results = mock.Mock()
        app._set_status = mock.Mock()
        app._set_action_state = mock.Mock()
        result = {"input": "one.md", "status": "ok"}
        app._handle_conversion_progress(1, 2, result)
        app._set_status.assert_called_once_with(
            "status_cancelling_file", name="one.md"
        )
        app._set_action_state.assert_called_once_with(
            "cancel_requested",
            progress_current=1,
            progress_total=2,
            active_name="one.md",
        )

    def test_validation_and_conversion_lock_mutable_controls_until_finish(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.files = [Path("one.md"), Path("two.md")]
        app._operation_controls = [mock.Mock(), mock.Mock()]
        app._theme_buttons = [mock.Mock()]
        app.generate_button = mock.Mock()
        app.cancel_button = mock.Mock()
        app.files_panel = mock.Mock()
        app.settings_panel = mock.Mock()
        app._t = lambda key, **kwargs: key
        app._refresh_file_conversion_states = mock.Mock()

        app._begin_operation("validate")

        self.assertEqual(app.operation, "validate")
        for control in app._operation_controls:
            control.config.assert_called_once_with(state="disabled")
        app.files_panel.set_interaction_enabled.assert_called_once_with(
            mutation_enabled=False,
            selection_enabled=False,
            reason="file_mutation_disabled",
        )
        app.settings_panel.set_enabled.assert_called_once_with(False)

        app._begin_operation("generate")
        self.assertEqual(app.operation, "generate")
        self.assertEqual(
            app._file_conversion_states,
            {Path("one.md"): "running", Path("two.md"): "pending"},
        )
        self.assertNotIn(
            mock.call(True),
            app.settings_panel.set_enabled.call_args_list,
        )

        app._close_requested = False
        app.root = mock.Mock()
        app.css_entry = mock.Mock()
        app.output_entry = mock.Mock()
        app._render_theme_cards = mock.Mock()
        app._update_zoom_controls = mock.Mock()
        app._update_page_controls = mock.Mock()
        app._refresh_generate_button = mock.Mock()
        app._finish_operation()

        self.assertEqual(app.operation, "idle")
        app.settings_panel.set_enabled.assert_called_with(True)
        app._refresh_generate_button.assert_called_once_with(
            preserve_action_state=True
        )

    def test_global_error_preserves_completed_rows_without_modal(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        completed = [{"input": "one.md", "status": "ok"}]
        app._conversion_results = completed
        app._render_results = mock.Mock()
        app._set_status = mock.Mock()
        app._reveal_terminal_results = mock.Mock()
        app._handle_generate_failed("worker stopped")
        app._render_results.assert_called_once_with(
            completed, global_error="worker stopped"
        )
        app._set_status.assert_called_once_with(
            "status_generation_error", error="worker stopped"
        )
        app._reveal_terminal_results.assert_called_once_with()

    def test_only_success_rows_offer_open_actions(self):
        row = ctk_results.ResultRow.__new__(ctk_results.ResultRow)
        row._mode = "large"
        row._expanded = False
        row.source_id = "source.md"
        row._on_toggle_details = mock.Mock()
        row.action_buttons = []
        row.details_button = None
        row._assets = mock.Mock()
        row._assets.image.return_value = mock.sentinel.icon
        row._labels = {
            "open_pdf": "open_pdf",
            "open_folder": "open_folder",
            "show_details": "show_details",
            "hide_details": "hide_details",
            "copy_details": "copy_details",
            "report_issue_action": "report_issue_action",
        }
        on_open = mock.Mock()
        on_copy = mock.Mock()
        on_report = mock.Mock()
        fonts = mock.Mock()
        fonts.font.return_value.measure.side_effect = lambda text: len(text)
        created_buttons = []

        def button(*args, **kwargs):
            widget = mock.Mock()
            widget.creation_options = kwargs
            created_buttons.append(widget)
            return widget

        with mock.patch.object(
            ctk_results, "IconButton", side_effect=button
        ):
            row.result = {
                "input": "ok.md", "output": "ok.pdf", "status": "ok",
                "error": None, "error_code": None,
            }
            row._build_actions(
                mock.Mock(), Path("ok.pdf"), "ok", fonts,
                on_open, on_copy, on_report,
            )
            row.result = {
                "input": "bad.md", "output": None, "status": "error",
                "error": "failed", "error_code": "RENDER_FAILED",
            }
            row._build_actions(
                mock.Mock(), None, "error", fonts,
                on_open, on_copy, on_report,
            )
            error_report_button = next(
                item for item in created_buttons
                if item.creation_options.get("accessible_name")
                == "report_issue_action"
            )
            error_report_button.creation_options["command"]()
            row.result = {
                "input": "later.md", "output": None,
                "status": "cancelled", "error": None, "error_code": None,
            }
            row._build_actions(
                mock.Mock(), None, "cancelled", fonts,
                on_open, on_copy, on_report,
            )
        labels = [
            item.creation_options.get("accessible_name")
            for item in created_buttons
        ]
        self.assertEqual(labels.count("open_pdf"), 1)
        self.assertEqual(labels.count("open_folder"), 1)
        self.assertEqual(labels.count("report_issue_action"), 1)
        self.assertNotIn("open_pdf", labels[2:])
        self.assertNotIn("open_folder", labels[2:])
        on_report.assert_called_once_with(
            "RENDER_FAILED", "failed"
        )

    def test_continue_close_choice_does_not_cancel_or_close(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app.root = mock.Mock()
        app.dialogs = mock.Mock()
        app.dialogs.ask_close_during_conversion.return_value = "continue"
        app._t = lambda key, **kwargs: key
        app._cancel_event = threading.Event()
        app._preview_generation = 3
        app._set_status = mock.Mock()
        app._close_requested = False
        app._close_dialog_open = False
        app.cancel_button = mock.Mock()
        app.status_label = mock.Mock()
        app._request_close()
        self.assertFalse(app._close_requested)
        self.assertFalse(app._cancel_event.is_set())
        self.assertEqual(app._preview_generation, 3)
        app.status_label.focus_set.assert_called_once_with()
        app._set_status.assert_not_called()

    def test_cancel_and_close_choice_waits_for_active_file(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app.root = mock.Mock()
        app.dialogs = mock.Mock()
        app.dialogs.ask_close_during_conversion.return_value = "cancel_close"
        app._t = lambda key, **kwargs: key
        app._cancel_event = threading.Event()
        app._preview_generation = 3
        app._set_status = mock.Mock()
        app._close_requested = False
        app._close_dialog_open = False
        app.cancel_button = mock.Mock()
        app._request_close()
        self.assertTrue(app._close_requested)
        self.assertTrue(app._cancel_event.is_set())
        self.assertEqual(app._preview_generation, 4)
        app.root.destroy.assert_not_called()
        app.cancel_button.config.assert_called_once_with(state="disabled")
        app._set_status.assert_called_once_with("status_closing")

    def test_idle_close_is_immediate(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "idle"
        app.root = mock.Mock()
        app._close_requested = False
        app._close_dialog_open = False
        app._preview_after = "preview-after"
        app._poll_after = "poll-after"
        app._preview_generation = 2
        app._responsive_controller = mock.Mock()
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
        app._responsive_controller.cancel.assert_called_once_with()

    def test_close_dialog_dismissal_and_escape_continue_by_default(self):
        dialogs = tk_dialogs.TkDialogs()
        dialog = mock.Mock()
        content = mock.Mock()
        actions = mock.Mock()
        cancel_button = mock.Mock()
        continue_button = mock.Mock()
        with mock.patch.object(tk_dialogs.tk, "Toplevel", return_value=dialog), \
                mock.patch.object(
                    tk_dialogs.ttk, "Frame", side_effect=[content, actions]
                ), mock.patch.object(tk_dialogs.ttk, "Label", return_value=mock.Mock()), \
                mock.patch.object(
                    tk_dialogs.ttk,
                    "Button",
                    side_effect=[cancel_button, continue_button],
                ):
            self.assertEqual(
                dialogs.ask_close_during_conversion(
                    mock.Mock(), "Closing", "Keep going?", "Continue", "Cancel"
                ),
                "continue",
            )
        continue_button.focus_set.assert_called_once_with()
        protocol_callback = dialog.protocol.call_args.args[1]
        bindings = {call.args[0]: call.args[1] for call in dialog.bind.call_args_list}
        escape_callback = bindings["<Escape>"]
        return_callback = bindings["<Return>"]
        protocol_callback()
        self.assertEqual(escape_callback(mock.Mock()), "break")
        self.assertEqual(return_callback(mock.Mock()), "break")
        self.assertGreaterEqual(dialog.destroy.call_count, 3)

    def test_cancel_and_close_after_terminal_event_closes_immediately(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.operation = "generate"
        app.root = mock.Mock()
        app.dialogs = mock.Mock()
        app._t = lambda key, **kwargs: key
        app._cancel_event = threading.Event()
        app._preview_generation = 1
        app._preview_after = None
        app._poll_after = None
        app._close_requested = False
        app._close_dialog_open = False
        app._invalidate_preview = mock.Mock()
        app.dialogs.ask_close_during_conversion.side_effect = lambda *args: (
            setattr(app, "operation", "idle") or "cancel_close"
        )
        app._request_close()
        self.assertTrue(app._close_requested)
        self.assertFalse(app._cancel_event.is_set())
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

    def test_result_details_copy_keeps_source_code_and_human_error(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.root = mock.Mock()
        app._set_status = mock.Mock()

        app._copy_result_details({
            "input": "C:/Données Ω/rapport.md",
            "error_code": "RENDER_FAILED",
            "error": "Chromium stopped safely",
        })

        app.root.clipboard_clear.assert_called_once_with()
        app.root.clipboard_append.assert_called_once_with(
            "C:/Données Ω/rapport.md: [RENDER_FAILED] Chromium stopped safely"
        )
        app._set_status.assert_called_once_with("status_details_copied")

    def test_file_row_show_and_copy_actions_use_public_desktop_boundaries(self):
        app = gui.LibreMarkPdfApp.__new__(gui.LibreMarkPdfApp)
        app.services = mock.Mock()
        app.dialogs = mock.Mock()
        app.root = mock.Mock()
        app._t = lambda key, **kwargs: key
        source = Path("folder/report.md")

        app._show_source_file(source)
        app._copy_source_path(source)

        app.services.open_path.assert_called_once_with(source.parent)
        app.root.clipboard_clear.assert_called_once_with()
        app.root.clipboard_append.assert_called_once_with(str(source))

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
        root = mock.Mock()
        with mock.patch.object(
            dialogs, "_ask_explicit_choice", return_value="cancel"
        ) as overwrite:
            self.assertIsNone(dialogs.ask_overwrite(
                root, "Existing", "Replace?", "Replace", "Keep", "Cancel"
            ))
        overwrite.assert_called_once_with(
            root,
            "Existing",
            "Replace?",
            (
                ("replace", "Replace"),
                ("keep", "Keep"),
                ("cancel", "Cancel"),
            ),
            default_choice="keep",
            dismiss_choice="cancel",
        )
        parent = mock.Mock()
        with mock.patch.object(
            dialogs, "_ask_explicit_choice", return_value="cancel"
        ) as trusted:
            self.assertFalse(dialogs.ask_trusted_html(
                parent, "Trusted", "Continue?", "Allow", "Cancel"
            ))
        trusted.assert_called_once_with(
            parent,
            "Trusted",
            "Continue?",
            (("allow", "Allow"), ("cancel", "Cancel")),
            default_choice="cancel",
            dismiss_choice="cancel",
            center_on_anchor=True,
        )
        compact_parent = mock.Mock()
        compact_parent.winfo_toplevel.return_value = mock.sentinel.owner
        with mock.patch.object(
            dialogs, "_ask_explicit_choice", return_value="allow"
        ) as compact_trusted:
            self.assertTrue(dialogs.ask_trusted_html(
                compact_parent, "Trusted", "Continue?", "Allow", "Cancel"
            ))
        compact_trusted.assert_called_once_with(
            compact_parent,
            "Trusted",
            "Continue?",
            (("allow", "Allow"), ("cancel", "Cancel")),
            default_choice="cancel",
            dismiss_choice="cancel",
            center_on_anchor=True,
        )
        with mock.patch.object(
            tk_dialogs.messagebox, "askyesno", return_value=True
        ) as restore:
            self.assertTrue(dialogs.ask_restore_header_footer(
                "Restore", "Replace customized values?"
            ))
        restore.assert_called_once_with(
            "Restore",
            "Replace customized values?",
            default=tk_dialogs.messagebox.NO,
        )
        with mock.patch.object(tk_dialogs.messagebox, "showinfo") as info:
            dialogs.show_info("Shortcuts", "Ctrl+O")
        info.assert_called_once_with("Shortcuts", "Ctrl+O")

    def test_about_dialog_copies_exact_text_and_supports_keyboard_dismissal(self):
        dialogs = tk_dialogs.TkDialogs()
        root = mock.Mock()
        dialog = mock.Mock()
        content = mock.Mock()
        actions = mock.Mock()
        details = mock.Mock()
        status = mock.Mock()
        copy_button = mock.Mock()
        close_button = mock.Mock()
        labels = [mock.Mock(), mock.Mock(), status]
        with mock.patch.object(tk_dialogs.tk, "Toplevel", return_value=dialog), \
                mock.patch.object(
                    tk_dialogs.ttk, "Frame", side_effect=[content, actions]
                ), mock.patch.object(
                    tk_dialogs.ttk, "Label", side_effect=labels
                ), mock.patch.object(
                    tk_dialogs.tk, "Text", return_value=details
                ), mock.patch.object(
                    tk_dialogs.ttk,
                    "Button",
                    side_effect=[copy_button, close_button],
                ) as button_type:
            dialogs.show_about(
                root,
                "About",
                "LibreMark PDF 1.0.0",
                "Technical information",
                "LibreMark PDF: 1.0.0\nSystem: Windows 10",
                "Copy technical information",
                "Technical information copied.",
                "Close",
            )

        copy_command = button_type.call_args_list[0].kwargs["command"]
        copy_command()
        root.clipboard_clear.assert_called_once_with()
        root.clipboard_append.assert_called_once_with(
            "LibreMark PDF: 1.0.0\nSystem: Windows 10"
        )
        status.configure.assert_called_once_with(
            text="Technical information copied."
        )
        copy_button.focus_set.assert_called_once_with()
        dialog.grab_set.assert_called_once_with()
        escape = {
            call.args[0]: call.args[1] for call in dialog.bind.call_args_list
        }["<Escape>"]
        self.assertEqual(escape(mock.Mock()), "break")
        dialog.destroy.assert_called_once_with()

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
        app._preflight_decisions = mock.Mock(return_value=([], [], []))
        app._begin_operation = mock.Mock()
        app._finish_operation = mock.Mock()
        app._set_action_state = mock.Mock()
        app.root = mock.Mock()
        app._invalidate_preview = mock.Mock()
        app._render_options = mock.Mock(return_value={})
        app._applied_options_summary = mock.Mock(return_value="snapshot")
        app._set_status = mock.Mock()
        with mock.patch.object(
            services.core, "render_profile_for_options", side_effect=RuntimeError("invalid")
        ):
            app._on_generate_clicked()
        self.assertEqual(app.dialogs.show_error.call_count, 1)
        self.assertEqual(
            app._set_status.call_args_list,
            [
                mock.call("status_validating"),
                mock.call("status_generation_error", error="invalid"),
            ],
        )


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
