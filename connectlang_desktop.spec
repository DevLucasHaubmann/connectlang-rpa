# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ConnectLang RPA Bot Desktop App.
# Generate the exe: uv run pyinstaller connectlang_desktop.spec

from PyInstaller.utils.hooks import collect_data_files

ctk_data = collect_data_files("customtkinter")

a = Analysis(
    ["src/connectlang_rpa/desktop/app.py"],
    pathex=["src"],
    binaries=[],
    datas=ctk_data + [("assets/icon.ico", "assets")],
    hiddenimports=[
        "customtkinter",
        "pydantic_settings",
        "structlog",
        "tenacity",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "playwright",
        "pytest",
        "mypy",
        "ruff",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ConnectLangRpaBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ConnectLangRpaBot",
)
