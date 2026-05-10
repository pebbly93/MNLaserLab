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
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "pydantic",
        "pydantic_core",
        "jinja2",
        "multipart",
        "email_validator",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MN_Laser_Lab_Browser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    icon=str(root / "desktop" / "assets" / "mn_laser_lab_logo.ico") if (root / "desktop" / "assets" / "mn_laser_lab_logo.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MN_Laser_Lab_Browser",
)
