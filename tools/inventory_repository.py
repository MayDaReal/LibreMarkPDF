"""Report generated workspace data without changing the checkout."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIRECTORIES = (
    ".ruff_cache", ".venv-linux-py39", ".venv-windows-py39", "__pycache__",
    "browser-linux", "browser-win", "browsers", "build", "dist",
    "libremark_pdf.egg-info", "venv", "venv-linux",
)
GENERATED_FILES = (".coverage", "coverage.xml")


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def inventory(root: Path = ROOT) -> dict:
    """Return status and size for generated paths known to this repository."""
    result = subprocess.run(
        ["git", "status", "--short"], cwd=root, check=True,
        stdout=subprocess.PIPE, text=True,
    )
    entries = []
    for name in GENERATED_DIRECTORIES:
        path = root / name
        if path.is_dir():
            entries.append({"path": name, "bytes": directory_size(path), "kind": "directory"})
    for name in GENERATED_FILES:
        path = root / name
        if path.is_file():
            entries.append({"path": name, "bytes": path.stat().st_size, "kind": "file"})
    return {
        "generated": sorted(entries, key=lambda item: item["path"]),
        "git_status": result.stdout.splitlines(),
        "repository": str(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = inventory()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["generated"]:
            print("{path}: {bytes} bytes ({kind})".format(**item))
        print("Git changes: {0}".format(len(report["git_status"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
