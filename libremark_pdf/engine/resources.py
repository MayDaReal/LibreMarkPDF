"""Frozen local resource resolution and validation for the rendering engine."""

from __future__ import annotations

import base64
import hashlib
import html as html_lib
import os
import re
import sys
from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote, urlparse

from .contracts import (
    CHROMIUM_REVISION,
    CHROMIUM_VERSION,
    ConversionError,
    DEFAULT_PROFILE_VERSION,
    MAX_RESOURCE_BYTES,
    MAX_RESOURCE_COUNT,
    MAX_TOTAL_RESOURCE_BYTES,
    PLAYWRIGHT_VERSION,
)

_PathInput = Union[str, os.PathLike]
_ALLOWED_RESOURCE_MIME = {
    ".gif": "image/gif", ".jpeg": "image/jpeg", ".jpg": "image/jpeg",
    ".png": "image/png", ".svg": "image/svg+xml",
}
_EMOJI_FILES = {
    "\u2705": "icons_check.png",
    "\u26A0\uFE0F": "icons_warning.png",
    "\u26A0": "icons_warning.png",
    "\U0001F7E0": "icons_orange.png",
    "\U0001F501": "icons_repeat.png",
    "\u26D4": "icons_no_entry.png",
}
_FONT_FILES = (
    ("NotoSans-Regular.ttf", "G1 Noto Sans", "400"),
    ("NotoSans-SemiBold.ttf", "G1 Noto Sans", "600"),
    ("NotoSansMono-Regular.ttf", "G1 Noto Sans Mono", "400"),
    ("NotoSansArabic-Regular.ttf", "G1 Noto Sans Arabic", "400"),
    ("NotoSansCJKsc-Regular.otf", "G1 Noto Sans CJK SC", "400"),
    ("NotoSansSymbols2-Regular.ttf", "G1 Noto Sans Symbols 2", "400"),
    ("NotoEmoji.ttf", "G1 Noto Emoji", "400"),
)

_default_css_path = None  # type: Optional[Path]
_icons_dir = None  # type: Optional[Path]
_fonts_dir = None  # type: Optional[Path]
_browsers_dir = None  # type: Optional[Path]
_icon_cache = {}  # type: dict[str, str]
_font_css_cache = None  # type: Optional[str]
_preview_font_css_cache = {}  # type: dict


def resource_path(relative: str, module_file: str) -> Path:
    """Resolve a frozen runtime resource from source, wheel, or PyInstaller."""
    frozen_base = getattr(sys, "_MEIPASS", None)
    if frozen_base:
        return Path(frozen_base) / relative

    source_base = Path(module_file).resolve().parent.parent
    source_candidate = source_base / relative
    if source_candidate.exists():
        return source_candidate

    wheel_candidate = Path(sys.prefix) / "libremark_pdf" / relative
    if wheel_candidate.exists():
        return wheel_candidate
    return source_candidate


def configure_resource_locations(
    default_css_path: Path, icons_dir: Path, fonts_dir: Path, browsers_dir: Path
) -> None:
    """Bind the façade-resolved immutable runtime resource locations."""
    global _default_css_path, _icons_dir, _fonts_dir, _browsers_dir
    _default_css_path = default_css_path
    _icons_dir = icons_dir
    _fonts_dir = fonts_dir
    _browsers_dir = browsers_dir


def _configured() -> None:
    if any(value is None for value in (
        _default_css_path, _icons_dir, _fonts_dir, _browsers_dir,
    )):
        raise RuntimeError("resource locations are not configured")


def prefer_bundled_browser() -> None:
    """Prefer the frozen browser at the same import-time boundary as before."""
    _configured()
    if _browsers_dir.exists():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(_browsers_dir))


