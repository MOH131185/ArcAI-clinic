# backend/main.py - Final Railway Deployment Version

import os
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import optional packages with graceful fallbacks
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
    logger.info("✅ Rate limiting available")
except ImportError:
    logger.warning("⚠️ slowapi not available, rate limiting disabled")
    RATE_LIMITING_AVAILABLE = False

# Try to import enhanced features with fallback to basic
try:
    from backend.ring1.enhanced_geocode import get_location_intelligence
    from backend.ring1.climate_analysis import get_climate_data, get_solar_analysis
    from backend.ring1.architectural_styles import get_architectural_recommendations
    ENHANCED_FEATURES = True
    logger.info("✅ Enhanced location intelligence available")
except ImportError:
    logger.warning("⚠️ Enhanced features not available, using basic functionality")
    try:
        from backend.ring1.geocode import geocode_address
        ENHANCED_FEATURES = False
        logger.info("✅ Basic geocoding available")
    except ImportError:
        logger.error("❌ No geocoding module available - using fallback")
        geocode_address = None
        ENHANCED_FEATURES = False

# Import core modules
try:
    from backend.ring2.main import generate_plan_png
    from backend.ring2.style import style_png
    from backend.ring3.dxf_generator import generate_dxf
    from backend.ring4.ifc_exporter import convert_dxf_to_ifc
    CORE_FEATURES_AVAILABLE = True
    logger.info("✅ Core generation features available")
except ImportError as e:
    logger.error(f"❌ Core features not available: {e}")
    CORE_FEATURES_AVAILABLE = False

# ─── CONFIGURATION ───────────────────────────────────────────────────────────

# Environment configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", 8000))

# Validate configuration
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_actual_google_maps_api_key_here":
    logger.warning("⚠️ GOOGLE_API_KEY not properly configured - some features may not work")
    API_CONFIGURED = False
else:
    API_CONFIGURED = True
    logger.info("✅ Google API key configured")

# Create output directory
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
logger.info(f"✅ Output directory created: {OUTPUT_DIR}")

# ─── APPLICATION SETUP ───────────────────────────────────────────────────────

app = FastAPI(
    title="AI Architecture Platform",
    description="Transform addresses into professional architectural designs with location intelligence",
    version="2.0.0",
    debug=DEBUG,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

# Setup rate limiting if available
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ Rate limiting configured")

# ─── MIDDLEWARE ──────────────────────────────────────────────────────────────

# CORS configuration - permissive for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
logger.info("✅ CORS middleware configured")

# ─── STATIC FILES ────────────────────────────────────────────────────────────

# Serve generated output files
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
logger.info("✅ Output files mounted at /outputs")

# ─── UTILITY FUNCTIONS ───────────────────────────────────────────────────────

def apply_rate_limit(endpoint_func):
    """Apply rate limiting if available."""
    if RATE_LIMITING_AVAILABLE:
        return limiter.limit("10/minute")(endpoint_func)
    return endpoint_func

def get_fallback_bbox(address: str) -> list:
    """Generate a fallback bounding box when geocoding fails."""
    # Default to London area
    return [-0.1276, 51.5074, -0.1176, 51.5174]

# ─── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint for health checks and basic info."""
    return {
        "message": "AI Architecture Platform",
        "status": "healthy",
        "version": "2.0.0",
        "description": "Transform addresses into professional architectural designs",
        "endpoints": {
            "status": "/api/status",
            "design": "/design/plan?address=your_address",
            "docs": "/docs" if DEBUG else "disabled"
        }
    }

@app.get("/api/status")
async def api_status(request: Request = None):
    """Comprehensive API status endpoint."""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "enhanced_location_intelligence": ENHANCED_FEATURES,
            "rate_limiting": RATE_LIMITING_AVAILABLE,
            "google_api_configured": API_CONFIGURED,
            "core_generation": CORE_FEATURES_AVAILABLE
        },
        "system": {
            "port": PORT,
            "debug": DEBUG,
            "output_directory": str(OUTPUT_DIR)
        }
    }

if ENHANCED_FEATURES:
    @app.get("/api/location-intelligence")
    async def analyze_location(request: Request, address: str = Query(..., description="Address to analyze")):
        """
        Comprehensive location intelligence analysis.
        Returns climate data, solar analysis, and architectural recommendations.
        """
        
        if not address.strip():
            raise HTTPException(400, "Address cannot be empty")
        
        if len(address) > 200:
            raise HTTPException(400, "Address too long (max 200 characters)")
        
        logger.info(f"🌍 Starting location intelligence analysis for: {address}")
        
        try:
            # Get location intelligence
            location_data = await get_location_intelligence(address)
            
            # Get climate data
            climate_data = await get_climate_data(
                location_data["coordinates"]["lat"], 
                location_data["coordinates"]["lng"]
            )
            
            # Get solar analysis
            solar_data = await get_solar_analysis(
                location_data["coordinates"]["lat"],
                location_data["coordinates"]["lng"]
            )
            
            # Get architectural recommendations
            architectural_data = await get_architectural_recommendations(
                location_data["coordinates"]["lat"],
                location_data["coordinates"]["lng"],
                location_data.get("country"),
                climate_data.get("climate_zone")
            )
            
            result = {
                "address": address,
                "timestamp": datetime.now().isoformat(),
                "location": location_data,
                "climate": climate_data,
                "solar": solar_data,
                "architecture": architectural_data,
                "recommendations": {
                    "building_orientation": solar_data.get("optimal_orientation"),
                    "materials": architectural_data.get("recommended_materials"),
                    "style": architectural_data.get("primary_styles"),
                    "climate_considerations": climate_data.get("design_recommendations")
                }
            }
            
            logger.info(f"✅ Location intelligence completed for: {address}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Location intelligence error: {e}")
            raise HTTPException(500, f"Location analysis failed: {str(e)}")

    # Apply rate limiting if available
    if RATE_LIMITING_AVAILABLE:
        analyze_location = limiter.limit("10/minute")(analyze_location)

