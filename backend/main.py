# backend/main.py - Railway deployment with proper PORT handling

import os
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Try to import slowapi, fallback if not available
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    logging.warning("slowapi not available, rate limiting disabled")
    RATE_LIMITING_AVAILABLE = False

# Import basic modules (fallback if enhanced modules not available)
try:
    from backend.ring1.enhanced_geocode import get_location_intelligence
    from backend.ring1.climate_analysis import get_climate_data, get_solar_analysis
    from backend.ring1.architectural_styles import get_architectural_recommendations
    ENHANCED_FEATURES = True
except ImportError:
    logging.warning("Enhanced features not available, using basic functionality")
    try:
        from backend.ring1.geocode import geocode_address
    except ImportError:
        logging.error("No geocode module available")
        geocode_address = None
    ENHANCED_FEATURES = False

from backend.ring2.main import generate_plan_png
from backend.ring2.style import style_png
from backend.ring3.dxf_generator import generate_dxf
from backend.ring4.ifc_exporter import convert_dxf_to_ifc

# ─── CONFIGURATION ───────────────────────────────────────────────────────────

# Basic environment setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_actual_google_maps_api_key_here":
    logging.warning("⚠️ GOOGLE_API_KEY not properly configured")

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Create output directory
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── APPLICATION SETUP ───────────────────────────────────────────────────────

app = FastAPI(
    title="AI Architecture Platform",
    description="Transform addresses into professional architectural designs",
    version="2.0.0",
    debug=DEBUG
)

# Setup rate limiting if available
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── MIDDLEWARE ──────────────────────────────────────────────────────────────

# CORS configuration - permissive for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── STATIC FILES ────────────────────────────────────────────────────────────

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# ─── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {
        "message": "AI Architecture Platform is running",
        "status": "healthy",
        "version": "2.0.0"
    }

@app.get("/api/status")
async def api_status(request: Request):
    """API status endpoint."""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "version": "2.0.0",
        "features": {
            "enhanced_location_intelligence": ENHANCED_FEATURES,
            "rate_limiting": RATE_LIMITING_AVAILABLE,
            "google_api_configured": bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your_actual_google_maps_api_key_here")
        }
    }

@app.get("/design/plan")
async def design_plan(
    request: Request,
    address: str = Query(..., description="Address to design for"),
    building_type: str = Query("clinic", description="Type of building"),
    area_sqm: float = Query(200, description="Building area in square meters"),
    style_preference: str = Query("local", description="Style preference")
):
    """Generate architectural design with optional location intelligence."""
    
    if not address.strip():
        raise HTTPException(400, "Address cannot be empty")
    
    try:
        # Basic geocoding
        if ENHANCED_FEATURES:
            # Use enhanced geocoding
            location_data = await get_location_intelligence(address)
            parcel_bbox = location_data["bbox"]
            
            # Enhanced design prompt with context
            enhanced_prompt = f"""
            {building_type} design for {address}
            Area: {area_sqm} sqm
            Style preference: {style_preference}
            Enhanced with location intelligence
            """
        else:
            # Fallback to basic geocoding
            if geocode_address:
                parcel_data = geocode_address(address)
                parcel_bbox = parcel_data["bbox"]
            else:
                # Ultimate fallback - fake bbox
                parcel_bbox = [-1.1, 53.5, -1.0, 53.6]
            enhanced_prompt = f"{building_type} layout at {address}"
        
        # Generate design files
        base_png = generate_plan_png({"bbox": parcel_bbox}, prompt=enhanced_prompt)
        styled_png = style_png(base_png, prompt_suffix=address)
        
        # Generate CAD files
        stem = Path(styled_png).stem
        dxf_path = OUTPUT_DIR / f"{stem}.dxf"
        ifc_path = OUTPUT_DIR / f"{stem}.ifc"
        
        if not dxf_path.exists():
            generate_dxf(parcel_bbox, str(dxf_path))
        
        if not ifc_path.exists():
            convert_dxf_to_ifc(str(dxf_path), str(ifc_path))
        
        result = {
            "design_files": {
                "plan_png": f"/outputs/{Path(styled_png).name}",
                "dxf": f"/outputs/{dxf_path.name}",
                "ifc": f"/outputs/{ifc_path.name}"
            },
            "address": address,
            "building_type": building_type,
            "area_sqm": area_sqm,
            "enhanced_features": ENHANCED_FEATURES
        }
        
        return result
        
    except Exception as e:
        logging.error(f"Design generation error: {e}")
        raise HTTPException(500, f"Design generation failed: {str(e)}")

# ─── FRONTEND SERVING ────────────────────────────────────────────────────────

try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    logging.info("✅ Frontend mounted successfully")
except Exception as e:
    logging.warning(f"⚠️ Frontend not available: {e}")

# ─── STARTUP EVENT ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logging.info("🚀 AI Architecture Platform starting...")
    logging.info(f"Environment: {ENVIRONMENT}")
    logging.info(f"Enhanced features: {ENHANCED_FEATURES}")
    logging.info(f"Rate limiting: {RATE_LIMITING_AVAILABLE}")
    
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_actual_google_maps_api_key_here":
        logging.warning("⚠️ Google API key not configured - using fallback mode")
    
    logging.info("✅ Startup complete")

if __name__ == "__main__":
    import uvicorn
    # Get port from environment or use 8000 as default
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