def renderer_identity() -> dict:
    """Return pinned renderer identities without starting or installing it."""
    _configured()
    executable_names = {"chrome-headless-shell", "chrome-headless-shell.exe"}
    browser_executables = []
    if _browsers_dir.is_dir():
        browser_executables = sorted(
            str(path)
            for path in _browsers_dir.rglob("*")
            if path.is_file() and path.name in executable_names
        )
    return {
        "chromium_revision": CHROMIUM_REVISION,
        "chromium_version": CHROMIUM_VERSION,
        "playwright_version": PLAYWRIGHT_VERSION,
        "render_profile": DEFAULT_PROFILE_VERSION,
        "browser_path": str(_browsers_dir),
        "browser_executables": browser_executables,
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _renderer_resource_hashes(theme_hash: Optional[str] = None) -> dict:
    """Return stable hashes of every local resource that changes rendering."""
    _configured()
    icon_hashes = {}
    if _icons_dir.is_dir():
        for path in sorted(_icons_dir.glob("*.png")):
            icon_hashes[path.name] = _sha256_file(path)
    font_hashes = {}
    for filename, _family, _weight in _FONT_FILES:
        path = _fonts_dir / filename
        font_hashes[filename] = _sha256_file(path) if path.is_file() else "missing"
    return {
        "css": theme_hash or _sha256_file(_default_css_path),
        "fonts": font_hashes,
        "icons": icon_hashes,
    }


def _icon_data_uri(filename: str) -> str:
    _configured()
    if filename not in _icon_cache:
        data = (_icons_dir / filename).read_bytes()
        _icon_cache[filename] = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    return _icon_cache[filename]


def _font_face_css() -> str:
    """Embed the seven exact static G1 font files in renderer input."""
    global _font_css_cache
    _configured()
    if _font_css_cache is None:
        rules = []
        for filename, family, weight in _FONT_FILES:
            path = _fonts_dir / filename
            if not path.is_file():
                raise ConversionError("FONT_NOT_FOUND: bundled font is missing: " + filename)
            mime = "font/otf" if path.suffix == ".otf" else "font/ttf"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            rules.append(
                "@font-face{font-family:'%s';src:url(data:%s;base64,%s);"
                "font-style:normal;font-weight:%s;font-display:block;}"
                % (family, mime, encoded, weight)
            )
        _font_css_cache = "\n".join(rules)
    return _font_css_cache


def _preview_template_font_css(text: str) -> str:
    """Embed only font families that can be selected by preview templates."""
    _configured()
    families = {"G1 Noto Sans"}
    if re.search(
        r"[\u0600-\u06ff\u0750-\u077f\u0870-\u089f"
        r"\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]", text,
    ):
        families.add("G1 Noto Sans Arabic")
    if re.search(
        r"[\u2e80-\u2fff\u3040-\u30ff\u31f0-\u31ff"
        r"\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]", text,
    ):
        families.add("G1 Noto Sans CJK SC")
    key = tuple(sorted(families))
    cached = _preview_font_css_cache.get(key)
    if cached is not None:
        return cached
    rules = []
    for filename, family, weight in _FONT_FILES:
        if family not in families or weight != "400":
            continue
        path = _fonts_dir / filename
        if not path.is_file():
            raise ConversionError("FONT_NOT_FOUND: bundled font is missing: " + filename)
        mime = "font/otf" if path.suffix == ".otf" else "font/ttf"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            "@font-face{font-family:'%s';src:url(data:%s;base64,%s);"
            "font-style:normal;font-weight:%s;font-display:block;}"
            % (family, mime, encoded, weight)
        )
    css = "\n".join(rules)
    _preview_font_css_cache[key] = css
    return css


def substitute_emoji_icons(html: str) -> str:
    """Replace supported status emoji with embedded PNG images."""
    for ch, filename in _EMOJI_FILES.items():
        if ch in html:
            uri = _icon_data_uri(filename)
            parts = re.split(r"(<[^>]+>)", html)
            protected_depth = 0
            out = []
            for part in parts:
                if part.startswith("<"):
                    if re.match(r"<\s*/\s*(code|pre)\b", part, re.I):
                        protected_depth = max(0, protected_depth - 1)
                    out.append(part)
                    if re.match(r"<\s*(code|pre)\b[^>]*>", part, re.I):
                        protected_depth += 1
                elif protected_depth:
                    out.append(part)
                else:
                    out.append(part.replace(ch, '<img class="emoji" src="{0}" alt="">'.format(uri)))
            html = "".join(out)
    return html


