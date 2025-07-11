# backend/ring1/geocode.py - Basic geocoding (fallback)

import os
from googlemaps import Client

# Initialize Google Maps client
try:
    gmaps = Client(key=os.getenv("AIzaSyA34NLQcrMsBNWG5CPTZjprRPnHH30EdyY"))
except Exception as e:
    print(f"Warning: Google Maps client initialization failed: {e}")
    gmaps = None

def geocode_address(address: str) -> dict:
    """
    Basic geocoding function for fallback compatibility.
    """
    if not address.strip():
        raise ValueError("Empty address")
    
    if not gmaps:
        raise ValueError("Google Maps API not available")
    
    try:
        results = gmaps.geocode(address)
        if not results:
            raise ValueError("No results for address")
        
        loc = results[0]["geometry"]["location"]
        
        # Create a bounding box around the point (50m×50m)
        delta = 0.0005
        xmin = loc["lng"] - delta
        xmax = loc["lng"] + delta
        ymin = loc["lat"] - delta
        ymax = loc["lat"] + delta
        
        return {
            "bbox": [xmin, ymin, xmax, ymax],
            "coordinates": {
                "lat": loc["lat"],
                "lng": loc["lng"]
            },
            "formatted_address": results[0]["formatted_address"]
        }
        
    except Exception as e:
        raise ValueError(f"Geocoding failed: {e}")
