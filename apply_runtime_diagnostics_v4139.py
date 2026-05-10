from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"

PATCH = r'''

# ---------------------------------------------------------------------------
# v41.3.9 - Runtime diagnostics
# ---------------------------------------------------------------------------

@app.get("/api/debug/runtime")
def debug_runtime_info():
    import os
    import sys
    import platform
    import inspect
    from pathlib import Path

    try:
        import app.legacy_logic as legacy_logic_module
        legacy_file = inspect.getfile(legacy_logic_module)
    except Exception as e:
        legacy_file = f"ERROR: {e}"

    try:
        main_file = __file__
    except Exception:
        main_file = "unknown"

    routes = []
    try:
        for r in app.routes:
            methods = sorted(list(getattr(r, "methods", []) or []))
            path = getattr(r, "path", "")
            if path:
                routes.append({"path": path, "methods": methods})
    except Exception as e:
        routes.append({"error": str(e)})

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

    return {
        "ok": True,
        "diagnostic": "v41.3.9",
        "cwd": os.getcwd(),
        "sys_executable": sys.executable,
        "platform": platform.platform(),
        "python_version": sys.version,
        "main_file": str(main_file),
        "legacy_logic_file": str(legacy_file),
        "frontend_dist_found": bool(found),
        "frontend_dist": str(found) if found else None,
        "checked_frontend_paths": checked,
        "routes_sample": routes[:200],
        "has_catalog_areas_get": any(r.get("path") == "/api/catalog/areas" and "GET" in r.get("methods", []) for r in routes if isinstance(r, dict)),
        "has_catalog_areas_post": any(r.get("path") == "/api/catalog/areas" and "POST" in r.get("methods", []) for r in routes if isinstance(r, dict)),
        "has_debug_static": any(r.get("path") == "/api/debug/static" for r in routes if isinstance(r, dict)),
    }
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    if "v41.3.9 - Runtime diagnostics" not in s:
        marker = '@app.get("/api/health")'
        if marker in s:
            s = s.replace(marker, PATCH.strip() + "\n\n" + marker, 1)
        else:
            s += "\n\n" + PATCH.strip() + "\n"

    MAIN.write_text(s, encoding="utf-8")
    print("Endpoint /api/debug/runtime aggiunto.")

if __name__ == "__main__":
    main()
