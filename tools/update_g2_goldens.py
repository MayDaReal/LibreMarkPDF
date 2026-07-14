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
    parser.add_argument("--review-ticket", required=True,
                        help="Pull request or review record approving this appearance change")
    parser.add_argument("--reviewer", required=True,
                        help="Named human reviewer who approved the rendered appearance")
    parser.add_argument("--explanation", required=True,
                        help="Why expected HTML, structure, or appearance changed")
    args = parser.parse_args()
    if not all(value.strip() for value in (args.review_ticket, args.reviewer, args.explanation)):
        parser.error("review ticket, reviewer, and explanation must be non-empty")
    with tempfile.TemporaryDirectory(prefix="libremark-g2-golden-") as temporary:
        actual_dir = Path(temporary) / "actual"
        evidence = g2_visual_harness.generate_actual(args.manifest, actual_dir)
        raster_root = args.expected.parent / "rasters"
        if raster_root.exists():
            shutil.rmtree(raster_root)
        raster_root.mkdir(parents=True)
        for fixture in evidence["fixtures"]:
            source = actual_dir / (fixture["fixture"] + "-pages")
            shutil.copytree(source, raster_root / fixture["fixture"])
        expected = dict(evidence)
        expected["golden_review"] = {
            "explanation": args.explanation,
            "review_ticket": args.review_ticket,
            "reviewer": args.reviewer,
        }
        args.expected.parent.mkdir(parents=True, exist_ok=True)
        args.expected.write_text(json.dumps(expected, ensure_ascii=False, indent=2,
                                            sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"expected": str(args.expected), "result": "updated"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
