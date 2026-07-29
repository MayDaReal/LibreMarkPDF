"""Explicit, review-gated writer for canonical visual expected data.

Normal harness execution cannot import or call this writer.  Golden updates are
therefore deliberate review events rather than a test side effect.
"""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import visual_regression


def main():
    parser = argparse.ArgumentParser(description="Create reviewed visual golden evidence")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual-dir", type=Path,
                        help="Complete reviewed candidate evidence; avoids re-rendering it")
    parser.add_argument("--candidate-commit", required=True,
                        help="Exact Git commit from which the approved evidence was generated")
    parser.add_argument("--review-tag", required=True,
                        help="Signed local tag recording the human golden review")
    parser.add_argument("--review-ticket", required=True,
                        help="Pull request or review record approving this appearance change")
    parser.add_argument("--reviewer", required=True,
                        help="Named human reviewer who approved the rendered appearance")
    parser.add_argument("--explanation", required=True,
                        help="Why expected HTML, structure, or appearance changed")
    parser.add_argument(
        "--structure-platform", choices=(visual_regression.LINUX_X86_64,
                                          visual_regression.WINDOWS_X64),
        help="Merge exact text and geometry for one reviewed native platform without replacing rasters",
    )
    args = parser.parse_args()
    if not all(value.strip() for value in (args.review_ticket, args.reviewer, args.explanation)):
        parser.error("review ticket, reviewer, and explanation must be non-empty")
    if len(args.candidate_commit) != 40 or any(
            character not in "0123456789abcdef" for character in args.candidate_commit.lower()):
        parser.error("candidate commit must be a 40-character hexadecimal Git object ID")
    if args.structure_platform and not args.actual_dir:
        parser.error("--structure-platform requires --actual-dir")
    if args.actual_dir:
        actual_dir = args.actual_dir
        evidence = visual_regression.collect_actual(args.manifest, actual_dir,
                                                    require_complete=True)
        evidence_path = actual_dir / "evidence.json"
        if not evidence_path.is_file():
            parser.error("reviewed actual directory has no evidence.json")
        stored_evidence = visual_regression.load_json(evidence_path)
        if stored_evidence != evidence:
            parser.error("reviewed actual evidence.json does not match its checkpoints")
        _write_expected(args, actual_dir, evidence, visual_regression.sha256_file(evidence_path))
    else:
        _generate_and_write_expected(args)
    print(json.dumps({"expected": str(args.expected), "result": "updated"}, sort_keys=True))
    return 0


def _generate_and_write_expected(args):
    """Render a new reviewed candidate only when no pre-reviewed evidence is supplied."""
    with tempfile.TemporaryDirectory(prefix="libremark-visual-golden-") as temporary:
        actual_dir = Path(temporary) / "actual"
        evidence = visual_regression.generate_actual(args.manifest, actual_dir)
        _write_expected(args, actual_dir, evidence,
                        visual_regression.sha256_file(actual_dir / "evidence.json"))


def _write_expected(args, actual_dir, evidence, evidence_sha256):
    """Copy only reviewed raster inputs and record immutable review provenance."""
    if args.structure_platform:
        expected = _merge_platform_structure(
            visual_regression.load_json(args.expected), evidence, args.structure_platform
        )
    else:
        raster_root = args.expected.parent / "rasters"
        if raster_root.exists():
            shutil.rmtree(raster_root)
        raster_root.mkdir(parents=True)
        for fixture in evidence["fixtures"]:
            source = actual_dir / (fixture["fixture"] + "-pages")
            shutil.copytree(source, raster_root / fixture["fixture"])
        expected = dict(evidence)
    expected["golden_review"] = {
        "candidate_commit": args.candidate_commit,
        "explanation": args.explanation,
        "review_tag": args.review_tag,
        "review_ticket": args.review_ticket,
        "reviewer": args.reviewer,
        "source_evidence_sha256": evidence_sha256,
    }
    args.expected.parent.mkdir(parents=True, exist_ok=True)
    args.expected.write_text(json.dumps(expected, ensure_ascii=False, indent=2,
                                        sort_keys=True) + "\n", encoding="utf-8")


def _merge_platform_structure(expected, evidence, platform_id):
    """Add exact native text/geometry while preserving approved Linux rasters."""
    if expected.get("pdfium_version") != evidence.get("pdfium_version"):
        raise ValueError("Geometry evidence uses a different PDFium version")
    if expected.get("raster_dpi") != evidence.get("raster_dpi"):
        raise ValueError("Geometry evidence uses a different raster DPI")
    actual_by_id = {item["fixture"]: item for item in evidence["fixtures"]}
    if set(actual_by_id) != {item["fixture"] for item in expected["fixtures"]}:
        raise ValueError("Geometry evidence fixture set does not match expected data")
    fixture_fields = (
        "markdown_sha256", "canonical_html_sha256", "embedded_image_sha256",
        "profile_canonical_sha256", "profile_fingerprint", "renderer_resource_hashes",
        "page_count", "links",
    )
    page_fields = ("width_points", "height_points", "image_count")
    for reference in expected["fixtures"]:
        candidate = actual_by_id[reference["fixture"]]
        if any(reference.get(key) != candidate.get(key) for key in fixture_fields):
            raise ValueError(
                "Geometry evidence changed a non-geometry fixture contract: {0}".format(
                    reference["fixture"]
                )
            )
        if len(reference["pages"]) != len(candidate["pages"]):
            raise ValueError("Geometry evidence changed pagination")
        for left, right in zip(reference["pages"], candidate["pages"]):
            if any(left.get(key) != right.get(key) for key in page_fields):
                raise ValueError("Geometry evidence changed a non-geometry page contract")
            for field in ("text_geometry_sha256", "text_sha256"):
                mapping = dict(left.get(field + "_by_platform", {}))
                mapping.setdefault(visual_regression.LINUX_X86_64, left[field])
                mapping[platform_id] = right[field]
                left[field + "_by_platform"] = mapping
    expected["structure_platforms"] = sorted({
        key
        for fixture in expected["fixtures"]
        for page in fixture["pages"]
        for key in page["text_geometry_sha256_by_platform"]
    })
    return expected


if __name__ == "__main__":
    raise SystemExit(main())
