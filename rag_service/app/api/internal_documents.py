"""
Internal Document File API
===========================
Provides RAW document file serving for Admin Service.
Serves DOCX and JSON files without rendering (Data Layer responsibility).

Admin Service handles rendering (Presentation Layer responsibility).

Security: Internal endpoints - should only be accessible from Admin Service.
"""

from fastapi import APIRouter, HTTPException, Header, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging
import aiofiles
from datetime import datetime

from app.core.config import Settings
from app.core.path_config import PathConfig

# Initialize settings and path config
settings = Settings()
path_config = PathConfig()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/documents", tags=["internal-documents"])


# ============================================================================
# Response Models
# ============================================================================

class DocumentFileResponse(BaseModel):
    """Response for raw document file metadata"""
    success: bool
    file_type: str  # "docx" or "json"
    file_path: str
    filename: str
    doc_id: str
    collection: str
    timestamp: str


class DocumentJSONResponse(BaseModel):
    """Response for JSON document content"""
    success: bool
    content_type: str  # "json"
    content: Dict[str, Any]
    doc_id: str
    collection: str
    filename: str
    timestamp: str


# ============================================================================
# Security Helper
# ============================================================================

async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    """Verify internal API key for security"""
    expected_key = getattr(settings, 'internal_api_key', 'dev-internal-key')
    
    if x_internal_api_key != expected_key:
        logger.warning(f"❌ Unauthorized access attempt - invalid API key")
        raise HTTPException(
            status_code=403,
            detail="Forbidden - Invalid internal API key"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def get_document_source_path(collection: str, doc_id: str) -> Path:
    """
    Get path to original DOCX file
    
    Args:
        collection: Collection name
        doc_id: Document ID
        
    Returns:
        Path to DOCX file
    """
    base_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
    doc_dir = base_path / collection / "documents" / doc_id
    
    if not doc_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found in collection '{collection}'"
        )
    
    # Find .doc or .docx file
    doc_files = list(doc_dir.glob("*.doc")) + list(doc_dir.glob("*.docx"))
    
    if not doc_files:
        raise HTTPException(
            status_code=404,
            detail=f"No DOCX file found for document '{doc_id}'"
        )
    
    return doc_files[0]


def get_document_json_path(collection: str, doc_id: str) -> Path:
    """
    Get path to processed JSON file
    
    Args:
        collection: Collection name
        doc_id: Document ID
        
    Returns:
        Path to JSON file
    """
    base_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
    doc_dir = base_path / collection / "documents" / doc_id
    
    if not doc_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found in collection '{collection}'"
        )
    
    # Find .json file (exclude questions.json)
    json_files = [f for f in doc_dir.glob("*.json") if f.name != "questions.json"]
    
    if not json_files:
        raise HTTPException(
            status_code=404,
            detail=f"No JSON file found for document '{doc_id}'"
        )
    
    return json_files[0]


async def read_json_file(json_path: Path) -> Dict[str, Any]:
    """
    Read and parse JSON file
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        Parsed JSON data
    """
    try:
        logger.info(f"📋 Reading JSON file: {json_path.name}")
        
        async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            json_data = json.loads(content)
        
        logger.info(f"✅ Successfully read JSON file: {json_path.name}")
        return json_data
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON format: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error reading JSON file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read JSON file: {str(e)}"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/collections/{collection}/documents/{doc_id}/file",
    summary="Get raw document file",
    description="Serve RAW document file (DOCX or JSON) for Admin Service to render",
    dependencies=[Depends(verify_internal_api_key)]
)
async def get_document_file(
    collection: str,
    doc_id: str,
    type: str = Query(..., regex="^(docx|json)$", description="File type: 'docx' or 'json'")
):
    """
    Serve RAW document file for Admin Service
    
    **Architecture**: 
    - RAG Service (Data Layer): Serves raw files
    - Admin Service (Presentation Layer): Renders HTML from DOCX
    
    Args:
        collection: Collection name (e.g., 'hop_dong')
        doc_id: Document ID (e.g., 'DOC_001')
        type: File type - 'docx' for raw DOCX file, 'json' for JSON data
        
    Returns:
        - DOCX: FileResponse with raw DOCX bytes
        - JSON: JSON response with parsed data
        
    Security:
        Requires X-Internal-API-Key header
    """
    try:
        logger.info(f"📡 Document file request: {collection}/{doc_id} (type={type})")
        
        if type == "docx":
            # Serve raw DOCX file (NO rendering here!)
            docx_path = get_document_source_path(collection, doc_id)
            logger.info(f"📄 Serving raw DOCX file: {docx_path.name}")
            
            return FileResponse(
                path=str(docx_path),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=docx_path.name,
                headers={
                    "X-Document-ID": doc_id,
                    "X-Collection": collection
                }
            )
            
        elif type == "json":
            # Serve JSON data (already parsed)
            json_path = get_document_json_path(collection, doc_id)
            json_data = await read_json_file(json_path)
            
            return DocumentJSONResponse(
                success=True,
                content_type="json",
                content=json_data,
                doc_id=doc_id,
                collection=collection,
                filename=json_path.name,
                timestamp=datetime.now().isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error serving document file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check for internal documents API"""
    return {
        "status": "healthy",
        "service": "internal-documents",
        "architecture": "Data Layer - Serves raw files only (NO rendering)",
        "endpoints": [
            "GET /internal/documents/collections/{collection}/documents/{doc_id}/file?type=docx",
            "GET /internal/documents/collections/{collection}/documents/{doc_id}/file?type=json"
        ]
    }
