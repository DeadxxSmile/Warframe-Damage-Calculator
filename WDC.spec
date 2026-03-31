# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project_dir = Path(SPECPATH)
source_dir = project_dir / "source"
data_dir = project_dir / "data"

datas = []
for path in source_dir.glob("*"):
    datas.append((str(path), "source"))

icon_path = project_dir / "wdc.ico"
if icon_path.exists():
    datas.append((str(icon_path), "."))

if (project_dir / "LICENSE").exists():
    datas.append((str(project_dir / "LICENSE"), "."))

if (data_dir / "weapons.db").exists():
    datas.append((str(data_dir / "weapons.db"), "data"))

hiddenimports = collect_submodules("PyQt6")

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="WDC",
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
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WDC",
)
