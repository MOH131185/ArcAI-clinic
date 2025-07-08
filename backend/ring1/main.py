# backend/ring1/main.py
from backend.ring1.geocode import geocode
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "outputs"
# ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_plan(address: str, prompt: str = "clinic layout") -> dict:
    """
    1. Geocode the address → {latitude, longitude, formatted_address}
    2. Draw a placeholder massing box and overlay prompt + location
    Returns JSON-serializable dict: {'plan_png': '<path>'}
    """
    # 1. Geocode
    loc = geocode(address)
    lat = loc["latitude"]
    lon = loc["longitude"]
    full_address = loc.get("formatted_address", "")

    # 2. Create blank canvas
    img = Image.new("RGB", (512, 512), color="white")
    draw = ImageDraw.Draw(img)

    # 3. Draw simple parcel box
    margin = 50
    draw.rectangle([margin, margin, 512 - margin, 512 - margin], outline="black", width=4)

    # 4. Overlay text
    font = ImageFont.load_default()
    text = f"{prompt} @ {full_address}"[:60]
    draw.text((margin + 5, margin + 5), text, fill="black", font=font)

    # 5. Save
    out_path = os.path.join(OUTPUT_DIR, "massing_demo.png")
    img.save(out_path)
    return {"plan_png": out_path}
from PIL import Image, ImageDraw
import os

def generate_plan(parcel: dict, prompt: str) -> str:
    """
    Create a very simple “massing” PNG demo:
      • parcel is the dict your geocoder returned (must contain a “bbox”: [xmin,ymin,xmax,ymax])
      • prompt is just a human label for naming the file
    Returns the path to the generated PNG.
    """
    # 1) Extract the bounding box
    try:
        xmin, ymin, xmax, ymax = parcel["bbox"]
    except (KeyError, ValueError, TypeError):
        raise ValueError("Invalid parcel data; expected parcel['bbox'] = [xmin,ymin,xmax,ymax]")

    # 2) Create a blank image and draw the box
    size = 512
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)

    # Transform world‐coords into image coords
    def to_img(x, y):
        # x → [0,size], y → [size,0]
        return (
            (x - xmin) / (xmax - xmin) * size,
            (ymax - y) / (ymax - ymin) * size
        )

    # four corners
    corners = [
        to_img(xmin, ymin),
        to_img(xmax, ymin),
        to_img(xmax, ymax),
        to_img(xmin, ymax),
    ]
    draw.polygon(corners, outline="black", fill=None)

    # 3) Save it out
    safe_name = prompt.strip().replace(" ", "_")
    out_path = os.path.join("outputs", f"{safe_name}.png")
    os.makedirs("outputs", exist_ok=True)
    img.save(out_path)

    return out_path
