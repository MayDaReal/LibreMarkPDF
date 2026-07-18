"""Pure tests for CLI output and exit-status contracts."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
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
                "theme": None,
            },
        )

    @mock.patch("libremark_pdf.cli.core.convert_batch")
    def test_date_and_legacy_render_date_are_equivalent(self, convert_batch):
        convert_batch.return_value = [{
            "input": "report.md", "output": "report.pdf", "status": "ok",
            "error": None, "error_code": None,
        }]
        for spelling in ("--date", "--render-date"):
            with self.subTest(spelling=spelling):
                status = cli.main(["convert", "report.md", spelling, "2026-07-14"])
                self.assertEqual(status, 0)
                self.assertEqual(
                    convert_batch.call_args.kwargs["render_date"], "2026-07-14"
                )

    def test_parser_failure_is_clean_json_when_requested(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main(["convert", "report.md", "--unknown", "--json"])
        self.assertEqual(status, 2)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["error_code"], "INVALID_ARGUMENT")

    def test_output_and_out_dir_are_mutually_exclusive(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = cli.main([
                "convert", "report.md", "--output", "one.pdf",
                "--out-dir", "pdfs", "--json",
            ])
        self.assertEqual(status, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("cannot be used together", json.loads(stdout.getvalue())["error"])

    @mock.patch("libremark_pdf.cli.core.convert_batch")
    def test_theme_selection_reaches_shared_core_and_enriches_json(self, convert_batch):
        convert_batch.return_value = [{
            "input": "report.md", "output": "report.pdf", "status": "ok",
            "error": None, "error_code": None,
        }]
        stdout = io.StringIO()
        with mock.patch("libremark_pdf.cli.core.resolve_theme_css") as resolve:
            resolve.return_value = mock.Mock(
                identifier="default", reference="default@1",
                css_path=cli.core.DEFAULT_CSS_PATH,
            )
            with redirect_stdout(stdout):
                status = cli.main([
                    "convert", "report.md", "--theme", "default@1",
                    "--date", "2026-07-14", "--json",
                ])
        self.assertEqual(status, 0)
        self.assertEqual(convert_batch.call_args.kwargs["theme"], "default@1")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["theme"], "default@1")
        self.assertEqual(payload["render_date"], "2026-07-14")
        self.assertEqual(payload["render_profile"], "default@1")
        self.assertEqual(payload["playwright_version"], "1.60.0")
        self.assertRegex(payload["renderer_fingerprint"], r"^[0-9a-f]{64}$")

    def test_css_and_theme_are_mutually_exclusive(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = cli.main([
                "convert", "report.md", "--css", "style.css",
                "--theme", "default@1", "--json",
            ])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(stdout.getvalue())["error_code"], "INVALID_ARGUMENT")

    def test_theme_commands_use_core_registry_and_clean_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            theme_root = Path(temporary) / "themes"
            fixture = (
                Path(__file__).resolve().parent
                / "fixtures" / "themes" / "community-blue"
            )
            with mock.patch.object(cli.core, "DEFAULT_THEME_ROOT", theme_root):
                outputs = []
                for arguments in (
                    ["theme", "install", str(fixture), "--json"],
                    ["theme", "list", "--json"],
                    ["theme", "show", "community-blue@1", "--json"],
                    ["theme", "remove", "community-blue@1", "--json"],
                ):
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        status = cli.main(arguments)
                    self.assertEqual(status, 0)
                    self.assertEqual(stderr.getvalue(), "")
                    outputs.append(json.loads(stdout.getvalue()))
        self.assertEqual(outputs[0]["reference"], "community-blue@1")
        self.assertEqual(
            [item["reference"] for item in outputs[1]],
            ["default@1", "community-blue@1"],
        )
        self.assertEqual(outputs[2]["reference"], "community-blue@1")
        self.assertEqual(outputs[3]["reference"], "community-blue@1")


class TestCliSubprocessContract(unittest.TestCase):
    def run_cli(self, *arguments, cwd=None):
        environment = os.environ.copy()
        root = str(Path(__file__).resolve().parent.parent)
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = root if not existing else root + os.pathsep + existing
        return subprocess.run(
            [sys.executable, "-m", "libremark_pdf", *arguments],
            cwd=cwd or root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_version_reports_all_pinned_identities(self):
        completed = self.run_cli("--version")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        for identity in (
            "LibreMark PDF 1.0.0", "render-profile default@1",
            "Playwright 1.60.0", "Chromium 148.0.7778.96", "revision 1223",
        ):
            self.assertIn(identity, completed.stdout)

    def test_unknown_option_is_one_json_document_with_no_stderr(self):
        completed = self.run_cli(
            "convert", "missing file.md", "--unknown", "--json"
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], "INVALID_ARGUMENT")

    def test_missing_unicode_space_path_is_structured_without_browser_launch(self):
        with tempfile.TemporaryDirectory(prefix="LibreMark CLI é space ") as temporary:
            missing = Path(temporary) / "introuvable é.md"
            completed = self.run_cli("convert", str(missing), "--json")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["input"], str(missing))
        self.assertEqual(payload["error_code"], "INPUT_NOT_FOUND")

    def test_collision_css_resource_and_destination_failures_are_json_clean(self):
        with tempfile.TemporaryDirectory(prefix="LibreMark CLI cases ") as temporary:
            root = Path(temporary)
            source = root / "report é.md"
            source.write_text("# Report", encoding="utf-8")

            collision = self.run_cli(
                "convert", str(source), "--output", str(source), "--json"
            )

            css = root / "unsafe.css"
            css.write_text("@import 'https://example.invalid/x.css';", encoding="utf-8")
            unsafe_css = self.run_cli(
                "convert", str(source), "--output", str(root / "css.pdf"),
                "--css", str(css), "--json",
            )

            resource_source = root / "resource.md"
            resource_source.write_text("![missing](absent.png)", encoding="utf-8")
            resource = self.run_cli(
                "convert", str(resource_source),
                "--output", str(root / "resource.pdf"), "--json",
            )

            blocked_parent = root / "not-a-directory"
            blocked_parent.write_text("file", encoding="utf-8")
            destination = self.run_cli(
                "convert", str(source),
                "--output", str(blocked_parent / "output.pdf"), "--json",
            )

        for completed, code in (
            (collision, "INPUT_OUTPUT_COLLISION"),
            (unsafe_css, "FORBIDDEN_CSS_URL"),
            (resource, "FORBIDDEN_RESOURCE"),
            (destination, "OUTPUT_UNAVAILABLE"),
        ):
            with self.subTest(code=code):
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stderr, "")
                self.assertEqual(json.loads(completed.stdout)["error_code"], code)

    def test_duplicate_batch_destinations_return_one_result_per_input(self):
        with tempfile.TemporaryDirectory(prefix="LibreMark duplicate ") as temporary:
            root = Path(temporary)
            first = root / "one" / "same.md"
            second = root / "two" / "same.md"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("# One", encoding="utf-8")
            second.write_text("# Two", encoding="utf-8")
            completed = self.run_cli(
                "convert", str(first), str(second),
                "--out-dir", str(root / "out"), "--json",
            )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(len(payload["results"]), 2)
        self.assertTrue(all(
            item["error_code"] == "DUPLICATE_OUTPUT"
            for item in payload["results"]
        ))

    def test_doctor_is_read_only_for_bundled_resource_files(self):
        tracked = [
            Path("style.css"),
            Path("fonts/NotoSans-Regular.ttf"),
            Path("icons/icons_check.png"),
        ]
        root = Path(__file__).resolve().parent.parent
        before = {str(path): (root / path).stat().st_mtime_ns for path in tracked}
        completed = self.run_cli("doctor", "--json")
        after = {str(path): (root / path).stat().st_mtime_ns for path in tracked}
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(json.loads(completed.stdout)["status"], "ok")
        self.assertEqual(after, before)


class TestCliSubprocessBrowserContract(unittest.TestCase):
    run_cli = TestCliSubprocessContract.run_cli

    def test_unicode_space_resource_and_css_success_is_clean_json(self):
        with tempfile.TemporaryDirectory(prefix="LibreMark succès é ") as temporary:
            root = Path(temporary)
            source = root / "rapport é space.md"
            image = root / "blue-square.svg"
            image.write_bytes(
                (
                    Path(__file__).resolve().parent
                    / "fixtures" / "g2" / "resources" / "blue-square.svg"
                ).read_bytes()
            )
            source.write_text(
                "# Rapport é\n\n![Blue](blue-square.svg)\n", encoding="utf-8"
            )
            css = root / "print style.css"
            css.write_text(".markdown-body { color: #123456; }\n", encoding="utf-8")
            output = root / "sortie é space.pdf"
            completed = self.run_cli(
                "convert", str(source), "--output", str(output),
                "--css", str(css), "--date", "2026-07-14", "--json",
            )
            exists = output.is_file() and output.read_bytes().startswith(b"%PDF-")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["render_date"], "2026-07-14")
        self.assertTrue(exists)

    def test_partial_batch_continues_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory(prefix="LibreMark partial ") as temporary:
            root = Path(temporary)
            good = root / "good.md"
            missing = root / "missing.md"
            good.write_text("# Good", encoding="utf-8")
            output_dir = root / "pdfs"
            completed = self.run_cli(
                "convert", str(good), str(missing),
                "--out-dir", str(output_dir), "--date", "2026-07-14", "--json",
            )
            good_pdf = output_dir / "good.pdf"
            exists = good_pdf.is_file() and good_pdf.read_bytes().startswith(b"%PDF-")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        results = json.loads(completed.stdout)["results"]
        self.assertEqual([item["status"] for item in results], ["ok", "error"])
        self.assertEqual(results[1]["error_code"], "INPUT_NOT_FOUND")
        self.assertTrue(exists)


if __name__ == "__main__":
    unittest.main()
