from __future__ import annotations

import hashlib
import re
import threading
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import PANEL_DIR, get_settings

_diffusion_lock = threading.Lock()
_diffusion_pipeline = None


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")
    return value[:80] or "panel"


def _mock_image(prompt: str, output: Path, panel_number: int | None = None) -> None:
    width = get_settings().image_width
    height = get_settings().image_height
    img = Image.new("RGB", (width, height), (238, 242, 250))
    draw = ImageDraw.Draw(img)
    # Deliberately use a small, dependency-free visual so tests can cover the full pipeline.
    draw.rectangle((35, 35, width - 35, height - 35), outline=(35, 42, 58), width=6)
    draw.ellipse((width * 0.23, height * 0.18, width * 0.77, height * 0.72), outline=(51, 63, 91), width=8)
    draw.line((width * 0.25, height * 0.78, width * 0.75, height * 0.78), fill=(51, 63, 91), width=8)
    label = f"COMICCRAFT • PANEL {panel_number or '?'}"
    draw.text((50, height - 105), label, fill=(30, 35, 50))
    excerpt = re.sub(r"\s+", " ", prompt)[:90]
    draw.text((50, height - 75), excerpt, fill=(70, 77, 92))
    img.save(output, "PNG")


def _get_diffusion_pipeline():
    global _diffusion_pipeline
    if _diffusion_pipeline is not None:
        return _diffusion_pipeline

    with _diffusion_lock:
        if _diffusion_pipeline is not None:
            return _diffusion_pipeline
        try:
            import torch
            from diffusers import DiffusionPipeline
        except ImportError as exc:
            raise RuntimeError(
                "Local Diffusers mode requires torch, diffusers, transformers, and accelerate. "
                "Install requirements-local.txt."
            ) from exc

        settings = get_settings()
        device = settings.local_device
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        dtype = torch.float16 if device in {"cuda", "mps"} else torch.float32
        pipe = DiffusionPipeline.from_pretrained(
            settings.local_diffusion_model,
            torch_dtype=dtype,
            use_safetensors=True,
        )
        pipe = pipe.to(device)
        _diffusion_pipeline = pipe
        return pipe


def generate_image(prompt: str, filename: str | None = None, panel_number: int | None = None) -> str:
    """Generate an image and return its absolute filesystem path as a string."""
    settings = get_settings()
    PANEL_DIR.mkdir(parents=True, exist_ok=True)

    if filename:
        stem = sanitize_filename(Path(filename).stem)
    else:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        stem = f"panel_{panel_number or 'x'}_{digest}"
    output = PANEL_DIR / f"{stem}.png"

    provider = settings.image_provider.lower()
    if provider == "mock":
        _mock_image(prompt, output, panel_number)
        return str(output)

    if provider == "hf":
        token = settings.resolved_hf_token
        if not token:
            raise RuntimeError("HF_TOKEN/HF_API_KEY is not configured for Hugging Face image generation.")
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError("huggingface_hub is not installed.") from exc

        client = InferenceClient(api_key=token, provider=settings.hf_provider)
        image = client.text_to_image(
            prompt=prompt,
            negative_prompt="text, letters, words, logo, watermark, blurry, low quality, distorted anatomy",
            width=settings.image_width,
            height=settings.image_height,
            model=settings.hf_image_model,
        )
        image.save(output)
        return str(output)

    if provider == "diffusers":
        pipe = _get_diffusion_pipeline()
        image = pipe(
            prompt,
            negative_prompt="text, letters, words, logo, watermark, blurry, low quality, distorted anatomy",
            num_inference_steps=settings.local_image_steps,
            guidance_scale=settings.local_guidance_scale,
            height=settings.image_height,
            width=settings.image_width,
        ).images[0]
        image.save(output)
        return str(output)

    raise RuntimeError(f"Unknown IMAGE_PROVIDER: {settings.image_provider!r}. Use hf, diffusers, or mock.")
