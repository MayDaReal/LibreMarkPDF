"""Focused pure tests for the non-production G1 spike tools."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from spikes.g1.fetch_font_candidates import iter_assets, load_manifest
from spikes.g1.visual_compare import (
    CHANGED_PIXEL_MAXIMUM_PERCENT,
    DELTA_THRESHOLD,
    LARGEST_REGION_MAXIMUM_PERCENT,
    SSIM_MINIMUM,
    changed_regions,
    global_ssim,
    page_metrics,
)
from spikes.g1.visual_probe import (
    DEFAULT_CHROMIUM_ARGS,
    font_face,
    output_is_outside_repository,
)


ROOT = Path(__file__).resolve().parent.parent


class TestFontCandidateManifest(unittest.TestCase):
    def test_manifest_pins_complete_font_and_license_records(self):
        manifest = load_manifest()
        self.assertEqual(manifest["schema"], 1)
        self.assertEqual(len(manifest["files"]), 7)
        self.assertGreater(sum(item["bytes"] for item in manifest["files"]), 20_000_000)
        for item in manifest["files"]:
            self.assertEqual(len(item["sha256"]), 64)
            self.assertEqual(len(item["license_sha256"]), 64)
            self.assertIn("css_family", item)
            self.assertIn("css_weight", item)
            self.assertTrue(any(revision in item["url"] for revision in manifest["sources"].values()))

    def test_reused_license_is_fetched_once(self):
        manifest = load_manifest()
        asset_paths = [asset["filename"] for asset in iter_assets(manifest)]
        self.assertEqual(len(asset_paths), len(set(asset_paths)))

    def test_legacy_variable_manifest_remains_selectable(self):
        legacy = load_manifest(ROOT / "spikes" / "g1" / "font_candidates.json")
        self.assertEqual(font_face(legacy["files"][0]), ("G1 Noto Sans", "100 900"))

    def test_fixture_covers_required_scripts(self):
        fixture = (
            ROOT / "spikes" / "g1" / "fixtures" / "visual-representative.md"
        ).read_text(encoding="utf-8")
        for sample in ("Français", "العربية", "简体中文", "😀", "```python"):
            self.assertIn(sample, fixture)

    def test_windows_runner_separates_download_and_offline_phases(self):
        runner = (
            ROOT / "spikes" / "g1" / "run_windows_visual_evidence.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn('[ValidateSet("Prepare", "Run")]', runner)
        self.assertIn("--verify-only", runner)
        self.assertIn("PLAYWRIGHT_BROWSERS_PATH", runner)
        self.assertNotIn("playwright install", runner)
        self.assertIn("Compress-Archive", runner)
        self.assertIn("Resolve-Path -LiteralPath $_.FullName -Relative", runner)
        self.assertNotIn(".Substring($EvidenceRoot.Length", runner)

    def test_visual_probe_rejects_system_font_fallback_for_candidate(self):
        probe = (ROOT / "spikes" / "g1" / "visual_probe.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("CSS.getPlatformFontsForNode", probe)
        self.assertIn('"chromium_args": args.chromium_arg', probe)
        self.assertIn("playwright.chromium.launch(args=args.chromium_arg)", probe)
        self.assertIn('not item["isCustomFont"]', probe)
        self.assertEqual(
            DEFAULT_CHROMIUM_ARGS,
            ["--disable-font-subpixel-positioning"],
        )


class TestVisualMetrics(unittest.TestCase):
    def test_approved_cross_os_thresholds_are_frozen(self):
        self.assertEqual(SSIM_MINIMUM, 0.70)
        self.assertEqual(DELTA_THRESHOLD, 16)
        self.assertEqual(CHANGED_PIXEL_MAXIMUM_PERCENT, 4.20)
        self.assertEqual(LARGEST_REGION_MAXIMUM_PERCENT, 0.05)

    def test_identical_images_pass_all_thresholds(self):
        image = Image.new("RGB", (4, 4), "white")
        metrics = page_metrics(image, image.copy())
        self.assertEqual(global_ssim(image, image.copy()), 1.0)
        self.assertEqual(changed_regions(image, image.copy()), (0, 0))
        self.assertTrue(metrics["threshold_pass"])

    def test_connected_changed_pixels_are_counted(self):
        reference = Image.new("RGB", (4, 4), "white")
        candidate = reference.copy()
        candidate.putpixel((1, 1), (0, 0, 0))
        candidate.putpixel((2, 2), (0, 0, 0))
        self.assertEqual(changed_regions(reference, candidate), (2, 2))

    def test_contiguous_geometry_change_fails_tight_region_limit(self):
        reference = Image.new("RGB", (100, 100), "white")
        candidate = reference.copy()
        for x in range(10):
            candidate.putpixel((x, 0), (0, 0, 0))
        metrics = page_metrics(reference, candidate)
        self.assertEqual(metrics["largest_changed_region_percent"], 0.1)
        self.assertFalse(metrics["threshold_pass"])

    def test_generated_outputs_inside_repository_are_rejected(self):
        self.assertFalse(output_is_outside_repository(ROOT / "generated"))
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(output_is_outside_repository(Path(directory) / "evidence"))


if __name__ == "__main__":
    unittest.main()
