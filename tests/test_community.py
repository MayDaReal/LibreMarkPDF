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

    def test_active_validation_docs_are_compact_and_available(self):
        for name in ("VALIDATION.md", "RELEASE.md", "PLATFORM_SUPPORT.md"):
            self.assertTrue((ROOT / "docs" / name).is_file(), name)

    def test_public_guides_link_the_published_release_candidate(self):
        release_url = (
            "https://github.com/MayDaReal/LibreMarkPDF/"
            "releases/tag/v0.1.0rc1"
        )
        for path in (
            ROOT / "README.md",
            ROOT / "docs" / "MANUAL_EN.md",
            ROOT / "docs" / "MANUEL_FR.md",
        ):
            self.assertIn(release_url, path.read_text(encoding="utf-8"), path)

    def test_release_guide_publishes_checksum_verification_key(self):
        release = (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8")
        self.assertIn("ssh-keygen -Y verify", release)
        self.assertIn(
            "SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM",
            release,
        )


if __name__ == "__main__":
    unittest.main()
