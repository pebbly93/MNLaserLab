from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

PATCH_CODE = r'''

# ---------------------------------------------------------------------------
# v41.3.2 - Static assets hardening for Electron/browser
# Evita pagina bianca da Strict MIME type checking:
# /assets/*.js o /assets/*.css non devono mai ricevere index.html.
# ---------------------------------------------------------------------------

from fastapi import Request
from fastapi.responses import FileResponse, Response, JSONResponse
import mimetypes

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("application/wasm", ".wasm")


def _frontend_dist_dir():
    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        here.parents[2] / "dist",
        here.parents[1] / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    for p in candidates:
        if p.exists() and (p / "index.html").exists():
            return p

    return None


@app.middleware("http")
async def static_asset_mime_guard(request: Request, call_next):
    path = request.url.path

    # Se il frontend chiede un asset Vite, servilo come file reale.
    # Se manca, restituisci 404 testuale, NON index.html.
    if path.startswith("/assets/"):
        dist = _frontend_dist_dir()
        if not dist:
            return Response("Frontend dist not found", status_code=404, media_type="text/plain")

        file_path = (dist / path.lstrip("/")).resolve()

        try:
            file_path.relative_to(dist.resolve())
        except Exception:
            return Response("Invalid asset path", status_code=403, media_type="text/plain")

        if not file_path.exists() or not file_path.is_file():
            return Response(f"Asset not found: {path}", status_code=404, media_type="text/plain")

        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    response = await call_next(request)

    # Evita cache aggressiva sull'HTML principale.
    if path in ("", "/") or path.endswith("index.html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

    return response


@app.get("/api/debug/static")
def debug_static_assets():
    dist = _frontend_dist_dir()
    assets = []

    if dist and (dist / "assets").exists():
        assets = sorted([p.name for p in (dist / "assets").glob("*")])[:50]

    return {
        "frontend_dist_found": bool(dist),
        "frontend_dist": str(dist) if dist else None,
        "index_exists": bool(dist and (dist / "index.html").exists()),
        "assets_count": len(assets),
        "assets_sample": assets,
    }
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    if "v41.3.2 - Static assets hardening" not in s:
        # Serve Path import se non c'è.
        if "from pathlib import Path" not in s:
            s = "from pathlib import Path\n" + s

        s += "\n\n" + PATCH_CODE.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Patch v41.3.2 applicata: MIME/static assets guard + debug endpoint.")

if __name__ == "__main__":
    main()
