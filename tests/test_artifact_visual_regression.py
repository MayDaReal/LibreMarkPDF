"""Focused checks for frozen-artifact visual comparison."""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "tools" / "artifact_visual_regression.py"
SPEC = importlib.util.spec_from_file_location("artifact_visual_regression", HARNESS)
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class TestArtifactVisualRegression(unittest.TestCase):
    def test_command_uses_exact_console_artifact_and_approved_options(self):
        fixture = {
            "markdown": Path("path with space") / "épreuve.md",
            "render_date": "2026-07-14",
            "trusted_html": True,
            "header_footer": {
                "top_center": "{title}",
                "bottom_center": "Page {page} / {total}",
            },
        }
        command = module.converter_command(
            Path("LibreMarkPDF-cli.exe"), fixture, Path("output é.pdf")
        )
        self.assertEqual(command[0], "LibreMarkPDF-cli.exe")
        self.assertIn("--json", command)
        self.assertIn("--date", command)
        self.assertIn("--trusted-html", command)
        self.assertIn("--header-center", command)
        self.assertIn("--footer-center", command)

    def test_harness_never_calls_a_source_conversion_function(self):
        source = HARNESS.read_text(encoding="utf-8")
        self.assertNotIn("core.convert_markdown_to_pdf", source)
        self.assertNotIn("core.convert_markdown_text_to_pdf", source)
        self.assertIn("subprocess.run(", source)
        self.assertNotIn("update_visual_goldens", source)

    def test_frozen_converter_does_not_inherit_source_browser_path(self):
        previous = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "source-browser"
        try:
            environment = module.converter_environment()
        finally:
            if previous is None:
                os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
            else:
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = previous
        self.assertNotIn("PLAYWRIGHT_BROWSERS_PATH", environment)

    def test_missing_converter_is_rejected_without_expected_writes(self):
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("converter executable is unavailable", source)
        self.assertNotIn("--update-goldens", source)
        self.assertNotIn("--write-expected", source)


if __name__ == "__main__":
    unittest.main()
