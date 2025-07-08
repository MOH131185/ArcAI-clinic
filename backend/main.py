# backend/main.py - Secure Configuration

import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import configuration
from backend.config import settings, validate_environment

# Import functions from the ring modules
from backend.ring1.geocode import geocode_address
from backend.ring2.main import generate_plan_png
from backend.ring2.style import style_png
from backend.ring3.dxf_generator import generate_dxf
from backend.ring4.ifc_exporter import convert_dxf_to_ifc

# ─── STARTUP VALIDATION ──────────────────────────────────────────────────────

if not validate_environment():
    exit(1)

# ─── APPLICATION SETUP ───────────────────────────────────────────────────────

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Clinic Layout Generator",
    description="Transform addresses into professional architectural files",
    version="1.0.0",
    debug=settings.debug
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── SECURITY MIDDLEWARE ─────────────────────────────────────────────────────

# Trusted hosts (prevents Host header attacks)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts
)

# CORS configuration
if settings.environment == "development":
    # Permissive CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Restrictive CORS for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"https://{host}" for host in settings.allowed_hosts],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# ─── STATIC FILE SERVING ─────────────────────────────────────────────────────

# Serve generated files
app.mount("/outputs", StaticFiles(directory=str(settings.output_directory)), name="outputs")

# ─── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/api/status")
@limiter.limit("30/minute")  # Higher limit for status endpoint
async def api_status(request: Request):
    """API status endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }

@app.get("/api/config")
@limiter.limit("10/minute")
async def get_config(request: Request):
    """Get public configuration information."""
    return {
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "max_file_size_mb": settings.max_file_size_mb,
        "supported_formats": ["PNG", "DXF", "IFC"],
        "environment": settings.environment
    }

@app.get("/design/plan")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def design_plan(request: Request, address: str = Query(..., description="Address to geocode")):
    """Generate clinic layout files for the given address."""
    
    # Input validation
    if not address.strip():
        raise HTTPException(400, "Address cannot be empty")
    
    if len(address) > 200:
        raise HTTPException(400, "Address too long (max 200 characters)")
    
    logging.info(f"🏗️ Processing request for address: {address}")
    
    try:
        # 1) Geocoding
        logging.info("📍 Starting geocoding...")
        parcel = geocode_address(address)
        logging.info(f"✅ Geocoding successful: {parcel}")
        
    except ValueError as e:
        logging.warning(f"⚠️ Geocoding validation error: {e}")
        raise HTTPException(400, f"Invalid address: {e}")
    except Exception as e:
        logging.error(f"❌ Geocoding error: {e}")
        raise HTTPException(500, f"Geocoding service unavailable: {e}")
    
    try:
        # 2) Image generation
        logging.info("🎨 Generating layout images...")
        base_png = generate_plan_png(parcel, prompt=f"clinic layout at {address}")
        styled_png = style_png(base_png, prompt_suffix=address)
        logging.info(f"✅ Images generated: {styled_png}")
        
    except Exception as e:
        logging.error(f"❌ Image generation error: {e}")
        raise HTTPException(500, f"Image generation failed: {e}")
    
    # Generate file paths
    stem = Path(styled_png).stem
    dxf_path = settings.output_directory / f"{stem}.dxf"
    ifc_path = settings.output_directory / f"{stem}.ifc"
    
    try:
        # 3) DXF generation
        if not dxf_path.exists():
            logging.info("📐 Generating DXF file...")
            generate_dxf(parcel["bbox"], str(dxf_path))
            logging.info(f"✅ DXF generated: {dxf_path}")
        
    except Exception as e:
        logging.error(f"❌ DXF generation error: {e}")
        raise HTTPException(500, f"DXF generation failed: {e}")
    
    try:
        # 4) IFC generation
        if not ifc_path.exists():
            logging.info("🏗️ Generating IFC file...")
            convert_dxf_to_ifc(str(dxf_path), str(ifc_path))
            logging.info(f"✅ IFC generated: {ifc_path}")
        
    except Exception as e:
        logging.error(f"❌ IFC generation error: {e}")
        raise HTTPException(500, f"IFC generation failed: {e}")
    
    # Return file URLs
    result = {
        "plan_png": f"/outputs/{Path(styled_png).name}",
        "dxf": f"/outputs/{dxf_path.name}",
        "ifc": f"/outputs/{ifc_path.name}",
        "address": address,
        "timestamp": Path(styled_png).stat().st_mtime
    }
    
    logging.info(f"🎉 Successfully processed request for: {address}")
    return result

# ─── FRONTEND SERVING ────────────────────────────────────────────────────────

# Serve frontend (must be last)
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    logging.info("✅ Frontend static files mounted successfully")
except Exception as e:
    logging.error(f"❌ Error mounting frontend: {e}")
    print("Make sure frontend/index.html exists")

# ─── STARTUP EVENT ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logging.info("🚀 Clinic Layout Generator starting up...")
    if settings.debug:
        settings.print_config_summary()
    logging.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logging.info("🛑 Clinic Layout Generator shutting down...")
    logging.info("✅ Application shutdown complete")
