# -*- mode: python ; coding: utf-8 -*-

import os


a = Analysis(
    ["libremark_pdf_entry.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("style.css", "."),
        ("icons", "icons"),
        ("assets", "assets"),
        ("browsers", "browsers"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LibreMarkPDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=os.environ.get("LIBREMARK_PDF_CONSOLE") == "1",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets\\libremark-pdf.ico"] if os.name == "nt" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LibreMarkPDF",
)
