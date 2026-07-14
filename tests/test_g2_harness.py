"""Unit coverage for the non-mutating Gate G2 visual comparison harness."""

import importlib.util
import json
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
        self.assertTrue(any(" " in str(item["markdown"]) for item in fixtures))
        self.assertTrue(any("é" in str(item["markdown"]) for item in fixtures))

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

    def test_generate_only_mode_cannot_write_expected_data(self):
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertIn("--generate-only", source)
        self.assertIn('"result": "generated"', source)

    def test_golden_writer_can_reuse_only_complete_reviewed_evidence(self):
        source = (ROOT / "tools" / "update_g2_goldens.py").read_text(encoding="utf-8")
        self.assertIn("--actual-dir", source)
        self.assertIn("require_complete=True", source)
        self.assertIn("source_evidence_sha256", source)

    def test_checkpoint_collection_rejects_an_incomplete_final_corpus(self):
        manifest = ROOT / "tests" / "fixtures" / "g2" / "manifest.json"
        with tempfile.TemporaryDirectory() as temporary:
            actual = Path(temporary) / "actual"
            entries = actual / "entries"
            entries.mkdir(parents=True)
            (entries / "01-headings.json").write_text(
                json.dumps({"schema": 1, "fixture": "01-headings"}), encoding="utf-8"
            )
            partial = g2_visual_harness.collect_actual(manifest, actual)
            self.assertEqual([item["fixture"] for item in partial["fixtures"]], ["01-headings"])
            with self.assertRaisesRegex(ValueError, "Incomplete canonical evidence"):
                g2_visual_harness.collect_actual(manifest, actual, require_complete=True)

    def test_embedded_image_hashes_are_payload_not_path_hashes(self):
        html = (
            '<img src="data:image/png;base64,YWJj">'
            '<img alt="same" src="data:image/gif;base64,YWJj">'
        )
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        self.assertEqual(g2_visual_harness.embedded_image_hashes(html), [expected, expected])

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

    def test_text_geometry_difference_fails_unconditionally(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected_root = root / "expected"
            actual_root = root / "actual"
            expected_raster = expected_root / "rasters" / "sample"
            actual_raster = actual_root / "sample-pages"
            expected_raster.mkdir(parents=True)
            actual_raster.mkdir(parents=True)
            Image.new("RGB", (2, 2), "white").save(expected_raster / "page-001.png")
            Image.new("RGB", (2, 2), "white").save(actual_raster / "page-001.png")
            common = {
                "canonical_html_sha256": "html", "embedded_image_sha256": [],
                "fixture": "sample", "links": [], "markdown_sha256": "markdown",
                "page_count": 1, "profile_canonical_sha256": "profile-json",
                "profile_fingerprint": "profile", "renderer_resource_hashes": {},
            }
            expected = dict(common, pages=[{
                "height_points": 842.0, "image": "page-001.png", "image_count": 0,
                "text_geometry_sha256": "left", "text_sha256": "text", "width_points": 595.0,
            }])
            actual = dict(common, pages=[{
                "height_points": 842.0, "image": "page-001.png", "image_count": 0,
                "text_geometry_sha256": "right", "text_sha256": "text", "width_points": 595.0,
            }])
            (expected_root / "expected.json").write_text(
                json.dumps({"schema": 1, "fixtures": [expected]}), encoding="utf-8"
            )
            (actual_root / "evidence.json").write_text(
                json.dumps({"schema": 1, "fixtures": [actual]}), encoding="utf-8"
            )
            report = g2_visual_harness.compare(
                expected_root / "expected.json", actual_root, root / "report.json", root / "diff"
            )
            self.assertEqual(report["result"], "fail")
            self.assertFalse(report["fixtures"][0]["pages"][0]["structural_pass"])
