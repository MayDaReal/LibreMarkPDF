"""Non-production G1 probe for offline browser controls and fingerprints."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Dict[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def render_profile() -> Dict[str, Any]:
    style = (ROOT / "style.css").read_bytes()
    icon = (ROOT / "icons" / "icons_check.png").read_bytes()
    return {
        "schema": 1,
        "paper": "A4",
        "locale": "en-US",
        "timezone": "UTC",
        "date": "2026-01-15",
        "java_script_enabled": False,
        "service_workers": "block",
        "network": "deny",
        "assets": [
            {"path": "icons/icons_check.png", "bytes": len(icon), "sha256": sha256(icon)},
            {"path": "style.css", "bytes": len(style), "sha256": sha256(style)},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Write JSON evidence here.")
    args = parser.parse_args()

    from playwright.sync_api import Route, sync_playwright

    profile = render_profile()
    profile_bytes = canonical_json(profile)
    icon = (ROOT / "icons" / "icons_check.png").read_bytes()
    icon_uri = "data:image/png;base64," + base64.b64encode(icon).decode("ascii")
    untrusted = '<script>globalThis.probeExecuted=true</script><img src="{}">'.format(
        icon_uri
    )
    safe_body = '<h1>Safe fixture</h1><img src="{}"><pre>{}</pre>'.format(
        icon_uri, html.escape(untrusted)
    )
    document = "<!doctype html><meta charset=utf-8><body>{}</body>".format(safe_body)
    attempted: List[str] = []
    responses: List[str] = []

    with sync_playwright() as playwright:
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
        page.set_content(document, wait_until="load")
        local_image_width = page.locator("img").evaluate("element => element.naturalWidth")
        script_executed = page.evaluate("Boolean(globalThis.probeExecuted)")

        hostile = context.new_page()
        hostile.set_content(
            '<img src="https://example.invalid/blocked.png">',
            wait_until="load",
        )
        hostile_image_width = hostile.locator("img").evaluate(
            "element => element.naturalWidth"
        )

        result = {
            "browser_version": browser.version,
            "profile": profile,
            "profile_fingerprint": sha256(
                b"libremark-render-profile-v1\0" + profile_bytes
            ),
            "html_fingerprint": sha256(
                b"libremark-html-v1\0" + document.encode("utf-8")
            ),
            "local_fixture": {
                "external_attempts": 0,
                "external_responses": len(responses),
                "embedded_image_natural_width": local_image_width,
                "script_executed": script_executed,
            },
            "hostile_fixture": {
                "blocked_attempts": attempted,
                "external_responses": len(responses),
                "remote_image_natural_width": hostile_image_width,
            },
        }
        context.close()
        browser.close()

    output = Path(args.output)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if script_executed or responses or local_image_width <= 0 or hostile_image_width != 0:
        return 1
    if attempted != ["https://example.invalid/blocked.png"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
