"""Generate the localized artifact manuals through LibreMark PDF's CLI."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from libremark_pdf import cli


MARKER = ".libremark-manual-staging"
MANUALS = ("MANUAL_EN", "MANUEL_FR")
RENDER_DATE = "2000-01-01"


def _prepare_output(output_dir: Path) -> None:
    if output_dir.exists():
        if not (output_dir / MARKER).is_file():
            raise RuntimeError(
                "Refusing to replace a directory not owned by manual staging: {0}".format(
                    output_dir
                )
            )
        shutil.rmtree(str(output_dir))
    output_dir.mkdir(parents=True)
    (output_dir / MARKER).write_text("generated; do not package\n", encoding="utf-8")


def stage_manuals(output_dir: Path, root: Path = ROOT) -> tuple[Path, Path]:
    """Recreate and verify the two PDFs consumed by the native build."""
    output_dir = output_dir.resolve()
    _prepare_output(output_dir)
    sources = tuple(root / "docs" / (name + ".md") for name in MANUALS)
    css_path = root / "style.css"
    arguments = [
        "convert",
        *(str(path) for path in sources),
        "--out-dir",
        str(output_dir),
        "--css",
        str(css_path),
        "--date",
        RENDER_DATE,
        "--json",
    ]
    if cli.main(arguments) != 0:
        raise RuntimeError("Localized manual PDF generation failed.")
    outputs = tuple(output_dir / (name + ".pdf") for name in MANUALS)
    missing = [
        path.name
        for path in outputs
        if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise RuntimeError(
            "Localized manual generation did not produce: {0}".format(
                ", ".join(missing)
            )
        )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        outputs = stage_manuals(args.output_dir)
    except Exception as exc:
        parser.exit(1, "ERROR {0}\n".format(exc))
    for output in outputs:
        print("Staged manual: {0}".format(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
