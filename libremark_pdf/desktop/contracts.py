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


class PreviewDocumentRequest(NamedTuple):
    """A multipage preview-document request from the Tk adapter."""

    generation: int
    source_path: Optional[Path]
    markdown_text: Optional[str]
    options: Dict[str, Any]


class PreviewPageRequest(NamedTuple):
    """A raster request for the active preview PDF."""

    generation: int
    page: int
    dpi: int


class PreviewEvent(NamedTuple):
    """A completed or failed preview event."""

    kind: str
    generation: int
    payload: Union[bytes, str]


class PreviewDocumentEvent(NamedTuple):
    """The first page and page count of a newly rendered preview PDF."""

    kind: str
    generation: int
    page: int
    total: int
    png: bytes


class PreviewPageEvent(NamedTuple):
    """One page rasterized from the active preview PDF."""

    kind: str
    generation: int
    page: int
    total: int
    png: bytes


class PreviewPageErrorEvent(NamedTuple):
    """A failed page rasterization that leaves the preview PDF active."""

    kind: str
    generation: int
    page: int
    error: str


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
