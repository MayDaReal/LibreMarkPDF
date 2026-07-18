"""Inspect PDFs produced by an exact frozen LibreMark PDF CLI artifact.

Rendering is delegated exclusively to the supplied console entry path. This
harness reuses the immutable G2 inspection and comparison functions and never
writes expected data.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from libremark_pdf import core
from tools import g2_visual_harness as visual


HEADER_OPTIONS = {
    "top_left": "--header-left",
    "top_center": "--header-center",
    "top_right": "--header-right",
    "bottom_left": "--footer-left",
    "bottom_center": "--footer-center",
    "bottom_right": "--footer-right",
}


def converter_command(converter, fixture, output_path):
    """Build one non-interactive artifact command from canonical fixture data."""
    command = [
        str(converter),
        "convert",
        str(fixture["markdown"]),
        "--output",
        str(output_path),
        "--date",
        fixture["render_date"],
        "--overwrite",
        "--json",
    ]
    if fixture["trusted_html"]:
        command.append("--trusted-html")
    for field, option in HEADER_OPTIONS.items():
        if field in fixture["header_footer"]:
            command.extend([option, fixture["header_footer"][field]])
    return command


def converter_environment():
    """Let the exact frozen artifact select its own bundled browser."""
    environment = os.environ.copy()
    environment.pop("PLAYWRIGHT_BROWSERS_PATH", None)
    return environment


def render_fixture(converter, fixture, actual_dir):
    """Run the exact artifact once and checkpoint inspected evidence."""
    header_footer = core.HeaderFooterConfig(**fixture["header_footer"])
    document = core.prepare_render_document(
        fixture["markdown"].read_text(encoding="utf-8"),
        render_date=fixture["render_date"],
        resource_root=fixture["markdown"].parent,
        trusted_html=fixture["trusted_html"],
        header_footer=header_footer,
    )
    pdf_path = actual_dir / (fixture["id"] + ".pdf")
    completed = subprocess.run(
        converter_command(converter, fixture, pdf_path),
        capture_output=True,
        env=converter_environment(),
        text=True,
        encoding="utf-8",
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "{0} emitted invalid JSON (exit {1}); stdout={2!r}; stderr={3!r}".format(
                fixture["id"], completed.returncode,
                completed.stdout, completed.stderr,
            )
        ) from exc
    if completed.returncode != 0 or completed.stderr or payload.get("status") != "ok":
        raise RuntimeError(
            "{0} artifact conversion failed (exit {1}); payload={2!r}; stderr={3!r}".format(
                fixture["id"], completed.returncode, payload, completed.stderr,
            )
        )
    if payload.get("renderer_fingerprint") != document.profile.fingerprint:
        raise RuntimeError(
            "{0} artifact/source renderer fingerprint mismatch".format(fixture["id"])
        )
    page_dir = actual_dir / (fixture["id"] + "-pages")
    entry = {
        "artifact_json": payload,
        "canonical_html_sha256": hashlib.sha256(
            document.full_html.encode("utf-8")
        ).hexdigest(),
        "embedded_image_sha256": visual.embedded_image_hashes(document.full_html),
        "fixture": fixture["id"],
        "markdown_sha256": fixture["markdown_sha256"],
        "pdf_sha256": visual.sha256_file(pdf_path),
        "profile_canonical_sha256": hashlib.sha256(
            document.profile.canonical_json().encode("utf-8")
        ).hexdigest(),
        "profile_fingerprint": document.profile.fingerprint,
        "renderer_resource_hashes": json.loads(
            document.profile.canonical_json()
        )["resource_hashes"],
    }
    entry.update(visual.pdf_evidence(pdf_path, page_dir))
    entry["schema"] = visual.SCHEMA
    visual._write_json_atomic(
        actual_dir / "entries" / (fixture["id"] + ".json"), entry
    )
    return entry


def generate(converter, manifest_path, actual_dir, fixture_ids=None):
    """Generate resumable evidence only through the exact frozen converter."""
    _manifest, fixtures = visual.fixture_inputs(manifest_path)
    if fixture_ids:
        requested = set(fixture_ids)
        known = {fixture["id"] for fixture in fixtures}
        unknown = requested - known
        if unknown:
            raise ValueError("Unknown fixture id: " + ", ".join(sorted(unknown)))
        fixtures = [fixture for fixture in fixtures if fixture["id"] in requested]
    actual_dir.mkdir(parents=True, exist_ok=True)
    for fixture in fixtures:
        render_fixture(converter, fixture, actual_dir)
    evidence = visual.collect_actual(manifest_path, actual_dir)
    visual._write_json_atomic(actual_dir / "evidence.json", evidence)
    return evidence


def main():
    parser = argparse.ArgumentParser(
        description="Run canonical comparisons through a frozen CLI artifact"
    )
    parser.add_argument("--converter", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--diff-dir", type=Path, required=True)
    parser.add_argument("--fixture", action="append", default=[])
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()
    if not args.converter.is_file():
        parser.error("converter executable is unavailable")
    if args.collect_only and args.fixture:
        parser.error("--collect-only cannot be combined with --fixture")
    if args.collect_only:
        evidence = visual.collect_actual(
            args.manifest, args.actual_dir, require_complete=True
        )
        visual._write_json_atomic(args.actual_dir / "evidence.json", evidence)
    else:
        evidence = generate(
            args.converter, args.manifest, args.actual_dir, args.fixture
        )
    if len(evidence["fixtures"]) < 30:
        print(json.dumps({
            "actual": str(args.actual_dir),
            "fixtures": len(evidence["fixtures"]),
            "result": "generated-partial",
        }, sort_keys=True))
        return 0
    report = visual.compare(
        args.expected, args.actual_dir, args.report, args.diff_dir
    )
    print(json.dumps({
        "actual": str(args.actual_dir),
        "fixtures": len(evidence["fixtures"]),
        "report": str(args.report),
        "result": report["result"],
    }, sort_keys=True))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
