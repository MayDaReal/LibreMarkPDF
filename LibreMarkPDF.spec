# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_data_files


browser_source = os.environ.get(
    "LIBREMARK_PDF_BROWSER_SOURCE",
    "browser-win" if sys.platform == "win32" else "browser-linux",
)
manual_source = os.environ.get("LIBREMARK_PDF_MANUAL_SOURCE")
if not manual_source:
    raise SystemExit(
        "LIBREMARK_PDF_MANUAL_SOURCE is required; use a native build script."
    )


a = Analysis(
    ["libremark_pdf_entry.py"],
    pathex=[],
    binaries=[],
    datas=collect_data_files("customtkinter") + [
        ("style.css", "."),
        ("VERSION", "."),
        ("icons", "icons"),
        ("assets", "assets"),
        ("fonts", "fonts"),
        ("licenses", "licenses"),
        ("LICENSE", "."),
        ("THIRD_PARTY_NOTICES.md", "."),
        ("docs/THEME_CONTRIBUTING.md", "docs"),
        ("docs/CLI_JSON_SCHEMA.json", "docs"),
        (os.path.join(manual_source, "MANUAL_EN.pdf"), "docs"),
        (os.path.join(manual_source, "MANUEL_FR.pdf"), "docs"),
    ],
    hiddenimports=["customtkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.datas += Tree(
    browser_source,
    prefix="browsers",
    excludes=[".links", ".links/*"],
)
pyz = PYZ(a.pure)

gui_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LibreMarkPDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets\\libremark-pdf.ico"] if os.name == "nt" else None,
)

cli_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LibreMarkPDF-cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets\\libremark-pdf.ico"] if os.name == "nt" else None,
)

debug_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LibreMarkPDF-debug",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets\\libremark-pdf.ico"] if os.name == "nt" else None,
)

coll = COLLECT(
    gui_exe,
    cli_exe,
    debug_exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LibreMarkPDF",
)
