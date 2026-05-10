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
    except Exception as exc:
        err = traceback.format_exc()
        log(err)
        print(err)
        _fatal_pause_on_windows()
        raise


if __name__ == "__main__":
    main()


# v42.0.7 fatal startup diagnostics
def _fatal_pause_on_windows():
    import os
    if os.name == "nt":
        try:
            input("\nErrore all'avvio. Premi INVIO per chiudere...")
        except Exception:
            pass
