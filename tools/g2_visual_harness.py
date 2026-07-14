"""Canonical Gate G2 PDF comparison harness.

This tool deliberately owns comparison only.  PDFs are produced through the
shared core API; PDFium then inspects and rasterizes the resulting files at the
ADR-002 fixed 144 DPI.  It never writes expected data.
"""

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from libremark_pdf import core


SCHEMA = 1
RASTER_DPI = 144
SSIM_MINIMUM = 0.70
DELTA_THRESHOLD = 16
CHANGED_PIXEL_MAXIMUM_PERCENT = 4.20
LARGEST_REGION_MAXIMUM_PERCENT = 0.05


def sha256_file(path):
    """Return the SHA-256 for one immutable input or evidence file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embedded_image_hashes(html):
    """Return ordered hashes for image payloads already embedded by core.

    This records fixture images as immutable rendering inputs without assigning
    browser-visible paths to the expected-data manifest.
    """
    hashes = []
    for value in re.findall(r"<img\b[^>]*\bsrc=[\"'](data:image/[^\"']+)[\"']", html, re.I):
        try:
            payload = value.split(",", 1)[1]
            decoded = base64.b64decode(payload, validate=True)
        except (IndexError, ValueError):
            raise ValueError("Malformed embedded image in canonical HTML")
        hashes.append(hashlib.sha256(decoded).hexdigest())
    return hashes


def text_geometry_sha256(text_page):
    """Hash extracted text order and PDFium character boxes at fixed precision."""
    boxes = []
    for index in range(text_page.count_chars()):
        box = text_page.get_charbox(index)
        boxes.append([round(float(value), 4) for value in box])
    payload = json.dumps(boxes, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RegionSet:
    """Run-length connected-component bookkeeping without a numeric dependency."""

    def __init__(self):
        self.parent = []
        self.area = []

    def create(self):
        label = len(self.parent)
        self.parent.append(label)
        self.area.append(0)
        return label

    def find(self, label):
        root = label
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[label] != label:
            parent = self.parent[label]
            self.parent[label] = root
            label = parent
        return root

    def union(self, first, second):
        first = self.find(first)
        second = self.find(second)
        if first == second:
            return first
        if self.area[first] < self.area[second]:
            first, second = second, first
        self.parent[second] = first
        self.area[first] += self.area[second]
        self.area[second] = 0
        return first

    def add(self, label, count):
        self.area[self.find(label)] += count

    def largest(self):
        return max((self.area[self.find(i)] for i in range(len(self.parent))), default=0)


def global_ssim(reference, candidate):
    """Calculate the frozen G1 global grayscale population SSIM variant."""
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
    denominator = (left_mean ** 2 + right_mean ** 2 + c1) * (
        left_variance + right_variance + c2
    )
    return ((2 * left_mean * right_mean + c1) * (2 * covariance + c2) / denominator
            if denominator else 1.0)


def changed_regions(reference, candidate, threshold=DELTA_THRESHOLD):
    """Return changed pixels and the largest 8-connected changed component."""
    left = reference.convert("RGB")
    right = candidate.convert("RGB")
    if left.size != right.size:
        raise ValueError("Changed-region analysis requires equal image dimensions")
    width, height = left.size
    left_pixels = left.load()
    right_pixels = right.load()
    regions = RegionSet()
    previous = []
    changed = 0
    for y in range(height):
        runs = []
        x = 0
        while x < width:
            first = left_pixels[x, y]
            second = right_pixels[x, y]
            if max(abs(first[channel] - second[channel]) for channel in range(3)) <= threshold:
                x += 1
                continue
            start = x
            x += 1
            while x < width:
                first = left_pixels[x, y]
                second = right_pixels[x, y]
                if max(abs(first[channel] - second[channel]) for channel in range(3)) <= threshold:
                    break
                x += 1
            end = x - 1
            overlaps = [label for prior_start, prior_end, label in previous
                        if prior_end >= start - 1 and prior_start <= end + 1]
            label = overlaps[0] if overlaps else regions.create()
            for other in overlaps[1:]:
                label = regions.union(label, other)
            length = end - start + 1
            regions.add(label, length)
            changed += length
            runs.append((start, end, label))
        previous = runs
    return changed, regions.largest()


def raster_metrics(reference, candidate):
    """Apply ADR-002 visual limits to one pair of equal-size page images."""
    if reference.size != candidate.size:
        return {"dimensions_equal": False, "threshold_pass": False}
    pixels = reference.width * reference.height
    changed, largest = changed_regions(reference, candidate)
    changed_percent = changed * 100.0 / pixels
    largest_percent = largest * 100.0 / pixels
    ssim = global_ssim(reference, candidate)
    return {
        "changed_pixel_percent": changed_percent,
        "dimensions_equal": True,
        "largest_changed_region_percent": largest_percent,
        "pixels": list(reference.size),
        "ssim": ssim,
        "threshold_pass": (ssim >= SSIM_MINIMUM
                           and changed_percent <= CHANGED_PIXEL_MAXIMUM_PERCENT
                           and largest_percent <= LARGEST_REGION_MAXIMUM_PERCENT),
    }


def pdf_evidence(pdf_path, raster_dir):
    """Inspect one PDF with pinned PDFium and retain canonical page rasters."""
    document = pdfium.PdfDocument(str(pdf_path))
    pages = []
    raster_dir.mkdir(parents=True, exist_ok=True)
    for index in range(len(document)):
        page = document[index]
        width, height = page.get_size()
        text_page = page.get_textpage()
        text = text_page.get_text_range()
        objects = list(page.get_objects())
        image_count = sum(1 for item in objects if str(item.type).lower().endswith("image"))
        bitmap = page.render(scale=RASTER_DPI / 72.0)
        image = bitmap.to_pil()
        image_path = raster_dir / "page-{:03d}.png".format(index + 1)
        image.save(image_path, format="PNG", optimize=False)
        pages.append({
            "height_points": round(height, 4),
            "image": image_path.name,
            "image_count": image_count,
            "text_geometry_sha256": text_geometry_sha256(text_page),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "width_points": round(width, 4),
        })
    raw = pdf_path.read_bytes()
    return {"links": sorted(set(match.decode("utf-8", "replace") for match in
                                 __import__("re").findall(rb"/URI\s*\(([^)]*)\)", raw))),
            "page_count": len(pages), "pages": pages}


def load_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != SCHEMA:
        raise ValueError("Unsupported schema in {}".format(path))
    return value


def fixture_inputs(manifest_path):
    """Validate fixture records and return immutable input hashes."""
    manifest = load_json(manifest_path)
    seen = set()
    records = []
    for fixture in manifest["fixtures"]:
        fixture_id = fixture["id"]
        if fixture_id in seen:
            raise ValueError("Duplicate fixture id: {}".format(fixture_id))
        seen.add(fixture_id)
        markdown_path = manifest_path.parent / fixture["markdown"]
        if not markdown_path.is_file():
            raise ValueError("Missing fixture: {}".format(markdown_path))
        records.append({"id": fixture_id, "markdown": markdown_path,
                        "markdown_sha256": sha256_file(markdown_path),
                        "render_date": fixture.get("render_date", "2026-07-14"),
                        "trusted_html": fixture.get("trusted_html", False),
                        "header_footer": fixture.get("header_footer", {})})
    if len(records) < 30:
        raise ValueError("Canonical corpus must contain at least 30 fixtures")
    return manifest, records


def generate_actual(manifest_path, actual_dir):
    """Render the corpus through core and emit a portable evidence manifest."""
    manifest, fixtures = fixture_inputs(manifest_path)
    actual_dir.mkdir(parents=True, exist_ok=True)
    evidence = {"fixtures": [], "pdfium_version": "5.11.0", "raster_dpi": RASTER_DPI,
                "schema": SCHEMA}
    # The harness has no renderer of its own: one core-managed browser is reused
    # solely to keep a 30-fixture comparison practical and deterministic.
    with core._BrowserRenderer() as renderer:
        for fixture in fixtures:
            header_footer = core.HeaderFooterConfig(**fixture["header_footer"])
            document = core.prepare_render_document(
                fixture["markdown"].read_text(encoding="utf-8"),
                render_date=fixture["render_date"], resource_root=fixture["markdown"].parent,
                trusted_html=fixture["trusted_html"], header_footer=header_footer,
            )
            pdf_path = actual_dir / (fixture["id"] + ".pdf")
            core.convert_markdown_to_pdf(fixture["markdown"], pdf_path,
                                         render_date=fixture["render_date"], overwrite=True,
                                         trusted_html=fixture["trusted_html"],
                                         header_footer=header_footer, _renderer=renderer)
            page_dir = actual_dir / (fixture["id"] + "-pages")
            entry = {"canonical_html_sha256": hashlib.sha256(
                        document.full_html.encode("utf-8")).hexdigest(),
                     "embedded_image_sha256": embedded_image_hashes(document.full_html),
                     "fixture": fixture["id"], "markdown_sha256": fixture["markdown_sha256"],
                     "pdf_sha256": sha256_file(pdf_path),
                     "profile_canonical_sha256": hashlib.sha256(
                        document.profile.canonical_json().encode("utf-8")).hexdigest(),
                     "profile_fingerprint": document.profile.fingerprint,
                     "renderer_resource_hashes": json.loads(
                        document.profile.canonical_json())["resource_hashes"]}
            entry.update(pdf_evidence(pdf_path, page_dir))
            evidence["fixtures"].append(entry)
    (actual_dir / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return evidence


def compare(expected_path, actual_dir, report_path, diff_dir):
    """Compare actual evidence to approved data and retain diffs on failure."""
    expected = load_json(expected_path)
    actual = load_json(actual_dir / "evidence.json")
    expected_by_id = {item["fixture"]: item for item in expected["fixtures"]}
    actual_by_id = {item["fixture"]: item for item in actual["fixtures"]}
    failures = []
    results = []
    for fixture_id in sorted(set(expected_by_id) | set(actual_by_id)):
        reference = expected_by_id.get(fixture_id)
        candidate = actual_by_id.get(fixture_id)
        if reference is None or candidate is None:
            failures.append({"fixture": fixture_id, "reason": "fixture-set-mismatch"})
            continue
        checks = {key: reference.get(key) == candidate.get(key) for key in
                  ("markdown_sha256", "canonical_html_sha256", "embedded_image_sha256",
                   "profile_canonical_sha256", "profile_fingerprint",
                   "renderer_resource_hashes", "page_count", "links")}
        page_results = []
        if len(reference["pages"]) != len(candidate["pages"]):
            checks["pagination"] = False
        for index, (left, right) in enumerate(zip(reference["pages"], candidate["pages"])):
            structural = all(left.get(key) == right.get(key) for key in
                             ("width_points", "height_points", "text_geometry_sha256",
                              "text_sha256", "image_count"))
            reference_image = Path(expected_path).parent / "rasters" / fixture_id / left["image"]
            candidate_image = actual_dir / (fixture_id + "-pages") / right["image"]
            metrics = raster_metrics(Image.open(reference_image), Image.open(candidate_image))
            if not metrics["threshold_pass"]:
                target = diff_dir / fixture_id
                target.mkdir(parents=True, exist_ok=True)
                difference = ImageChops.difference(Image.open(reference_image).convert("RGB"),
                                                    Image.open(candidate_image).convert("RGB"))
                difference.point(lambda value: min(255, value * 4)).save(
                    target / "page-{:03d}-diff.png".format(index + 1), format="PNG")
            page_results.append({"page": index + 1, "structural_pass": structural,
                                 "visual": metrics})
        passed = all(checks.values()) and all(item["structural_pass"] and
                                               item["visual"]["threshold_pass"]
                                               for item in page_results)
        if not passed:
            failures.append({"fixture": fixture_id, "checks": checks,
                             "pages": page_results})
        results.append({"fixture": fixture_id, "pass": passed, "checks": checks,
                        "pages": page_results})
    report = {"failures": failures, "fixtures": results, "result": "pass" if not failures else "fail",
              "schema": SCHEMA, "thresholds": {"changed_pixel_maximum_percent": CHANGED_PIXEL_MAXIMUM_PERCENT,
              "delta_threshold": DELTA_THRESHOLD, "largest_changed_region_maximum_percent": LARGEST_REGION_MAXIMUM_PERCENT,
              "raster_dpi": RASTER_DPI, "ssim_minimum": SSIM_MINIMUM}}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Run the immutable G2 visual comparison")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--diff-dir", type=Path, required=True)
    args = parser.parse_args()
    generate_actual(args.manifest, args.actual_dir)
    report = compare(args.expected, args.actual_dir, args.report, args.diff_dir)
    print(json.dumps({"report": str(args.report), "result": report["result"]}, sort_keys=True))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
