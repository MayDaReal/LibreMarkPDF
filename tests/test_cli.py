"""Pure tests for CLI output and exit-status contracts."""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from libremark_pdf import cli


class TestConvertCommand(unittest.TestCase):
    @mock.patch("libremark_pdf.cli.core.convert_batch")
    def test_json_success_has_no_stderr(self, convert_batch):
        convert_batch.return_value = [
            {
                "input": "report.md",
                "output": "report.pdf",
                "status": "ok",
                "error": None,
            }
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main(["convert", "report.md", "--json"])

        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["status"], "ok")

    @mock.patch("libremark_pdf.cli.core.convert_batch")
    def test_human_failure_uses_stderr_and_nonzero_status(self, convert_batch):
        convert_batch.return_value = [
            {
                "input": "missing.md",
                "output": None,
                "status": "error",
                "error": "Input file not found",
            }
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main(["convert", "missing.md"])

        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ERROR missing.md: Input file not found", stderr.getvalue())

    def test_multiple_inputs_reject_single_output_as_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main(
                ["convert", "a.md", "b.md", "--output", "out.pdf", "--json"]
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(stderr.getvalue(), "")

    @mock.patch("libremark_pdf.cli.core.convert_batch")
    def test_safety_and_determinism_options_reach_shared_core(self, convert_batch):
        convert_batch.return_value = [
            {
                "input": "report.md",
                "output": "report.pdf",
                "status": "ok",
                "error": None,
                "error_code": None,
            }
        ]

        status = cli.main(
            [
                "convert", "report.md", "--overwrite", "--trusted-html",
                "--render-date", "2026-07-14",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            convert_batch.call_args.kwargs,
            {
                "output_dir": None,
                "css_path": None,
                "header_footer": mock.ANY,
                "render_date": "2026-07-14",
                "trusted_html": True,
                "overwrite": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
