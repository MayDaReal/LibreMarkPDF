"""Regression checks for contributor bootstrap and repository tooling."""

import unittest
from pathlib import Path
from unittest import mock

from tools import check_source_hygiene, run_tests


ROOT = Path(__file__).resolve().parent.parent


class TestContributorTooling(unittest.TestCase):
    def test_bootstraps_use_platform_locks_and_exact_browser_install(self):
        windows = (ROOT / "bootstrap-windows.ps1").read_text(encoding="utf-8")
        linux = (ROOT / "bootstrap-linux.sh").read_text(encoding="utf-8")
        for text, lock in ((windows, "windows-x64-py39.txt"), (linux, "linux-x86_64-py39.txt")):
            self.assertIn(lock, text)
            self.assertIn("--require-hashes", text)
            self.assertIn("pip check", text)
            self.assertIn("playwright install --only-shell chromium", text)
            self.assertIn("chromium_headless_shell-1223", text)
        self.assertIn("browser-win", windows)
        self.assertIn("browser-linux", linux)
        self.assertIn("Python.Python.3.9", windows)
        self.assertIn("GnuWin32.Make", windows)
        self.assertIn("Confirm-Install", windows)
        self.assertIn("confirm_install", linux)
        self.assertIn("--install-python", linux)
        self.assertIn("--install-make", linux)

    def test_windows_validator_defaults_match_the_bootstrap(self):
        validator = (
            ROOT / "tools" / "validate-windows-artifact.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn('.venv-windows-py39\\Scripts\\python.exe', validator)
        self.assertIn('dist\\$Version\\windows-x64', validator)

    def test_makefile_exposes_non_overlapping_test_and_validation_targets(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in (
            "test-pure:", "test:", "test-ui:", "test-visual:",
            "build-windows:", "build-linux:", "validate-windows:",
            "validate-linux:", "compare-platforms:", "release-checklist:",
            "repository-check:", "clean-generated:",
        ):
            self.assertIn(target, makefile)

    def test_repository_hygiene_rejects_local_work_and_archive_paths(self):
        rejected = check_source_hygiene.find_forbidden(
            (
                ".work/ui-redesign/STATE.md",
                "tmp/report.md",
                "archive/old-plan.md",
                "old/script.py",
                "backup/settings.json",
                "libremark_pdf/core.py",
            )
        )
        self.assertEqual(
            rejected,
            [
                ".work/ui-redesign/STATE.md",
                "archive/old-plan.md",
                "backup/settings.json",
                "old/script.py",
                "tmp/report.md",
            ],
        )

    def test_root_build_entries_are_unambiguous(self):
        for obsolete in (
            "build.sh",
            "build.bat",
            "build_portable.bat",
            "build_linux_portable.sh",
            "LibreMarkPDF-portable.spec",
            "refactoring.md",
            "pre_gui_cleanup.md",
        ):
            self.assertFalse((ROOT / obsolete).exists(), obsolete)
        self.assertTrue((ROOT / "LibreMarkPDF.spec").is_file())
        self.assertTrue((ROOT / "tools" / "build-windows-artifact.bat").is_file())
        self.assertTrue((ROOT / "tools" / "build-linux-artifact.sh").is_file())

    def test_version_is_single_root_source(self):
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1.0rc1")
        package = (ROOT / "libremark_pdf" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn(' / "VERSION"', package)

    def test_test_runner_keeps_suites_separate(self):
        pure_command = run_tests.command_for_suite("pure")
        self.assertIn("tests.test_cli.TestConvertCommand", pure_command)
        self.assertIn("tests.test_cli.TestCliSubprocessContract", pure_command)
        self.assertNotIn("tests.test_cli.TestCliSubprocessBrowserContract", pure_command)
        ui_command = run_tests.command_for_suite("ui")
        self.assertIn("tests.test_gui", ui_command)
        self.assertIn("tests.test_ctk_shell", ui_command)
        self.assertIn("tests.test_i18n", ui_command)
        self.assertIn("tests.test_desktop_reporting", ui_command)
        self.assertEqual(
            unittest.defaultTestLoader.loadTestsFromNames(
                run_tests.UI_TESTS
            ).countTestCases(),
            226,
        )
        self.assertIn("tests.test_visual_regression", run_tests.command_for_suite("visual"))
        coverage_command = run_tests.command_for_suite("pure", coverage=True)
        self.assertEqual(
            coverage_command[:5],
            [run_tests.sys.executable, "-m", "coverage", "run", "-m"],
        )

    def test_test_runner_honors_hosted_browser_staging(self):
        staged = "/tmp/staged-playwright-browser"
        with mock.patch.dict(
            run_tests.os.environ,
            {"PLAYWRIGHT_BROWSERS_PATH": staged},
        ):
            self.assertEqual(run_tests.default_browser_dir(), Path(staged))

    def test_hosted_workflows_cover_headless_linux_and_private_repositories(self):
        quality = (ROOT / ".github" / "workflows" / "quality.yml").read_text(
            encoding="utf-8"
        )
        security = (ROOT / ".github" / "workflows" / "security.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ruff check libremark_pdf tests tools", quality)
        self.assertNotIn("tests tools spikes", quality)
        self.assertIn("python tools/run_tests.py pure", quality)
        self.assertIn(
            "xvfb-run -a python tools/run_tests.py all --coverage", quality
        )
        self.assertNotIn("tests.test_g1_spikes", quality)
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"coverage[toml]==7.10.7"', project)
        self.assertIn("fail_under = 75", project)
        self.assertIn("github.event.repository.private == false", security)
        combined = quality + security
        for floating in (
            "actions/checkout@v",
            "actions/setup-python@v",
            "actions/upload-artifact@v",
            "actions/dependency-review-action@v",
        ):
            self.assertNotIn(floating, combined)
        for version in ("v7.0.1", "v7.1.0", "v7.0.2", "v5.0.0"):
            self.assertIn("# " + version, combined)


if __name__ == "__main__":
    unittest.main()
