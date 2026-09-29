from __future__ import annotations

from .config import get_settings
from .gemini_client import GeminiClient
from .schemas import ComicOutline, ComicRequest


def generate_outline(request: ComicRequest) -> list[dict]:
    """Generate the project's structured five-panel comic outline."""
    settings = get_settings()
    prompt = f"""
You are the comic planning stage of ComicCraft.
Create exactly 5 sequential comic panels from the user's idea.

User idea: {request.story_prompt}
Main character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}

Requirements:
- Keep the same main character and visual identity across all panels.
- Create a clear beginning, rising action, turning point, and resolution.
- Each scene description should explain what is visible and what is happening.
- Each image_prompt should be optimized for a text-to-image diffusion model.
- Put visual details in image_prompt: subject, action, environment, camera/composition, lighting, mood, and art style.
- Do not include written words, captions, speech bubbles, logos, watermarks, or UI text inside the generated artwork.
- Avoid copying any existing copyrighted character or franchise.
""".strip()

    if settings.image_provider == "mock":
        return [
            {
                "panel": i,
                "title": f"Panel {i}: {['The Beginning','A New Trail','The Turning Point','The Brave Choice','A New Dawn'][i-1]}",
                "scene_description": f"{request.character_name} moves the story forward in the {request.setting} during panel {i}.",
                "image_prompt": f"{request.character_name}, {request.setting}, panel {i}, {request.art_style}, {request.tone}, cinematic comic illustration, dynamic composition, consistent character design, no text",
            }
            for i in range(1, 6)
        ]

    result = GeminiClient().generate_structured(settings.gemini_outline_model, prompt, ComicOutline)
    panels = sorted(result.panels, key=lambda p: p.panel)
    if [p.panel for p in panels] != [1, 2, 3, 4, 5]:
        raise ValueError("Gemini did not return exactly one outline panel for each number 1-5.")
    return [panel.model_dump() for panel in panels]
