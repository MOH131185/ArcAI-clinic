# backend/ring3/dxf_generator.py

import ezdxf
from pathlib import Path

def generate_dxf(bbox: list, out_path: str):
    """
    A stub: draws the parcel bbox as a rectangle in DXF.
    """
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    xmin, ymin, xmax, ymax = bbox
    msp.add_lwpolyline([(xmin,ymin),(xmin,ymax),(xmax,ymax),(xmax,ymin),(xmin,ymin)])
    Path(out_path).parent.mkdir(exist_ok=True)
    doc.saveas(out_path)
