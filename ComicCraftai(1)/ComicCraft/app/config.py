from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PANEL_DIR = STATIC_DIR / "panels"
EXPORT_DIR = STATIC_DIR / "exports"
TEMPLATE_DIR = BASE_DIR / "templates"


class Settings(BaseSettings):
    """Application configuration loaded from environment/.env."""

    app_name: str = "ComicCraft"
    app_version: str = "1.0.0"
    debug: bool = True

    gemini_api_key: str = ""
    gemini_outline_model: str = "gemini-3.8-flash"
    gemini_story_model: str = "gemini-2.5-pro"

    hf_token: str = ""
    # HF_API_KEY is retained for compatibility with the project documentation.
    hf_api_key: str = ""
    hf_provider: str = "auto"
    hf_image_model: str = "stabilityai/stable-diffusion-3.5-large"

    image_provider: str = "hf"  # hf | diffusers | mock
    local_diffusion_model: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    local_device: str = "auto"  # auto | cuda | mps | cpu
    local_image_steps: int = 20
    local_guidance_scale: float = 7.0

    image_width: int = 768
    image_height: int = 768
    image_timeout_seconds: int = 180

    panel_count: int = 5
    max_prompt_length: int = 1200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def resolved_hf_token(self) -> str:
        return self.hf_token or self.hf_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_directories() -> None:
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
