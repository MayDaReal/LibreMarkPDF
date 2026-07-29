"""Regression checks for contributor bootstrap and repository tooling."""

import unittest
from pathlib import Path

from tools import check_source_hygiene, inventory_repository, run_tests


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
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1.0.dev1")
        package = (ROOT / "libremark_pdf" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn(' / "VERSION"', package)

    def test_inventory_reports_only_known_generated_paths(self):
        report = inventory_repository.inventory(ROOT)
        known = set(inventory_repository.GENERATED_DIRECTORIES)
        known.update(inventory_repository.GENERATED_FILES)
        self.assertTrue(all(item["path"] in known for item in report["generated"]))

    def test_test_runner_keeps_suites_separate(self):
        ui_command = run_tests.command_for_suite("ui")
        self.assertIn("tests.test_gui", ui_command)
        self.assertIn("tests.test_ctk_shell", ui_command)
        self.assertIn("tests.test_i18n", ui_command)
        self.assertIn("tests.test_desktop_reporting", ui_command)
        self.assertEqual(
            unittest.defaultTestLoader.loadTestsFromNames(
                run_tests.UI_TESTS
            ).countTestCases(),
            221,
        )
        self.assertIn("tests.test_visual_regression", run_tests.command_for_suite("visual"))

    def test_hosted_workflows_cover_headless_linux_and_private_repositories(self):
        quality = (ROOT / ".github" / "workflows" / "quality.yml").read_text(
            encoding="utf-8"
        )
        security = (ROOT / ".github" / "workflows" / "security.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ruff check libremark_pdf tests tools", quality)
        self.assertNotIn("tests tools spikes", quality)
        self.assertIn(
            "xvfb-run -a python -m unittest discover -s tests -v", quality
        )
        self.assertIn("github.event.repository.private == false", security)


if __name__ == "__main__":
    unittest.main()
