"""
Form Service - Main FastAPI Application
Handles form rendering, filling, and CCCD scanning.
Internal service called by query-service.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx
import base64

from config import settings
from src.models import (
    CCCDScanRequest, CCCDScanResponse,
    FormRenderRequest, FormRenderResponse,
    FormFillRequest,
    FormDetectResponse, DetectedPosition,
    FormFinalizeRequest, FormFinalizeResponse,
    HealthResponse
)
from src.services.cccd_scanner import CCCDScanner
from src.services.form_renderer import FormRenderer
from src.services.form_filler import FormFiller
from src.services.template_processor import TemplateProcessor

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
template_processor = TemplateProcessor()


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


# ============= FORM TEMPLATE ADMIN =============

@app.post("/forms/detect", response_model=FormDetectResponse)
async def detect_form_fields(file: UploadFile = File(...)):
    """
    Detect fillable field positions in uploaded DOCX.
    
    Args:
        file: DOCX file to analyze
        
    Returns:
        List of detected positions with context
    """
    if not file.filename or not file.filename.endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    try:
        # Read file
        content = await file.read()
        
        # Analyze with TemplateProcessor
        result = template_processor.analyze(content)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.errors or ['Analysis failed'])
        
        # Convert to simplified format (just positions, no field names)
        positions = []
        for idx, field in enumerate(result.fields):
            pos = DetectedPosition(
                index=idx,
                paragraph_index=field.paragraph_index,
                text=field.original_text[:50] if field.original_text else field.label,
                pattern_type=field.field_type,
                label=field.label or "",
                full_paragraph=field.full_paragraph or field.original_text or field.label,
                context_before=field.context_before or [],
                context_after=field.context_after or []
            )
            # Debug log first position
            if idx == 0:
                logger.info(f"First position - label: '{pos.label}', context_before: {len(pos.context_before)}, context_after: {len(pos.context_after)}")
            positions.append(pos)
        
        logger.info(f"Detected {len(positions)} positions in {file.filename}")
        
        return FormDetectResponse(
            success=True,
            positions=positions,
            total_positions=len(positions),
            message=f"Detected {len(positions)} fillable positions"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/forms/finalize", response_model=FormFinalizeResponse)
async def finalize_form_template(
    file: UploadFile = File(...),
    selected_indices: str = Form("")
):
    """
    Create final template with {{field_N}} placeholders at selected positions.
    
    Args:
        file: Original DOCX file
        selected_indices: Comma-separated list of indices (e.g., "0,1,5,7")
        
    Returns:
        Template DOCX with placeholders inserted
    """
    if not file.filename or not file.filename.endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    try:
        # Read file
        content = await file.read()
        
        # Parse selected indices
        if not selected_indices:
            raise HTTPException(status_code=400, detail="No positions selected")
        
        try:
            indices = [int(idx.strip()) for idx in selected_indices.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid indices format")
        
        # Re-analyze to get field info
        analyze_result = template_processor.analyze(content)
        if not analyze_result.success:
            raise HTTPException(status_code=500, detail="Failed to analyze document")
        
        all_fields = analyze_result.fields
        
        # Filter to selected fields and assign field_N names (unified convention)
        confirmed_fields = []
        for idx in indices:
            if 0 <= idx < len(all_fields):
                field = all_fields[idx]
                confirmed_fields.append({
                    'paragraph_index': field.paragraph_index,
                    'field_name': f"field_{idx + 1}",  # field_1, field_2, ... (unified naming)
                    'label': field.label or '',
                    'field_type': field.field_type or 'dots'
                })
        
        # Create template with placeholders
        create_result = template_processor.create_template(content, confirmed_fields)
        
        if not create_result.success or not create_result.template_bytes:
            raise HTTPException(
                status_code=500, 
                detail=create_result.errors or ['Template creation failed']
            )
        
        template_bytes = create_result.template_bytes
        placeholders = create_result.placeholders
        
        # Encode to base64 for JSON transport
        template_b64 = base64.b64encode(template_bytes).decode('utf-8')
        
        logger.info(f"Created template with {len(placeholders)} placeholders")
        
        return FormFinalizeResponse(
            success=True,
            template_content=template_b64,
            placeholders=placeholders,
            message=f"Template created with {len(placeholders)} fields"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Finalize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            "forms_detect": "POST /forms/detect",
            "forms_finalize": "POST /forms/finalize",
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
