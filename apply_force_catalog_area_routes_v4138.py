from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

ROUTES = r'''
# ---------------------------------------------------------------------------
# v41.3.8 - Forced catalog areas routes before SPA/static fallback
# ---------------------------------------------------------------------------

@app.get("/api/catalog/areas")
def forced_catalog_areas_api():
    db = load_db()
    return get_catalog_areas(db)


@app.post("/api/catalog/areas")
def forced_add_catalog_area_api(payload: Payload):
    def fn(db):
        return add_catalog_area(db, payload.data)
    return mutate(fn)


@app.delete("/api/catalog/areas/{name:path}")
def forced_delete_catalog_area_api(name: str):
    def fn(db):
        return delete_catalog_area(db, name)
    return mutate(fn)


@app.get("/api/debug/static")
def forced_debug_static_assets_api():
    from pathlib import Path
    import os

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    checked = []
    found = None

    for p in candidates:
        checked.append(str(p))
        if p.exists() and (p / "index.html").exists():
            found = p
            break

    assets = []
    if found and (found / "assets").exists():
        assets = sorted([x.name for x in (found / "assets").glob("*")])

    return {
        "ok": True,
        "frontend_dist_found": bool(found),
        "frontend_dist": str(found) if found else None,
        "cwd": os.getcwd(),
        "checked_paths": checked,
        "index_exists": bool(found and (found / "index.html").exists()),
        "assets_count": len(assets),
        "assets_sample": assets[:30],
    }
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    # Rimuove eventuale blocco v41.3.8 vecchio per evitare duplicati.
    s = re.sub(
        r"\n# -{75}\n# v41\.3\.8 - Forced catalog areas routes before SPA/static fallback.*?(?=\n@app\.|\ndef |\n# -{75}|\Z)",
        "\n",
        s,
        flags=re.DOTALL
    )

    # Inserisce subito prima della route /api/categories, quindi molto prima del fallback SPA.
    marker = '@app.get("/api/categories")'
    if marker not in s:
        marker = '@app.get("/api/taxonomy")'

    if marker not in s:
        raise RuntimeError("Non trovo un punto sicuro dove inserire le route forzate")

    s = s.replace(marker, ROUTES.strip() + "\n\n" + marker, 1)

    MAIN.write_text(s, encoding="utf-8")
    print("Route forzate /api/catalog/areas e /api/debug/static inserite prima delle API catalogo.")

if __name__ == "__main__":
    main()
