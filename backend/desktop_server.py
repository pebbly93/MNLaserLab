from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from app.main import app


def _frontend_dist() -> Path | None:
    env_path = os.environ.get("MN_DESKTOP_DIST", "").strip()
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    # Sviluppo: repo/backend/desktop_server.py -> repo/frontend/dist
    candidates.append(Path(__file__).resolve().parents[1] / "frontend" / "dist")
    # PyInstaller: cartella temporanea _MEIPASS, se inserita in futuro
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "frontend")
    for p in candidates:
        if p.exists() and (p / "index.html").exists():
            return p
    return None


dist = _frontend_dist()
if dist is not None:
    # Deve restare dopo le route /api definite in app.main.
    app.mount("/", StaticFiles(directory=str(dist), html=True), name="desktop_frontend")


if __name__ == "__main__":
    port = int(os.environ.get("MN_BACKEND_PORT", "8000"))
    uvicorn.run(app, host=os.environ.get("MN_BACKEND_HOST", "0.0.0.0"), port=port, log_level="info")
