"""Inventory ELF dependencies and glibc requirements for a Linux candidate."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


GLIBC_RE = re.compile(r"\bGLIBC_(\d+(?:\.\d+)*)\b")


def _version_key(value):
    return tuple(int(part) for part in value.split("."))


def inspect(artifact_dir: Path) -> dict:
    if shutil.which("ldd") is None or shutil.which("readelf") is None:
        raise RuntimeError("ldd and readelf are required for Linux inspection")
    elf_files = []
    missing = []
    glibc_versions = set()
    for path in sorted(item for item in artifact_dir.rglob("*") if item.is_file()):
        with path.open("rb") as stream:
            if stream.read(4) != b"\x7fELF":
                continue
        relative = path.relative_to(artifact_dir).as_posix()
        ldd = subprocess.run(
            ["ldd", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        dependency_text = (ldd.stdout + ldd.stderr).strip()
        unresolved = sorted(set(
            line.strip() for line in dependency_text.splitlines()
            if "not found" in line
        ))
        missing.extend("{0}: {1}".format(relative, line) for line in unresolved)
        readelf = subprocess.run(
            ["readelf", "--version-info", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        glibc_versions.update(GLIBC_RE.findall(readelf.stdout))
        elf_files.append({
            "ldd_exit": ldd.returncode,
            "path": relative,
            "unresolved": unresolved,
        })
    browser_sandboxes = sorted(
        path.relative_to(artifact_dir).as_posix()
        for path in artifact_dir.rglob("chrome-sandbox")
        if path.is_file()
    )
    return {
        "artifact": str(artifact_dir.resolve()),
        "browser_sandbox_helpers": browser_sandboxes,
        "elf_files": elf_files,
        "glibc_versions": sorted(glibc_versions, key=_version_key),
        "maximum_glibc_symbol": (
            max(glibc_versions, key=_version_key) if glibc_versions else None
        ),
        "unresolved_libraries": sorted(missing),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.artifact_dir.is_dir():
        parser.error("artifact directory is unavailable")
    result = inspect(args.artifact_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "elf_files": len(result["elf_files"]),
        "maximum_glibc_symbol": result["maximum_glibc_symbol"],
        "output": str(args.output),
        "unresolved_libraries": len(result["unresolved_libraries"]),
    }, sort_keys=True))
    return 0 if not result["unresolved_libraries"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
