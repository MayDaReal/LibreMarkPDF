"""Focused tests for the Linux x86_64 candidate lane."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import generate_windows_sbom
from tools import inspect_linux_artifact
from tools import verify_locked_environment


ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "requirements" / "locks" / "linux-x86_64-py39.txt"


class TestLinuxPackaging(unittest.TestCase):
    def test_linux_lock_is_exact_hashed_and_licensed(self):
        packages = generate_windows_sbom.locked_packages(LOCK)
        self.assertGreaterEqual(len(packages), 15)
        self.assertNotIn("NOASSERTION", [item["license"] for item in packages])
        for package in packages:
            self.assertEqual(len(package["hashes"]), 1)

    def test_locked_environment_reports_exact_mismatch(self):
        with mock.patch(
            "tools.verify_locked_environment.importlib.metadata.version",
            return_value="0",
        ):
            result = verify_locked_environment.verify(LOCK)
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(result["mismatches"]), result["packages"])

    def test_portable_spec_accepts_an_external_browser_staging_root(self):
        spec = (ROOT / "LibreMarkPDF.spec").read_text(encoding="utf-8")
        self.assertIn("LIBREMARK_PDF_BROWSER_SOURCE", spec)
        self.assertIn("Tree(", spec)
        self.assertIn('prefix="browsers"', spec)
        self.assertIn('excludes=[".links", ".links/*"]', spec)

    def test_build_is_no_download_no_elevation_and_has_three_entries(self):
        script = (
            ROOT / "tools" / "build-linux-artifact.sh"
        ).read_text(encoding="utf-8")
        for marker in (
            "linux-x86_64-py39.txt",
            "sys.version_info[:2] == (3, 9)",
            "PyInstaller.__version__ == '6.21.0'",
            "chromium_headless_shell-1223",
            "LibreMarkPDF-cli",
            "LibreMarkPDF-debug",
            "stage_manual_pdfs.py",
            "LIBREMARK_PDF_MANUAL_SOURCE",
            "tar --sort=name",
            "gzip -n",
        ):
            self.assertIn(marker, script)
        for forbidden in (
            "pip install",
            "playwright install",
            "install-deps",
            "sudo ",
            "apt ",
            "dnf ",
            "curl ",
            "wget ",
        ):
            self.assertNotIn(forbidden, script)

    def test_runner_covers_linux_candidate_boundaries(self):
        script = (
            ROOT / "tools" / "validate-linux-artifact.sh"
        ).read_text(encoding="utf-8")
        for marker in (
            "--require-offline",
            "--inspect-only",
            "getconf GNU_LIBC_VERSION",
            "dev_fuse",
            "empty-path",
            "partial-batch",
            "DUPLICATE_OUTPUT",
            "permission",
            "theme-install",
            "community-blue@1",
            "Xvfb",
            "inspect_linux_artifact.py",
            "artifact_visual_regression.py",
            "LINUX_VALIDATION_MANIFEST.sha256",
            "manual-linux-gui-review.md",
            "MANUAL_EN.pdf",
            "MANUEL_FR.pdf",
            "browsers/.links",
            'PLAYWRIGHT_BROWSERS_PATH="$browser_source"',
            "run env",
            "git-porcelain-before.txt",
            "cmp -s",
            "offline-verdict.json",
            "size-performance.json",
            "must be clean before building",
            "Canonical comparison failed",
        ):
            self.assertIn(marker, script)
        self.assertNotIn("sudo ", script)
        self.assertNotIn('python_bin="$(realpath "$python_bin")"', script)

    def test_runner_uses_posix_temporary_storage_for_permission_case(self):
        script = (
            ROOT / "tools" / "validate-linux-artifact.sh"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'mktemp -d "${TMPDIR:-/tmp}/libremark-pdf-permission.XXXXXX"',
            script,
        )
        self.assertIn(
            ': > "$permission_dir/write-probe"',
            script,
        )
        self.assertIn(
            'rm -rf -- "$permission_probe_root"',
            script,
        )
        self.assertNotIn('permission_dir="$runtime/no-write"', script)

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires native Linux")
    def test_elf_inspector_records_glibc_and_no_missing_library(self):
        true_path = Path(shutil.which("true") or "/bin/true")
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary)
            shutil.copy2(true_path, artifact / "candidate")
            result = inspect_linux_artifact.inspect(artifact)
        self.assertEqual(len(result["elf_files"]), 1)
        self.assertEqual(result["unresolved_libraries"], [])
        self.assertTrue(result["glibc_versions"])

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires native Linux")
    def test_elf_inspector_uses_pyinstaller_runtime_library_path(self):
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary)
            internal = artifact / "_internal"
            internal.mkdir()
            (internal / "library.so").write_bytes(b"\x7fELF")
            with mock.patch(
                "tools.inspect_linux_artifact.subprocess.run",
                return_value=completed,
            ) as run:
                inspect_linux_artifact.inspect(artifact)
        ldd_call = run.call_args_list[0]
        self.assertEqual(ldd_call.args[0][0], "ldd")
        self.assertEqual(
            ldd_call.kwargs["env"]["LD_LIBRARY_PATH"].split(":")[0],
            str(internal.resolve()),
        )

    def test_sbom_can_name_the_linux_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "candidate"
            artifact.mkdir()
            (artifact / "LibreMarkPDF-cli").write_bytes(b"linux")
            document = generate_windows_sbom.generate(
                LOCK,
                artifact,
                "b" * 40,
                "2026-07-18T12:00:00Z",
                package_name="LibreMark PDF Linux x86_64 portable candidate",
                document_name="LibreMark-PDF-Linux-x86_64-test",
            )
        self.assertEqual(
            document["packages"][0]["name"],
            "LibreMark PDF Linux x86_64 portable candidate",
        )
        self.assertEqual(document["name"], "LibreMark-PDF-Linux-x86_64-test")
        json.dumps(document)

    def test_platform_guide_limits_linux_support_to_validated_matrix(self):
        guide = (ROOT / "docs" / "PLATFORM_SUPPORT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("aucune compatibilité Linux générale", guide)
        self.assertIn("Ubuntu 24.04 x86_64", guide)
        self.assertIn("Windows x64", guide)


if __name__ == "__main__":
    unittest.main()
