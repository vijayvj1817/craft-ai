from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import EXPORT_DIR, TEMPLATE_DIR, ensure_directories, get_settings
from .exporters import save_pdf
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .schemas import ComicRequest, ComicResult

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def _title_from_request(request: ComicRequest) -> str:
    return f"{request.character_name}'s {request.tone.title()} Adventure"


def _run_pipeline(request: ComicRequest) -> ComicResult:
    settings = get_settings()
    if settings.image_provider != "mock" and not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")
    if settings.image_provider == "hf" and not settings.resolved_hf_token:
        raise HTTPException(status_code=503, detail="HF_TOKEN/HF_API_KEY is not configured.")

    try:
        outline = generate_outline(request)
        story = generate_story(outline, request)

        image_paths = []
        for panel in outline:
            prompt = (
                f"{panel['image_prompt']}. Main character named {request.character_name}. "
                f"Setting: {request.setting}. Tone: {request.tone}. "
                "Keep character appearance consistent across all five panels."
            )
            image_paths.append(generate_image(prompt, panel_number=panel["panel"]))

        layout = build_comic_layout(image_paths, story, outline)
        pdf_path = save_pdf(layout, comic_title=_title_from_request(request))
        return ComicResult(
            title=_title_from_request(request),
            request=request,
            layout=layout,
            pdf_path=pdf_path,
            pdf_url=f"/download/{Path(pdf_path).name}",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "tones": ["light-hearted", "dramatic", "poetic", "funny"],
            "styles": ["anime", "pixel art", "comic book", "realistic"],
            "settings": ["school", "forest", "space", "city"],
        },
    )


@router.post("/generate", response_class=HTMLResponse)
def generate_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    comic_request = ComicRequest(
        story_prompt=story_prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style,
    )
    result = _run_pipeline(comic_request)
    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context={"result": result.model_dump()},
    )


@router.post("/generate-comic/json", response_model=ComicResult)
def generate_json(comic_request: ComicRequest):
    return _run_pipeline(comic_request)


@router.get("/download/{filename}")
def download_pdf(filename: str):
    # Only a basename is accepted, and the resolved path must stay under EXPORT_DIR.
    candidate = (EXPORT_DIR / Path(filename).name).resolve()
    root = EXPORT_DIR.resolve()
    if candidate.parent != root or candidate.suffix.lower() != ".pdf" or not candidate.exists():
        raise HTTPException(status_code=404, detail="PDF not found.")
    return FileResponse(
        candidate,
        media_type="application/pdf",
        filename=candidate.name,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/export-success", response_class=HTMLResponse)
def export_success(request: Request, filename: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "filename": Path(filename).name if filename else None,
            "download_url": f"/download/{quote(Path(filename).name)}" if filename else None,
        },
    )


@router.get("/test-image", response_class=HTMLResponse)
def test_image_page(request: Request, prompt: str = "A brave fox exploring an enchanted forest, comic book art"):
    return templates.TemplateResponse(
        request=request,
        name="test_image.html",
        context={"prompt": prompt, "image_url": None},
    )


@router.post("/test-image", response_class=HTMLResponse)
def test_image(
    request: Request,
    prompt: str = Form(...),
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        image_path = generate_image(prompt.strip(), panel_number=0)
        image_url = f"/static/panels/{Path(image_path).name}"
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request=request,
        name="test_image.html",
        context={"prompt": prompt, "image_url": image_url},
    )


@router.get("/health")
def health():
    ensure_directories()
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "image_provider": settings.image_provider,
        "gemini_configured": bool(settings.gemini_api_key),
        "huggingface_configured": bool(settings.resolved_hf_token),
    }
