from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import PANEL_DIR, STATIC_DIR, ensure_directories, get_settings
from .routes import router

ensure_directories()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI comic story and illustration generator built with FastAPI, Gemini, and Stable Diffusion/Hugging Face.",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)


@app.get("/api")
def api_root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "generate": "/generate-comic/json",
        "test_image": "/test-image",
    }
