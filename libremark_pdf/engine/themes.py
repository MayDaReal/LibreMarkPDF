"""Validated local theme registry for the private rendering engine."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Optional, Union

from .contracts import (
    ConversionError,
    DEFAULT_PROFILE_VERSION,
    DEFAULT_THEME_ID,
    MAX_RESOURCE_BYTES,
    MAX_TOTAL_RESOURCE_BYTES,
    ThemeInfo,
)

_PathInput = Union[str, os.PathLike]
THEME_MANIFEST_SCHEMA = 1
THEME_MANIFEST_NAME = "theme.json"
_THEME_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_THEME_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
_THEME_ALLOWED_SUFFIXES = {".css", ".gif", ".jpeg", ".jpg", ".md", ".png", ".svg", ".txt"}

_resource_path = None  # type: Optional[Callable[[str], Path]]
_default_css_path = None  # type: Optional[Path]
_default_theme_root = None  # type: Optional[Path]
_sha256_file = None  # type: Optional[Callable[[Path], str]]
_is_within = None  # type: Optional[Callable[[Path, Path], bool]]
_validate_image_bytes = None  # type: Optional[Callable[[bytes, str], None]]
_css_has_forbidden_resources = None  # type: Optional[Callable[[str], bool]]


def configure_theme_dependencies(
    resource_path: Callable[[str], Path],
    default_css_path: Path,
    default_theme_root: Path,
    sha256_file: Callable[[Path], str],
    is_within: Callable[[Path, Path], bool],
    validate_image_bytes: Callable[[bytes, str], None],
    css_has_forbidden_resources: Callable[[str], bool],
) -> None:
    """Bind resource-domain services without importing the public façade."""
    global _resource_path, _default_css_path, _default_theme_root
    global _sha256_file, _is_within, _validate_image_bytes, _css_has_forbidden_resources
    _resource_path = resource_path
    _default_css_path = default_css_path
    _default_theme_root = default_theme_root
    _sha256_file = sha256_file
    _is_within = is_within
    _validate_image_bytes = validate_image_bytes
    _css_has_forbidden_resources = css_has_forbidden_resources


def _configured() -> None:
    if any(value is None for value in (
        _resource_path,
        _default_css_path,
        _default_theme_root,
        _sha256_file,
        _is_within,
        _validate_image_bytes,
        _css_has_forbidden_resources,
    )):
        raise RuntimeError("theme dependencies are not configured")


def _theme_error(code: str, message: str) -> ConversionError:
    return ConversionError("{0}: {1}".format(code, message))


def _default_theme_info() -> ThemeInfo:
    _configured()
    return ThemeInfo("default", "1", {"en": "Default", "fr": "Par défaut"},
                     _default_css_path, _sha256_file(_default_css_path),
                     (_resource_path("LICENSE"),), (DEFAULT_PROFILE_VERSION,), "bundled")


def _manifest_relative_path(value: Any, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise _theme_error("THEME_INVALID", "{0} must be a relative POSIX path".format(field))
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise _theme_error("THEME_TRAVERSAL", "{0} escapes the theme package".format(field))
    return path


def _theme_file(root: Path, value: Any, field: str) -> Path:
    relative = _manifest_relative_path(value, field)
    path = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise _theme_error("THEME_TRAVERSAL", "{0} uses a symbolic link".format(field))
    if not _is_within(path.resolve(), root.resolve()):
        raise _theme_error("THEME_TRAVERSAL", "{0} escapes the theme package".format(field))
    return path


def validate_theme_package(package_path: _PathInput) -> ThemeInfo:
    """Validate a local theme package without installing or rendering it."""
    _configured()
    root = Path(package_path)
    if not root.is_dir() or root.is_symlink():
        raise _theme_error("THEME_NOT_FOUND", "theme package directory is unavailable")
    manifest_path = root / THEME_MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise _theme_error("THEME_INVALID", "theme.json is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _theme_error("THEME_INVALID", "theme.json must be valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != THEME_MANIFEST_SCHEMA:
        raise _theme_error("THEME_INCOMPATIBLE", "unsupported theme manifest schema")
    identifier, version, names = manifest.get("id"), manifest.get("version"), manifest.get("name")
    profiles, files, licenses = manifest.get("render_profiles"), manifest.get("files"), manifest.get("licenses")
    if not isinstance(identifier, str) or not _THEME_ID_RE.fullmatch(identifier):
        raise _theme_error("THEME_INVALID", "theme id is invalid")
    if identifier == "default":
        raise _theme_error("THEME_DUPLICATE", "the bundled default id is reserved")
    if not isinstance(version, str) or not _THEME_VERSION_RE.fullmatch(version):
        raise _theme_error("THEME_INVALID", "theme version is invalid")
    if (not isinstance(names, dict) or not isinstance(names.get("en"), str)
            or not names["en"].strip() or not isinstance(names.get("fr"), str)
            or not names["fr"].strip()):
        raise _theme_error("THEME_INVALID", "name must contain non-empty en and fr values")
    if (not isinstance(profiles, list) or DEFAULT_PROFILE_VERSION not in profiles
            or any(not isinstance(item, str) for item in profiles)):
        raise _theme_error("THEME_INCOMPATIBLE", "theme does not support render profile " + DEFAULT_PROFILE_VERSION)
    if not isinstance(files, dict) or not files:
        raise _theme_error("THEME_INVALID", "files must contain hashed package files")
    if not isinstance(licenses, list) or not licenses:
        raise _theme_error("THEME_LICENSE_MISSING", "at least one licence file is required")
    expected_files, total_bytes = {}, 0
    for raw_name, digest in files.items():
        path = _theme_file(root, raw_name, "files")
        relative = _manifest_relative_path(raw_name, "files")
        if path.suffix.lower() not in _THEME_ALLOWED_SUFFIXES:
            raise _theme_error("THEME_UNSUPPORTED_FILE", str(relative))
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise _theme_error("THEME_INVALID", "file hashes must be lowercase SHA-256")
        if not path.is_file():
            raise _theme_error("THEME_INVALID", "declared file is missing: " + str(relative))
        size = path.stat().st_size
        total_bytes += size
        if size > MAX_RESOURCE_BYTES or total_bytes > MAX_TOTAL_RESOURCE_BYTES:
            raise _theme_error("THEME_TOO_LARGE", "theme exceeds configured size limits")
        if _sha256_file(path) != digest:
            raise _theme_error("THEME_HASH_MISMATCH", str(relative))
        if path.suffix.lower() in {".gif", ".jpeg", ".jpg", ".png", ".svg"}:
            try:
                _validate_image_bytes(path.read_bytes(), path.suffix.lower())
            except ConversionError as exc:
                raise _theme_error("THEME_FORBIDDEN_CONTENT", "unsafe image asset: " + str(relative)) from exc
        expected_files[str(relative)] = path
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*")
                    if path.is_file() and path != manifest_path}
    if actual_files != set(expected_files):
        raise _theme_error("THEME_UNDECLARED_FILE", "every package file must be hashed")
    css_relative = _manifest_relative_path(manifest.get("css"), "css")
    css_path = expected_files.get(str(css_relative))
    if css_path is None or css_path.suffix.lower() != ".css":
        raise _theme_error("THEME_INVALID", "css must name a declared CSS file")
    try:
        css_text = css_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _theme_error("THEME_INVALID", "theme CSS must be UTF-8") from exc
    if "\x00" in css_text:
        raise _theme_error("THEME_INVALID", "theme CSS contains a null byte")
    if _css_has_forbidden_resources(css_text) or re.search(r"(?is)<\s*script\b|javascript\s*:|https?\s*:|file\s*:", css_text):
        raise _theme_error("THEME_FORBIDDEN_CONTENT", "theme CSS contains script, remote, file, or resource-loader content")
    license_paths = []
    for raw_license in licenses:
        relative = _manifest_relative_path(raw_license, "licenses")
        license_path = expected_files.get(str(relative))
        if license_path is None or license_path.suffix.lower() != ".txt":
            raise _theme_error("THEME_LICENSE_MISSING", str(relative))
        try:
            license_text = license_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise _theme_error("THEME_LICENSE_MISSING", "licence must be non-empty UTF-8 text") from exc
        if not license_text.strip():
            raise _theme_error("THEME_LICENSE_MISSING", str(relative))
        license_paths.append(license_path)
    preview = manifest.get("preview", {})
    if not isinstance(preview, dict):
        raise _theme_error("THEME_INVALID", "preview must be an object")
    def preview_path(role: str, suffixes: set) -> Optional[Path]:
        value = preview.get(role)
        if value is None:
            return None
        relative = _manifest_relative_path(value, "preview." + role)
        path = expected_files.get(str(relative))
        if path is None or path.suffix.lower() not in suffixes:
            raise _theme_error("THEME_INVALID", "invalid preview " + role)
        return path
    preview_markdown = preview_path("markdown", {".md"})
    preview_image = preview_path("image", {".gif", ".jpeg", ".jpg", ".png", ".svg"})
    if preview_markdown is not None:
        try:
            preview_text = preview_markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise _theme_error("THEME_INVALID", "theme preview Markdown must be UTF-8") from exc
        if re.search(r"(?is)<\s*script\b|javascript\s*:|(?:https?|file)\s*:|(?<!:)//", preview_text):
            raise _theme_error("THEME_FORBIDDEN_CONTENT", "theme preview contains script, remote, or file content")
    return ThemeInfo(identifier, version, {"en": names["en"].strip(), "fr": names["fr"].strip()}, css_path,
                     files[str(css_relative)], tuple(license_paths), tuple(profiles), "local", preview_markdown, preview_image)


def _theme_root(theme_root: Optional[_PathInput]) -> Path:
    _configured()
    return Path(theme_root) if theme_root is not None else _default_theme_root


def list_themes(theme_root: Optional[_PathInput] = None) -> list:
    """List the bundled default and every validated installed local theme."""
    root = _theme_root(theme_root)
    themes = [_default_theme_info()]
    if root.is_dir():
        for package in sorted(path for path in root.iterdir() if not path.name.startswith(".")):
            themes.append(validate_theme_package(package))
    return themes


def show_theme(reference: str, theme_root: Optional[_PathInput] = None) -> ThemeInfo:
    """Return one installed theme by id or exact id@version reference."""
    if reference in ("default", DEFAULT_THEME_ID):
        return _default_theme_info()
    identifier, separator, version = reference.partition("@")
    if not _THEME_ID_RE.fullmatch(identifier):
        raise _theme_error("THEME_NOT_FOUND", "unknown theme: " + reference)
    package = _theme_root(theme_root) / identifier
    if not package.is_dir():
        raise _theme_error("THEME_NOT_FOUND", "unknown theme: " + reference)
    info = validate_theme_package(package)
    if separator and info.version != version:
        raise _theme_error("THEME_NOT_FOUND", "unknown theme version: " + reference)
    return info


def install_theme(package_path: _PathInput, theme_root: Optional[_PathInput] = None, replace: bool = False) -> ThemeInfo:
    """Validate and atomically install or update one local theme package."""
    source, info, root = Path(package_path), validate_theme_package(package_path), _theme_root(theme_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise _theme_error("THEME_INSTALL_FAILED", "cannot create theme directory") from exc
    destination = root / info.identifier
    if destination.exists() and not replace:
        raise _theme_error("THEME_DUPLICATE", "theme id is already installed")
    temporary = Path(tempfile.mkdtemp(prefix=".libremark-theme-", dir=str(root)))
    backup, moved_old = root / (".libremark-backup-" + info.identifier), False
    try:
        shutil.copytree(str(source), str(temporary), dirs_exist_ok=True)
        validate_theme_package(temporary)
        if destination.exists():
            if backup.exists():
                raise _theme_error("THEME_INSTALL_FAILED", "stale theme backup exists")
            os.replace(str(destination), str(backup)); moved_old = True
        os.replace(str(temporary), str(destination)); temporary = None
        if moved_old:
            shutil.rmtree(str(backup), ignore_errors=True)
        return validate_theme_package(destination)
    except Exception:
        if moved_old and backup.exists() and not destination.exists():
            os.replace(str(backup), str(destination))
        raise
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(str(temporary), ignore_errors=True)


def remove_theme(reference: str, theme_root: Optional[_PathInput] = None) -> ThemeInfo:
    """Atomically remove one installed theme; the bundled default is immutable."""
    info = show_theme(reference, theme_root)
    if info.identifier == "default":
        raise _theme_error("THEME_DEFAULT_IMMUTABLE", "default@1 cannot be removed")
    root = _theme_root(theme_root)
    destination = root / info.identifier
    tombstone = root / (".libremark-remove-" + info.identifier)
    if tombstone.exists():
        raise _theme_error("THEME_REMOVE_FAILED", "stale removal path exists")
    try:
        os.replace(str(destination), str(tombstone))
    except OSError as exc:
        raise _theme_error("THEME_REMOVE_FAILED", "could not remove theme") from exc
    shutil.rmtree(str(tombstone), ignore_errors=True)
    return info


def resolve_theme_css(reference: Optional[str], theme_root: Optional[_PathInput] = None) -> ThemeInfo:
    """Resolve the selected theme through the validated shared-core registry."""
    return show_theme(reference or DEFAULT_THEME_ID, theme_root)
