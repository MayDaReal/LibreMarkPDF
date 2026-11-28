# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import sysconfig
from importlib.metadata import distribution
from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_data_files, copy_metadata


browser_source = os.environ.get(
    "LIBREMARK_PDF_BROWSER_SOURCE",
    "browser-win" if sys.platform == "win32" else "browser-linux",
)
manual_source = os.environ.get("LIBREMARK_PDF_MANUAL_SOURCE")
if not manual_source:
    raise SystemExit(
        "LIBREMARK_PDF_MANUAL_SOURCE is required; use a native build script."
    )

interpreter_licenses = (
    Path(sys.base_prefix) / "LICENSE.txt",
    Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
)
interpreter_license = next((path for path in interpreter_licenses if path.is_file()), None)
if interpreter_license is None:
    raise SystemExit("The native CPython installation must include LICENSE.txt.")

native_licenses = [(str(interpreter_license), "licenses/CPython")]
for package in ("darkdetect", "greenlet", "Pillow", "pypdfium2", "PyInstaller",
                "setuptools", "tkinterdnd2"):
    wheel = distribution(package)
    licenses = [
        file for file in wheel.files or ()
        if len(file.parts) > 1 and file.parts[0].endswith(".dist-info")
        and (file.parts[1] == "licenses"
             or file.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")))
    ]
    if not licenses:
        raise SystemExit(f"The locked {package} wheel is missing its license files.")
    for file in licenses:
        destination = Path("licenses", package, *file.parts[1:-1])
        native_licenses.append((str(file.locate()), str(destination)))

a = Analysis(
    ["libremark_pdf_entry.py"],
    pathex=[],
    binaries=[],
    datas=collect_data_files("customtkinter") + copy_metadata("playwright") + native_licenses + [
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
    hiddenimports=["customtkinter", "PIL._tkinter_finder"],
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
