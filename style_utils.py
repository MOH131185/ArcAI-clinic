import os
import json
import numpy as np
from fastapi import APIRouter
from typing import List

router = APIRouter()

# Load saved embeddings
with open("backend/clip_embeddings.json", "r") as f:
    EMBEDDINGS = json.load(f)

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

@router.get("/recommend-style")
def recommend_style(reference_image: str = "page7_10.jpeg", top_k: int = 5):
    reference_vector = np.array(EMBEDDINGS["embeddings"][reference_image])
    
    similarities = []
    for img_name, vec in EMBEDDINGS["embeddings"].items():
        if img_name != reference_image:
            similarity = cosine_similarity(reference_vector, np.array(vec))
            similarities.append((img_name, float(similarity)))
    
    # Sort by similarity and return top matches
    similarities.sort(key=lambda x: x[1], reverse=True)
    return {
        "reference": reference_image,
        "recommended_styles": similarities[:top_k]
    }
