# backend/ring1/geocode.py

import os
from googlemaps import Client

gmaps = Client(key=os.getenv("GOOGLE_API_KEY"))

def geocode_address(address: str) -> dict:
    if not address.strip():
        raise ValueError("Empty address")

    results = gmaps.geocode(address)
    if not results:
        raise ValueError("No results for address")

    loc = results[0]["geometry"]["location"]
    # for demo we fake a 50m×50m bbox around the point
    delta = 0.0005
    xmin = loc["lng"] - delta
    xmax = loc["lng"] + delta
    ymin = loc["lat"] - delta
    ymax = loc["lat"] + delta

    return {"bbox": [xmin, ymin, xmax, ymax]}
