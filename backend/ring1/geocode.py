import os
import requests
from dotenv import load_dotenv

# Load env vars from backend/.env
load_dotenv(override=True)

GOOGLE_KEY = os.getenv("GOOGLE_GEOCODE_KEY")
if not GOOGLE_KEY:
    raise RuntimeError("Missing GOOGLE_GEOCODE_KEY in environment")

class Geocoder:
    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def geocode_address(self, address: str) -> dict:
        address = address.strip()
        if not address:
            raise ValueError("Address must not be empty")

        params = {
            "address": address,
            "key": GOOGLE_KEY,
        }
        resp = requests.get(self.BASE_URL, params=params, timeout=5)
        data = resp.json()

        if data.get("status") != "OK":
            msg = data.get("error_message") or data.get("status")
            raise ValueError(f"Geocoding failed: {msg}")

        result = data["results"][0]
        loc    = result["geometry"]["location"]
        return {
            "latitude":           loc["lat"],
            "longitude":          loc["lng"],
            "formatted_address": result["formatted_address"],
        }

