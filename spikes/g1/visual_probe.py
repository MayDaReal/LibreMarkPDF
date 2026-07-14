"""Render non-production G1 visual evidence with current or candidate fonts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from libremark_pdf import core  # noqa: E402
from spikes.g1.fetch_font_candidates import load_manifest, sha256_file  # noqa: E402


HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "visual-representative.md"
FONT_MANIFEST = HERE / "font_candidates_static.json"
TEST_DATE = "2026-01-15"
LEGACY_FONT_CSS = {
    "NotoSans.ttf": ("G1 Noto Sans", "100 900"),
    "NotoSansMono.ttf": ("G1 Noto Sans Mono", "100 900"),
    "NotoSansArabic.ttf": ("G1 Noto Sans Arabic", "100 900"),
    "NotoSansCJKsc-Regular.otf": ("G1 Noto Sans CJK SC", "400"),
    "NotoSansSymbols2-Regular.ttf": ("G1 Noto Sans Symbols 2", "400"),
    "NotoEmoji.ttf": ("G1 Noto Emoji", "100 900"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def data_uri(path: Path) -> str:
    mime = "font/otf" if path.suffix.lower() == ".otf" else "font/ttf"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return "data:{};base64,{}".format(mime, encoded)


def font_face(item: Dict[str, Any]) -> tuple:
    if "css_family" in item and "css_weight" in item:
        return item["css_family"], item["css_weight"]
    return LEGACY_FONT_CSS[item["filename"]]


def candidate_font_css(manifest: Dict[str, Any], font_dir: Path) -> str:
    rules = []
    for item in manifest["files"]:
        family, weight = font_face(item)
        path = font_dir / item["filename"]
        rules.append(
            "@font-face {{font-family:'{}';src:url('{}');font-style:normal;"
            "font-weight:{};font-display:block;}}".format(
                family, data_uri(path), weight
            )
        )
    rules.append(
        ".markdown-body{font-family:'G1 Noto Sans','G1 Noto Sans Arabic',"
        "'G1 Noto Sans CJK SC','G1 Noto Emoji','G1 Noto Sans Symbols 2',"
        "sans-serif;}"
    )
    rules.append(
        ".markdown-body code,.markdown-body pre{font-family:'G1 Noto Sans Mono',"
        "monospace;}"
    )
    return "\n".join(rules)


def footer_template(
    profile: str, manifest: Dict[str, Any], font_dir: Optional[Path]
) -> str:
    template = core.build_footer_template(core.HeaderFooterConfig())
    if profile == "current":
        return template
    if font_dir is None:
        raise ValueError("Candidate profile requires a font directory")
    proportional = [
        item for item in manifest["files"] if font_face(item)[0] == "G1 Noto Sans"
    ]
    font_rule = "<style>{}</style>".format(
        "".join(
            "@font-face{{font-family:'G1 Noto Sans';src:url('{}');font-style:normal;"
            "font-weight:{};font-display:block;}}".format(
                data_uri(font_dir / item["filename"]), font_face(item)[1]
            )
            for item in proportional
        )
    )
    return font_rule + template.replace(
        "font-family: Helvetica, Arial, sans-serif;",
        "font-family: 'G1 Noto Sans', sans-serif;",
    )


def output_is_outside_repository(output_dir: Path) -> bool:
    resolved = output_dir.resolve()
    return resolved != ROOT and ROOT not in resolved.parents


def rasterize_pdf(pdf_path: Path, output_dir: Path) -> List[Dict[str, Any]]:
    import pypdfium2 as pdfium

    records = []
    document = pdfium.PdfDocument(str(pdf_path))
    try:
        for index in range(len(document)):
            page = document[index]
            width_points, height_points = page.get_size()
            text_page = page.get_textpage()
            try:
                extracted = text_page.get_text_range()
            finally:
                text_page.close()
            bitmap = page.render(scale=2.0)
            image = bitmap.to_pil().convert("RGB")
            image_path = output_dir / "page-{:03d}.png".format(index + 1)
            image.save(image_path, format="PNG", optimize=False)
            records.append(
                {
                    "height_points": height_points,
                    "image": image_path.name,
                    "image_bytes": image_path.stat().st_size,
                    "image_pixels": list(image.size),
                    "image_sha256": sha256_file(image_path),
                    "page": index + 1,
                    "text_characters": len(extracted),
                    "text_sha256": sha256_bytes(extracted.encode("utf-8")),
                    "width_points": width_points,
                }
            )
    finally:
        document.close()
    return records


def package_version(name: str) -> str:
    return importlib.metadata.version(name)


def browser_executable(default_path: Path) -> Path:
    if default_path.is_file():
        return default_path
    browser_root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""))
    if browser_root.is_dir():
        names = ("chrome-headless-shell.exe", "chrome-headless-shell")
        candidates = sorted(
            path
            for name in names
            for path in browser_root.rglob(name)
            if path.is_file()
        )
        if len(candidates) == 1:
            return candidates[0]
    raise ValueError("Could not identify the installed Chromium executable")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("current", "candidate"), required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--font-manifest", default=FONT_MANIFEST, type=Path)
    parser.add_argument(
        "--font-root",
        type=Path,
        help="Directory produced by fetch_font_candidates.py.",
    )
    args = parser.parse_args()

    if not output_is_outside_repository(args.output_dir):
        parser.error("Generated visual evidence must be written outside the repository")
    if args.profile == "candidate" and args.font_root is None:
        parser.error("--font-root is required for the candidate profile")

    manifest_path = args.font_manifest.resolve()
    manifest = load_manifest(manifest_path)
    font_dir = args.font_root / "fonts" if args.font_root else None
    if font_dir is not None:
        for item in manifest["files"]:
            path = font_dir / item["filename"]
            if not path.is_file() or sha256_file(path) != item["sha256"]:
                parser.error("Font verification failed: {}".format(path))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    markdown_text = FIXTURE.read_text(encoding="utf-8")
    body_html = core.markdown_to_html(markdown_text)
    title = core.extract_title(body_html)
    css = core.DEFAULT_CSS_PATH.read_text(encoding="utf-8")
    if args.profile == "candidate" and font_dir is not None:
        css += "\n" + candidate_font_css(manifest, font_dir)
    full_html = core.build_full_html(body_html, title, css)
    html_fingerprint = sha256_bytes(
        b"libremark-g1-visual-html-v1\0" + full_html.encode("utf-8")
    )

    from playwright.sync_api import Route, sync_playwright

    attempted: List[str] = []
    responses: List[str] = []
    pdf_path = args.output_dir / "visual-{}.pdf".format(args.profile)
    with sync_playwright() as playwright:
        browser_path = browser_executable(Path(playwright.chromium.executable_path))
        browser = playwright.chromium.launch()
        context = browser.new_context(
            java_script_enabled=False,
            locale="en-US",
            timezone_id="UTC",
            service_workers="block",
        )

        def deny(route: Route) -> None:
            attempted.append(route.request.url)
            route.abort()

        context.route("http://**/*", deny)
        context.route("https://**/*", deny)
        page = context.new_page()
        page.on("response", lambda response: responses.append(response.url))
        page.set_content(full_html, wait_until="load")
        page.evaluate("document.fonts.ready")
        font_status = page.evaluate(
            """() => ({
                status: document.fonts.status,
                body: getComputedStyle(document.querySelector('.markdown-body')).fontFamily,
                mono: getComputedStyle(document.querySelector('code')).fontFamily
            })"""
        )
        cdp = context.new_cdp_session(page)
        cdp.send("DOM.enable")
        cdp.send("CSS.enable")
        document_node = cdp.send("DOM.getDocument")
        article_nodes = cdp.send(
            "DOM.querySelectorAll",
            {
                "nodeId": document_node["root"]["nodeId"],
                "selector": ".markdown-body, .markdown-body *",
            },
        )["nodeIds"]
        font_totals: Dict[tuple, Dict[str, Any]] = {}
        for node_id in article_nodes:
            for font in cdp.send(
                "CSS.getPlatformFontsForNode", {"nodeId": node_id}
            )["fonts"]:
                key = (
                    font["familyName"],
                    font["postScriptName"],
                    font["isCustomFont"],
                )
                if key not in font_totals:
                    font_totals[key] = dict(font)
                else:
                    font_totals[key]["glyphCount"] += font["glyphCount"]
        platform_fonts = sorted(
            font_totals.values(),
            key=lambda item: (item["familyName"], item["postScriptName"]),
        )
        page.pdf(
            path=str(pdf_path),
            format="A4",
            margin=core.MARGIN_WITH_HEADER_FOOTER,
            display_header_footer=True,
            header_template=core.build_header_template(core.HeaderFooterConfig()),
            footer_template=footer_template(args.profile, manifest, font_dir),
            print_background=True,
        )
        browser_version = browser.version
        context.close()
        browser.close()

    pages = rasterize_pdf(pdf_path, args.output_dir)
    asset_records = []
    for path in [core.DEFAULT_CSS_PATH, FIXTURE, manifest_path]:
        asset_records.append(
            {
                "bytes": path.stat().st_size,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
        )
    font_records = []
    if font_dir is not None:
        for item in manifest["files"]:
            font_records.append(
                {
                    "bytes": item["bytes"],
                    "family": item["family"],
                    "filename": item["filename"],
                    "role": item["role"],
                    "sha256": item["sha256"],
                }
            )

    profile_data = {
        "date": TEST_DATE,
        "font_manifest_sha256": sha256_file(manifest_path) if font_dir else None,
        "html_fingerprint": html_fingerprint,
        "locale": "en-US",
        "margins": core.MARGIN_WITH_HEADER_FOOTER,
        "network": "deny",
        "paper": "A4",
        "profile": args.profile,
        "raster_dpi": 144,
        "service_workers": "block",
        "timezone": "UTC",
    }
    evidence = {
        "assets": asset_records,
        "browser": {
            "executable_bytes": browser_path.stat().st_size,
            "executable_sha256": sha256_file(browser_path),
            "version": browser_version,
        },
        "environment": {
            "architecture": platform.machine(),
            "os": platform.platform(),
            "pillow": package_version("Pillow"),
            "playwright": package_version("playwright"),
            "pypdfium2": package_version("pypdfium2"),
            "python": platform.python_version(),
        },
        "font_status": font_status,
        "platform_fonts": platform_fonts,
        "fonts": font_records,
        "network": {
            "attempted": attempted,
            "responses": responses,
        },
        "pages": pages,
        "pdf": {
            "bytes": pdf_path.stat().st_size,
            "filename": pdf_path.name,
            "sha256": sha256_file(pdf_path),
        },
        "profile": profile_data,
        "profile_fingerprint": sha256_bytes(
            b"libremark-g1-visual-profile-v1\0"
            + json.dumps(
                profile_data,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ),
        "schema": 1,
    }
    evidence_path = args.output_dir / "evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))

    if attempted or responses or not pages or font_status["status"] != "loaded":
        return 1
    if args.profile == "candidate" and any(
        not item["isCustomFont"] for item in platform_fonts if item["glyphCount"]
    ):
        return 1
    if browser_version != "148.0.7778.96":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
