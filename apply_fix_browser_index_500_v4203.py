from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

SAFE_CODE = r'''
# ---------------------------------------------------------------------------
# v42.0.3 - Safe Browser Edition frontend serving
# ---------------------------------------------------------------------------

def safe_browser_frontend_dist_dir():
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "frontend" / "dist")
        candidates.append(Path(sys._MEIPASS) / "dist")

    checked = []

    for p in candidates:
        try:
            checked.append(str(p))
            if p.exists() and (p / "index.html").exists():
                return p, checked
        except Exception as e:
            checked.append(f"{p} -> ERROR {e}")

    return None, checked


@app.get("/api/debug/browser-dist")
def debug_browser_dist_api():
    dist, checked = safe_browser_frontend_dist_dir()
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


@app.get("/browser-health")
def browser_health_api():
    return {"ok": True, "mode": "browser-edition", "route": "browser-health"}


@app.get("/")
def safe_browser_index():
    from fastapi.responses import FileResponse, Response

    dist, checked = safe_browser_frontend_dist_dir()

    if not dist:
        return Response(
            "frontend/dist non trovato.\n\nPercorsi controllati:\n" + "\n".join(checked),
            status_code=404,
            media_type="text/plain",
        )

    index = dist / "index.html"

    if not index.exists():
        return Response(
            f"index.html non trovato in: {dist}",
            status_code=404,
            media_type="text/plain",
        )

    return FileResponse(
        index,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    # Rimuove route duplicate @app.get("/") più vecchie per evitare conflitti.
    # Lascia API e altre route intatte.
    s = re.sub(
        r'\n@app\.get\("/"\)\ndef browser_index\(\):.*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)',
        '\n',
        s,
        flags=re.DOTALL
    )

    s = re.sub(
        r'\n@app\.get\("/"\)\ndef safe_browser_index\(\):.*?(?=\n@app\.|\ndef |\n# -{20,}|\Z)',
        '\n',
        s,
        flags=re.DOTALL
    )

    if "v42.0.3 - Safe Browser Edition frontend serving" not in s:
        # Deve stare alla fine, dopo tutte le API.
        s += "\n\n" + SAFE_CODE.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Patch v42.0.3 applicata: / sicuro e diagnostica /api/debug/browser-dist.")

if __name__ == "__main__":
    main()
