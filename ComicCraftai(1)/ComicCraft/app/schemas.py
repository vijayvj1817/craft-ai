from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


TONE_OPTIONS = ("light-hearted", "dramatic", "poetic", "funny")
STYLE_OPTIONS = ("anime", "pixel art", "comic book", "realistic")
SETTING_OPTIONS = ("school", "forest", "space", "city")


class ComicRequest(BaseModel):
    story_prompt: str = Field(min_length=5, max_length=1200)
    character_name: str = Field(min_length=1, max_length=80)
    setting: str = Field(min_length=1, max_length=80)
    tone: str = Field(min_length=1, max_length=40)
    art_style: str = Field(min_length=1, max_length=60)

    @field_validator("story_prompt", "character_name", "setting", "tone", "art_style")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value


class PanelOutline(BaseModel):
    panel: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=120)
    scene_description: str = Field(min_length=1, max_length=800)
    image_prompt: str = Field(min_length=1, max_length=1400)


class ComicOutline(BaseModel):
    panels: List[PanelOutline] = Field(min_length=5, max_length=5)


class StoryPanel(BaseModel):
    panel: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=120)
    scene_description: str = Field(min_length=1, max_length=800)
    caption: str = Field(min_length=1, max_length=500)
    narration: str = Field(min_length=1, max_length=1400)
    dialogue: List[str] = Field(min_length=0, max_length=6)


class ComicStory(BaseModel):
    panels: List[StoryPanel] = Field(min_length=5, max_length=5)


class LayoutPanel(BaseModel):
    panel: int
    title: str
    image_path: str
    image_url: str
    scene_description: str
    caption: str
    narration: str
    dialogue: List[str]
    image_prompt: str


class ComicResult(BaseModel):
    title: str
    request: ComicRequest
    layout: List[LayoutPanel]
    pdf_path: str
    pdf_url: str
