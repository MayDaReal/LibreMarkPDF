"""Regression tests for the PyInstaller entry point and build contract."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestPackagingConfiguration(unittest.TestCase):
    def test_entry_point_imports_main_from_the_package(self):
        entry = (ROOT / "libremark_pdf_entry.py").read_text(encoding="utf-8")
        self.assertIn("from libremark_pdf.__main__ import main", entry)

    def test_portable_spec_uses_onedir_collection_and_matching_resources(self):
        portable = (ROOT / "LibreMarkPDF.spec").read_text(
            encoding="utf-8"
        )

        self.assertIn('["libremark_pdf_entry.py"]', portable)
        self.assertIn("exclude_binaries=True", portable)
        self.assertIn("COLLECT(", portable)
        for resource in (
            "style.css", "icons", "assets", "browsers", "fonts", "licenses",
            "LICENSE", "THIRD_PARTY_NOTICES.md", "THEME_CONTRIBUTING.md",
            "CLI_JSON_SCHEMA.json", "customtkinter",
        ):
            self.assertIn(resource, portable)
        self.assertIn('hiddenimports=["customtkinter"]', portable)

    def test_portable_spec_has_distinct_gui_cli_and_diagnostic_entry_paths(self):
        spec = (ROOT / "LibreMarkPDF.spec").read_text(encoding="utf-8")
        self.assertIn('name="LibreMarkPDF"', spec)
        self.assertIn('name="LibreMarkPDF-cli"', spec)
        self.assertIn('name="LibreMarkPDF-debug"', spec)
        self.assertIn("gui_exe", spec)
        self.assertIn("cli_exe", spec)
        self.assertIn("debug_exe", spec)
        self.assertIn("console=False", spec)
        self.assertGreaterEqual(spec.count("console=True"), 2)

    def test_no_competing_debug_spec_exists(self):
        self.assertFalse((ROOT / "LibreMarkPDF-debug.spec").exists())

    def test_portable_build_uses_locked_environment_and_external_paths(self):
        script = (
            ROOT / "tools" / "build-windows-artifact.bat"
        ).read_text(encoding="utf-8")

        self.assertIn("LibreMarkPDF.spec", script)
        self.assertIn("LIBREMARK_PDF_DISTPATH", script)
        self.assertIn("LIBREMARK_PDF_WORKPATH", script)
        self.assertIn("LIBREMARK_PDF_PYTHON", script)
        self.assertIn("sys.version_info[:2] == (3, 9)", script)
        self.assertIn("PyInstaller.__version__ == '6.21.0'", script)
        self.assertIn("chrome-headless-shell.exe", script)
        self.assertIn("LibreMarkPDF-cli.exe", script)
        self.assertIn("LibreMarkPDF-debug.exe", script)
        self.assertNotIn("pip install", script)
        self.assertNotIn("playwright install", script)

    def test_native_runner_covers_mandatory_candidate_boundaries(self):
        script = (ROOT / "tools" / "validate-windows-artifact.ps1").read_text(
            encoding="utf-8"
        )
        for marker in (
            "RequireOffline",
            "PROCESSOR_ARCHITECTURE",
            "PROCESSOR_ARCHITEW6432",
            "NativeArchitecture",
            "git log -1 --show-signature",
            "unittest",
            "LibreMarkPDF-cli.exe",
            "empty-profile",
            "empty-localappdata",
            "partial-batch",
            "permission",
            "theme-convert",
            "artifact_visual_regression.py",
            "generate_windows_sbom.py",
            "Get-AuthenticodeSignature",
            "manual-gui-review.md",
            "WINDOWS_VALIDATION_MANIFEST.sha256",
        ):
            self.assertIn(marker, script)

    def test_frozen_entry_dispatches_by_authoritative_executable_name(self):
        entry = (ROOT / "libremark_pdf_entry.py").read_text(encoding="utf-8")
        self.assertIn('"libremarkpdf-cli"', entry)
        self.assertIn('"libremarkpdf-debug"', entry)
        self.assertIn("from libremark_pdf.cli import main as cli_main", entry)
        self.assertIn("from libremark_pdf.gui import launch", entry)

    def test_canonical_brand_assets_exist(self):
        for size in (16, 32, 48, 64, 128, 256):
            self.assertTrue(
                (ROOT / "assets" / f"libremark-pdf-logo-{size}.png").is_file()
            )
        self.assertTrue((ROOT / "assets" / "libremark-pdf.ico").is_file())

    def test_modern_ui_licenses_and_icon_manifest_are_packaged(self):
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(
            encoding="utf-8"
        )
        for name in (
            "Bootstrap-Icons-LICENSE.txt",
            "CustomTkinter-LICENSE.txt",
        ):
            self.assertTrue((ROOT / "licenses" / name).is_file())
            self.assertIn(name, project)
        self.assertIn("assets/ui-icons/manifest.json", project)
        self.assertIn("assets/ui-icons/svg/*.svg", project)
        self.assertIn("assets/ui-icons/png/*.png", project)
        self.assertIn("CustomTkinter/issues/2857", notices)

    def test_cli_json_schema_is_valid_json_and_covers_batch_results(self):
        schema = json.loads(
            (ROOT / "docs" / "CLI_JSON_SCHEMA.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("result", schema["$defs"])
        self.assertEqual(schema["oneOf"][1]["properties"]["results"]["minItems"], 1)


if __name__ == "__main__":
    unittest.main()
