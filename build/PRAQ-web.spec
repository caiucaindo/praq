# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).parent.resolve()

datas = [
    (str(project_root / "config.json"), "."),
    (str(project_root / "frontend" / "dist"), "frontend/dist"),
]

hiddenimports = [
    "google.genai",
    "google.genai.types",
    "groq",
    "keyboard",
    "PIL",
    "PIL.Image",
    "pyautogui",
    "pyperclip",
    "pyscreeze",
    "webview",
    "webview.platforms.edgechromium",
]

a = Analysis(
    [str(project_root / "PRAQ_web.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "pytest",
        "tkinter",
        "webview.platforms.qt",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="PRAQ",
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
    icon=str(project_root / "assets" / "icon.ico"),
    version=str(project_root / "build" / "version_info.txt"),
)
