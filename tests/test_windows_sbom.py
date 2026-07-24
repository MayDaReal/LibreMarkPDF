"""Pure tests for the exact-candidate SPDX generator."""

import json
import tempfile
import unittest
from pathlib import Path

from tools import generate_windows_sbom


class TestWindowsSbom(unittest.TestCase):
    def test_lock_and_artifact_inventory_are_hashed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = root / "lock.txt"
            lock.write_text(
                "Markdown==3.9 \\\n"
                "  --hash=sha256:"
                "9f4d91ed810864ea88a6f32c07ba8bee1346c0cc1f6b1f9f6c822f2a9667d280\n",
                encoding="utf-8",
            )
            artifact = root / "candidate"
            artifact.mkdir()
            (artifact / "LibreMarkPDF-cli.exe").write_bytes(b"candidate")
            document = generate_windows_sbom.generate(
                lock, artifact, "a" * 40, "2026-07-18T12:00:00Z"
            )
        self.assertEqual(document["spdxVersion"], "SPDX-2.3")
        self.assertEqual(len(document["files"]), 1)
        self.assertEqual(
            len(
                document["packages"][0]["packageVerificationCode"][
                    "packageVerificationCodeValue"
                ]
            ),
            40,
        )
        self.assertEqual(document["files"][0]["licenseConcluded"], "NOASSERTION")
        self.assertEqual(document["files"][0]["copyrightText"], "NOASSERTION")
        self.assertEqual(
            [item["algorithm"] for item in document["files"][0]["checksums"]],
            ["SHA1", "SHA256"],
        )
        self.assertEqual(document["packages"][1]["licenseDeclared"], "BSD-3-Clause")
        self.assertEqual(
            document["packages"][1]["checksums"][0]["checksumValue"],
            "9f4d91ed810864ea88a6f32c07ba8bee1346c0cc1f6b1f9f6c822f2a9667d280",
        )
        json.dumps(document)

    def test_every_locked_windows_dependency_has_a_declared_mapping(self):
        lock = (
            Path(__file__).resolve().parent.parent
            / "requirements" / "locks" / "windows-x64-py39.txt"
        )
        packages = generate_windows_sbom.locked_packages(lock)
        self.assertGreaterEqual(len(packages), 19)
        self.assertNotIn("NOASSERTION", [item["license"] for item in packages])
        licenses = {item["name"].lower(): item["license"] for item in packages}
        self.assertEqual(licenses["customtkinter"], "MIT")
        self.assertEqual(licenses["darkdetect"], "BSD-3-Clause")


if __name__ == "__main__":
    unittest.main()
