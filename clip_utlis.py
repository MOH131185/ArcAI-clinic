# clip_utils.py

import json
import os
from pathlib import Path

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

# device setup
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# load CLIP
MODEL_NAME = "openai/clip-vit-base-patch32"
MODEL = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
PROCESSOR = CLIPProcessor.from_pretrained(MODEL_NAME)

# where we store your embeddings
EMBEDDINGS_PATH = Path("static") / "clip_embeddings.json"


def get_image_embedding(image_path: str) -> torch.Tensor | None:
    """
    Load an image, preprocess it, and return its CLIP embedding (512-d float32 tensor).
    Returns None on failure.
    """
    if not os.path.exists(image_path):
        print(f"⚠️ Image not found: {image_path}")
        return None

    try:
        img = Image.open(image_path).convert("RGB")
        inputs = PROCESSOR(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            emb = MODEL.get_image_features(**inputs)  # shape (1, 512)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
        return emb.squeeze(0).cpu()
    except Exception as e:
        print(f"⚠️ Error embedding image '{image_path}': {e}")
        return None


def get_text_embedding(text: str) -> torch.Tensor | None:
    """
    Tokenize a text prompt and return its CLIP text embedding (512-d float32 tensor).
    Returns None on failure.
    """
    try:
        inputs = PROCESSOR(text=[text], return_tensors="pt", padding=True).to(DEVICE)
        with torch.no_grad():
            emb = MODEL.get_text_features(**inputs)  # shape (1, 512)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
        return emb.squeeze(0).cpu()
    except Exception as e:
        print(f"⚠️ Error embedding text “{text}”: {e}")
        return None


def load_embeddings() -> dict[str, list[float]]:
    """
    Load the embeddings JSON from disk (filename → 512-dim list).
    Raises FileNotFoundError if missing.
    """
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(f"No embeddings file at {EMBEDDINGS_PATH!r}")
    with open(EMBEDDINGS_PATH, "r") as f:
        return json.load(f)


def save_embeddings(embeddings: dict[str, list[float]]) -> None:
    """
    Write the embeddings dict to disk atomically.
    """
    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = EMBEDDINGS_PATH.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(embeddings, f)
    tmp_path.replace(EMBEDDINGS_PATH)
