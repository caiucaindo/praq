# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).parent.resolve()

assets = [
    "chevron-down.svg",
    "chevron-left-active.svg",
    "chevron-left.svg",
    "chevron-right-active.svg",
    "chevron-right.svg",
    "dropdown-chevron-down.svg",
    "dropdown-chevron-right.svg",
    "icon.ico",
    "logo-sem-fundo.png",
    "logo.png",
    "settings.svg",
    "x-active.svg",
    "x.svg",
]

datas = [
    (str(project_root / "config.json"), "."),
]
datas += [
    (str(project_root / "assets" / asset), "assets")
    for asset in assets
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
]

a = Analysis(
    [str(project_root / "PRAQ.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tkinter",
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
