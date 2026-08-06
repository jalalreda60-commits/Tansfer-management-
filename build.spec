# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for Transfer Management System.

Build locally with:
    pyinstaller build.spec

The GitHub Actions workflow (.github/workflows/build-exe.yml) runs this
exact spec on a windows-latest runner to produce the distributable .exe.
"""
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden_imports = (
    collect_submodules("sqlalchemy.dialects.sqlite")
    + collect_submodules("PySide6.QtCharts")
    + collect_submodules("PySide6.QtPrintSupport")
    + [
        "openpyxl.cell._writer",
    ]
)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("app/resources", "app/resources"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtNetwork",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "tkinter",
        "matplotlib",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TransferManagementSystem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Drop a 256x256 .ico at app/resources/icon.ico and point this at it
    # to brand the .exe / taskbar icon.
    icon=None,
)
