from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_ROOT = Path(__file__).resolve().parents[1] / "frontend"
FRONTEND_DIST = FRONTEND_ROOT / "dist"
FRONTEND_SRC = FRONTEND_ROOT / "src"


def get_frontend_directory() -> Path:
    if FRONTEND_DIST.exists():
        return FRONTEND_DIST
    return FRONTEND_SRC


def setup_frontend(app: FastAPI) -> None:
    frontend_directory = get_frontend_directory()
    app.mount(
        "/frontend",
        StaticFiles(directory=frontend_directory, html=True),
        name="frontend",
    )

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(frontend_directory / "index.html")

    @app.get("/profile", include_in_schema=False)
    async def profile() -> RedirectResponse:
        return RedirectResponse(url="/frontend/#profile")
