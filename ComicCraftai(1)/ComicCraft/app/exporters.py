from __future__ import annotations

import re
import unicodedata
import uuid
from pathlib import Path

from fpdf import FPDF

from .config import EXPORT_DIR


def _pdf_text(value: str) -> str:
    """Convert smart Unicode punctuation into text accepted by the built-in PDF font."""
    value = unicodedata.normalize("NFKD", value)
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u2026", "...")
    value = value.replace("\u00a0", " ")
    return value.encode("latin-1", "replace").decode("latin-1")


def save_pdf(layout: list[dict], comic_title: str = "ComicCraft Comic") -> str:
    """Write one page per panel and return the generated PDF path."""
    if len(layout) != 5:
        raise ValueError("ComicCraft PDF export expects five panels.")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"comic_{uuid.uuid4().hex[:12]}.pdf"
    pdf_path = EXPORT_DIR / filename

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_title(_pdf_text(comic_title))
    pdf.set_author("ComicCraft")

    for panel in layout:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, _pdf_text(f"Panel {panel['panel']}: {panel['title']}"), new_x="LMARGIN", new_y="NEXT", align="C")

        image_path = Path(panel["image_path"])
        if image_path.exists():
            # Fit a square image into the printable width while keeping margins.
            pdf.image(str(image_path), x=15, y=32, w=180, h=118, keep_aspect_ratio=True)
        else:
            pdf.set_xy(15, 60)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(180, 7, _pdf_text(f"Image missing: {image_path.name}"))

        pdf.set_y(157)
        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(180, 6, _pdf_text(panel.get("scene_description", "")))

        if panel.get("caption"):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(180, 6, _pdf_text(f"Caption: {panel['caption']}"))

        pdf.ln(1)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(180, 6, _pdf_text(panel.get("narration", "")))

        for line in panel.get("dialogue", []):
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(180, 6, _pdf_text(line))

    pdf.output(str(pdf_path))
    return str(pdf_path)
