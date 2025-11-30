"""
Form Service - Main FastAPI Application
Handles form rendering, filling, and CCCD scanning.
Internal service called by query-service.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx

from config import settings
from src.models import (
    CCCDScanRequest, CCCDScanResponse,
    FormRenderRequest, FormRenderResponse,
    FormFillRequest,
    HealthResponse
)
from src.services.cccd_scanner import CCCDScanner
from src.services.form_renderer import FormRenderer
from src.services.form_filler import FormFiller

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Form Service",
    description="Internal service for form rendering, filling, and CCCD scanning",
    version="1.0.0"
)

# CORS
cors_origins = settings.CORS_ORIGINS.split(",") if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
cccd_scanner = CCCDScanner()
form_renderer = FormRenderer()
form_filler = FormFiller()


# ============= HEALTH CHECK =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and storage connectivity"""
    storage_status = "unknown"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.STORAGE_SERVICE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                storage_status = "healthy" if data.get("storage_connected") else "unhealthy"
            else:
                storage_status = "unhealthy"
    except Exception as e:
        logger.warning(f"Storage health check failed: {e}")
        storage_status = "unreachable"
    
    return HealthResponse(
        status="healthy",
        service="form-service",
        storage_service=storage_status
    )


# ============= CCCD SCANNING =============

@app.post("/cccd/scan", response_model=CCCDScanResponse)
async def scan_cccd(request: CCCDScanRequest):
    """
    Scan CCCD QR code from image.
    
    Args:
        image_data: Base64 encoded image containing CCCD
        
    Returns:
        Extracted CCCD data (scan_cccd, scan_ho_ten, etc.)
    """
    try:
        result = cccd_scanner.scan(request.image_data)
        return result
    except Exception as e:
        logger.error(f"CCCD scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= FORM RENDERING =============

@app.post("/render", response_model=FormRenderResponse)
async def render_form(request: FormRenderRequest):
    """
    Render DOCX form template to HTML.
    
    Args:
        template_path: Path in MinIO (e.g., forms/{doc_id}/{form_file})
        
    Returns:
        HTML content with placeholders wrapped in CSS classes
    """
    try:
        result = await form_renderer.render(request.template_path)
        return result
    except Exception as e:
        logger.error(f"Render error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= FORM FILLING =============

@app.post("/fill")
async def fill_form(request: FormFillRequest):
    """
    Fill form template with data and return DOCX as base64.
    
    Args:
        template_path: Path in MinIO
        data: Dictionary with values {scan_ho_ten: "...", form_nghe_nghiep: "..."}
        
    Returns:
        JSON with base64 encoded filled DOCX
    """
    import base64
    
    try:
        filled_content, error = await form_filler.fill(
            template_path=request.template_path,
            data=request.data
        )
        
        if error:
            return {
                "success": False,
                "message": error,
                "file_bytes": None
            }
        
        # filled_content is guaranteed to be bytes here (not None)
        assert filled_content is not None
        
        # Encode to base64 for JSON transport
        file_bytes_b64 = base64.b64encode(filled_content).decode("utf-8")
        
        # Generate filename from template path
        template_name = request.template_path.split("/")[-1]
        base_name = template_name.rsplit(".", 1)[0]
        filename = f"{base_name}_filled.docx"
        
        return {
            "success": True,
            "message": f"Form filled successfully",
            "file_bytes": file_bytes_b64,
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fill error: {e}")
        return {
            "success": False,
            "message": str(e),
            "file_bytes": None
        }


# ============= ROOT =============

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "form-service",
        "version": "1.0.0",
        "description": "Internal service for form rendering, filling, and CCCD scanning",
        "endpoints": {
            "health": "GET /health",
            "cccd_scan": "POST /cccd/scan",
            "render": "POST /render",
            "fill": "POST /fill",
            "docs": "GET /docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=True
    )
