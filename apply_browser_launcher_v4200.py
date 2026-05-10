from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
LAUNCHER = BACKEND / "mn_laser_browser_launcher.py"
BAT = ROOT / "Avvia_MN_Laser_Lab_Browser_Windows.bat"
PS1 = ROOT / "Avvia_MN_Laser_Lab_Browser_Windows.ps1"
SPEC = ROOT / "mn_laser_lab_browser.spec"
REQ = BACKEND / "requirements_browser.txt"
WORKFLOW = ROOT / ".github" / "workflows" / "build-browser-windows.yml"


LAUNCHER_CODE = r'''
from __future__ import annotations

import os
import sys
import time
import socket
import threading
import traceback
import webbrowser
from pathlib import Path

import uvicorn

from app.main import app


APP_NAME = "MN Laser Lab Manager"
HOST = os.environ.get("MN_BACKEND_HOST", "0.0.0.0")
PORT = int(os.environ.get("MN_BACKEND_PORT", "8000"))
OPEN_BROWSER = os.environ.get("MN_OPEN_BROWSER", "1") != "0"


def app_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "MN Laser Lab Manager"

    return Path.home() / ".mn_laser_lab_manager"


def log_path() -> Path:
    p = app_data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p / "browser_launcher.log"


def log(message: str):
    try:
        path = log_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {message}\n")
    except Exception:
        pass


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except Exception:
        return False


def open_browser_when_ready():
    url = f"http://127.0.0.1:{PORT}/"

    for _ in range(80):
        if is_port_open("127.0.0.1", PORT):
            time.sleep(0.45)
            log(f"Opening browser: {url}")
            webbrowser.open(url)
            return

        time.sleep(0.25)

    log("Backend did not become ready in time; opening browser anyway")
    webbrowser.open(url)


def print_banner():
    local_url = f"http://127.0.0.1:{PORT}/"
    lan_url = f"http://IP_DEL_PC:{PORT}/"

    print("")
    print("=" * 72)
    print(f" {APP_NAME} - Browser Edition")
    print("=" * 72)
    print(f" Locale : {local_url}")
    print(f" LAN    : {lan_url}")
    print("")
    print(" Da smartphone sulla stessa rete Wi-Fi:")
    print(f"  1. trova l'IP del PC")
    print(f"  2. apri http://IP_DEL_PC:{PORT}/")
    print("")
    print(f" Log: {log_path()}")
    print("=" * 72)
    print("")


def main():
    app_data_dir().mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log(f"Starting {APP_NAME} Browser Edition")
    log(f"Python executable: {sys.executable}")
    log(f"CWD: {os.getcwd()}")
    log(f"HOST={HOST} PORT={PORT}")

    print_banner()

    if OPEN_BROWSER:
        threading.Thread(target=open_browser_when_ready, daemon=True).start()

    try:
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="info",
            access_log=True,
        )
    except Exception:
        err = traceback.format_exc()
        log(err)
        raise


if __name__ == "__main__":
    main()
'''


BAT_CODE = r'''@echo off
setlocal

title MN Laser Lab Manager - Browser Edition

cd /d "%~dp0"

echo Avvio MN Laser Lab Manager Browser Edition...
echo.

if exist "MN_Laser_Lab_Browser.exe" (
    start "" "MN_Laser_Lab_Browser.exe"
    exit /b 0
)

if exist "backend\.venv\Scripts\python.exe" (
    backend\.venv\Scripts\python.exe backend\mn_laser_browser_launcher.py
    exit /b %ERRORLEVEL%
)

python backend\mn_laser_browser_launcher.py
pause
'''


PS1_CODE = r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "Avvio MN Laser Lab Manager - Browser Edition..." -ForegroundColor Cyan

$Exe = Join-Path $Root "MN_Laser_Lab_Browser.exe"
$VenvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Launcher = Join-Path $Root "backend\mn_laser_browser_launcher.py"

if (Test-Path $Exe) {
    Start-Process $Exe
    exit
}

if (Test-Path $VenvPython) {
    & $VenvPython $Launcher
    exit
}

python $Launcher
'''


SPEC_CODE = r'''
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
'''


REQ_CODE = r'''
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-multipart
reportlab
jinja2
pyinstaller
'''


WORKFLOW_CODE = r'''
name: Build Browser Windows

on:
  push:
    tags:
      - "browser-v*"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-browser-windows:
    runs-on: windows-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Build frontend
        working-directory: frontend
        run: |
          npm install
          npm run build

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements_browser.txt

      - name: Build browser launcher exe
        run: |
          pyinstaller mn_laser_lab_browser.spec --clean --noconfirm

      - name: Prepare package
        shell: pwsh
        run: |
          New-Item -ItemType Directory -Force -Path package | Out-Null
          Copy-Item dist\MN_Laser_Lab_Browser.exe package\MN_Laser_Lab_Browser.exe
          Copy-Item Avvia_MN_Laser_Lab_Browser_Windows.bat package\Avvia_MN_Laser_Lab_Browser_Windows.bat
          Copy-Item Avvia_MN_Laser_Lab_Browser_Windows.ps1 package\Avvia_MN_Laser_Lab_Browser_Windows.ps1
          Copy-Item README.md package\README.txt -ErrorAction SilentlyContinue
          Compress-Archive -Path package\* -DestinationPath MN_Laser_Lab_Browser_Windows.zip -Force

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MN_Laser_Lab_Browser_Windows
          path: MN_Laser_Lab_Browser_Windows.zip

      - name: Release
        uses: softprops/action-gh-release@v2
        with:
          files: MN_Laser_Lab_Browser_Windows.zip
'''


def ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def main():
    ensure_dir(LAUNCHER)
    LAUNCHER.write_text(LAUNCHER_CODE.strip() + "\n", encoding="utf-8")

    BAT.write_text(BAT_CODE, encoding="utf-8")
    PS1.write_text(PS1_CODE.strip() + "\n", encoding="utf-8")
    SPEC.write_text(SPEC_CODE.strip() + "\n", encoding="utf-8")
    REQ.write_text(REQ_CODE.strip() + "\n", encoding="utf-8")

    WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW.write_text(WORKFLOW_CODE.strip() + "\n", encoding="utf-8")

    print("Browser Edition v42.0.0 files created:")
    for p in [LAUNCHER, BAT, PS1, SPEC, REQ, WORKFLOW]:
        print(" -", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
