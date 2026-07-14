"""Compare two G1 visual-probe outputs against ADR-002 thresholds."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from PIL import Image, ImageChops


SSIM_MINIMUM = 0.995
DELTA_THRESHOLD = 16
CHANGED_PIXEL_MAXIMUM_PERCENT = 0.10
LARGEST_REGION_MAXIMUM_PERCENT = 0.50


class RegionSet:
    def __init__(self) -> None:
        self.parent: List[int] = []
        self.area: List[int] = []

    def create(self) -> int:
        label = len(self.parent)
        self.parent.append(label)
        self.area.append(0)
        return label

    def find(self, label: int) -> int:
        root = label
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[label] != label:
            parent = self.parent[label]
            self.parent[label] = root
            label = parent
        return root

    def union(self, first: int, second: int) -> int:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root == second_root:
            return first_root
        if self.area[first_root] < self.area[second_root]:
            first_root, second_root = second_root, first_root
        self.parent[second_root] = first_root
        self.area[first_root] += self.area[second_root]
        self.area[second_root] = 0
        return first_root

    def add(self, label: int, count: int) -> None:
        self.area[self.find(label)] += count

    def largest(self) -> int:
        return max((self.area[self.find(i)] for i in range(len(self.parent))), default=0)


def global_ssim(reference: Image.Image, candidate: Image.Image) -> float:
    left = reference.convert("L").tobytes()
    right = candidate.convert("L").tobytes()
    if len(left) != len(right) or not left:
        raise ValueError("SSIM requires equal non-empty images")
    count = len(left)
    left_mean = sum(left) / count
    right_mean = sum(right) / count
    left_variance = sum((value - left_mean) ** 2 for value in left) / count
    right_variance = sum((value - right_mean) ** 2 for value in right) / count
    covariance = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right)
    ) / count
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    numerator = (2 * left_mean * right_mean + c1) * (2 * covariance + c2)
    denominator = (
        (left_mean**2 + right_mean**2 + c1)
        * (left_variance + right_variance + c2)
    )
    return numerator / denominator if denominator else 1.0


def changed_regions(
    reference: Image.Image,
    candidate: Image.Image,
    threshold: int = DELTA_THRESHOLD,
) -> Tuple[int, int]:
    left = reference.convert("RGB")
    right = candidate.convert("RGB")
    if left.size != right.size:
        raise ValueError("Changed-region analysis requires equal image dimensions")
    width, height = left.size
    left_pixels = left.load()
    right_pixels = right.load()
    regions = RegionSet()
    previous: List[Tuple[int, int, int]] = []
    changed = 0

    for y in range(height):
        runs: List[Tuple[int, int, int]] = []
        x = 0
        while x < width:
            left_pixel = left_pixels[x, y]
            right_pixel = right_pixels[x, y]
            is_changed = max(
                abs(left_pixel[channel] - right_pixel[channel]) for channel in range(3)
            ) > threshold
            if not is_changed:
                x += 1
                continue
            start = x
            x += 1
            while x < width:
                left_pixel = left_pixels[x, y]
                right_pixel = right_pixels[x, y]
                if max(
                    abs(left_pixel[channel] - right_pixel[channel])
                    for channel in range(3)
                ) <= threshold:
                    break
                x += 1
            end = x - 1
            overlaps = [
                label
                for previous_start, previous_end, label in previous
                if previous_end >= start - 1 and previous_start <= end + 1
            ]
            label = overlaps[0] if overlaps else regions.create()
            for other in overlaps[1:]:
                label = regions.union(label, other)
            length = end - start + 1
            regions.add(label, length)
            changed += length
            runs.append((start, end, label))
        previous = runs
    return changed, regions.largest()


def page_metrics(reference: Image.Image, candidate: Image.Image) -> Dict[str, Any]:
    if reference.size != candidate.size:
        return {
            "candidate_pixels": list(candidate.size),
            "dimensions_equal": False,
            "reference_pixels": list(reference.size),
            "threshold_pass": False,
        }
    pixel_count = reference.width * reference.height
    changed, largest = changed_regions(reference, candidate)
    ssim = global_ssim(reference, candidate)
    changed_percent = changed * 100.0 / pixel_count
    largest_percent = largest * 100.0 / pixel_count
    return {
        "changed_pixel_percent": changed_percent,
        "dimensions_equal": True,
        "largest_changed_region_percent": largest_percent,
        "pixels": list(reference.size),
        "ssim": ssim,
        "threshold_pass": (
            ssim >= SSIM_MINIMUM
            and changed_percent <= CHANGED_PIXEL_MAXIMUM_PERCENT
            and largest_percent <= LARGEST_REGION_MAXIMUM_PERCENT
        ),
    }


def load_evidence(directory: Path) -> Dict[str, Any]:
    path = directory / "evidence.json"
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("schema") != 1 or not evidence.get("pages"):
        raise ValueError("Unsupported or empty evidence: {}".format(path))
    return evidence


def dimensions_equal(first: Dict[str, Any], second: Dict[str, Any]) -> bool:
    return math.isclose(first["width_points"], second["width_points"], abs_tol=0.01) and math.isclose(
        first["height_points"], second["height_points"], abs_tol=0.01
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", required=True, type=Path)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diff-dir", required=True, type=Path)
    parser.add_argument(
        "--comparison",
        choices=("cross-os", "appearance"),
        default="cross-os",
    )
    args = parser.parse_args()

    reference = load_evidence(args.reference_dir)
    candidate = load_evidence(args.candidate_dir)
    reference_pages: Sequence[Dict[str, Any]] = reference["pages"]
    candidate_pages: Sequence[Dict[str, Any]] = candidate["pages"]
    page_count_equal = len(reference_pages) == len(candidate_pages)
    args.diff_dir.mkdir(parents=True, exist_ok=True)
    comparisons = []

    for index in range(min(len(reference_pages), len(candidate_pages))):
        reference_page = reference_pages[index]
        candidate_page = candidate_pages[index]
        reference_image = Image.open(args.reference_dir / reference_page["image"])
        candidate_image = Image.open(args.candidate_dir / candidate_page["image"])
        metrics = page_metrics(reference_image, candidate_image)
        metrics.update(
            {
                "page": index + 1,
                "page_dimensions_equal": dimensions_equal(
                    reference_page, candidate_page
                ),
                "text_equal": (
                    reference_page["text_sha256"] == candidate_page["text_sha256"]
                ),
            }
        )
        if reference_image.size == candidate_image.size and metrics.get(
            "changed_pixel_percent", 0
        ) > 0:
            difference = ImageChops.difference(
                reference_image.convert("RGB"), candidate_image.convert("RGB")
            ).point(lambda value: min(255, value * 4))
            diff_path = args.diff_dir / "page-{:03d}-diff.png".format(index + 1)
            difference.save(diff_path, format="PNG", optimize=False)
            metrics["diff"] = diff_path.name
        comparisons.append(metrics)

    structural_pass = (
        page_count_equal
        and all(item["page_dimensions_equal"] for item in comparisons)
        and all(item["text_equal"] for item in comparisons)
    )
    raster_pass = page_count_equal and all(
        item["threshold_pass"] for item in comparisons
    )
    fingerprints_equal = (
        reference["profile_fingerprint"] == candidate["profile_fingerprint"]
        and reference["profile"]["html_fingerprint"]
        == candidate["profile"]["html_fingerprint"]
    )
    cross_os_pass = structural_pass and raster_pass and fingerprints_equal
    report = {
        "candidate_environment": candidate["environment"],
        "comparison": args.comparison,
        "fingerprints_equal": fingerprints_equal,
        "page_count_equal": page_count_equal,
        "pages": comparisons,
        "reference_environment": reference["environment"],
        "result": (
            "pass"
            if args.comparison == "cross-os" and cross_os_pass
            else "review" if args.comparison == "appearance" else "fail"
        ),
        "schema": 1,
        "structural_pass": structural_pass,
        "thresholds": {
            "changed_pixel_maximum_percent": CHANGED_PIXEL_MAXIMUM_PERCENT,
            "delta_threshold": DELTA_THRESHOLD,
            "largest_changed_region_maximum_percent": LARGEST_REGION_MAXIMUM_PERCENT,
            "raster_dpi": 144,
            "ssim_minimum": SSIM_MINIMUM,
            "ssim_variant": "global grayscale population SSIM",
        },
        "visual_threshold_pass": raster_pass,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.comparison == "cross-os" and not cross_os_pass:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
