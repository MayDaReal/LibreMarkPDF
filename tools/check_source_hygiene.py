"""Reject generated or sensitive paths from a staged source manifest."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


FORBIDDEN_PARTS = {
    "__pycache__",
    ".coverage",
    ".libremark-pdf",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "browsers",
    "browser-linux",
    "browser-win",
    "build",
    "dist",
    "venv",
    "venv-linux",
}
FORBIDDEN_SUFFIXES = {".exe", ".pdf", ".pyc", ".pyo"}


def find_forbidden(paths: Iterable[str]) -> list[str]:
    """Return sorted manifest paths that must not ship in source archives."""
    rejected = []
    for raw_path in paths:
        path = Path(raw_path)
        if FORBIDDEN_PARTS.intersection(path.parts) or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            rejected.append(path.as_posix())
    return sorted(rejected)


def source_paths() -> Sequence[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Check newline-delimited archive members instead of the worktree.",
    )
    args = parser.parse_args()
    paths = (
        args.manifest.read_text(encoding="utf-8").splitlines()
        if args.manifest
        else source_paths()
    )
    rejected = find_forbidden(paths)
    if rejected:
        for path in rejected:
            print("forbidden source path: {}".format(path), file=sys.stderr)
        return 1
    print("source hygiene: ok ({} source paths)".format(len(paths)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
