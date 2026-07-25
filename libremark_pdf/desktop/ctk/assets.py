"""Manifest-backed local icon loading for source and frozen execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import customtkinter as ctk
from PIL import Image

from .theme import ICON_COLORS


ICON_NAMES = (
    "arrow-clockwise",
    "arrows-fullscreen",
    "box-arrow-up-right",
    "bug",
    "check-circle-fill",
    "chevron-left",
    "chevron-right",
    "copy",
    "dash",
    "exclamation-circle-fill",
    "file-earmark-text",
    "floppy",
    "folder2-open",
    "info-circle-fill",
    "pencil",
    "plus",
    "three-dots-vertical",
    "trash3",
    "x-lg",
)
ICON_SIZES = (16, 20, 24)
CONTEXT_ICON_COLORS = {
    "on-primary": "#FFFFFF",
}


def default_asset_root() -> Path:
    """Resolve UI assets through the application's canonical resource path."""
    from ... import core

    return core.resource_path("assets/ui-icons")


def product_logo(size: int = 32) -> ctk.CTkImage:
    """Load the canonical local product logo at a logical size."""
    from ... import core

    path = core.resource_path(
        "assets/libremark-pdf-logo-{0}.png".format(size)
    )
    with Image.open(path) as source:
        image = source.convert("RGBA").copy()
    return ctk.CTkImage(
        light_image=image,
        dark_image=image,
        size=(size, size),
    )


class UiAssetRegistry:
    """Validate, load and retain local CustomTkinter icon images."""

    def __init__(
        self,
        root,
        asset_root: Optional[Path] = None,
    ) -> None:
        self.root = root
        self.asset_root = (
            Path(asset_root) if asset_root is not None else default_asset_root()
        )
        self.manifest = self._load_manifest()
        self._pil_images = {}  # type: Dict[Tuple[str, int, str], Image.Image]
        self._images = {}  # type: Dict[Tuple[str, int, str], ctk.CTkImage]

    def _load_manifest(self) -> dict:
        path = self.asset_root / "manifest.json"
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                "UI icon manifest is unavailable or invalid: {0}".format(path)
            ) from exc
        if manifest.get("schema") != 1:
            raise RuntimeError("Unsupported UI icon manifest schema")
        if tuple(manifest.get("icons", ())) != ICON_NAMES:
            raise RuntimeError("UI icon manifest does not match the registry")
        if tuple(manifest.get("sizes", ())) != ICON_SIZES:
            raise RuntimeError("UI icon manifest has unexpected sizes")
        if manifest.get("colors") != ICON_COLORS:
            raise RuntimeError("UI icon manifest has unexpected colors")
        return manifest

    def path_for(self, name: str, size: int, color: str) -> Path:
        """Return a validated raster path for a known icon variant."""
        key = "{0}:{1}:{2}".format(name, size, color)
        record = self.manifest["files"].get(key)
        if record is None:
            raise KeyError("Unknown UI icon variant: {0}".format(key))
        path = self.asset_root / record["path"]
        if not path.is_file():
            raise RuntimeError("UI icon file is missing: {0}".format(path))
        return path

    def image(
        self,
        name: str,
        size: int = 20,
        color: str = "neutral",
    ) -> ctk.CTkImage:
        """Return and retain a local icon image."""
        key = (name, size, color)
        if key not in self._images:
            path = self.path_for(name, size, color)
            pil_image = Image.open(path).convert("RGBA")
            expected_hash = self.manifest["files"][
                "{0}:{1}:{2}".format(name, size, color)
            ]["sha256"]
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                raise RuntimeError(
                    "UI icon hash does not match manifest: {0}".format(path)
                )
            self._pil_images[key] = pil_image
            self._images[key] = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=(size, size),
            )
        return self._images[key]

    @property
    def retained_image_count(self) -> int:
        """Return the number of icon variants retained by the registry."""
        return len(self._images)
