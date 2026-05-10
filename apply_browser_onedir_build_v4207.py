from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "mn_laser_lab_browser.spec"
BAT = ROOT / "Avvia_MN_Laser_Lab_Browser_Windows.bat"
WORKFLOW = ROOT / ".github" / "workflows" / "build-browser-windows.yml"
LAUNCHER = ROOT / "backend" / "mn_laser_browser_launcher.py"

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
'''

BAT_CODE = r'''@echo off
setlocal

title MN Laser Lab Manager - Browser Edition

cd /d "%~dp0"

echo ============================================================
echo  MN Laser Lab Manager - Browser Edition
echo ============================================================
echo.

set MN_OPEN_BROWSER=1
set MN_BACKEND_HOST=0.0.0.0
set MN_BACKEND_PORT=8000

if exist "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe" (
    echo Avvio da cartella onedir...
    echo.
    "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"
    echo.
    echo L'app si e' chiusa. Codice errore: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

if exist "MN_Laser_Lab_Browser.exe" (
    echo Avvio EXE singolo...
    echo.
    "MN_Laser_Lab_Browser.exe"
    echo.
    echo L'app si e' chiusa. Codice errore: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo ERRORE: eseguibile non trovato.
echo Cerca:
echo - MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe
echo - MN_Laser_Lab_Browser.exe
echo.
pause
exit /b 1
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

      - name: Build browser launcher onedir
        run: |
          pyinstaller mn_laser_lab_browser.spec --clean --noconfirm

      - name: Prepare package
        shell: pwsh
        run: |
          New-Item -ItemType Directory -Force -Path package | Out-Null
          Copy-Item dist\MN_Laser_Lab_Browser package\MN_Laser_Lab_Browser -Recurse
          Copy-Item Avvia_MN_Laser_Lab_Browser_Windows.bat package\Avvia_MN_Laser_Lab_Browser_Windows.bat
          Copy-Item Avvia_MN_Laser_Lab_Browser_Windows.ps1 package\Avvia_MN_Laser_Lab_Browser_Windows.ps1 -ErrorAction SilentlyContinue
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

LAUNCHER_PATCH = r'''
# v42.0.7 fatal startup diagnostics
def _fatal_pause_on_windows():
    import os
    if os.name == "nt":
        try:
            input("\nErrore all'avvio. Premi INVIO per chiudere...")
        except Exception:
            pass
'''

def main():
    SPEC.write_text(SPEC_CODE.strip() + "\n", encoding="utf-8")
    BAT.write_text(BAT_CODE, encoding="utf-8")
    WORKFLOW.write_text(WORKFLOW_CODE.strip() + "\n", encoding="utf-8")

    s = LAUNCHER.read_text(encoding="utf-8")
    if "v42.0.7 fatal startup diagnostics" not in s:
        s += "\n\n" + LAUNCHER_PATCH.strip() + "\n"

    # Rende il main più diagnostico se crasha prima/durante uvicorn.
    if "except Exception as exc:" not in s:
        s = s.replace(
            "    except Exception:\n        err = traceback.format_exc()\n        log(err)\n        raise",
            "    except Exception as exc:\n        err = traceback.format_exc()\n        log(err)\n        print(err)\n        _fatal_pause_on_windows()\n        raise"
        )

    LAUNCHER.write_text(s, encoding="utf-8")

    print("Patch v42.0.7 applicata: PyInstaller onedir + BAT diagnostico.")

if __name__ == "__main__":
    main()
