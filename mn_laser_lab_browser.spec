# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

root = Path.cwd()
backend = root / "backend"
frontend_dist = root / "frontend" / "dist"

datas = [
    (str(backend / "app"), "app"),
]

if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))

block_cipher = None

a = Analysis(
    [str(backend / "mn_laser_browser_launcher.py")],
    pathex=[str(backend), str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "pydantic",
        "pydantic_core",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MN_Laser_Lab_Browser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "desktop" / "assets" / "mn_laser_lab_logo.ico") if (root / "desktop" / "assets" / "mn_laser_lab_logo.ico").exists() else None,
)
