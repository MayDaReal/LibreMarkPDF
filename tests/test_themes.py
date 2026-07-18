"""Security and lifecycle tests for local community themes."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from libremark_pdf import core
from libremark_pdf.engine import themes


ROOT = Path(__file__).resolve().parent.parent
VALID_THEME = ROOT / "tests" / "fixtures" / "themes" / "community-blue"


def copy_theme(destination: Path) -> Path:
    package = destination / "package"
    shutil.copytree(str(VALID_THEME), str(package))
    return package


def rewrite_manifest(package: Path, change) -> None:
    path = package / core.THEME_MANIFEST_NAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    change(manifest)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class TestThemeValidation(unittest.TestCase):
    def test_core_reexports_the_internal_theme_domain(self):
        for name in (
            "validate_theme_package", "list_themes", "show_theme", "install_theme",
            "remove_theme", "resolve_theme_css",
        ):
            self.assertIs(getattr(core, name), getattr(themes, name), name)
        self.assertNotIn("libremark_pdf.core", Path(themes.__file__).read_text(encoding="utf-8"))

    def test_default_theme_is_an_exact_style_css_alias(self):
        info = core.show_theme("default@1", theme_root=Path("unused"))
        self.assertEqual(info.css_path, core.DEFAULT_CSS_PATH)
        self.assertEqual(info.css_sha256, hashlib.sha256(
            core.DEFAULT_CSS_PATH.read_bytes()
        ).hexdigest())
        self.assertEqual(info.reference, "default@1")

    def test_valid_manifest_hashes_every_package_file(self):
        info = core.validate_theme_package(VALID_THEME)
        self.assertEqual(info.reference, "community-blue@1")
        manifest = json.loads(
            (VALID_THEME / "theme.json").read_text(encoding="utf-8")
        )
        actual = {
            path.relative_to(VALID_THEME).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in VALID_THEME.rglob("*")
            if path.is_file() and path.name != "theme.json"
        }
        self.assertEqual(manifest["files"], actual)

    def test_rejects_traversal_missing_licence_and_incompatible_profile(self):
        changes = (
            lambda data: data.update(css="../style.css"),
            lambda data: data.update(licenses=[]),
            lambda data: data.update(render_profiles=["future@2"]),
        )
        codes = ("THEME_TRAVERSAL", "THEME_LICENSE_MISSING", "THEME_INCOMPATIBLE")
        for change, code in zip(changes, codes):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temporary:
                package = copy_theme(Path(temporary))
                rewrite_manifest(package, change)
                with self.assertRaisesRegex(core.ConversionError, code):
                    core.validate_theme_package(package)

    def test_rejects_whitespace_or_non_text_licence(self):
        for payload in (b"   \n", b"\xff\xfe"):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temporary:
                package = copy_theme(Path(temporary))
                licence = package / "LICENSE.txt"
                licence.write_bytes(payload)
                digest = hashlib.sha256(payload).hexdigest()
                rewrite_manifest(
                    package,
                    lambda data: data["files"].update({"LICENSE.txt": digest}),
                )
                with self.assertRaisesRegex(
                    core.ConversionError, "THEME_LICENSE_MISSING"
                ):
                    core.validate_theme_package(package)

    def test_rejects_remote_script_hash_mismatch_and_undeclared_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = copy_theme(Path(temporary))
            css = package / "style.css"
            css.write_text("@import url(https://example.invalid/x.css);", encoding="utf-8")
            digest = hashlib.sha256(css.read_bytes()).hexdigest()
            rewrite_manifest(
                package, lambda data: data["files"].update({"style.css": digest})
            )
            with self.assertRaisesRegex(core.ConversionError, "THEME_FORBIDDEN_CONTENT"):
                core.validate_theme_package(package)

        with tempfile.TemporaryDirectory() as temporary:
            package = copy_theme(Path(temporary))
            (package / "style.css").write_text("<script>x</script>", encoding="utf-8")
            digest = hashlib.sha256((package / "style.css").read_bytes()).hexdigest()
            rewrite_manifest(
                package, lambda data: data["files"].update({"style.css": digest})
            )
            with self.assertRaisesRegex(core.ConversionError, "THEME_FORBIDDEN_CONTENT"):
                core.validate_theme_package(package)

        with tempfile.TemporaryDirectory() as temporary:
            package = copy_theme(Path(temporary))
            (package / "style.css").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(core.ConversionError, "THEME_HASH_MISMATCH"):
                core.validate_theme_package(package)

        with tempfile.TemporaryDirectory() as temporary:
            package = copy_theme(Path(temporary))
            (package / "undeclared.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(core.ConversionError, "THEME_UNDECLARED_FILE"):
                core.validate_theme_package(package)

    def test_rejects_remote_preview_markdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = copy_theme(Path(temporary))
            preview = package / "preview.md"
            preview.write_text(
                "![remote](https://example.invalid/image.png)", encoding="utf-8"
            )
            digest = hashlib.sha256(preview.read_bytes()).hexdigest()
            rewrite_manifest(
                package, lambda data: data["files"].update({"preview.md": digest})
            )
            with self.assertRaisesRegex(
                core.ConversionError, "THEME_FORBIDDEN_CONTENT"
            ):
                core.validate_theme_package(package)

    def test_rejects_active_svg_even_when_not_selected_as_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = copy_theme(Path(temporary))
            svg = package / "asset.svg"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><script>x()</script></svg>',
                encoding="utf-8",
            )
            digest = hashlib.sha256(svg.read_bytes()).hexdigest()
            rewrite_manifest(
                package, lambda data: data["files"].update({"asset.svg": digest})
            )
            with self.assertRaisesRegex(
                core.ConversionError, "THEME_FORBIDDEN_CONTENT"
            ):
                core.validate_theme_package(package)


class TestThemeLifecycle(unittest.TestCase):
    def test_install_list_show_select_update_and_remove(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "installed"
            installed = core.install_theme(VALID_THEME, theme_root=root)
            self.assertEqual(installed.reference, "community-blue@1")
            self.assertEqual(
                [item.reference for item in core.list_themes(root)],
                ["default@1", "community-blue@1"],
            )
            self.assertEqual(
                core.show_theme("community-blue", root).css_sha256,
                installed.css_sha256,
            )
            self.assertEqual(
                core.resolve_theme_css("community-blue@1", root).css_path,
                root / "community-blue" / "style.css",
            )
            with self.assertRaisesRegex(core.ConversionError, "THEME_DUPLICATE"):
                core.install_theme(VALID_THEME, theme_root=root)
            updated = core.install_theme(VALID_THEME, theme_root=root, replace=True)
            self.assertEqual(updated.reference, "community-blue@1")
            removed = core.remove_theme("community-blue@1", root)
            self.assertEqual(removed.reference, "community-blue@1")
            self.assertEqual(
                [item.reference for item in core.list_themes(root)], ["default@1"]
            )

    def test_failed_atomic_update_restores_existing_theme(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "installed"
            original = core.install_theme(VALID_THEME, theme_root=root)
            real_replace = core.os.replace
            calls = []

            def fail_publication(source, destination):
                calls.append((source, destination))
                if ".libremark-theme-" in source:
                    raise PermissionError("simulated publication failure")
                return real_replace(source, destination)

            with mock.patch.object(core.os, "replace", side_effect=fail_publication):
                with self.assertRaisesRegex(PermissionError, "publication failure"):
                    core.install_theme(VALID_THEME, theme_root=root, replace=True)
            restored = core.show_theme("community-blue@1", root)
            self.assertEqual(restored.css_sha256, original.css_sha256)
            self.assertEqual(
                list(root.glob(".libremark-theme-*"))
                + list(root.glob(".libremark-backup-*")),
                [],
            )

    def test_default_theme_cannot_be_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(core.ConversionError, "THEME_DEFAULT_IMMUTABLE"):
                core.remove_theme("default@1", Path(temporary))

    def test_remove_is_logically_atomic_when_cleanup_is_delayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "installed"
            core.install_theme(VALID_THEME, theme_root=root)
            def delayed_cleanup(path, ignore_errors=False):
                if not ignore_errors:
                    raise PermissionError("locked")

            with mock.patch.object(core.shutil, "rmtree", side_effect=delayed_cleanup):
                removed = core.remove_theme("community-blue@1", root)
            self.assertEqual(removed.reference, "community-blue@1")
            with self.assertRaisesRegex(core.ConversionError, "THEME_NOT_FOUND"):
                core.show_theme("community-blue@1", root)
            self.assertTrue((root / ".libremark-remove-community-blue").exists())

    def test_prepare_render_document_uses_selected_theme_and_rejects_css_mix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "installed"
            core.install_theme(VALID_THEME, theme_root=root)
            document = core.prepare_render_document(
                "# Theme", render_date="2026-07-14",
                theme="community-blue@1", theme_root=root,
            )
            self.assertEqual(document.profile.theme_name, "community-blue@1")
            self.assertIn("#123456", document.full_html)
            with self.assertRaisesRegex(core.ConversionError, "INVALID_OPTIONS"):
                core.prepare_render_document(
                    "# Theme", css_path=core.DEFAULT_CSS_PATH,
                    theme="community-blue@1", theme_root=root,
                )

    def test_explicit_default_alias_preserves_default_render_input_exactly(self):
        implicit = core.prepare_render_document(
            "# Exact default", render_date="2026-07-14"
        )
        explicit = core.prepare_render_document(
            "# Exact default", render_date="2026-07-14", theme="default@1"
        )
        self.assertEqual(explicit.profile.canonical_json(), implicit.profile.canonical_json())
        self.assertEqual(explicit.profile.fingerprint, implicit.profile.fingerprint)
        self.assertEqual(explicit.full_html, implicit.full_html)


if __name__ == "__main__":
    unittest.main()
