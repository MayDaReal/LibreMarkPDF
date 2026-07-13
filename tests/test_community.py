"""Regression checks for actionable open-source health files."""

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


if __name__ == "__main__":
    unittest.main()
