"""Unit coverage for the non-mutating canonical visual comparison."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
HARNESS_PATH = ROOT / "tools" / "visual_regression.py"
SPEC = importlib.util.spec_from_file_location("visual_regression", HARNESS_PATH)
visual_regression = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = visual_regression
SPEC.loader.exec_module(visual_regression)
UPDATE_PATH = ROOT / "tools" / "update_visual_goldens.py"
UPDATE_SPEC = importlib.util.spec_from_file_location(
    "update_visual_goldens_for_test", UPDATE_PATH
)
update_visual_goldens = importlib.util.module_from_spec(UPDATE_SPEC)
UPDATE_SPEC.loader.exec_module(update_visual_goldens)


class TestVisualRegression(unittest.TestCase):
    def test_source_generation_uses_the_current_chromium_owner(self):
        self.assertIs(
            visual_regression.chromium.BrowserRenderer,
            __import__(
                "libremark_pdf.engine.chromium", fromlist=["BrowserRenderer"]
            ).BrowserRenderer,
        )
        self.assertFalse(hasattr(visual_regression.core, "_BrowserRenderer"))

    def test_fixture_manifest_has_the_required_corpus_size(self):
        manifest, fixtures = visual_regression.fixture_inputs(
            ROOT / "tests" / "fixtures" / "canonical" / "manifest.json"
        )
        self.assertEqual(manifest["schema"], 1)
        self.assertGreaterEqual(len(fixtures), 30)
        self.assertTrue(any(" " in str(item["markdown"]) for item in fixtures))
        self.assertTrue(any("é" in str(item["markdown"]) for item in fixtures))

    def test_identical_rasters_meet_frozen_thresholds(self):
        image = Image.new("RGB", (4, 4), "white")
        metrics = visual_regression.raster_metrics(image, image.copy())
        self.assertTrue(metrics["threshold_pass"])
        self.assertEqual(metrics["changed_pixel_percent"], 0.0)
        self.assertEqual(metrics["largest_changed_region_percent"], 0.0)

    def test_cross_platform_region_limit_matches_approved_policy(self):
        self.assertEqual(visual_regression.LARGEST_REGION_MAXIMUM_PERCENT, 0.10)

    def test_dimension_mismatch_fails_unconditionally(self):
        metrics = visual_regression.raster_metrics(
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
        source = (ROOT / "tools" / "update_visual_goldens.py").read_text(encoding="utf-8")
        self.assertIn("--actual-dir", source)
        self.assertIn("require_complete=True", source)
        self.assertIn("source_evidence_sha256", source)

    def test_checkpoint_collection_rejects_an_incomplete_final_corpus(self):
        manifest = ROOT / "tests" / "fixtures" / "canonical" / "manifest.json"
        with tempfile.TemporaryDirectory() as temporary:
            actual = Path(temporary) / "actual"
            entries = actual / "entries"
            entries.mkdir(parents=True)
            (entries / "01-headings.json").write_text(
                json.dumps({"schema": 1, "fixture": "01-headings"}), encoding="utf-8"
            )
            partial = visual_regression.collect_actual(manifest, actual)
            self.assertEqual([item["fixture"] for item in partial["fixtures"]], ["01-headings"])
            with self.assertRaisesRegex(ValueError, "Incomplete canonical evidence"):
                visual_regression.collect_actual(manifest, actual, require_complete=True)

    def test_embedded_image_hashes_are_payload_not_path_hashes(self):
        html = (
            '<img src="data:image/png;base64,YWJj">'
            '<img alt="same" src="data:image/gif;base64,YWJj">'
        )
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        self.assertEqual(visual_regression.embedded_image_hashes(html), [expected, expected])

    def test_missing_expected_data_fails_without_writing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "expected.json"
            actual = root / "actual"
            actual.mkdir()
            (actual / "evidence.json").write_text('{"schema": 1, "fixtures": []}', encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                visual_regression.compare(expected, actual, root / "report.json", root / "diff")
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
            report = visual_regression.compare(
                expected_root / "expected.json", actual_root, root / "report.json", root / "diff"
            )
            self.assertEqual(report["result"], "fail")
            self.assertFalse(report["fixtures"][0]["pages"][0]["structural_pass"])

    def test_platform_geometry_remains_exact_per_reviewed_platform(self):
        page = {
            "text_geometry_sha256": "linux",
            "text_geometry_sha256_by_platform": {
                "linux-x86_64": "linux",
                "windows-x64": "windows",
            },
        }
        self.assertEqual(
            visual_regression.expected_page_hash(
                page, "text_geometry_sha256", "windows-x64"
            ), "windows"
        )
        self.assertEqual(
            visual_regression.expected_page_hash(
                page, "text_geometry_sha256", "linux-x86_64"
            ), "linux"
        )
        self.assertIsNone(
            visual_regression.expected_page_hash(
                page, "text_geometry_sha256", "macos-arm64"
            )
        )

    def test_platform_geometry_merge_preserves_non_geometry_contract(self):
        common = {
            "canonical_html_sha256": "html", "embedded_image_sha256": [],
            "fixture": "sample", "links": [], "markdown_sha256": "markdown",
            "page_count": 1, "profile_canonical_sha256": "profile-json",
            "profile_fingerprint": "profile", "renderer_resource_hashes": {},
        }
        expected = {
            "fixtures": [dict(common, pages=[{
                "height_points": 842.0, "image": "page-001.png", "image_count": 0,
                "text_geometry_sha256": "linux", "text_sha256": "text",
                "width_points": 595.0,
            }])],
            "pdfium_version": "5.11.0", "raster_dpi": 144, "schema": 1,
        }
        evidence = {
            "fixtures": [dict(common, pages=[{
                "height_points": 842.0, "image": "page-001.png", "image_count": 0,
                "text_geometry_sha256": "windows", "text_sha256": "text",
                "width_points": 595.0,
            }])],
            "pdfium_version": "5.11.0", "platform_id": "windows-x64",
            "raster_dpi": 144, "schema": 1,
        }
        merged = update_visual_goldens._merge_platform_structure(
            expected, evidence, "windows-x64"
        )
        self.assertEqual(
            merged["fixtures"][0]["pages"][0][
                "text_geometry_sha256_by_platform"
            ],
            {"linux-x86_64": "linux", "windows-x64": "windows"},
        )
        self.assertEqual(
            merged["fixtures"][0]["pages"][0]["text_sha256_by_platform"],
            {"linux-x86_64": "text", "windows-x64": "text"},
        )
        self.assertEqual(
            merged["structure_platforms"], ["linux-x86_64", "windows-x64"]
        )
