"""Regression tests for the PyInstaller entry point and build contract."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestPackagingConfiguration(unittest.TestCase):
    def test_entry_point_imports_main_from_the_package(self):
        entry = (ROOT / "libremark_pdf_entry.py").read_text(encoding="utf-8")
        self.assertIn("from libremark_pdf.__main__ import main", entry)

    def test_spec_uses_package_entry_without_manual_hidden_imports(self):
        spec = (ROOT / "LibreMarkPDF.spec").read_text(encoding="utf-8")
        self.assertIn('["libremark_pdf_entry.py"]', spec)
        self.assertIn("hiddenimports=[]", spec)
        self.assertNotIn("libremark_pdf\\\\__main__.py", spec)

    def test_no_competing_debug_spec_exists(self):
        self.assertFalse((ROOT / "LibreMarkPDF-debug.spec").exists())

    def test_windows_build_uses_the_authoritative_spec(self):
        script = (ROOT / "build.bat").read_text(encoding="utf-8")
        self.assertIn("python -m PyInstaller --noconfirm --clean LibreMarkPDF.spec", script)
        self.assertIn('if /i "%~1"=="--console"', script)

    def test_canonical_brand_assets_exist(self):
        for size in (16, 32, 48, 64, 128, 256):
            self.assertTrue(
                (ROOT / "assets" / f"libremark-pdf-logo-{size}.png").is_file()
            )
        self.assertTrue((ROOT / "assets" / "libremark-pdf.ico").is_file())


if __name__ == "__main__":
    unittest.main()
