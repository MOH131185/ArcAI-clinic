# backend/ring2/main.py

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def generate_plan_png(parcel: dict, prompt: str) -> str:
    """
    Creates a dummy massing diagram (PNG) with bbox and returns its path.
    """

    stem = prompt.replace(" ", "_").replace(",", "")
    out = Path("outputs") / f"{stem}.png"

    # simple white square with red bbox outline
    img = Image.new("RGB", (512, 512), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 462, 462], outline="red", width=4)

    img.save(out)
    return str(out)
