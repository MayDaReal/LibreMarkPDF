"""Regression coverage for the conversion-jobs engine boundary."""

import inspect
import unittest

from libremark_pdf import core
from libremark_pdf.engine import jobs


class TestConversionJobsBoundary(unittest.TestCase):
    def test_core_reexports_canonical_job_functions(self):
        for name in (
            "convert_markdown_text_to_pdf", "convert_markdown_to_pdf",
            "plan_batch_outputs", "convert_batch",
        ):
            self.assertIs(getattr(core, name), getattr(jobs, name))

    def test_job_signatures_remain_publicly_compatible(self):
        self.assertEqual(
            tuple(inspect.signature(jobs.convert_batch).parameters),
            ("input_paths", "output_dir", "css_path", "header_footer", "render_date",
             "trusted_html", "overwrite", "theme", "theme_root", "cancel_event",
             "progress_callback", "cancel_current_event", "stage_callback",
             "overwrite_targets"),
        )

    def test_jobs_do_not_import_the_public_facade(self):
        with open(jobs.__file__, encoding="utf-8") as source:
            self.assertNotIn("libremark_pdf.core", source.read())
