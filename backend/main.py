from dotenv import load_dotenv
import os

# Load .env in this folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from ring1.geocode import Geocoder

# Instantiate your Google geocoder
api_key = os.getenv("GOOGLE_GEOCODE_KEY")
geocoder = Geocoder(api_key=api_key)
@app.get("/geocode")
async def geocode(address: str):
    result = geocoder.geocode_address(address)
    return result
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
import os

# load the .env file next to this script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from ring1.geocode import Geocoder

api_key = os.getenv("GOOGLE_GEOCODE_KEY")
geocoder = Geocoder(api_key=api_key)

app = FastAPI()

@app.get("/geocode")
async def geocode(
    address: str = Query(
        ...,
        min_length=1,
        description="Place name or postal address",
    )
):
    try:
        return geocoder.geocode_address(address)
    except ValueError as ve:
        # bad input -> HTTP 400
        raise HTTPException(status_code=400, detail=str(ve))
