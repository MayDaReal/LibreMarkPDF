# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ["libremark_pdf_entry.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("style.css", "."),
        ("icons", "icons"),
        ("fonts", "fonts"),
        ("licenses", "licenses"),
        ("LICENSE", "."),
        ("THIRD_PARTY_NOTICES.md", "."),
        ("docs/THEME_CONTRIBUTING.md", "docs"),
        ("docs/CLI_JSON_SCHEMA.json", "docs"),
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
    a.binaries,
    a.datas,
    [],
    name='LibreMarkPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=os.environ.get("LIBREMARK_PDF_CONSOLE") == "1",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets\\libremark-pdf.ico"] if os.name == "nt" else None,
)
