from __future__ import annotations

from .config import get_settings
from .gemini_client import GeminiClient
from .schemas import ComicRequest, ComicStory


def generate_story(outline: list[dict], request: ComicRequest) -> list[dict]:
    """Expand the five outline panels into narration, captions, and dialogue."""
    settings = get_settings()
    if settings.image_provider == "mock":
        return [
            {
                "panel": panel["panel"],
                "title": panel["title"],
                "scene_description": panel["scene_description"],
                "caption": f"Meanwhile, the {request.setting} grows quieter as the story moves to panel {panel['panel']}...",
                "narration": (
                    f"{request.character_name} faces the next challenge with a {request.tone} spirit. "
                    f"The moment changes everything and pushes the adventure toward its conclusion."
                ),
                "dialogue": [f"{request.character_name}: We keep going!"] if panel["panel"] % 2 else [
                    f"{request.character_name}: I think I know what to do."
                ],
            }
            for panel in outline
        ]

    prompt = f"""
You are the story-writing stage of ComicCraft.
Turn the following five-panel outline into a cohesive comic script.

Main character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}
Original story idea: {request.story_prompt}

Outline:
{outline}

Requirements:
- Return exactly five panels, numbered 1 through 5.
- Keep continuity across panels and preserve the outline's scene and title.
- Write concise comic narration that is easy to read beside artwork.
- Caption is a short ambient/environmental line.
- Dialogue should be a small list of short spoken lines; it can be empty when dialogue is unnecessary.
- Keep the tone consistent with the user's request.
- Do not put stage directions into dialogue.
""".strip()

    result = GeminiClient().generate_structured(settings.gemini_story_model, prompt, ComicStory)
    panels = sorted(result.panels, key=lambda p: p.panel)
    if [p.panel for p in panels] != [1, 2, 3, 4, 5]:
        raise ValueError("Gemini did not return exactly one story panel for each number 1-5.")
    return [panel.model_dump() for panel in panels]
