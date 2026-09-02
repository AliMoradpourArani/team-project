"""Serve the production frontend from the FastAPI process when a build is present."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..database.connection import REPOSITORY_ROOT


def _frontend_dist() -> Path:
    configured = os.getenv("FRONTEND_DIST_PATH")
    return Path(configured).resolve() if configured else (REPOSITORY_ROOT / "frontend" / "dist").resolve()


def install_frontend(app: FastAPI, dist_root: Path | None = None) -> None:
    """Attach SPA/static routes if a production frontend build is available."""
    root = (dist_root or _frontend_dist()).resolve()
    index = root / "index.html"
    if not index.is_file():
        return

    assets = root / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return FileResponse(index)

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_fallback(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = (root / full_path).resolve()
        if candidate != root and root in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