@app.get("/design/plan")
async def design_plan(
    request: Request,
    address: str = Query(..., description="Address to design for"),
    building_type: str = Query("clinic", description="Type of building (clinic, office, residential)"),
    area_sqm: float = Query(200, description="Building area in square meters"),
    style_preference: str = Query("local", description="Style preference (local, modern, traditional)")
):
    """
    Generate architectural design with optional location intelligence.
    Creates PNG floor plan, DXF CAD file, and IFC BIM file.
    """
    
    # Input validation
    if not address.strip():
        raise HTTPException(400, "Address cannot be empty")
    
    if area_sqm < 50 or area_sqm > 10000:
        raise HTTPException(400, "Building area must be between 50 and 10,000 sqm")
    
    if not CORE_FEATURES_AVAILABLE:
        raise HTTPException(500, "Core generation features not available")
    
    logger.info(f"🏗️ Starting design generation for: {address}")
    
    try:
        # Enhanced or basic geocoding
        if ENHANCED_FEATURES and API_CONFIGURED:
            logger.info("Using enhanced location intelligence")
            location_data = await get_location_intelligence(address)
            parcel_bbox = location_data["bbox"]
            
            # Enhanced design prompt with context
            enhanced_prompt = f"""
            {building_type} design for {address}
            Area: {area_sqm} sqm
            Style preference: {style_preference}
            Enhanced with location intelligence and climate considerations
            """
            
            design_context = {
                "enhanced": True,
                "location_data": location_data
            }
        else:
            logger.info("Using basic geocoding")
            if geocode_address and API_CONFIGURED:
                parcel_data = geocode_address(address)
                parcel_bbox = parcel_data["bbox"]
            else:
                logger.warning("Using fallback bounding box")
                parcel_bbox = get_fallback_bbox(address)
            
            enhanced_prompt = f"{building_type} layout at {address} - {area_sqm} sqm"
            design_context = {
                "enhanced": False,
                "fallback_used": not API_CONFIGURED
            }
        
        # Generate design files
        logger.info("🎨 Generating floor plan...")
        base_png = generate_plan_png({"bbox": parcel_bbox}, prompt=enhanced_prompt)
        
        logger.info("🎨 Applying styling...")
        styled_png = style_png(base_png, prompt_suffix=f"{address} - {style_preference}")
        
        # Generate CAD files
        stem = Path(styled_png).stem
        dxf_path = OUTPUT_DIR / f"{stem}.dxf"
        ifc_path = OUTPUT_DIR / f"{stem}.ifc"
        
        logger.info("📐 Generating DXF file...")
        if not dxf_path.exists():
            generate_dxf(parcel_bbox, str(dxf_path))
        
        logger.info("🏗️ Generating IFC file...")
        if not ifc_path.exists():
            convert_dxf_to_ifc(str(dxf_path), str(ifc_path))
        
        # Prepare result
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
                "enhanced_features": ENHANCED_FEATURES,
                "api_configured": API_CONFIGURED,
                "generation_timestamp": datetime.now().isoformat()
            },
            "design_context": design_context
        }
        
        logger.info(f"🎉 Design generation completed successfully for: {address}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Design generation error: {e}")
        raise HTTPException(500, f"Design generation failed: {str(e)}")

# Apply rate limiting if available
if RATE_LIMITING_AVAILABLE:
    design_plan = limiter.limit("5/minute")(design_plan)

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ─── FRONTEND SERVING ────────────────────────────────────────────────────────

# Serve frontend static files (must be last)
try:
    if Path("frontend").exists() and Path("frontend/index.html").exists():
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
        logger.info("✅ Frontend mounted successfully")
    else:
        logger.warning("⚠️ Frontend directory not found")
        
        @app.get("/frontend-status")
        async def frontend_status():
            return {
                "frontend_available": False,
                "message": "Frontend files not found",
                "api_only": True
            }
            
except Exception as e:
    logger.error(f"❌ Error mounting frontend: {e}")

# ─── STARTUP/SHUTDOWN EVENTS ─────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("🚀 AI Architecture Platform starting up...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Enhanced features: {ENHANCED_FEATURES}")
    logger.info(f"Rate limiting: {RATE_LIMITING_AVAILABLE}")
    logger.info(f"Google API configured: {API_CONFIGURED}")
    logger.info(f"Core features: {CORE_FEATURES_AVAILABLE}")
    
    if not API_CONFIGURED:
        logger.warning("⚠️ Google API key not configured - using fallback mode")
    
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("🛑 AI Architecture Platform shutting down...")
    logger.info("✅ Application shutdown complete")

# ─── MAIN EXECUTION ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info(f"🚀 Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
