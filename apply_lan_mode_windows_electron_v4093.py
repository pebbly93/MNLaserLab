from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

DESKTOP_MAIN = ROOT / "desktop" / "main.js"
DESKTOP_SERVER = ROOT / "backend" / "desktop_server.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND_MAIN = ROOT / "frontend" / "src" / "main.jsx"
FRONTEND_API = ROOT / "frontend" / "src" / "api.js"


def patch_desktop_main():
    p = DESKTOP_MAIN
    s = p.read_text(encoding="utf-8")

    # Electron deve continuare ad aprire localmente il PC.
    # Non cambiamo APP_URL/HEALTH_URL a 0.0.0.0, perché nel browser 0.0.0.0 non è l'indirizzo da aprire.
    if "MN_BACKEND_HOST" not in s:
        insert = '''
// v40.9.3 - LAN mode.
// Backend FastAPI ascolta su 0.0.0.0, ma Electron apre l'app su 127.0.0.1.
process.env.MN_BACKEND_HOST = process.env.MN_BACKEND_HOST || "0.0.0.0";
process.env.MN_BACKEND_PORT = process.env.MN_BACKEND_PORT || "8000";

'''
        marker = "const PORT ="
        if marker in s:
            s = s.replace(marker, insert + marker, 1)
        else:
            s = insert + s

    p.write_text(s, encoding="utf-8")
    print("desktop/main.js aggiornato")


def patch_desktop_server():
    p = DESKTOP_SERVER
    s = p.read_text(encoding="utf-8")

    if "import os" not in s.splitlines()[:40]:
        lines = s.splitlines()
        pos = 0
        for i, line in enumerate(lines[:40]):
            if line.startswith("import ") or line.startswith("from "):
                pos = i + 1
        lines.insert(pos, "import os")
        s = "\n".join(lines) + "\n"

    s = s.replace(
        'uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")',
        'uvicorn.run(app, host=os.environ.get("MN_BACKEND_HOST", "0.0.0.0"), port=port, log_level="info")'
    )

    s = s.replace(
        "uvicorn.run(app, host='127.0.0.1', port=port, log_level='info')",
        'uvicorn.run(app, host=os.environ.get("MN_BACKEND_HOST", "0.0.0.0"), port=port, log_level="info")'
    )

    p.write_text(s, encoding="utf-8")
    print("backend/desktop_server.py aggiornato")


def patch_cors():
    p = MAIN_API
    s = p.read_text(encoding="utf-8")

    old = 'app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])'

    new = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\\\\.0\\\\.0\\\\.1|192\\\\.168\\\\.\\\\d+\\\\.\\\\d+|10\\\\.\\\\d+\\\\.\\\\d+\\\\.\\\\d+|172\\\\.(1[6-9]|2\\\\d|3[0-1])\\\\.\\\\d+\\\\.\\\\d+):(5173|8000)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

    if old in s:
        s = s.replace(old, new, 1)
    elif "allow_origin_regex" not in s and "CORSMiddleware" in s:
        print("ATTENZIONE: CORS presente ma non nel formato atteso. Verifica manualmente backend/app/main.py")
    else:
        print("ATTENZIONE: middleware CORS non trovato.")

    p.write_text(s, encoding="utf-8")
    print("backend/app/main.py CORS aggiornato")


def patch_frontend_api_js():
    p = FRONTEND_API
    if not p.exists():
        print("frontend/src/api.js non trovato")
        return

    s = p.read_text(encoding="utf-8")

    replacement = '''const API_HOST =
  typeof window !== 'undefined' && window.location && window.location.hostname
    ? window.location.hostname
    : '127.0.0.1';

const BASE = `http://${API_HOST}:8000/api`;'''

    s = re.sub(
        r"const\s+BASE\s*=\s*['\"]http://127\.0\.0\.1:8000/api['\"]\s*;",
        replacement,
        s,
        count=1
    )

    s = re.sub(
        r"const\s+BASE\s*=\s*['\"]http://localhost:8000/api['\"]\s*;",
        replacement,
        s,
        count=1
    )

    p.write_text(s, encoding="utf-8")
    print("frontend/src/api.js aggiornato")


def patch_frontend_main_jsx():
    p = FRONTEND_MAIN
    s = p.read_text(encoding="utf-8")

    old = """? 'http://127.0.0.1:8000'
        : window.location.origin.includes('5173')
          ? 'http://127.0.0.1:8000'"""

    new = """? `http://${window.location.hostname}:8000`
        : window.location.origin.includes('5173')
          ? `http://${window.location.hostname}:8000`"""

    if old in s:
        s = s.replace(old, new, 1)
    else:
        # fallback più semplice sulle stringhe note
        s = s.replace("'http://127.0.0.1:8000'", "`http://${window.location.hostname}:8000`")

    p.write_text(s, encoding="utf-8")
    print("frontend/src/main.jsx aggiornato")


def main():
    patch_desktop_main()
    patch_desktop_server()
    patch_cors()
    patch_frontend_api_js()
    patch_frontend_main_jsx()
    print("Patch v40.9.3 LAN mode completata.")


if __name__ == "__main__":
    main()
