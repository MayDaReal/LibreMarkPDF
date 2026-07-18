"""Characterization tests for the extracted local-resource domain."""

import base64
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libremark_pdf import core
from libremark_pdf.engine import resources


class TestResourceDomainCharacterization(unittest.TestCase):
    _PNG = b"\x89PNG\r\n\x1a\nsmall-png"

    def test_core_reexports_the_canonical_resource_implementations(self):
        for name in (
            "renderer_identity",
            "substitute_emoji_icons",
            "embed_local_resources",
        ):
            self.assertIs(getattr(core, name), getattr(resources, name), name)
        self.assertNotIn("libremark_pdf.core", Path(resources.__file__).read_text(encoding="utf-8"))

    def test_resource_hashes_match_the_frozen_runtime_files(self):
        hashes = resources._renderer_resource_hashes()
        self.assertEqual(hashes["css"], hashlib.sha256(core.DEFAULT_CSS_PATH.read_bytes()).hexdigest())
        self.assertEqual(
            hashes["fonts"],
            {name: hashlib.sha256((core.FONTS_DIR / name).read_bytes()).hexdigest()
             for name, _family, _weight in core._FONT_FILES},
        )
        self.assertEqual(
            hashes["icons"],
            {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(core.ICONS_DIR.glob("*.png"))},
        )

    def test_resource_path_keeps_all_three_layout_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen = root / "frozen"
            frozen.mkdir()
            (frozen / "style.css").write_text("body{}", encoding="utf-8")
            with mock.patch.object(sys, "_MEIPASS", str(frozen), create=True):
                self.assertEqual(core.resource_path("style.css"), frozen / "style.css")
            wheel = root / "libremark_pdf" / "style.css"
            wheel.parent.mkdir()
            wheel.write_text("body{}", encoding="utf-8")
            with mock.patch.object(core, "__file__", str(root / "missing" / "core.py")):
                with mock.patch.object(sys, "prefix", str(root)):
                    self.assertEqual(core.resource_path("style.css"), wheel)

    def test_data_uris_and_resource_limits_keep_stable_rejections(self):
        encoded = base64.b64encode(self._PNG).decode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            html = '<img src="data:image/png;base64,{0}">'.format(encoded)
            self.assertIn(encoded, core.embed_local_resources(html, tmp))
            with mock.patch.object(resources, "MAX_RESOURCE_COUNT", 1):
                with self.assertRaisesRegex(core.ConversionError, "image count exceeds configured limit"):
                    core.embed_local_resources(html + html, tmp)
            with mock.patch.object(resources, "MAX_TOTAL_RESOURCE_BYTES", len(self._PNG) - 1):
                with self.assertRaisesRegex(core.ConversionError, "total image size exceeds configured limit"):
                    core.embed_local_resources(html, tmp)


if __name__ == "__main__":
    unittest.main()
