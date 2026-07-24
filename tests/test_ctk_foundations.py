"""Public-behavior tests for modern UI tokens, assets and atomic widgets."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import customtkinter as ctk
from PIL import Image

from libremark_pdf.desktop.ctk.assets import (
    ICON_NAMES,
    ICON_SIZES,
    default_asset_root,
)
from libremark_pdf.desktop.ctk.components import (
    ATOMIC_COMPONENTS,
)
from libremark_pdf.desktop.ctk.theme import (
    COLORS,
    FONT_SPECS,
    ICON_COLORS,
    RADII,
    SIZES,
    SPACING,
    install_light_theme,
)
from libremark_pdf.i18n import t


ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = ROOT / "assets" / "ui-icons"


def run_gallery_probe(language="en", asset_root=None):
    command = [
        sys.executable,
        "-m",
        "tools.ui_component_gallery",
        "--lang",
        language,
        "--probe",
    ]
    if asset_root is not None:
        command.extend(("--asset-root", str(asset_root)))
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class TestModernUiTokens(unittest.TestCase):
    @staticmethod
    def _contrast(first, second):
        def luminance(value):
            channels = [
                int(value[index:index + 2], 16) / 255
                for index in (1, 3, 5)
            ]
            channels = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return (
                0.2126 * channels[0]
                + 0.7152 * channels[1]
                + 0.0722 * channels[2]
            )

        lighter, darker = sorted(
            (luminance(first), luminance(second)),
            reverse=True,
        )
        return (lighter + 0.05) / (darker + 0.05)

    def test_normative_light_tokens_are_centralized(self):
        self.assertEqual(COLORS["app_bg"], "#F5F7FA")
        self.assertEqual(COLORS["surface"], "#FFFFFF")
        self.assertEqual(COLORS["primary"], "#0B5ED7")
        self.assertEqual(COLORS["text"], "#172033")
        self.assertEqual(SPACING, {
            "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32,
        })
        self.assertEqual(RADII["control"], 6)
        self.assertEqual(RADII["card"], 8)
        self.assertEqual(RADII["pill"], 999)
        self.assertEqual(SIZES["button"], 36)
        self.assertEqual(SIZES["primary_button"], 40)
        self.assertEqual(SIZES["icon_button"], 32)
        self.assertGreaterEqual(min(size for size, _ in FONT_SPECS.values()), 11)

    def test_light_mode_is_explicit(self):
        install_light_theme()
        self.assertEqual(ctk.get_appearance_mode(), "Light")

    def test_text_and_focus_token_pairs_meet_prescribed_contrast(self):
        text_pairs = (
            ("text", "surface"),
            ("text_secondary", "surface"),
            ("primary", "surface"),
            ("success", "success_subtle"),
            ("warning", "warning_subtle"),
            ("error", "error_subtle"),
            ("info", "info_subtle"),
        )
        for foreground, background in text_pairs:
            self.assertGreaterEqual(
                self._contrast(COLORS[foreground], COLORS[background]),
                4.5,
                (foreground, background),
            )
        for foreground, background in (
            ("surface", "primary"),
            ("primary", "surface"),
            ("primary", "surface_hover"),
        ):
            self.assertGreaterEqual(
                self._contrast(COLORS[foreground], COLORS[background]),
                3.0,
                (foreground, background),
            )


class TestModernUiAssets(unittest.TestCase):
    def test_manifest_covers_only_the_prescribed_local_subset(self):
        manifest = json.loads(
            (ASSET_ROOT / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema"], 1)
        self.assertEqual(tuple(manifest["icons"]), ICON_NAMES)
        self.assertEqual(tuple(manifest["sizes"]), ICON_SIZES)
        self.assertEqual(manifest["colors"], ICON_COLORS)
        self.assertEqual(len(manifest["sources"]), len(ICON_NAMES))
        self.assertEqual(
            len(manifest["files"]),
            len(ICON_NAMES) * len(ICON_SIZES) * len(ICON_COLORS),
        )
        self.assertEqual(
            manifest["origin"]["archive_sha256"],
            "821d76089e8568f89e695cb821000abb9a63d486008794995acc21b1c66f39fc",
        )
        self.assertEqual(manifest["origin"]["license"]["spdx"], "MIT")
        license_path = ROOT / manifest["origin"]["license"]["path"]
        self.assertEqual(
            manifest["origin"]["license"]["sha256"],
            hashlib.sha256(license_path.read_bytes()).hexdigest(),
        )

    def test_every_manifest_raster_has_exact_size_and_transparency(self):
        manifest = json.loads(
            (ASSET_ROOT / "manifest.json").read_text(encoding="utf-8")
        )
        for key, record in manifest["files"].items():
            path = ASSET_ROOT / record["path"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                record["sha256"],
                key,
            )
            size = int(key.split(":")[1])
            with Image.open(path) as image:
                self.assertEqual(image.size, (size, size), key)
                self.assertEqual(image.mode, "RGBA", key)
        for name, record in manifest["sources"].items():
            path = ASSET_ROOT / record["path"]
            source = path.read_text(encoding="utf-8")
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                record["sha256"],
                name,
            )
            for forbidden in ("<script", "href=", "url(", "@import"):
                self.assertNotIn(forbidden, source.lower(), name)
        self.assertEqual(
            {path.relative_to(ASSET_ROOT).as_posix()
             for path in (ASSET_ROOT / "png").glob("*.png")},
            {record["path"] for record in manifest["files"].values()},
        )
        self.assertEqual(
            {path.relative_to(ASSET_ROOT).as_posix()
             for path in (ASSET_ROOT / "svg").glob("*.svg")},
            {record["path"] for record in manifest["sources"].values()},
        )

    def test_default_root_uses_frozen_resource_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            frozen = Path(temporary)
            with mock.patch.object(sys, "_MEIPASS", str(frozen), create=True):
                self.assertEqual(
                    default_asset_root(),
                    frozen / "assets" / "ui-icons",
                )

    def test_registry_loads_unicode_source_path_and_retains_images(self):
        with tempfile.TemporaryDirectory() as temporary:
            unicode_root = Path(temporary) / "épreuve" / "ui-icons"
            shutil.copytree(ASSET_ROOT, unicode_root)
            probe = run_gallery_probe(asset_root=unicode_root)
            self.assertGreaterEqual(probe["assets_retained"], 76)


class TestComponentGallery(unittest.TestCase):
    def test_atomic_component_catalog_is_complete(self):
        self.assertEqual(set(ATOMIC_COMPONENTS), {
            "CardFrame",
            "FocusRing",
            "IconButton",
            "PrimaryButton",
            "SecondaryButton",
            "SectionTitle",
            "StatusBadge",
            "Tooltip",
        })

    def test_gallery_builds_in_english_and_french_without_business_services(self):
        for language in ("en", "fr"):
            probe = run_gallery_probe(language)
            self.assertIn(t("gallery_title", language), probe["title"])
            self.assertEqual(probe["customtkinter"], "6.0.0")
            self.assertGreaterEqual(probe["assets_retained"], 76)
            self.assertEqual(probe["primary_height"], 40)
            self.assertEqual(probe["pressed_color"], COLORS["primary_pressed"])
            self.assertEqual(probe["disabled_state"], "disabled")
            self.assertEqual(probe["focus_border"], {
                "color": COLORS["primary"],
                "width": 2,
            })
            self.assertEqual(probe["icon_size"], 32)
            self.assertTrue(probe["tooltip_visible"])
            x, y, width, height = probe["tooltip_bounds"]
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)
            if sys.platform == "win32":
                self.assertEqual(probe["font_interface"], "Segoe UI")
                self.assertIn(
                    probe["font_monospace"],
                    ("Cascadia Mono", "Consolas", "TkFixedFont"),
                )

    def test_foundations_do_not_use_private_customtkinter_apis(self):
        sources = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "libremark_pdf/desktop/ctk/theme.py",
                "libremark_pdf/desktop/ctk/assets.py",
                "libremark_pdf/desktop/ctk/components.py",
                "tools/ui_component_gallery.py",
            )
        )
        for private_name in (
            "ThemeManager",
            "ScalingTracker",
            "DrawEngine",
            "._canvas",
            "._draw",
        ):
            self.assertNotIn(private_name, sources)


if __name__ == "__main__":
    unittest.main()
