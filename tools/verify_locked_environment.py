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
    args = parser.parse_args()
    result = verify(args.lock)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
