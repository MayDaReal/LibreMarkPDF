"""Regression tests for local, privacy-preserving desktop reports."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from libremark_pdf.desktop import reporting


class TestDesktopReporting(unittest.TestCase):
    def test_anonymization_covers_known_names_windows_posix_unc_and_unicode_paths(self):
        message = (
            "Failed C:\\Users\\Élodie\\private report.md, "
            "\\\\server\\share\\secret.md and /home/élodie/notes.md; "
            "selected report final.md"
        )
        result = reporting.anonymize_text(
            message,
            private_paths=(Path("D:/Documents/report final.md"),),
        )

        for private_value in (
            "Users", "Élodie", "server", "share", "home", "élodie",
            "private report.md", "secret.md", "notes.md", "report final.md",
        ):
            self.assertNotIn(private_value, result)
        self.assertIn("<private-path>", result)
        self.assertIn("<source-1.md>", result)

    def test_sanitization_uses_stable_aliases_for_case_and_escaped_paths(self):
        source = Path("C:/Users/Élodie/Project File/source.md")
        output = Path("D:/PDF exports")
        aliases = {
            source: "<source-1.md>",
            output: "<output-folder>",
        }
        message = (
            r"C:\\USERS\\ÉLODIE\\PROJECT FILE\\SOURCE.MD then "
            r"D:\\PDF exports and C:\Users\Élodie\Project File\source.md"
        )

        result = reporting.sanitize_report_text(
            message, (source, output), aliases
        )

        self.assertEqual(result.count("<source-1.md>"), 2)
        self.assertIn("<output-folder>", result)
        for private_value in ("ÉLODIE", "Project File", "PDF exports"):
            self.assertNotIn(private_value.lower(), result.lower())

    def test_sanitization_removes_unknown_unc_posix_and_windows_paths(self):
        text = (
            r"\\server\private share\file.md, "
            r"C:\Users\Alice\notes.md; /home/alice/private/notes.md"
        )

        result = reporting.sanitize_report_text(text)

        self.assertEqual(result.count("<private-path>"), 3)
        for private_value in ("server", "Alice", "home", "notes.md"):
            self.assertNotIn(private_value.lower(), result.lower())

    def test_report_excludes_diagnostics_until_explicitly_requested(self):
        service = reporting.ReportingService()
        report = service.build_report(
            language="en",
            summary="Preview did not refresh",
            steps="Select a file",
            expected="A current preview",
            error_code="PREVIEW_FAILED",
        )

        self.assertIn("Preview did not refresh", report)
        self.assertIn("PREVIEW_FAILED", report)
        self.assertNotIn("application_version", report)
        self.assertNotIn("technical diagnostics", report.lower())

    def test_report_sanitizes_error_context_before_display(self):
        service = reporting.ReportingService()
        source = Path("C:/Users/Alice/private.md")

        report = service.build_report(
            language="en",
            summary="Preview failed",
            error_code="PREVIEW_FAILED",
            error_context="Could not read C:\\Users\\Alice\\private.md",
            private_paths=(source,),
            path_aliases={source: "<source-1.md>"},
        )

        self.assertIn("Error context\nCould not read <source-1.md>", report)
        self.assertNotIn("Alice", report)
        self.assertNotIn("private.md", report)

    def test_diagnostics_contain_only_safe_identifiers_and_anonymized_error(self):
        service = reporting.ReportingService()
        with mock.patch.object(
            reporting, "_resource_presence", return_value={"browser": True}
        ), mock.patch.object(
            reporting.platform, "system", return_value="Windows"
        ), mock.patch.object(
            reporting.platform, "release", return_value="10"
        ), mock.patch.object(
            reporting.platform, "machine", return_value="AMD64"
        ), mock.patch.object(
            reporting.platform, "python_version", return_value="3.9.13"
        ):
            payload = service.diagnostic_payload(
                language="fr",
                theme="default@1",
                file_count=2,
                has_drag_and_drop=False,
                error_code="RENDER_FAILED",
                error_message="Could not read C:\\Users\\Alice\\secret.md",
                private_paths=(Path("C:/Users/Alice/secret.md"),),
                generated_at=datetime(2026, 7, 21, 10, 30, tzinfo=timezone.utc),
            )

        self.assertEqual(payload["file_count"], 2)
        self.assertEqual(payload["interface_language"], "fr")
        self.assertEqual(payload["resources"], {"browser": True})
        self.assertEqual(payload["generated_at"], "2026-07-21T10:30:00+00:00")
        serialized = repr(payload)
        for excluded in ("Alice", "secret.md", "PLAYWRIGHT_BROWSERS_PATH"):
            self.assertNotIn(excluded, serialized)
        for forbidden_key in (
            "markdown", "pdf", "css_content", "user", "hostname", "clipboard"
        ):
            self.assertNotIn(forbidden_key, payload)

        self.assertEqual(
            set(payload),
            {
                "application_version", "architecture", "chromium_revision",
                "chromium_version", "drag_and_drop", "error_code",
                "error_message", "file_count", "generated_at",
                "interface_language", "playwright_version", "python_version",
                "render_profile", "resources", "system", "theme",
            },
        )

    def test_save_report_writes_the_reviewed_utf8_text_exactly(self):
        service = reporting.ReportingService()
        text = "Rapport modifiable — échec\n"
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "rapport.txt"
            service.save_report(path, text)
            self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_support_channel_is_absent_by_default_and_uses_only_injected_url(self):
        service = reporting.ReportingService()
        self.assertFalse(service.has_support_channel)
        with self.assertRaises(reporting.SupportChannelUnavailable):
            service.open_support_page()

        opener = mock.Mock()
        configured = reporting.ReportingService(
            support_url="https://support.invalid/project",
            support_opener=opener,
        )
        self.assertTrue(configured.has_support_channel)
        configured.open_support_page()
        opener.assert_called_once_with("https://support.invalid/project")

    def test_reporting_module_has_no_http_client_or_socket_transport(self):
        source = Path(reporting.__file__).read_text(encoding="utf-8")
        for forbidden in ("requests", "urllib.request", "http.client", "socket"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
