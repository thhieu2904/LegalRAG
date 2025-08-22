"""
Document Management API Endpoints
Cung cấp REST APIs để quản lý documents và form files
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from pathlib import Path
import shutil
import tempfile
import logging

from ..services.document_manager import DocumentManagerService
from ..services.hybrid_document_service import HybridDocumentService
from ..models.schemas import QueryResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Document Management"])

# Dependency
def get_document_manager() -> DocumentManagerService:
    return DocumentManagerService()

def get_hybrid_document_service() -> HybridDocumentService:
    return HybridDocumentService(migration_phase=1)

# ============================================================================
# Request/Response Models
# ============================================================================

class CreateDocumentRequest(BaseModel):
    title: str
    code: Optional[str] = None
    collection_id: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    code: Optional[str]
    collection_id: str
    created_at: str
    updated_at: str
    files: Dict[str, Any]
    metadata: Dict[str, Any]

class CollectionResponse(BaseModel):
    collection_id: str
    name: str
    document_count: int
    documents: List[DocumentResponse]

class DocumentListResponse(BaseModel):
    collections: List[CollectionResponse]
    total_documents: int

class FileUploadResponse(BaseModel):
    filename: str
    path: str
    size: int
    checksum: str
    added_at: str

# ============================================================================
# Document CRUD Operations
# ============================================================================

@router.post("/", response_model=Dict[str, str])
async def create_document(
    request: CreateDocumentRequest,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Tạo document mới"""
    try:
        document_id = doc_manager.create_document(
            collection_id=request.collection_id,
            title=request.title,
            code=request.code,
            metadata=request.metadata
        )
        return {"document_id": document_id, "message": "Document created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    collection_id: Optional[str] = None,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Lấy danh sách documents"""
    try:
        result = doc_manager.list_documents(collection_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{collection_id}/{document_id}", response_model=DocumentResponse)
async def get_document(
    collection_id: str,
    document_id: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Lấy thông tin document"""
    doc_info = doc_manager.get_document_info(collection_id, document_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_info

@router.delete("/{collection_id}/{document_id}")
async def delete_document(
    collection_id: str,
    document_id: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Xóa document"""
    success = doc_manager.delete_document(collection_id, document_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    return {"message": "Document deleted successfully"}

# ============================================================================
# File Operations
# ============================================================================

@router.post("/{collection_id}/{document_id}/files/{file_type}", response_model=FileUploadResponse)
async def upload_file(
    collection_id: str,
    document_id: str,
    file_type: str,  # source, processed, form, router
    file: UploadFile = File(...),
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Upload file vào document"""
    
    # Validate file_type
    valid_types = ["source", "processed", "form", "router"]
    if file_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file_type. Must be one of: {valid_types}"
        )
    
    # Validate document exists
    doc_info = doc_manager.get_document_info(collection_id, document_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")
    
    tmp_path = None
    try:
        # Save uploaded file to temporary location
        suffix = Path(file.filename).suffix if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Add file to document
        file_info = doc_manager.add_file(
            collection_id=collection_id,
            document_id=document_id,
            file_type=file_type,
            file_path=tmp_path,
            filename=file.filename
        )
        
        # Clean up temporary file
        Path(tmp_path).unlink()
        
        return file_info
        
    except Exception as e:
        # Clean up on error
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{collection_id}/{document_id}/files/{file_type}")
async def download_file(
    collection_id: str,
    document_id: str,
    file_type: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Download file từ document"""
    file_path = doc_manager.get_file_path(collection_id, document_id, file_type)
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type='application/octet-stream'
    )

@router.get("/{collection_id}/{document_id}/files")
async def list_document_files(
    collection_id: str,
    document_id: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Lấy danh sách files của document"""
    doc_info = doc_manager.get_document_info(collection_id, document_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc_info.get("files", {})

# ============================================================================
# Form-specific Operations
# ============================================================================

@router.get("/with-forms", response_model=List[DocumentResponse])
async def get_documents_with_forms(
    collection_id: Optional[str] = None,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Lấy danh sách documents có form files"""
    return doc_manager.get_documents_with_forms(collection_id)

@router.get("/{collection_id}/{document_id}/has-form")
async def check_has_form(
    collection_id: str,
    document_id: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Kiểm tra document có form file không"""
    has_form = doc_manager.has_form_file(collection_id, document_id)
    return {"has_form": has_form}

@router.get("/{collection_id}/{document_id}/files/form")
async def download_form_file(
    collection_id: str,
    document_id: str,
    hybrid_service: HybridDocumentService = Depends(get_hybrid_document_service)
):
    """Download form file cho document cụ thể"""
    try:
        # Get form file path using hybrid service
        form_path = hybrid_service.get_form_file_path(collection_id, document_id)
        
        if not form_path or not Path(form_path).exists():
            raise HTTPException(status_code=404, detail="Form file not found")
        
        # Get filename
        filename = Path(form_path).name
        
        # Return file response
        return FileResponse(
            path=form_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error downloading form file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{collection_id}/{document_id}/files/form/{filename}")
async def download_specific_form_file(
    collection_id: str,
    document_id: str,
    filename: str
):
    """Download specific form file với filename"""
    try:
        # Build form file path directly
        storage_base = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
        form_path = storage_base / collection_id / "documents" / document_id / "forms" / filename
        
        if not form_path.exists():
            raise HTTPException(status_code=404, detail="Form file not found")
        
        # Return file response
        return FileResponse(
            path=str(form_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error downloading specific form file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Collection Operations
# ============================================================================

@router.get("/collections")
async def list_collections(
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Lấy danh sách collections"""
    result = doc_manager.list_documents()
    return {
        "collections": [
            {
                "collection_id": coll["collection_id"],
                "name": coll["name"],
                "document_count": coll["document_count"]
            }
            for coll in result["collections"]
        ]
    }

@router.get("/collections/{collection_id}/registry")
async def get_collection_registry(
    collection_id: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Lấy registry của collection"""
    try:
        registry = doc_manager.load_collection_registry(collection_id)
        return registry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Utility Operations
# ============================================================================

@router.post("/migrate-from-old-structure")
async def migrate_from_old_structure(
    source_dir: str,
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """
    Migrate documents từ old structure sang new structure
    TODO: Implement migration logic
    """
    # This would implement migration from the old documents/ structure
    # to the new collection-first structure
    return {"message": "Migration not implemented yet"}

# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check(
    doc_manager: DocumentManagerService = Depends(get_document_manager)
):
    """Health check for document management service"""
    storage_root = None
    try:
        # Check if storage root exists and is writable
        storage_root = doc_manager.storage_root
        if not storage_root.exists():
            storage_root.mkdir(parents=True, exist_ok=True)
        
        # Try to create a test file
        test_file = storage_root / "health_check.tmp"
        test_file.write_text("health check")
        test_file.unlink()
        
        return {
            "status": "healthy",
            "storage_root": str(storage_root),
            "storage_exists": storage_root.exists(),
            "storage_writable": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "storage_root": str(storage_root) if storage_root else "unknown",
            "storage_exists": storage_root.exists() if storage_root else False,
            "storage_writable": False
        }
