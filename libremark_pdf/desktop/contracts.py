"""Typed queue messages shared by toolkit-independent desktop services."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Union


class PreviewRequest(NamedTuple):
    """A preview request accepted from a desktop adapter queue."""

    generation: int
    source_path: Optional[Path]
    markdown_text: Optional[str]
    options: Dict[str, Any]

    @classmethod
    def from_queue_item(
        cls, item: Union["PreviewRequest", tuple]
    ) -> "PreviewRequest":
        """Keep the root service facade compatible with positional callers."""
        if isinstance(item, cls):
            return item
        return cls(*item)


class PreviewEvent(NamedTuple):
    """A completed or failed preview event."""

    kind: str
    generation: int
    payload: Union[bytes, str]


class ConversionProgressEvent(NamedTuple):
    """A single conversion-progress event."""

    kind: str
    index: int
    total: int
    result: Dict[str, Any]


class ConversionTerminalEvent(NamedTuple):
    """A terminal conversion event containing results or an error message."""

    kind: str
    payload: Union[list, str]
