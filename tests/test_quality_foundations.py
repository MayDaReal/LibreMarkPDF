"""Focused checks for package and source-hygiene foundations."""

import unittest
from pathlib import Path

from tools.check_source_hygiene import find_forbidden


ROOT = Path(__file__).resolve().parent.parent


class TestQualityFoundations(unittest.TestCase):
    def test_python_314_and_console_entry_are_declared(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.14,<3.15"', pyproject)
        self.assertIn('libremark-pdf = "libremark_pdf.__main__:main"', pyproject)

    def test_renderer_is_exactly_constrained(self):
        constraints = (ROOT / "requirements" / "constraints.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("playwright==1.65.2", constraints)
        self.assertNotIn("playwright>=", constraints.lower())

    def test_release_lock_uses_hashes(self):
        lock = (
            ROOT / "requirements" / "locks" / "linux-x86_64-py314.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("playwright==1.65.2", lock)
        self.assertGreaterEqual(lock.count("--hash=sha256:"), 15)

    def test_hygiene_rejects_generated_outputs(self):
        self.assertEqual(
            find_forbidden(["README.md", "dist/app.exe", "notes/report.pdf"]),
            ["dist/app.exe", "notes/report.pdf"],
        )


if __name__ == "__main__":
    unittest.main()
