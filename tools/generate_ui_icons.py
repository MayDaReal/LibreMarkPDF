"""Generate deterministic local PNG variants from approved Bootstrap SVGs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from libremark_pdf.desktop.ctk.assets import ICON_NAMES, ICON_SIZES
from libremark_pdf.desktop.ctk.theme import ICON_COLORS


DEFAULT_ASSET_ROOT = ROOT / "assets" / "ui-icons"
ORIGIN = {
    "archive": "bootstrap-icons-1.11.1.zip",
    "archive_sha256": (
        "821d76089e8568f89e695cb821000abb9a63d486008794995acc21b1c66f39fc"
    ),
    "project": "Bootstrap Icons",
    "source": "https://github.com/twbs/icons/releases/tag/v1.11.1",
    "version": "1.11.1",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(asset_root: Path) -> dict:
    """Rasterize all prescribed sizes and semantic color variants."""
    svg_root = asset_root / "svg"
    png_root = asset_root / "png"
    png_root.mkdir(parents=True, exist_ok=True)
    files = {}
    sources = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for name in ICON_NAMES:
                source = svg_root / "{0}.svg".format(name)
                svg = source.read_text(encoding="utf-8")
                sources[name] = {
                    "path": source.relative_to(asset_root).as_posix(),
                    "sha256": _sha256(source),
                }
                for size in ICON_SIZES:
                    for color_name, color_value in ICON_COLORS.items():
                        page = browser.new_page(
                            viewport={"width": size + 8, "height": size + 8},
                            device_scale_factor=4,
                        )
                        try:
                            page.set_content(
                                "<style>html,body{{margin:0;background:transparent;"
                                "color:{0}}}svg{{display:block;width:{1}px;"
                                "height:{1}px}}</style>{2}".format(
                                    color_value,
                                    size,
                                    svg,
                                )
                            )
                            raw = page.locator("svg").screenshot(
                                omit_background=True
                            )
                        finally:
                            page.close()
                        image = Image.open(BytesIO(raw)).convert("RGBA")
                        image = image.resize(
                            (size, size),
                            Image.Resampling.LANCZOS,
                        )
                        filename = "{0}-{1}-{2}.png".format(
                            name,
                            size,
                            color_name,
                        )
                        output = png_root / filename
                        image.save(output, format="PNG", optimize=True)
                        files["{0}:{1}:{2}".format(
                            name, size, color_name
                        )] = {
                            "path": output.relative_to(asset_root).as_posix(),
                            "sha256": _sha256(output),
                        }
        finally:
            browser.close()
    license_path = ROOT / "licenses" / "Bootstrap-Icons-LICENSE.txt"
    origin = dict(ORIGIN)
    origin["license"] = {
        "path": license_path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(license_path),
        "spdx": "MIT",
    }
    manifest = {
        "schema": 1,
        "origin": origin,
        "icons": list(ICON_NAMES),
        "sizes": list(ICON_SIZES),
        "colors": ICON_COLORS,
        "sources": sources,
        "files": files,
    }
    (asset_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, default=DEFAULT_ASSET_ROOT)
    args = parser.parse_args()
    manifest = generate(args.asset_root.resolve())
    print(
        "Generated {0} PNG files from {1} Bootstrap Icons.".format(
            len(manifest["files"]),
            len(manifest["icons"]),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
