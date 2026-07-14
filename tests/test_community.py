"""Regression checks for actionable open-source health files."""

import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestCommunityHealth(unittest.TestCase):
    def test_required_policies_exist(self):
        for name in (
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "SUPPORT.md",
            "GOVERNANCE.md",
            "CHANGELOG.md",
            "ROADMAP.md",
            "THIRD_PARTY_NOTICES.md",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_security_policy_has_private_reporting_fallback(self):
        policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("Report a vulnerability", policy)
        self.assertIn("Do not include exploit details", " ".join(policy.split()))

    def test_all_specialized_issue_forms_exist(self):
        issue_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
        for name in (
            "bug.yml",
            "feature.yml",
            "packaging.yml",
            "rendering.yml",
            "translation.yml",
            "theme.yml",
        ):
            self.assertTrue((issue_dir / name).is_file(), name)

    def test_documentation_sync_covers_five_public_contracts(self):
        checklist = (ROOT / "docs" / "DOCUMENTATION_SYNC.md").read_text(
            encoding="utf-8"
        )
        for name in (
            "README.md",
            "MANUAL_EN.md",
            "MANUEL_FR.md",
            "convert --help",
            "SKILL.md",
        ):
            self.assertIn(name, checklist)

    def test_closed_g1_records_are_archived_and_hash_preserved(self):
        reliability = ROOT / "docs" / "project-reliability"
        archive = reliability / "archive" / "g1"
        self.assertEqual(list(reliability.glob("G1_*")), [])

        manifest_entries = {}
        manifest = archive / "G1_EVIDENCE_MANIFEST.sha256"
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, original_path = line.split(maxsplit=1)
            manifest_entries[Path(original_path).name] = digest.lower()

        for name in (
            "BACKLOG.md",
            "G1_EXECUTION_BOARD.md",
            "G1_GATE_REPORT.md",
            "G1_IDENTITY_RESEARCH.md",
            "G1_QAS_EVIDENCE.md",
            "G1_RENDERER_SPIKE_REPORT.md",
            "G1_WINDOWS_NATIVE_EVIDENCE.md",
        ):
            archived = archive / name
            self.assertTrue(archived.is_file(), name)
            actual = hashlib.sha256(archived.read_bytes()).hexdigest()
            self.assertEqual(actual, manifest_entries[name], name)

    def test_active_backlog_excludes_closed_gate_work(self):
        active = (
            ROOT / "docs" / "project-reliability" / "BACKLOG.md"
        ).read_text(encoding="utf-8")
        self.assertIn("archive/g1/README.md", active)
        self.assertNotIn("## Lot 0", active)
        self.assertNotIn("## Lot 1A", active)


if __name__ == "__main__":
    unittest.main()
