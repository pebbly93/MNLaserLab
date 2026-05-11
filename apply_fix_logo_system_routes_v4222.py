from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

PATCH = r'''
# ---------------------------------------------------------------------------
# v42.2.2 - Safe logo and system APIs before SPA fallback
# ---------------------------------------------------------------------------

@app.get("/api/system/version")
def mn_system_version_api_safe():
    return {
        "ok": True,
        "current_version": "42.2.2",
        "channel": "browser-edition",
        "automatic_updates": False,
        "message": "Aggiornamenti automatici non ancora attivi. Usa il pacchetto Browser Edition aggiornato dalla release GitHub.",
    }


@app.get("/api/system/status")
def mn_system_status_api_safe():
    import os
    import sys
    import socket
    import platform
    from datetime import datetime

    def get_lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    db = load_db()
    port = int(os.environ.get("MN_BACKEND_PORT", "8000"))
    lan_ip = get_lan_ip()

    return {
        "ok": True,
        "app": "MN Laser Lab Manager",
        "edition": "Browser Edition",
        "version": "42.2.2",
        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "port": port,
        "local_url": f"http://127.0.0.1:{port}/",
        "lan_ip": lan_ip,
        "lan_url": f"http://{lan_ip}:{port}/",
        "db_counts": {
            "materials": len(db.get("materials", {}) or {}),
            "components": len(db.get("components", {}) or {}),
            "products": len(db.get("products", {}) or {}),
            "quotes": len(db.get("quotes", []) or []),
            "customers": len(db.get("customers", {}) or {}),
            "suppliers": len(db.get("suppliers", {}) or {}),
            "sales": len(db.get("sales", []) or []),
        },
    }


def mn_logo_svg_response():
    from fastapi.responses import Response

    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <rect width="120" height="120" rx="28" fill="#ffffff"/>
      <circle cx="60" cy="60" r="45" fill="none" stroke="#0f172a" stroke-width="4" opacity=".16"/>
      <path d="M24 72V43h12l12 16 12-16h12v34H60V60L50 73h-5L36 60v17H24z" fill="#0f172a"/>
      <path d="M76 43h22v11H88v23H76z" fill="#058482"/>
      <path d="M30 86c15 8 48 8 62-2" fill="none" stroke="#058482" stroke-width="6" stroke-linecap="round"/>
    </svg>"""

    return Response(
        svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/mn_laser_lab_logo.png")
def mn_logo_png_safe():
    # Manteniamo il vecchio URL richiesto dal frontend, ma rispondiamo con SVG valido.
    return mn_logo_svg_response()


@app.get("/logo.png")
def mn_logo_png_alias_safe():
    return mn_logo_svg_response()


@app.get("/api/debug/logo")
def mn_debug_logo_safe():
    return {
        "ok": True,
        "mode": "embedded-svg-fallback",
        "url": "/mn_laser_lab_logo.png",
    }
'''

def remove_old_routes(s: str) -> str:
    route_names = [
        "mn_logo_png",
        "mn_logo_png_alias",
        "mn_favicon_ico",
        "browser_logo_png",
        "browser_favicon",
        "mn_debug_logo",
        "mn_system_version_api_safe",
        "mn_system_status_api_safe",
    ]

    for name in route_names:
        s = re.sub(
            rf"\n@app\.get\([^\n]+\)\ndef {name}\(.*?\):.*?(?=\n@app\.|\ndef |\n# -{{20,}}|\Z)",
            "\n",
            s,
            flags=re.DOTALL,
        )

    # Rimuove eventuali blocchi precedenti della stessa patch.
    s = re.sub(
        r"\n# -{20,}\n# v42\.2\.2 - Safe logo and system APIs before SPA fallback.*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)",
        "\n",
        s,
        flags=re.DOTALL,
    )

    return s

def main():
    s = MAIN.read_text(encoding="utf-8")
    s = remove_old_routes(s)

    # Inseriamo prima del catch-all SPA, altrimenti /api/system/version può finire intercettato male.
    marker = '@app.get("/{full_path:path}")'
    if marker in s:
        s = s.replace(marker, PATCH.strip() + "\n\n" + marker, 1)
    else:
        s += "\n\n" + PATCH.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Patch v42.2.2 applicata: logo fallback e API system sicure.")

if __name__ == "__main__":
    main()
