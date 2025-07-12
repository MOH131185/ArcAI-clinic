# backend/main.py - Fixed Frontend Mounting

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
    logger.info("✅ Geocoding available")
except ImportError:
    logger.warning("⚠️ Geocoding not available")
    GEOCODING_AVAILABLE = False

try:
    from backend.ring2.main import generate_plan_png
    from backend.ring2.style import style_png
    from backend.ring3.dxf_generator import generate_dxf
    from backend.ring4.ifc_exporter import convert_dxf_to_ifc
    GENERATION_AVAILABLE = True
    logger.info("✅ File generation available")
except ImportError:
    logger.warning("⚠️ File generation not available")
    GENERATION_AVAILABLE = False

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", 8000))

# Create directories
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Check frontend directory
FRONTEND_DIR = Path("frontend")
FRONTEND_HTML = FRONTEND_DIR / "index.html"

logger.info(f"Frontend directory exists: {FRONTEND_DIR.exists()}")
logger.info(f"Frontend index.html exists: {FRONTEND_HTML.exists()}")

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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Mount outputs first (before frontend)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
logger.info("✅ Outputs directory mounted")

# API Endpoints
@app.get("/api/status")
async def api_status():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "port": PORT,
        "frontend_available": FRONTEND_HTML.exists(),
        "features": {
            "geocoding": GEOCODING_AVAILABLE,
            "generation": GENERATION_AVAILABLE,
            "google_api": bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your_actual_google_maps_api_key_here")
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": "2025-01-12"}

@app.get("/design/plan")
async def design_plan(
    address: str = Query(..., description="Address to design for"),
    building_type: str = Query("clinic", description="Building type"),
    area_sqm: float = Query(200, description="Area in square meters"),
    style_preference: str = Query("local", description="Style preference")
):
    if not address.strip():
        raise HTTPException(400, "Address required")
    
    logger.info(f"🏗️ Generating design for: {address}")
    
    try:
        # Basic geocoding or fallback
        if GEOCODING_AVAILABLE and GOOGLE_API_KEY:
            parcel = geocode_address(address)
            bbox = parcel["bbox"]
            logger.info("✅ Using real geocoding")
        else:
            # Fallback bbox (London area)
            bbox = [-0.1276, 51.5074, -0.1176, 51.5174]
            logger.warning("⚠️ Using fallback bbox")
        
        if not GENERATION_AVAILABLE:
            raise HTTPException(500, "File generation modules not available")
        
        # Generate files
        prompt = f"{building_type} layout at {address} - {area_sqm} sqm"
        base_png = generate_plan_png({"bbox": bbox}, prompt=prompt)
        styled_png = style_png(base_png, prompt_suffix=f"{address}_{style_preference}")
        
        # Generate CAD files
        stem = Path(styled_png).stem
        dxf_path = OUTPUT_DIR / f"{stem}.dxf"
        ifc_path = OUTPUT_DIR / f"{stem}.ifc"
        
        if not dxf_path.exists():
            generate_dxf(bbox, str(dxf_path))
            
        if not ifc_path.exists():
            convert_dxf_to_ifc(str(dxf_path), str(ifc_path))
        
        result = {
            "success": True,
            "design_files": {
                "plan_png": f"/outputs/{Path(styled_png).name}",
                "dxf": f"/outputs/{dxf_path.name}",
                "ifc": f"/outputs/{ifc_path.name}"
            },
            "project_info": {
                "address": address,
                "building_type": building_type,
                "area_sqm": area_sqm,
                "style_preference": style_preference
            },
            "system_info": {
                "geocoding_used": GEOCODING_AVAILABLE and bool(GOOGLE_API_KEY),
                "generation_available": GENERATION_AVAILABLE
            }
        }
        
        logger.info(f"✅ Design generation completed for: {address}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Design generation failed: {e}")
        raise HTTPException(500, f"Generation failed: {str(e)}")

# Mount frontend LAST (very important!)
try:
    if FRONTEND_DIR.exists() and FRONTEND_HTML.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
        logger.info("✅ Frontend mounted successfully - beautiful interface available")
    else:
        logger.error(f"❌ Frontend not found. Directory exists: {FRONTEND_DIR.exists()}, HTML exists: {FRONTEND_HTML.exists()}")
        
        # Fallback root endpoint if frontend not available
        @app.get("/")
        async def root_fallback():
            return {
                "message": "🏗️ AI Architecture Platform",
                "status": "online",
                "version": "2.0.0",
                "frontend_status": "not_available",
                "api_endpoints": {
                    "status": "/api/status",
                    "health": "/api/health", 
                    "design": "/design/plan?address=your_address"
                },
                "note": "Frontend interface not available. API endpoints working."
            }
            
except Exception as e:
    logger.error(f"❌ Frontend mount error: {e}")
    
    # Fallback root endpoint
    @app.get("/")
    async def root_error():
        return {
            "message": "🏗️ AI Architecture Platform",
            "status": "online", 
            "frontend_error": str(e),
            "api_available": True
        }

# Startup event
@app.on_event("startup")
async def startup():
    logger.info("🚀" + "="*50)
    logger.info("🚀 AI ARCHITECTURE PLATFORM STARTING")
    logger.info("🚀" + "="*50)
    logger.info(f"🔧 Environment: {ENVIRONMENT}")
    logger.info(f"🔧 Port: {PORT}")
    logger.info(f"🔧 Geocoding: {GEOCODING_AVAILABLE}")
    logger.info(f"🔧 Generation: {GENERATION_AVAILABLE}")
    logger.info(f"🔧 Google API: {bool(GOOGLE_API_KEY)}")
    logger.info(f"🔧 Frontend dir: {FRONTEND_DIR.exists()}")
    logger.info(f"🔧 Frontend HTML: {FRONTEND_HTML.exists()}")
    logger.info("🚀" + "="*50)

# Main execution
if __name__ == "__main__":
    import uvicorn
    logger.info(f"🚀 Starting uvicorn server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
