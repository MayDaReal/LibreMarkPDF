"""Stable launch facade for the Tk desktop adapter."""

from .desktop.services import open_path, run_conversion_job, run_preview_worker
from .desktop.tk.app import LibreMarkPdfApp, _HAS_DND, launch


# Retain these module-level names for existing embedders while desktop adapters
# import toolkit-neutral services directly.
_open_path = open_path
_run_preview_worker = run_preview_worker
_run_conversion_job = run_conversion_job


if __name__ == "__main__":
    launch()
