"""Generate application logo assets from the canonical vector master."""

from __future__ import annotations

import hashlib
from importlib import metadata
from pathlib import Path

import cairosvg
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent / "sources" / "libremark-pdf-logo.svg"
ASSETS_DIR = ROOT / "assets"
PNG_SIZES = (16, 32, 48, 64, 128, 256)
EXPECTED_TOOLS = {"CairoSVG": "2.9.1", "Pillow": "13.0.0"}


def _verify_tools() -> None:
    for package, expected in EXPECTED_TOOLS.items():
        actual = metadata.version(package)
        if actual != expected:
            raise RuntimeError(
                f"Expected {package} {expected}, found {actual}. "
                "Install tools/svg-asset-forge/requirements.txt exactly."
            )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    _verify_tools()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    for size in PNG_SIZES:
        output = ASSETS_DIR / f"libremark-pdf-logo-{size}.png"
        temporary = output.with_suffix(".tmp.png")
        try:
            cairosvg.svg2png(
                url=str(SOURCE),
                write_to=str(temporary),
                output_width=size,
                output_height=size,
            )
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        generated.append(output)

    ico_output = ASSETS_DIR / "libremark-pdf.ico"
    ico_temporary = ico_output.with_suffix(".tmp.ico")
    try:
        with Image.open(generated[-1]) as source_image:
            source_image.convert("RGBA").save(
                ico_temporary,
                format="ICO",
                sizes=[(size, size) for size in PNG_SIZES],
            )
        ico_temporary.replace(ico_output)
    finally:
        ico_temporary.unlink(missing_ok=True)
    generated.append(ico_output)

    print(f"source  {SOURCE.relative_to(ROOT)}  {_sha256(SOURCE)}")
    for path in generated:
        print(f"output  {path.relative_to(ROOT)}  {_sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
