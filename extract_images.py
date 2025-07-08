# extract_images.py

import os
from typing import Tuple
from pdf2image import convert_from_path

def extract_images(pdf_path: str, out_dir: str) -> Tuple[int, int]:
    """
    Convert each page of `pdf_path` into a JPEG under `out_dir`.
    Returns a tuple (num_processed, num_skipped).
    """
    os.makedirs(out_dir, exist_ok=True)
    try:
        images = convert_from_path(pdf_path)
    except Exception as e:
        # if pdf2image can’t load the PDF
        print(f"⚠️ Error opening {pdf_path}: {e}")
        return 0, 0

    processed = 0
    skipped   = 0

    for i, img in enumerate(images, start=1):
        out_file = os.path.join(out_dir, f"page_{i}.jpg")
        try:
            img.save(out_file, format="JPEG")
            processed += 1
        except Exception as e:
            print(f"⚠️ Failed to save {out_file}: {e}")
            skipped += 1

    return processed, skipped

