# backend/ring3/vectoriser.py

import os
import cv2
import numpy as np
import ezdxf

def raster_to_dxf(input_png: str, eps: float = 1.0, thresh: int = 200) -> str:
    """
    Take a clean massing‐layout PNG and vectorize its black/white edges into a DXF polyline file.

    - eps: approximation epsilon (smaller -> more points)
    - thresh: binary threshold level
    """
    # ensure outputs dir exists
    os.makedirs("outputs", exist_ok=True)

    # load image, convert to grayscale & binary
    img = cv2.imread(input_png, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not open {input_png}")
    _, bw = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY_INV)

    # find contours (external)
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # prepare DXF document
    base = os.path.splitext(os.path.basename(input_png))[0]
    dxf_path = os.path.join("outputs", f"{base}.dxf")
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # for each contour, approximate and add polyline
    for cnt in contours:
        # approximate to reduce points
        approx = cv2.approxPolyDP(cnt, eps, False)
        # convert to list of tuples
        pts = [(float(pt[0][0]), float(pt[0][1]), 0.0) for pt in approx]
        if len(pts) >= 2:
            msp.add_lwpolyline(pts, dxfattribs={"closed": True})

    doc.saveas(dxf_path)
    return dxf_path
