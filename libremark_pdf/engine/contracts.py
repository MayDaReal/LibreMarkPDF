"""Shared engine contracts with no adapter dependencies."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any, Callable, Optional

import markdown as md_lib
import playwright

PROFILE_SCHEMA = 1
DEFAULT_PROFILE_VERSION = "default@1"
DEFAULT_THEME_ID = "default@1"
PLAYWRIGHT_VERSION = version("playwright")
_BROWSER_MANIFEST = Path(playwright.__file__).parent / "driver" / "package" / "browsers.json"
_BROWSERS = {
    entry["name"]: entry
    for entry in json.loads(_BROWSER_MANIFEST.read_text(encoding="utf-8"))["browsers"]
}
CHROMIUM_VERSION = _BROWSERS["chromium-headless-shell"]["browserVersion"]
CHROMIUM_REVISION = _BROWSERS["chromium-headless-shell"]["revision"]
FFMPEG_REVISION = _BROWSERS["ffmpeg"]["revision"]
MARKDOWN_EXTENSIONS = ("extra", "sane_lists")
MAX_RESOURCE_BYTES = 5 * 1024 * 1024
MAX_RESOURCE_COUNT = 32
MAX_TOTAL_RESOURCE_BYTES = 20 * 1024 * 1024
MAX_MARKDOWN_BYTES = 10 * 1024 * 1024
RENDER_TIMEOUT_MS = 30_000

MARGIN_NO_HEADER_FOOTER = {
    "top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm",
}
MARGIN_WITH_HEADER_FOOTER = {
    "top": "22mm", "bottom": "20mm", "left": "16mm", "right": "16mm",
}

_resource_hashes: Optional[Callable[[Optional[str]], dict]] = None


def configure_resource_hashes(provider: Callable[[Optional[str]], dict]) -> None:
    """Bind the resource-domain hash provider after its resources initialize."""
    global _resource_hashes
    _resource_hashes = provider


class ConversionError(Exception):
    """Conversion failure with an actionable message safe for front ends."""


@dataclass(frozen=True)
class RenderProfile:
    """Versioned, canonical rendering inputs used by the shared core."""

    render_date: str
    raw_html_policy: str = "safe"
    network_policy: str = "deny-all"
    profile_version: str = DEFAULT_PROFILE_VERSION
    theme_name: str = DEFAULT_THEME_ID
    theme_hash: Optional[str] = None
    header_footer: tuple = ()

    def canonical_json(self) -> str:
        if _resource_hashes is None:
            raise RuntimeError("renderer resource hashes are not configured")
        payload = {
            "chrome_revision": CHROMIUM_REVISION,
            "color_scheme": "light",
            "locale": "en-US",
            "markdown_extensions": list(MARKDOWN_EXTENSIONS),
            "markdown_version": md_lib.__version__,
            "margins": {"header_footer": MARGIN_WITH_HEADER_FOOTER,
                        "none": MARGIN_NO_HEADER_FOOTER},
            "network_policy": self.network_policy,
            "page": {"background": True, "format": "A4", "media": "print", "scale": 1},
            "playwright_version": PLAYWRIGHT_VERSION,
            "profile_schema": PROFILE_SCHEMA,
            "profile_version": self.profile_version,
            "raw_html_policy": self.raw_html_policy,
            "renderer_flags": ["--disable-font-subpixel-positioning"],
            "header_footer": list(self.header_footer),
            "resource_hashes": _resource_hashes(self.theme_hash),
            "resource_limits": {
                "count": MAX_RESOURCE_COUNT,
                "bytes_per_resource": MAX_RESOURCE_BYTES,
                "markdown_bytes": MAX_MARKDOWN_BYTES,
                "total_bytes": MAX_TOTAL_RESOURCE_BYTES,
            },
            "render_date": self.render_date,
            "timeouts_ms": {"render": RENDER_TIMEOUT_MS},
            "theme": {"name": self.theme_name, "version": self.theme_hash},
            "timezone": "UTC",
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass
class HeaderFooterConfig:
    """Text templates for the three header and three footer positions."""

    top_left: str = ""
    top_center: str = ""
    top_right: str = ""
    bottom_left: str = ""
    bottom_center: str = "Page {page} / {total}"
    bottom_right: str = ""

    def is_empty(self) -> bool:
        return not any((self.top_left, self.top_center, self.top_right,
                        self.bottom_left, self.bottom_center, self.bottom_right))

    @classmethod
    def none(cls) -> "HeaderFooterConfig":
        """Return a configuration that disables headers and footers."""
        return cls("", "", "", "", "", "")


@dataclass(frozen=True)
class ThemeInfo:
    """Validated local theme metadata returned by the shared core API."""

    identifier: str
    version: str
    names: dict
    css_path: Path
    css_sha256: str
    licenses: tuple
    render_profiles: tuple
    source: str
    preview_markdown: Optional[Path] = None
    preview_image: Optional[Path] = None

    @property
    def reference(self) -> str:
        return "{0}@{1}".format(self.identifier, self.version)

    def as_dict(self) -> dict:
        return {"css_sha256": self.css_sha256, "id": self.identifier,
                "licenses": [str(path) for path in self.licenses],
                "name": dict(self.names),
                "preview_image": str(self.preview_image) if self.preview_image is not None else None,
                "preview_markdown": str(self.preview_markdown) if self.preview_markdown is not None else None,
                "reference": self.reference, "render_profiles": list(self.render_profiles),
                "source": self.source, "version": self.version}


@dataclass(frozen=True)
class RenderDocument:
    """Fully resolved deterministic document passed to the locked renderer."""

    full_html: str
    profile: RenderProfile
    render_date: str
    title: str = "Document"


@dataclass(frozen=True)
class BatchPlan:
    """One preflighted batch destination exposed to interactive adapters."""

    input_path: Path
    output_path: Path
    error: Optional[str] = None

    @property
    def error_code(self) -> Optional[str]:
        if not self.error:
            return None
        match = re.match(r"^([A-Z][A-Z0-9_]+):", self.error)
        return match.group(1) if match else "INTERNAL_ERROR"
