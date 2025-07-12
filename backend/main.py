# backend/main.py - Railway Production Version

import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports with fallbacks
try:
    from backend.ring1.geocode import geocode_address
    GEOCODING_AVAILABLE = True
except ImportError:
    logger.warning("Geocoding not available")
    GEOCODING_AVAILABLE = False

try:
    from backend.ring2.main import generate_plan_png
    from backend.ring2.style import style_png
    from backend.ring3.dxf_generator import generate_dxf
    from backend.ring4.ifc_exporter import convert_dxf_to_ifc
    GENERATION_AVAILABLE = True
except ImportError:
    logger.warning("File generation not available")
    GENERATION_AVAILABLE = False

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", 8000))

# Create directories
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="AI Architecture Platform",
    description="Transform addresses into professional architectural designs",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "🏗️ AI Architecture Platform",
        "status": "online",
        "version": "2.0.0",
        "features": {
            "geocoding": GEOCODING_AVAILABLE,
            "generation": GENERATION_AVAILABLE
        }
    }

@app.get("/api/status")
async def api_status():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "port": PORT,
        "features": {
            "geocoding": GEOCODING_AVAILABLE,
            "generation": GENERATION_AVAILABLE,
            "google_api": bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "AIzaSyA34NLQcrMsBNWG5CPTZjprRPnHH30EdyY")
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/design/plan")
async def design_plan(
    address: str = Query(...),
    building_type: str = Query("clinic"),
    area_sqm: float = Query(200),
    style_preference: str = Query("local")
):
    if not address.strip():
        raise HTTPException(400, "Address required")
    
    logger.info(f"Generating design for: {address}")
    
    try:
        # Basic geocoding or fallback
        if GEOCODING_AVAILABLE and GOOGLE_API_KEY:
            parcel = geocode_address(address)
            bbox = parcel["bbox"]
        else:
            # Fallback bbox (London area)
            bbox = [-0.1276, 51.5074, -0.1176, 51.5174]
            logger.warning("Using fallback bbox")
        
        if not GENERATION_AVAILABLE:
            raise HTTPException(500, "File generation not available")
        
        # Generate files
        prompt = f"{building_type} layout at {address}"
        base_png = generate_plan_png({"bbox": bbox}, prompt=prompt)
        styled_png = style_png(base_png, prompt_suffix=address)
        
        # Generate CAD files
        stem = Path(styled_png).stem
        dxf_path = OUTPUT_DIR / f"{stem}.dxf"
        ifc_path = OUTPUT_DIR / f"{stem}.ifc"
        
        if not dxf_path.exists():
            generate_dxf(bbox, str(dxf_path))
        
        if not ifc_path.exists():
            convert_dxf_to_ifc(str(dxf_path), str(ifc_path))
        
        return {
            "success": True,
            "design_files": {
                "plan_png": f"/outputs/{Path(styled_png).name}",
                "dxf": f"/outputs/{dxf_path.name}",
                "ifc": f"/outputs/{ifc_path.name}"
            },
            "project_info": {
                "address": address,
                "building_type": building_type,
                "area_sqm": area_sqm
            }
        }
        
    except Exception as e:
        logger.error(f"Design generation failed: {e}")
        raise HTTPException(500, f"Generation failed: {str(e)}")

# Mount frontend
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    logger.info("Frontend mounted")
except Exception as e:
    logger.error(f"Frontend mount failed: {e}")

# Startup event
@app.on_event("startup")
async def startup():
    logger.info(f"🚀 Starting AI Architecture Platform on port {PORT}")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Geocoding: {GEOCODING_AVAILABLE}")
    logger.info(f"Generation: {GENERATION_AVAILABLE}")

# Main execution
if __name__ == "__main__":
    import uvicorn
    logger.info(f"🚀 Running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
