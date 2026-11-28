"""Verify that every exact locked distribution is installed."""

import argparse
import importlib.metadata
import json
from pathlib import Path

try:
    from tools.generate_windows_sbom import locked_packages
except ModuleNotFoundError:  # Direct execution places tools/ on sys.path.
    from generate_windows_sbom import locked_packages


def verify(lock_path: Path) -> dict:
    mismatches = []
    packages = locked_packages(lock_path)
    for package in packages:
        try:
            actual = importlib.metadata.version(package["name"])
        except importlib.metadata.PackageNotFoundError:
            actual = None
        if actual != package["version"]:
            mismatches.append({
                "actual": actual,
                "expected": package["version"],
                "name": package["name"],
            })
    return {
        "lock": str(lock_path.resolve()),
        "mismatches": mismatches,
        "packages": len(packages),
        "status": "ok" if not mismatches else "error",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--check-browser", action="store_true")
    args = parser.parse_args()
    result = verify(args.lock)
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "ok":
        return 1
    if args.check_browser:
        from libremark_pdf import core

        identity = core.renderer_identity()
        browser_root = Path(identity["browser_path"])
        expected = {
            f"chromium_headless_shell-{identity['chromium_revision']}",
            f"ffmpeg-{identity['ffmpeg_revision']}",
        }
        actual = {
            path.name for path in browser_root.iterdir()
            if path.is_dir() and path.name.startswith(("chromium", "ffmpeg-"))
        } if browser_root.is_dir() else set()
        if actual != expected or not identity["browser_executables"]:
            parser.exit(1, f"Exact Chromium and FFmpeg payloads required in {browser_root}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
