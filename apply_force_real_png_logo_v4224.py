from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

PATCH = r'''
# ---------------------------------------------------------------------------
# v42.2.4 - Force real PNG logo
# ---------------------------------------------------------------------------

def mn_real_png_logo_path():
    from pathlib import Path
    import sys

    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "public" / "mn_laser_lab_logo.png",
        here.parents[2] / "frontend" / "dist" / "mn_laser_lab_logo.png",
        here.parents[2] / "desktop" / "assets" / "mn_laser_lab_logo.png",
        Path.cwd() / "frontend" / "public" / "mn_laser_lab_logo.png",
        Path.cwd() / "frontend" / "dist" / "mn_laser_lab_logo.png",
        Path.cwd() / "desktop" / "assets" / "mn_laser_lab_logo.png",
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates += [
            Path(sys._MEIPASS) / "frontend" / "dist" / "mn_laser_lab_logo.png",
            Path(sys._MEIPASS) / "frontend" / "public" / "mn_laser_lab_logo.png",
            Path(sys._MEIPASS) / "desktop" / "assets" / "mn_laser_lab_logo.png",
        ]

    for p in candidates:
        try:
            if p.exists() and p.is_file() and p.stat().st_size > 100:
                return p
        except Exception:
            pass

    return None


@app.get("/mn_laser_lab_logo.png")
def mn_laser_lab_logo_real_png():
    from fastapi.responses import FileResponse, Response

    p = mn_real_png_logo_path()
    if p:
        return FileResponse(
            p,
            media_type="image/png",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    return Response("MN Laser Lab logo PNG not found", status_code=404, media_type="text/plain")


@app.get("/logo.png")
def mn_laser_lab_logo_real_png_alias():
    return mn_laser_lab_logo_real_png()


@app.get("/api/debug/logo")
def mn_laser_lab_logo_debug():
    p = mn_real_png_logo_path()
    return {
        "ok": True,
        "real_logo_found": bool(p),
        "path": str(p) if p else None,
        "mode": "real-png" if p else "missing",
        "url": "/mn_laser_lab_logo.png",
    }
'''

def remove_old_logo_routes(s: str) -> str:
    names = [
        "mn_logo_png_safe",
        "mn_logo_png_alias_safe",
        "mn_logo_png_real_preferred",
        "mn_logo_png_alias_real_preferred",
        "mn_debug_logo_safe",
        "mn_debug_logo_real_preferred",
        "mn_laser_lab_logo_real_png",
        "mn_laser_lab_logo_real_png_alias",
        "mn_laser_lab_logo_debug",
        "mn_logo_png",
        "mn_logo_png_alias",
    ]

    for name in names:
        s = re.sub(
            rf"\n@app\.get\([^\n]+\)\ndef {name}\(.*?\):.*?(?=\n@app\.|\ndef |\n# -{{20,}}|\Z)",
            "\n",
            s,
            flags=re.DOTALL,
        )

    return s

def main():
    s = MAIN.read_text(encoding="utf-8")
    s = remove_old_logo_routes(s)

    marker = '@app.get("/{full_path:path}")'
    if marker in s:
        s = s.replace(marker, PATCH.strip() + "\n\n" + marker, 1)
    else:
        s += "\n\n" + PATCH.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Patch v42.2.4 applicata: logo PNG reale forzato.")

if __name__ == "__main__":
    main()
