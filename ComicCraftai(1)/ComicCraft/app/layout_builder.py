from __future__ import annotations

from pathlib import Path


def build_comic_layout(
    image_paths: list[str],
    story: list[dict],
    outline: list[dict],
) -> list[dict]:
    """Merge image files, story panels, and outline metadata into renderable layout records."""
    if not (len(image_paths) == len(story) == len(outline) == 5):
        raise ValueError("ComicCraft expects exactly five image paths, story panels, and outline panels.")

    story_by_panel = {panel["panel"]: panel for panel in story}
    outline_by_panel = {panel["panel"]: panel for panel in outline}
    layout = []

    for panel_number in range(1, 6):
        story_panel = story_by_panel[panel_number]
        outline_panel = outline_by_panel[panel_number]
        image_path = str(Path(image_paths[panel_number - 1]).resolve())
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Generated image not found: {image_path}")

        dialogue = story_panel.get("dialogue", [])
        layout.append(
            {
                "panel": panel_number,
                "title": story_panel.get("title") or outline_panel["title"],
                "image_path": image_path,
                "image_url": f"/static/panels/{Path(image_path).name}",
                "scene_description": story_panel.get("scene_description") or outline_panel["scene_description"],
                "caption": story_panel.get("caption", ""),
                "narration": story_panel.get("narration", ""),
                "dialogue": dialogue,
                "image_prompt": outline_panel["image_prompt"],
            }
        )
    return layout
