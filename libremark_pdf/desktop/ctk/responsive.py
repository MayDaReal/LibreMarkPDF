"""Debounced responsive mode resolution for the modern desktop shell."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional


COMPACT_MAX_WIDTH = 759
MEDIUM_MAX_WIDTH = 1099
RESIZE_DEBOUNCE_MS = 100


def resolve_layout_mode(width: int) -> str:
    """Return the normative layout mode for a window width."""
    if width <= COMPACT_MAX_WIDTH:
        return "compact"
    if width <= MEDIUM_MAX_WIDTH:
        return "medium"
    return "large"


class DebouncedLayoutController:
    """Coalesce configure events before applying a shell layout."""

    def __init__(
        self,
        root: tk.Misc,
        apply_layout: Callable[[int, int], None],
        delay_ms: int = RESIZE_DEBOUNCE_MS,
    ) -> None:
        if delay_ms < 80 or delay_ms > 120:
            raise ValueError("Resize debounce must be between 80 and 120 ms")
        self.root = root
        self.apply_layout = apply_layout
        self.delay_ms = delay_ms
        self._after_id = None  # type: Optional[str]
        self._pending_size = None  # type: Optional[tuple[int, int]]
        self._last_applied_size = None  # type: Optional[tuple[int, int]]

    @property
    def pending(self) -> bool:
        """Return whether a layout application is currently scheduled."""
        return self._after_id is not None

    def schedule(self, width: int, height: int) -> None:
        """Replace any pending layout request with the latest window size."""
        size = (width, height)
        if size == self._pending_size:
            return
        if self._after_id is None and size == self._last_applied_size:
            return
        self._pending_size = size
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(self.delay_ms, self.flush)

    def flush(self) -> None:
        """Apply the latest scheduled size exactly once."""
        self._after_id = None
        size = self._pending_size
        self._pending_size = None
        if size is not None:
            self.apply_layout(*size)
            self._last_applied_size = size

    def cancel(self) -> None:
        """Cancel pending work during application shutdown."""
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._pending_size = None
