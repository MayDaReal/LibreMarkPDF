"""Compatibility facade for toolkit-independent desktop services."""

from .desktop.services import (
    DEFAULT_DESKTOP_SERVICES,
    DesktopServices,
    open_path,
    run_conversion_job,
    run_preview_worker,
)
