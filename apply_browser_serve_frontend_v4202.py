from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

PATCH = r'''

# ---------------------------------------------------------------------------
# v42.0.2 - Browser Edition frontend serving
# Serve React/Vite dist directly from FastAPI without Electron.
# ---------------------------------------------------------------------------

from fastapi import Request
from fastapi.responses import FileResponse, Response
import mimetypes

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("application/wasm", ".wasm")


def browser_frontend_dist_dir():
    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
        Path(getattr(sys, "_MEIPASS", "")) / "frontend" / "dist" if hasattr(sys, "_MEIPASS") else None,
    ]

    for p in candidates:
        if not p:
            continue
        try:
            if p.exists() and (p / "index.html").exists():
                return p
        except Exception:
            pass

    return None


@app.get("/assets/{asset_path:path}")
def browser_assets(asset_path: str):
    dist = browser_frontend_dist_dir()
    if not dist:
        return Response("frontend dist not found", status_code=404, media_type="text/plain")

    file_path = (dist / "assets" / asset_path).resolve()

    try:
        file_path.relative_to((dist / "assets").resolve())
    except Exception:
        return Response("invalid asset path", status_code=403, media_type="text/plain")

    if not file_path.exists() or not file_path.is_file():
        return Response(f"asset not found: {asset_path}", status_code=404, media_type="text/plain")

    media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/mn_laser_lab_logo.png")
def browser_logo_png():
    dist = browser_frontend_dist_dir()
    if dist and (dist / "mn_laser_lab_logo.png").exists():
        return FileResponse(dist / "mn_laser_lab_logo.png", media_type="image/png")

    return Response("logo not found", status_code=404, media_type="text/plain")


@app.get("/favicon.ico")
def browser_favicon():
    dist = browser_frontend_dist_dir()
    if dist and (dist / "favicon.ico").exists():
        return FileResponse(dist / "favicon.ico", media_type="image/x-icon")

    return Response(status_code=204)


@app.get("/")
def browser_index():
    dist = browser_frontend_dist_dir()
    if not dist:
        return Response("frontend dist not found. Run: cd frontend && npm run build", status_code=404, media_type="text/plain")

    return FileResponse(
        dist / "index.html",
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/{full_path:path}")
def browser_spa_fallback(full_path: str, request: Request):
    # Non intercettare API.
    if full_path.startswith("api/"):
        return Response("api route not found", status_code=404, media_type="text/plain")

    # Non restituire index.html per asset mancanti: causerebbe Strict MIME type checking.
    if full_path.startswith("assets/"):
        return Response(f"asset not found: {full_path}", status_code=404, media_type="text/plain")

    dist = browser_frontend_dist_dir()
    if not dist:
        return Response("frontend dist not found. Run: cd frontend && npm run build", status_code=404, media_type="text/plain")

    return FileResponse(
        dist / "index.html",
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    if "v42.0.2 - Browser Edition frontend serving" in s:
        print("Patch già presente.")
        return

    if "from pathlib import Path" not in s:
        lines = s.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from __future__ import"):
                insert_at = i + 1
        lines.insert(insert_at, "from pathlib import Path")
        s = "\n".join(lines) + "\n"

    if "import sys" not in s:
        lines = s.splitlines()
        insert_at = 0
        for i, line in enumerate(lines[:80]):
            if line.startswith("from __future__ import") or line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, "import sys")
        s = "\n".join(lines) + "\n"

    # Inseriamo alla fine: le API già definite restano prioritarie.
    s += "\n\n" + PATCH.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Patch v42.0.2 applicata: FastAPI serve frontend/dist su /.")

if __name__ == "__main__":
    main()
