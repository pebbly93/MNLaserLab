from pathlib import Path
import re

MAIN = Path("backend/app/main.py")

SAFE_ROUTES = r'''
# ---------------------------------------------------------------------------
# v42.0.4 - Single safe frontend route for Browser Edition
# ---------------------------------------------------------------------------

def mn_browser_dist():
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates += [
            Path(sys._MEIPASS) / "frontend" / "dist",
            Path(sys._MEIPASS) / "dist",
        ]

    checked = []
    for p in candidates:
        try:
            checked.append(str(p))
            if p.exists() and (p / "index.html").exists():
                return p, checked
        except Exception as e:
            checked.append(f"{p} ERROR {e}")

    return None, checked


@app.get("/api/debug/browser-dist")
def mn_debug_browser_dist():
    dist, checked = mn_browser_dist()
    assets = []
    if dist and (dist / "assets").exists():
        assets = sorted([p.name for p in (dist / "assets").glob("*")])

    return {
        "ok": True,
        "dist_found": bool(dist),
        "dist": str(dist) if dist else None,
        "checked": checked,
        "assets_count": len(assets),
        "assets_sample": assets[:30],
    }


@app.get("/assets/{asset_path:path}")
def mn_browser_assets(asset_path: str):
    from fastapi.responses import FileResponse, Response
    import mimetypes

    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")

    dist, checked = mn_browser_dist()
    if not dist:
        return Response("frontend/dist non trovato\n" + "\n".join(checked), status_code=404, media_type="text/plain")

    file_path = (dist / "assets" / asset_path).resolve()
    assets_dir = (dist / "assets").resolve()

    try:
        file_path.relative_to(assets_dir)
    except Exception:
        return Response("invalid asset path", status_code=403, media_type="text/plain")

    if not file_path.exists():
        return Response(f"asset not found: {asset_path}", status_code=404, media_type="text/plain")

    media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return FileResponse(file_path, media_type=media_type)


@app.get("/")
def mn_browser_index():
    from fastapi.responses import FileResponse, Response

    dist, checked = mn_browser_dist()
    if not dist:
        return Response(
            "frontend/dist non trovato.\n\nPercorsi controllati:\n" + "\n".join(checked),
            status_code=404,
            media_type="text/plain",
        )

    index = dist / "index.html"
    if not index.exists():
        return Response(f"index.html non trovato in {dist}", status_code=404, media_type="text/plain")

    return FileResponse(index, media_type="text/html")


@app.get("/{full_path:path}")
def mn_browser_spa(full_path: str):
    from fastapi.responses import FileResponse, Response

    if full_path.startswith("api/"):
        return Response("api route not found", status_code=404, media_type="text/plain")

    if full_path.startswith("assets/"):
        return Response(f"asset not found: {full_path}", status_code=404, media_type="text/plain")

    dist, checked = mn_browser_dist()
    if not dist:
        return Response(
            "frontend/dist non trovato.\n\nPercorsi controllati:\n" + "\n".join(checked),
            status_code=404,
            media_type="text/plain",
        )

    return FileResponse(dist / "index.html", media_type="text/html")
'''

def strip_frontend_routes(s: str) -> str:
    # Rimuove tutte le vecchie route frontend/browser duplicate.
    patterns = [
        r'\n# -{20,}\n# v42\.0\.[\s\S]*?(?=\n# -{20,}|\n@app\.|\Z)',
        r'\n@app\.get\("/"\)\ndef [\s\S]*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)',
        r'\n@app\.get\("/assets/\{asset_path:path\}"\)\ndef [\s\S]*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)',
        r'\n@app\.get\("/\{full_path:path\}"\)\ndef [\s\S]*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)',
        r'\n@app\.get\("/api/debug/browser-dist"\)\ndef [\s\S]*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)',
    ]

    for pat in patterns:
        s = re.sub(pat, "\n", s, flags=re.DOTALL)

    return s

def main():
    s = MAIN.read_text(encoding="utf-8")

    # Assicura Path dopo eventuale __future__.
    if "from pathlib import Path" not in s:
        lines = s.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from __future__ import"):
                insert_at = i + 1
        lines.insert(insert_at, "from pathlib import Path")
        s = "\n".join(lines) + "\n"

    s = strip_frontend_routes(s)

    # Le nuove route vanno in fondo, dopo tutte le API.
    s = s.rstrip() + "\n\n" + SAFE_ROUTES.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Fix v42.0.4 applicato: una sola route frontend sicura.")

if __name__ == "__main__":
    main()
