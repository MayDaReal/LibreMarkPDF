"""Run one non-overlapping LibreMark PDF test suite with a staged browser."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PURE_TESTS = [
    "tests.test_cli",
    "tests.test_community",
    "tests.test_i18n",
    "tests.test_packaging",
    "tests.test_quality_foundations",
    "tests.test_core.TestTitleExtraction",
    "tests.test_core.TestHeaderFooterConfig",
    "tests.test_core.TestTemplateBuilding",
    "tests.test_core.TestMarkdownConversion",
]


def command_for_suite(suite: str) -> list[str]:
    """Return the single unittest command for the requested suite."""
    if suite == "pure":
        return [sys.executable, "-m", "unittest", *PURE_TESTS]
    if suite == "all":
        return [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    if suite == "ui":
        return [sys.executable, "-m", "unittest", "tests.test_gui", "-v"]
    if suite == "visual":
        return [sys.executable, "-m", "unittest", "tests.test_visual_regression", "-v"]
    raise ValueError("Unknown suite: {0}".format(suite))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", choices=("pure", "all", "ui", "visual"))
    parser.add_argument(
        "--browser-dir",
        type=Path,
        default=ROOT / ("browser-win" if os.name == "nt" else "browser-linux"),
    )
    args = parser.parse_args()
    environment = os.environ.copy()
    environment["PLAYWRIGHT_BROWSERS_PATH"] = str(args.browser_dir.resolve())
    return subprocess.run(command_for_suite(args.suite), cwd=ROOT, env=environment).returncode


if __name__ == "__main__":
    raise SystemExit(main())
