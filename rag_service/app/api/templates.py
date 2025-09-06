from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/templates", tags=["templates"])

# Template directory paths
COLLECTIONS_DIR = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "data" / "storage" / "templates"  # For legacy support

@router.get("/{collection_id}/{doc_id}/{template_name}")
async def get_collection_template(collection_id: str, doc_id: str, template_name: str):
    """
    Download a template file from specific collection/document
    """
    try:
        # Validate inputs (basic security)
        for param in [collection_id, doc_id, template_name]:
            if ".." in param or "/" in param or "\\" in param:
                raise HTTPException(status_code=400, detail="Invalid parameter")
        
        # Template path in collection structure - use forms directory since we don't separate forms/templates anymore
        template_path = COLLECTIONS_DIR / collection_id / "documents" / doc_id / "forms" / template_name
        
        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found in {collection_id}/{doc_id}")
        
        if not template_path.is_file():
            raise HTTPException(status_code=400, detail=f"'{template_name}' is not a file")
        
        logger.info(f"Serving collection template: {template_path}")
        return FileResponse(
            path=str(template_path),
            filename=template_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving template {template_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Legacy global template endpoint (fallback)
@router.get("/{template_name}")
async def get_global_template(template_name: str):
    """
    Download a template file by name
    """
    try:
        # Validate template name (basic security)
        if ".." in template_name or "/" in template_name or "\\" in template_name:
            raise HTTPException(status_code=400, detail="Invalid template name")
        
        template_path = TEMPLATE_DIR / template_name
        
        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        if not template_path.is_file():
            raise HTTPException(status_code=400, detail=f"'{template_name}' is not a file")
        
        logger.info(f"Serving template: {template_path}")
        return FileResponse(
            path=str(template_path),
            filename=template_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving template {template_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
async def list_templates():
    """
    List all available templates
    """
    try:
        if not TEMPLATE_DIR.exists():
            return {"templates": [], "count": 0}
        
        templates = []
        for file_path in TEMPLATE_DIR.glob("*.docx"):
            templates.append({
                "name": file_path.name,
                "size": file_path.stat().st_size
            })
        
        return {
            "templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