def _resource_error(message: str) -> ConversionError:
    return ConversionError("FORBIDDEN_RESOURCE: " + message)


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def _validate_image_bytes(data: bytes, suffix: str) -> None:
    """Validate bytes against the narrow image types accepted by safe mode."""
    if not data or len(data) > MAX_RESOURCE_BYTES:
        raise _resource_error("image is empty or exceeds configured size limit")
    if suffix == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise _resource_error("PNG signature does not match its extension")
    if suffix in (".jpg", ".jpeg") and not data.startswith(b"\xff\xd8\xff"):
        raise _resource_error("JPEG signature does not match its extension")
    if suffix == ".gif" and not data.startswith((b"GIF87a", b"GIF89a")):
        raise _resource_error("GIF signature does not match its extension")
    if suffix == ".svg":
        if not re.search(rb"(?is)<\s*svg\b", data):
            raise _resource_error("SVG signature does not match its extension")
        if re.search(
            rb"(?is)<\s*(script|iframe|object|embed|foreignObject)\b|\bon\w+\s*=|"
            rb"\b(?:href|src|xlink:href)\s*=\s*['\"]?\s*(?:https?:|//|file:)|"
            rb"@import|url\s*\(", data,
        ):
            raise _resource_error("SVG contains active or network-capable content")


def _validated_image_data_uri(value: str, resource_root: Path) -> tuple:
    """Validate an image and return a renderer-safe data URI."""
    if value.startswith("data:"):
        match = re.match(r"^data:([^;,]+);base64,([A-Za-z0-9+/=]+)$", value, re.I)
        if not match or match.group(1).lower() not in _ALLOWED_RESOURCE_MIME.values():
            raise _resource_error("unsupported or malformed data URI")
        try:
            data = base64.b64decode(match.group(2), validate=True)
        except ValueError as exc:
            raise _resource_error("malformed data URI") from exc
        suffix = next(suffix for suffix, mime in _ALLOWED_RESOURCE_MIME.items()
                      if mime == match.group(1).lower())
        _validate_image_bytes(data, suffix)
        return value, len(data)

    parsed = urlparse(value)
    if parsed.scheme or value.startswith("//") or parsed.query or parsed.fragment:
        raise _resource_error("only relative local image paths are allowed")
    candidate = (resource_root / unquote(value)).resolve()
    if not _is_within(candidate, resource_root) or not candidate.is_file():
        raise _resource_error("image is missing or escapes the source directory")
    suffix = candidate.suffix.lower()
    mime = _ALLOWED_RESOURCE_MIME.get(suffix)
    if mime is None:
        raise _resource_error("unsupported image type")
    data = candidate.read_bytes()
    _validate_image_bytes(data, suffix)
    return "data:{0};base64,{1}".format(mime, base64.b64encode(data).decode("ascii")), len(data)


def embed_local_resources(html: str, resource_root: _PathInput) -> str:
    """Embed approved local image references before Chromium receives HTML."""
    root = Path(resource_root).resolve()
    if not root.is_dir():
        raise _resource_error("source directory is unavailable")
    count = 0
    total_bytes = 0

    def replace(match: re.Match) -> str:
        nonlocal count, total_bytes
        count += 1
        if count > MAX_RESOURCE_COUNT:
            raise _resource_error("image count exceeds configured limit")
        quote, value = match.group(1), html_lib.unescape(match.group(2))
        uri, resource_bytes = _validated_image_data_uri(value, root)
        total_bytes += resource_bytes
        if total_bytes > MAX_TOTAL_RESOURCE_BYTES:
            raise _resource_error("total image size exceeds configured limit")
        return "src={0}{1}{0}".format(quote, uri)

    return re.sub(r"\bsrc\s*=\s*(['\"])(.*?)\1", replace, html, flags=re.I | re.S)


def _css_has_forbidden_resources(css: str) -> bool:
    """CSS URLs would bypass the image embedding boundary, so reject them."""
    return bool(re.search(r"(?is)@import\b|url\s*\(", css))
