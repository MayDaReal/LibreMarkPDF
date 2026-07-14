"""Unit coverage for the non-mutating Gate G2 visual comparison harness."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
HARNESS_PATH = ROOT / "tools" / "g2_visual_harness.py"
SPEC = importlib.util.spec_from_file_location("g2_visual_harness", HARNESS_PATH)
g2_visual_harness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = g2_visual_harness
SPEC.loader.exec_module(g2_visual_harness)


class TestG2VisualHarness(unittest.TestCase):
    def test_fixture_manifest_has_the_required_corpus_size(self):
        manifest, fixtures = g2_visual_harness.fixture_inputs(
            ROOT / "tests" / "fixtures" / "g2" / "manifest.json"
        )
        self.assertEqual(manifest["schema"], 1)
        self.assertGreaterEqual(len(fixtures), 30)

    def test_identical_rasters_meet_frozen_thresholds(self):
        image = Image.new("RGB", (4, 4), "white")
        metrics = g2_visual_harness.raster_metrics(image, image.copy())
        self.assertTrue(metrics["threshold_pass"])
        self.assertEqual(metrics["changed_pixel_percent"], 0.0)
        self.assertEqual(metrics["largest_changed_region_percent"], 0.0)

    def test_dimension_mismatch_fails_unconditionally(self):
        metrics = g2_visual_harness.raster_metrics(
            Image.new("RGB", (4, 4), "white"), Image.new("RGB", (5, 4), "white")
        )
        self.assertFalse(metrics["threshold_pass"])

    def test_normal_harness_has_no_golden_update_option(self):
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("--update-goldens", source)
        self.assertNotIn("--write-expected", source)

    def test_missing_expected_data_fails_without_writing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "expected.json"
            actual = root / "actual"
            actual.mkdir()
            (actual / "evidence.json").write_text('{"schema": 1, "fixtures": []}', encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                g2_visual_harness.compare(expected, actual, root / "report.json", root / "diff")
            self.assertFalse(expected.exists())
