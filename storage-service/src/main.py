"""
Storage Service - MinIO File Management
Simple file wrapper for upload/download/delete operations.

Separation of Concerns:
  - Storage: File operations (upload/download/delete/list)
  - Admin: Orchestration + metadata extraction
  - Embedding: Chunking strategy
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
import io

from .config import settings
from .minio_client import init_minio_client, get_minio_client
from .models import (
    FileUploadResponse,
    FileListResponse,
    DeleteResponse,
    HealthResponse,
    TextExtractionResponse,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MinIO client
init_minio_client(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

# Initialize FastAPI app
app = FastAPI(
    title="Storage Service",
    description="Simple file storage wrapper with MinIO",
    version="2.0.0"
)

# Add CORS middleware
cors_origins = settings.CORS_ORIGINS.split(",") if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= HEALTH CHECK =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and MinIO connection"""
    try:
        minio = get_minio_client()
        minio.list_files(settings.MINIO_BUCKET, recursive=False)
        return HealthResponse(
            status="healthy",
            service="storage-service",
            storage_connected=True
        )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="storage-service",
            storage_connected=False
        )


# ============= FILE OPERATIONS (SIMPLE CRUD) =============

@app.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    document_id: str = Query(..., description="Document ID from admin-service"),
):
    """
    Upload file to MinIO storage
    
    Path: documents/{document_id}/{filename}
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename required")
        
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
            )
        
        file_path = f"documents/{document_id}/{file.filename}"
        minio = get_minio_client()
        minio.upload_file(
            bucket=settings.MINIO_BUCKET,
            file_path=file_path,
            file_data=content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        logger.info(f"✅ File uploaded: {file_path}")
        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            file_path=file_path,
            file_size=len(content),
            bucket=settings.MINIO_BUCKET,
            content_type=file.content_type or "application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download")
async def download_file(
    file_path: str = Query(..., description="File path in MinIO")
):
    """Download file from MinIO storage"""
    try:
        minio = get_minio_client()
        if not minio.file_exists(settings.MINIO_BUCKET, file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = minio.download_file(settings.MINIO_BUCKET, file_path)
        filename = file_path.split("/")[-1]
        
        # Use RFC 5987 encoding for UTF-8 filenames
        from urllib.parse import quote
        filename_encoded = quote(filename, safe='')
        
        logger.info(f"✅ File downloaded: {file_path}")
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list", response_model=FileListResponse)
async def list_files(
    prefix: str = Query(default="documents/", description="Folder prefix")
):
    """List files in MinIO bucket"""
    try:
        minio = get_minio_client()
        files = minio.list_files(settings.MINIO_BUCKET, prefix=prefix, recursive=True)
        
        return FileListResponse(
            success=True,
            files=[
                {
                    "name": f["name"],
                    "size": f["size"],
                    "content_type": "application/octet-stream",
                    "last_modified": f.get("last_modified")
                }
                for f in files
            ],
            total=len(files)
        )
    except Exception as e:
        logger.error(f"❌ List failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete", response_model=DeleteResponse)
async def delete_file(
    file_path: str = Query(..., description="File path to delete")
):
    """Delete file from MinIO storage"""
    try:
        minio = get_minio_client()
        minio.delete_file(settings.MINIO_BUCKET, file_path)
        
        logger.info(f"✅ File deleted: {file_path}")
        return DeleteResponse(
            success=True,
            message="File deleted successfully",
            file_path=file_path
        )
    except Exception as e:
        logger.error(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= TEXT EXTRACTION (LOW-LEVEL, FOR ADMIN) =============

@app.post("/extract-text", response_model=TextExtractionResponse)
async def extract_text(
    file: UploadFile = File(...),
):
    """
    Extract text from PDF file (LOW-LEVEL)
    
    ⚠️ ADMIN-SERVICE will handle metadata extraction + chunking
    Storage only extracts raw text.
    
    Returns: {success, text, pages, character_count, word_count}
    """
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=415, detail="Only PDF files supported")
        
        content = await file.read()
        
        from .extractors.pdf_extractor import PDFExtractor
        text = PDFExtractor.extract_text(content)
        metadata = PDFExtractor.extract_metadata(content)
        
        word_count = len(text.split())
        char_count = len(text)
        
        logger.info(f"✅ Text extracted: {char_count} chars, {word_count} words")
        
        return TextExtractionResponse(
            success=True,
            text=text,
            pages=metadata.get("pages", 0),
            character_count=char_count,
            word_count=word_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Text extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= ROOT ENDPOINT =============

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "storage-service",
        "version": "2.0.0",
        "status": "running",
        "description": "Simple file storage wrapper (CRUD only). Metadata extraction and chunking are handled by other services.",
        "endpoints": {
            "health": "GET /health",
            "file_operations": {
                "upload": "POST /upload",
                "download": "GET /download",
                "list": "GET /list",
                "delete": "DELETE /delete"
            },
            "extraction": {
                "extract_text": "POST /extract-text (low-level, for admin-service)"
            },
            "docs": "GET /docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
