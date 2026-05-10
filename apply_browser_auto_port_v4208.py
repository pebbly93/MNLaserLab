from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "backend" / "mn_laser_browser_launcher.py"
BAT = ROOT / "Avvia_MN_Laser_Lab_Browser_Windows.bat"

NEW_LAUNCHER = r'''
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
PREFERRED_PORT = int(os.environ.get("MN_BACKEND_PORT", "8000"))
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


def find_free_port(start_port: int) -> int:
    """
    Se 8000 è occupata, prova porte successive.
    """
    for port in range(start_port, start_port + 20):
        if not is_port_open("127.0.0.1", port):
            return port
    return start_port


def open_browser_when_ready(port: int):
    url = f"http://127.0.0.1:{port}/"

    for _ in range(80):
        if is_port_open("127.0.0.1", port):
            time.sleep(0.45)
            log(f"Opening browser: {url}")
            webbrowser.open(url)
            return
        time.sleep(0.25)

    log("Backend did not become ready in time; opening browser anyway")
    webbrowser.open(url)


def print_banner(port: int, port_changed: bool):
    local_url = f"http://127.0.0.1:{port}/"
    lan_url = f"http://IP_DEL_PC:{port}/"

    print("")
    print("=" * 72)
    print(f" {APP_NAME} - Browser Edition")
    print("=" * 72)

    if port_changed:
        print(f" Porta 8000 occupata: uso automaticamente la porta {port}")
        print("-" * 72)

    print(f" Locale : {local_url}")
    print(f" LAN    : {lan_url}")
    print("")
    print(" Da smartphone sulla stessa rete Wi-Fi:")
    print("  1. trova l'IP del PC")
    print(f"  2. apri http://IP_DEL_PC:{port}/")
    print("")
    print(f" Log: {log_path()}")
    print("=" * 72)
    print("")


def fatal_pause_on_windows():
    if os.name == "nt":
        try:
            input("\nErrore all'avvio. Premi INVIO per chiudere...")
        except Exception:
            pass


def main():
    app_data_dir().mkdir(parents=True, exist_ok=True)

    port = find_free_port(PREFERRED_PORT)
    port_changed = port != PREFERRED_PORT

    os.environ["MN_BACKEND_PORT"] = str(port)

    log("=" * 60)
    log(f"Starting {APP_NAME} Browser Edition")
    log(f"Python executable: {sys.executable}")
    log(f"CWD: {os.getcwd()}")
    log(f"HOST={HOST} PORT={port}")

    print_banner(port, port_changed)

    if OPEN_BROWSER:
        threading.Thread(target=open_browser_when_ready, args=(port,), daemon=True).start()

    try:
        uvicorn.run(
            app,
            host=HOST,
            port=port,
            log_level="info",
            access_log=True,
        )
    except Exception:
        err = traceback.format_exc()
        log(err)
        print(err)
        fatal_pause_on_windows()
        raise


if __name__ == "__main__":
    main()
'''

NEW_BAT = r'''@echo off
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

def main():
    LAUNCHER.write_text(NEW_LAUNCHER.strip() + "\n", encoding="utf-8")
    BAT.write_text(NEW_BAT, encoding="utf-8")
    print("Patch v42.0.8 applicata: porta automatica se 8000 è occupata.")

if __name__ == "__main__":
    main()
