"""Toolkit-independent local problem-report construction."""

from __future__ import annotations

import json
import platform
import re
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional

from .. import __version__, core, i18n


_WINDOWS_PATH = re.compile(
    r"(?<![\w])(?:[A-Za-z]:[\\/]|\\\\)[^\r\n,;\"'<>|]+"
)
_POSIX_PATH = re.compile(r"(?<![\w.])/(?:[^/\r\n,;\"'<>]+/)*[^\r\n,;\"'<>]*")
_TRAILING_PUNCTUATION = ".,;:)]}"


class SupportChannelUnavailable(RuntimeError):
    """Raised when no owner-provided support page is configured."""


def _replace_path_match(match: "re.Match[str]") -> str:
    value = match.group(0)
    suffix = ""
    while value and value[-1] in _TRAILING_PUNCTUATION:
        suffix = value[-1] + suffix
        value = value[:-1]
    return "<private-path>" + suffix


def anonymize_text(text: str, private_paths: Iterable[Path] = ()) -> str:
    """Replace known names and path-shaped text with non-identifying aliases."""
    anonymized = text
    known_values = []
    for index, path in enumerate(private_paths, start=1):
        candidate = Path(path)
        alias = "<source-{0}{1}>".format(index, candidate.suffix.lower())
        for value in (str(candidate), candidate.name):
            if value:
                known_values.append((value, alias))
    for value, alias in sorted(known_values, key=lambda item: len(item[0]), reverse=True):
        anonymized = anonymized.replace(value, alias)
    anonymized = _WINDOWS_PATH.sub(_replace_path_match, anonymized)
    anonymized = _POSIX_PATH.sub(_replace_path_match, anonymized)
    return anonymized


def _resource_presence() -> dict:
    def available(check: Callable[[], bool]) -> bool:
        try:
            return bool(check())
        except Exception:
            return False

    return {
        "browser": available(
            lambda: bool(core.renderer_identity().get("browser_executables"))
        ),
        "css": available(core.DEFAULT_CSS_PATH.is_file),
        "default_theme": available(
            lambda: core.show_theme(core.DEFAULT_THEME_ID).css_path.is_file()
        ),
        "fonts": available(
            lambda: core.FONTS_DIR.is_dir() and all(
                (core.FONTS_DIR / item[0]).is_file() for item in core._FONT_FILES
            )
        ),
        "icons": available(core.ICONS_DIR.is_dir),
        "license": available(lambda: core.resource_path("LICENSE").is_file()),
    }


class ReportingService:
    """Build and save local reports without sending application data."""

    def __init__(
        self,
        support_url: Optional[str] = None,
        support_opener: Optional[Callable[[str], object]] = None,
    ) -> None:
        if support_url and not support_url.startswith("https://"):
            raise ValueError("support URL must use HTTPS")
        self.support_url = support_url
        self._support_opener = support_opener or webbrowser.open

    @property
    def has_support_channel(self) -> bool:
        return bool(self.support_url)

    def diagnostic_payload(
        self,
        *,
        language: str,
        theme: str,
        file_count: int,
        has_drag_and_drop: bool,
        error_code: str = "",
        error_message: str = "",
        private_paths: Iterable[Path] = (),
        generated_at: Optional[datetime] = None,
    ) -> dict:
        """Return the minimal consent-only diagnostic without private paths."""
        private_path_values = tuple(private_paths)
        timestamp = generated_at or datetime.now().astimezone()
        payload = {
            "application_version": __version__,
            "architecture": platform.machine() or "unknown",
            "chromium_revision": core.CHROMIUM_REVISION,
            "chromium_version": core.CHROMIUM_VERSION,
            "drag_and_drop": bool(has_drag_and_drop),
            "error_code": (
                anonymize_text(error_code, private_paths=private_path_values)
                if error_code else None
            ),
            "file_count": int(file_count),
            "generated_at": timestamp.isoformat(timespec="seconds"),
            "interface_language": language,
            "playwright_version": core.PLAYWRIGHT_VERSION,
            "python_version": platform.python_version(),
            "render_profile": core.DEFAULT_PROFILE_VERSION,
            "resources": _resource_presence(),
            "system": " ".join(
                value for value in (platform.system(), platform.release()) if value
            ),
            "theme": theme,
        }
        if error_message:
            payload["error_message"] = anonymize_text(
                error_message, private_paths=private_path_values
            )
        return payload

    def build_report(
        self,
        *,
        language: str,
        summary: str,
        steps: str = "",
        expected: str = "",
        error_code: str = "",
        diagnostics: Optional[dict] = None,
    ) -> str:
        """Format a readable UTF-8 report with an optional JSON block."""
        sections = [
            i18n.t("report_document_title", language),
            "",
            i18n.t("report_summary", language),
            summary.strip(),
        ]
        for key, value in (
            ("report_steps", steps),
            ("report_expected", expected),
        ):
            if value.strip():
                sections.extend(("", i18n.t(key, language), value.strip()))
        if error_code.strip():
            sections.extend((
                "",
                "{0}: {1}".format(
                    i18n.t("report_error_code", language),
                    anonymize_text(error_code.strip()),
                ),
            ))
        if diagnostics is not None:
            sections.extend((
                "",
                i18n.t("report_diagnostics_heading", language),
                json.dumps(diagnostics, ensure_ascii=False, indent=2, sort_keys=True),
            ))
        return "\n".join(sections).rstrip() + "\n"

    def save_report(self, path: Path, report: str) -> None:
        """Save exactly the reviewed report as UTF-8 text."""
        Path(path).write_text(report, encoding="utf-8")

    def open_support_page(self) -> None:
        """Open only an explicitly configured page through the system browser."""
        if not self.support_url:
            raise SupportChannelUnavailable("support channel is not configured")
        self._support_opener(self.support_url)


DEFAULT_REPORTING_SERVICE = ReportingService()
