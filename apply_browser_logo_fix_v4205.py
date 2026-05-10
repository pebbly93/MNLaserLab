from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"
FRONTEND_PUBLIC = ROOT / "frontend" / "public"
FRONTEND_DIST = ROOT / "frontend" / "dist"
DESKTOP_LOGO = ROOT / "desktop" / "assets" / "mn_laser_lab_logo.png"

PATCH = r'''
# ---------------------------------------------------------------------------
# v42.0.5 - Browser Edition logo/static public files
# ---------------------------------------------------------------------------

def mn_find_public_file(filename):
    from pathlib import Path
    import sys

    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist" / filename,
        here.parents[2] / "frontend" / "public" / filename,
        here.parents[2] / "desktop" / "assets" / filename,
        here.parents[1] / "frontend" / "dist" / filename,
        here.parents[1] / "frontend" / "public" / filename,
        Path.cwd() / "frontend" / "dist" / filename,
        Path.cwd() / "frontend" / "public" / filename,
        Path.cwd() / "desktop" / "assets" / filename,
        Path.cwd() / filename,
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates += [
            Path(sys._MEIPASS) / "frontend" / "dist" / filename,
            Path(sys._MEIPASS) / "frontend" / "public" / filename,
            Path(sys._MEIPASS) / "desktop" / "assets" / filename,
            Path(sys._MEIPASS) / filename,
        ]

    for p in candidates:
        try:
            if p.exists() and p.is_file():
                return p
        except Exception:
            pass

    return None


@app.get("/mn_laser_lab_logo.png")
def mn_logo_png():
    from fastapi.responses import FileResponse, Response

    p = mn_find_public_file("mn_laser_lab_logo.png")
    if p:
        return FileResponse(p, media_type="image/png")

    return Response("logo not found", status_code=404, media_type="text/plain")


@app.get("/logo.png")
def mn_logo_png_alias():
    from fastapi.responses import FileResponse, Response

    p = mn_find_public_file("mn_laser_lab_logo.png") or mn_find_public_file("logo.png")
    if p:
        return FileResponse(p, media_type="image/png")

    return Response("logo not found", status_code=404, media_type="text/plain")


@app.get("/favicon.ico")
def mn_favicon_ico():
    from fastapi.responses import FileResponse, Response

    p = mn_find_public_file("favicon.ico")
    if p:
        return FileResponse(p, media_type="image/x-icon")

    return Response(status_code=204)


@app.get("/api/debug/logo")
def mn_debug_logo():
    p = mn_find_public_file("mn_laser_lab_logo.png")
    return {
        "ok": True,
        "found": bool(p),
        "path": str(p) if p else None,
    }
'''

def copy_logo_to_frontend():
    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)

    targets = [
        FRONTEND_PUBLIC / "mn_laser_lab_logo.png",
    ]

    possible_sources = [
        DESKTOP_LOGO,
        ROOT / "mn_laser_lab_logo.png",
        ROOT / "frontend" / "src" / "assets" / "mn_laser_lab_logo.png",
    ]

    src = None
    for p in possible_sources:
        if p.exists():
            src = p
            break

    if src:
        for t in targets:
            shutil.copyfile(src, t)
        print(f"Logo copiato da {src} a frontend/public/mn_laser_lab_logo.png")
    else:
        print("Logo sorgente non trovato: salto copia file.")

def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    if "v42.0.5 - Browser Edition logo/static public files" not in s:
        # Inserisce prima del catch-all SPA se presente.
        marker = '@app.get("/{full_path:path}")'
        if marker in s:
            s = s.replace(marker, PATCH.strip() + "\n\n" + marker, 1)
        else:
            s += "\n\n" + PATCH.strip() + "\n"

        MAIN.write_text(s, encoding="utf-8")
        print("Route logo aggiunte.")
    else:
        print("Route logo già presenti.")

def main():
    copy_logo_to_frontend()
    patch_main()
    print("Patch v42.0.5 completata.")

if __name__ == "__main__":
    main()
