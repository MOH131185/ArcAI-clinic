# backend/ring2/style.py

from PIL import Image, ImageFilter
from pathlib import Path

def style_png(input_png: str, prompt_suffix: str) -> str:
    """
    Applies a mild blur as “style” and returns new filename.
    """
    img = Image.open(input_png)
    styled = img.filter(ImageFilter.GaussianBlur(2))

    stem = Path(input_png).stem
    out = Path("outputs") / f"{stem}_styled.png"
    styled.save(out)
    return str(out)
