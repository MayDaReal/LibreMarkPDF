"""Regression tests for the PyInstaller entry point and build contract."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import stage_manual_pdfs


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
            "CLI_JSON_SCHEMA.json", "MANUAL_EN.pdf", "MANUEL_FR.pdf",
            "customtkinter",
        ):
            self.assertIn(resource, portable)
        self.assertIn(
            'hiddenimports=["customtkinter", "PIL._tkinter_finder"]',
            portable,
        )
        self.assertIn('excludes=[".links", ".links/*"]', portable)
        self.assertNotIn('("docs/MANUAL_EN.md", "docs")', portable)
        self.assertNotIn('("docs/MANUEL_FR.md", "docs")', portable)

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
        self.assertIn("stage_manual_pdfs.py", script)
        self.assertIn("LIBREMARK_PDF_MANUAL_SOURCE", script)

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
            "MANUAL_EN.pdf",
            "MANUEL_FR.pdf",
            "browsers\\.links",
        ):
            self.assertIn(marker, script)

    def test_windows_evidence_manifest_preserves_unicode_paths(self):
        script = (ROOT / "tools" / "validate-windows-artifact.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("[char]0x00E9", script)
        self.assertIn("[IO.File]::WriteAllLines(", script)
        self.assertIn("[Text.UTF8Encoding]::new($false)", script)
        self.assertNotIn("Set-Content -LiteralPath $ManifestPath -Encoding ASCII", script)

    def test_manual_staging_uses_the_authoritative_cli_and_tracked_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            for name in stage_manual_pdfs.MANUALS:
                (root / "docs" / (name + ".md")).write_text(
                    "# Guide\n", encoding="utf-8"
                )
            (root / "style.css").write_text("body {}\n", encoding="utf-8")
            output = root / "staging"

            def convert(arguments):
                out_dir = Path(arguments[arguments.index("--out-dir") + 1])
                for name in stage_manual_pdfs.MANUALS:
                    (out_dir / (name + ".pdf")).write_bytes(b"%PDF-manual")
                return 0

            with mock.patch.object(
                stage_manual_pdfs.cli, "main", side_effect=convert
            ) as cli_main:
                outputs = stage_manual_pdfs.stage_manuals(output, root=root)

        arguments = cli_main.call_args.args[0]
        self.assertEqual(arguments[0], "convert")
        self.assertEqual(
            arguments[1:3],
            [str(root / "docs" / "MANUAL_EN.md"),
             str(root / "docs" / "MANUEL_FR.md")],
        )
        self.assertIn(str(root / "style.css"), arguments)
        self.assertIn(stage_manual_pdfs.RENDER_DATE, arguments)
        self.assertEqual([path.name for path in outputs], [
            "MANUAL_EN.pdf", "MANUEL_FR.pdf",
        ])

    def test_manual_staging_fails_on_cli_error_or_missing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "staging"
            with mock.patch.object(stage_manual_pdfs.cli, "main", return_value=1):
                with self.assertRaisesRegex(RuntimeError, "generation failed"):
                    stage_manual_pdfs.stage_manuals(output)
            with mock.patch.object(stage_manual_pdfs.cli, "main", return_value=0):
                with self.assertRaisesRegex(RuntimeError, "did not produce"):
                    stage_manual_pdfs.stage_manuals(output)

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
