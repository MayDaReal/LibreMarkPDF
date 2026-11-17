"""Run one non-overlapping LibreMark PDF test suite with a staged browser."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PURE_TESTS = [
    "tests.test_cli.TestConvertCommand",
    "tests.test_cli.TestCliSubprocessContract",
    "tests.test_community",
    "tests.test_i18n",
    "tests.test_packaging",
    "tests.test_quality_foundations",
    "tests.test_core.TestTitleExtraction",
    "tests.test_core.TestHeaderFooterConfig",
    "tests.test_core.TestTemplateBuilding",
    "tests.test_core.TestMarkdownConversion",
]
UI_TESTS = [
    "tests.test_gui",
    "tests.test_ctk_files",
    "tests.test_ctk_foundations",
    "tests.test_ctk_settings",
    "tests.test_ctk_shell",
    "tests.test_i18n",
    "tests.test_desktop_reporting",
]


def default_browser_dir() -> Path:
    """Return the staged browser path selected by the caller or platform."""
    configured = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if configured:
        return Path(configured)
    return ROOT / ("browser-win" if os.name == "nt" else "browser-linux")


def command_for_suite(suite: str, *, coverage: bool = False) -> list[str]:
    """Return the single unittest command for the requested suite."""
    if suite == "pure":
        command = [sys.executable, "-m", "unittest", *PURE_TESTS]
    elif suite == "all":
        command = [
            sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"
        ]
    elif suite == "ui":
        command = [sys.executable, "-m", "unittest", *UI_TESTS, "-v"]
    elif suite == "visual":
        command = [
            sys.executable, "-m", "unittest", "tests.test_visual_regression", "-v"
        ]
    else:
        raise ValueError("Unknown suite: {0}".format(suite))
    if coverage:
        command = [sys.executable, "-m", "coverage", "run", *command[1:]]
    return command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", choices=("pure", "all", "ui", "visual"))
    parser.add_argument(
        "--browser-dir",
        type=Path,
        default=default_browser_dir(),
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="run the selected unittest suite through coverage",
    )
    args = parser.parse_args()
    environment = os.environ.copy()
    environment["PLAYWRIGHT_BROWSERS_PATH"] = str(args.browser_dir.resolve())
    return subprocess.run(
        command_for_suite(args.suite, coverage=args.coverage),
        cwd=ROOT,
        env=environment,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
