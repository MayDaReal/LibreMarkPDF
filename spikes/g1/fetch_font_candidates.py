"""Fetch or verify the immutable G1 font candidate set."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable


HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "font_candidates_static.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or not manifest.get("files"):
        raise ValueError("Unsupported or empty font manifest")
    filenames = [item["filename"] for item in manifest["files"]]
    if len(filenames) != len(set(filenames)):
        raise ValueError("Duplicate font filename in manifest")
    return manifest


def iter_assets(manifest: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    emitted = set()
    for item in manifest["files"]:
        assets = (
            {
                "bytes": item["bytes"],
                "filename": Path("fonts") / item["filename"],
                "sha256": item["sha256"],
                "url": item["url"],
            },
            {
                "bytes": item["license_bytes"],
                "filename": Path("licenses") / item["license_filename"],
                "sha256": item["license_sha256"],
                "url": item["license_url"],
            },
        )
        for asset in assets:
            if asset["filename"] not in emitted:
                emitted.add(asset["filename"])
                yield asset


def verify(path: Path, expected_bytes: int, expected_sha256: str) -> None:
    if not path.is_file():
        raise ValueError("Missing asset: {}".format(path))
    if path.stat().st_size != expected_bytes:
        raise ValueError("Unexpected size for {}".format(path))
    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise ValueError("Unexpected SHA-256 for {}: {}".format(path, actual_sha256))


def fetch(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "LibreMarkPDF-G1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with temporary.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--manifest", default=MANIFEST_PATH, type=Path)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing files without using the network.",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    records = []
    for asset in iter_assets(manifest):
        target = args.output_dir / asset["filename"]
        if not args.verify_only and not target.exists():
            fetch(asset["url"], target)
        verify(target, asset["bytes"], asset["sha256"])
        records.append(
            {
                "bytes": asset["bytes"],
                "path": str(asset["filename"]).replace("\\", "/"),
                "sha256": asset["sha256"],
            }
        )

    print(json.dumps({"status": "ok", "verified": records}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
