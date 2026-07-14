"""Explicit, review-gated writer for Gate G2 expected visual data.

Normal harness execution cannot import or call this writer.  Golden updates are
therefore deliberate review events rather than a test side effect.
"""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import g2_visual_harness


def main():
    parser = argparse.ArgumentParser(description="Create reviewed G2 golden evidence")
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
    args = parser.parse_args()
    if not all(value.strip() for value in (args.review_ticket, args.reviewer, args.explanation)):
        parser.error("review ticket, reviewer, and explanation must be non-empty")
    if len(args.candidate_commit) != 40 or any(
            character not in "0123456789abcdef" for character in args.candidate_commit.lower()):
        parser.error("candidate commit must be a 40-character hexadecimal Git object ID")
    if args.actual_dir:
        actual_dir = args.actual_dir
        evidence = g2_visual_harness.collect_actual(args.manifest, actual_dir,
                                                     require_complete=True)
        evidence_path = actual_dir / "evidence.json"
        if not evidence_path.is_file():
            parser.error("reviewed actual directory has no evidence.json")
        stored_evidence = g2_visual_harness.load_json(evidence_path)
        if stored_evidence != evidence:
            parser.error("reviewed actual evidence.json does not match its checkpoints")
        _write_expected(args, actual_dir, evidence, g2_visual_harness.sha256_file(evidence_path))
    else:
        _generate_and_write_expected(args)
    print(json.dumps({"expected": str(args.expected), "result": "updated"}, sort_keys=True))
    return 0


def _generate_and_write_expected(args):
    """Render a new reviewed candidate only when no pre-reviewed evidence is supplied."""
    with tempfile.TemporaryDirectory(prefix="libremark-g2-golden-") as temporary:
        actual_dir = Path(temporary) / "actual"
        evidence = g2_visual_harness.generate_actual(args.manifest, actual_dir)
        _write_expected(args, actual_dir, evidence,
                        g2_visual_harness.sha256_file(actual_dir / "evidence.json"))


def _write_expected(args, actual_dir, evidence, evidence_sha256):
    """Copy only reviewed raster inputs and record immutable review provenance."""
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


if __name__ == "__main__":
    raise SystemExit(main())
