import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import clip
from PIL import Image

# 1) Load the CLIP model once
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL, PREPROCESS = clip.load("ViT-B/32", device=DEVICE)

def get_image_embedding(image_path: str) -> Optional[torch.Tensor]:
    """
    Load an image from disk, preprocess it, and return its CLIP embedding.
    Returns a 1D float32 tensor of length 512, or None on failure.
    """
    if not os.path.exists(image_path):
        print(f"⚠️ Image not found: {image_path}")
        return None
    try:
        img = Image.open(image_path).convert("RGB")
        x = PREPROCESS(img).unsqueeze(0).to(DEVICE)  # shape (1,3,224,224)
        with torch.no_grad():
            emb = MODEL.encode_image(x)                # (1,512)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb.squeeze(0).cpu()
    except Exception as e:
        print(f"⚠️ Error embedding {image_path}: {e}")
        return None

def get_text_embedding(text: str) -> Optional[torch.Tensor]:
    """
    Tokenize a text prompt and return its CLIP embedding.
    Returns a 1D float32 tensor of length 512, or None on failure.
    """
    try:
        tokens = clip.tokenize([text], truncate=True).to(DEVICE)  # (1, token_len)
        with torch.no_grad():
            emb = MODEL.encode_text(tokens)                        # (1,512)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb.squeeze(0).cpu()
    except Exception as e:
        print(f"⚠️ Error embedding text “{text}”: {e}")
        return None

def embed_images(image_dir: str, embeddings_file: str) -> Tuple[int, List[str]]:
    """
    Walk `image_dir`, embed each image, and write out a JSON map
    { filename: [floats], … } to `embeddings_file`.
    Returns (number_of_successes, list_of_skipped_filenames).
    """
    os.makedirs(os.path.dirname(embeddings_file), exist_ok=True)
    processed = 0
    skipped: List[str] = []
    results: Dict[str, List[float]] = {}

    for fn in sorted(os.listdir(image_dir)):
        path = os.path.join(image_dir, fn)
        emb = get_image_embedding(path)
        if emb is None:
            skipped.append(fn)
        else:
            results[fn] = emb.tolist()
            processed += 1

    with open(embeddings_file, "w") as f:
        json.dump(results, f)

    return processed, skipped

def load_embeddings(fname: str) -> Dict[str, torch.Tensor]:
    """
    Load embeddings from JSON at `fname`, supporting both:
    1) a dict { filename: [floats], … }
    2) a list [ { "filename":…, "embedding":[…] }, … ]
    Returns a dict filename→FloatTensor(512).
    """
    p = Path(fname)
    if not p.exists():
        raise FileNotFoundError(f"No embeddings file at {fname!r}")

    raw = json.loads(p.read_text())
    out: Dict[str, torch.Tensor] = {}

    if isinstance(raw, dict):
        # { filename: [floats], … }
        for fn, emb_list in raw.items():
            out[fn] = torch.tensor(emb_list, dtype=torch.float32)
    elif isinstance(raw, list):
        # [ { "filename":…, "embedding":[…] }, … ]
        for item in raw:
            fn = item["filename"]
            emb_list = item["embedding"]
            out[fn] = torch.tensor(emb_list, dtype=torch.float32)
    else:
        raise ValueError(f"Unexpected embeddings format in {fname!r}")

    return out

def search_embeddings(
    embeddings: Dict[str, torch.Tensor],
    query: str,
    k: int = 5
) -> List[Dict[str, float]]:
    """
    Given a map filename→embedding, embed `query` and
    return the top-k nearest pages as
    [ {"filename":…, "score":…}, … ].
    """
    text_emb = get_text_embedding(query)
    if text_emb is None:
        return []

    # ensure both are float32
    text_emb = text_emb.to(torch.float32)
    results: List[Dict[str, float]] = []

    for fn, img_emb in embeddings.items():
        img_emb = img_emb.to(torch.float32)
        score = float(text_emb @ img_emb)
        results.append({"filename": fn, "score": score})

    # sort descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]
