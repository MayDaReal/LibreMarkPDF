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


if __name__ == "__main__":
    unittest.main()
