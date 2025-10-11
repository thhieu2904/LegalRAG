"""
Documents API Endpoints
=======================

Handles document listing and information using PathConfig service.
Loads data from metadata.json for performance and consistency.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
import json
from pathlib import Path

from ..core.admin_path_config import get_admin_path_config
from ..services.rag_client import get_rag_client
from ..services.document_renderer import get_document_renderer

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/collections/{collection_name}/documents")
async def list_documents(collection_name: str):
    """
    Get list of documents in a collection
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        List of documents with metadata and file information
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"📄 Listing documents for collection: {collection_name}")
        
        # Load from metadata.json (faster and more reliable than filesystem scan)
        metadata_file = path_config.get_collection_metadata(collection_name)
        documents_data = []
        
        if not metadata_file.exists():
            logger.warning(f"⚠️ Metadata file not found for {collection_name}")
            # Fallback to PathConfig list_documents method
            return await _list_documents_from_filesystem(path_config, collection_name)
        
        # Load documents from metadata.json
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        documents = metadata.get("documents", [])
        logger.info(f"📋 Found {len(documents)} documents in metadata")
        
        for doc in documents:
            try:
                doc_id = doc.get("id", "")
                if not doc_id:
                    logger.warning("⚠️ Document missing ID, skipping")
                    continue
                
                # Check questions.json existence and count
                questions_info = await _get_questions_info(path_config, collection_name, doc_id)
                
                # Check forms existence
                forms_info = await _get_forms_info(path_config, collection_name, doc_id)
                
                # Build document info
                document_info = {
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "effective_date": doc.get("effective_date", ""),
                    "code": doc.get("code", ""),
                    "executing_agency": doc.get("executing_agency", ""),
                    
                    # File information
                    "source_file": _extract_filename_from_source(doc.get("source", "")),
                    "has_original_doc": True,  # Assume true if in metadata
                    "has_processed_json": True,  # Assume true if in metadata
                    
                    # Questions information
                    "has_questions": questions_info["has_questions"],
                    "question_count": questions_info["question_count"],
                    
                    # Forms information  
                    "has_forms": forms_info["has_forms"],
                    "form_count": forms_info["form_count"],
                    
                    # Metadata fields
                    "applicant_type": doc.get("applicant_type", []),
                    "processing_time_text": doc.get("processing_time_text", ""),
                    "fee_text": doc.get("fee_text", ""),
                    "fee_vnd": doc.get("fee_vnd", 0),
                    
                    # Status
                    "status": "active"
                }
                
                documents_data.append(document_info)
                
            except Exception as e:
                logger.error(f"❌ Error processing document {doc.get('id', 'unknown')}: {e}")
                # Add basic info even if error
                documents_data.append({
                    "doc_id": doc.get("id", "unknown"),
                    "title": doc.get("title", "Unknown"),
                    "error": str(e),
                    "status": "error"
                })
        
        # Sort by doc_id for consistent ordering
        documents_data.sort(key=lambda x: x.get("doc_id", ""))
        
        logger.info(f"📊 Returning {len(documents_data)} documents for {collection_name}")
        
        return {
            "success": True,
            "data": documents_data,
            "collection": collection_name,
            "total": len(documents_data),
            "message": f"Found {len(documents_data)} documents"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing documents for {collection_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/collections/{collection_name}/documents/{doc_id}")
async def get_document_detail(collection_name: str, doc_id: str):
    """
    Get detailed information about a specific document
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID (e.g., DOC_001)
        
    Returns:
        Detailed document information including content preview
    """
    try:
        path_config = get_admin_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        logger.info(f"📋 Getting details for document: {collection_name}/{doc_id}")
        
        # Find document in metadata
        metadata_file = path_config.get_collection_metadata(collection_name)
        if not metadata_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Collection metadata not found"
            )
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        documents = metadata.get("documents", [])
        document = None
        for doc in documents:
            if doc.get("id") == doc_id:
                document = doc
                break
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{doc_id}' not found in collection '{collection_name}'"
            )
        
        # Get additional information
        questions_info = await _get_questions_info(path_config, collection_name, doc_id)
        forms_info = await _get_forms_info(path_config, collection_name, doc_id)
        files_info = await _get_files_info(path_config, collection_name, doc_id)
        
        # Build detailed response
        document_detail = {
            **document,  # All metadata fields
            
            # Enhanced information
            "questions": {
                "has_questions": questions_info["has_questions"],
                "question_count": questions_info["question_count"],
                "questions_preview": questions_info.get("questions_preview", [])
            },
            "forms": {
                "has_forms": forms_info["has_forms"],
                "form_count": forms_info["form_count"],
                "form_files": forms_info.get("form_files", [])
            },
            "files": files_info,
            
            # API URLs for further operations
            "api_urls": {
                "questions": f"/api/questions/collections/{collection_name}/documents/{doc_id}",
                "forms": f"/api/forms/collections/{collection_name}/documents/{doc_id}",
                "content": f"/api/content/collections/{collection_name}/documents/{doc_id}"
            }
        }
        
        logger.info(f"✅ Document detail loaded for {doc_id}")
        
        return {
            "success": True,
            "data": document_detail
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting document detail for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document detail: {str(e)}"
        )

async def _list_documents_from_filesystem(path_config, collection_name: str):
    """
    Fallback method to list documents from filesystem using PathConfig
    """
    try:
        logger.info(f"📁 Using filesystem fallback for {collection_name}")
        
        # Use PathConfig list_documents method
        documents = path_config.list_documents(collection_name)
        documents_data = []
        
        for doc in documents:
            doc_id = doc["doc_id"]
            
            # Get questions info
            questions_info = await _get_questions_info(path_config, collection_name, doc_id)
            
            document_info = {
                "doc_id": doc_id,
                "title": doc_id,  # Fallback to doc_id as title
                "source_file": doc.get("doc_file") or doc.get("json_file"),
                "has_questions": questions_info["has_questions"],
                "question_count": questions_info["question_count"],
                "has_forms": doc.get("has_forms", False),
                "status": "active"
            }
            
            documents_data.append(document_info)
        
        return {
            "success": True,
            "data": documents_data,
            "collection": collection_name,
            "total": len(documents_data),
            "message": f"Found {len(documents_data)} documents (filesystem scan)"
        }
        
    except Exception as e:
        logger.error(f"❌ Filesystem fallback failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents from filesystem: {str(e)}"
        )

async def _get_questions_info(path_config, collection_name: str, doc_id: str) -> Dict[str, Any]:
    """Get questions information for a document"""
    try:
        questions_file = path_config.get_document_dir(collection_name, doc_id) / "questions.json"
        
        if not questions_file.exists():
            return {
                "has_questions": False,
                "question_count": 0
            }
        
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        # Count questions
        question_count = 0
        questions_preview = []
        
        if isinstance(questions_data, dict):
            if questions_data.get("main_question"):
                question_count += 1
                questions_preview.append({
                    "type": "main",
                    "text": questions_data["main_question"][:100] + "..." if len(questions_data["main_question"]) > 100 else questions_data["main_question"]
                })
            
            variants = questions_data.get("question_variants", [])
            question_count += len(variants)
            
            for i, variant in enumerate(variants[:3]):  # Preview first 3 variants
                questions_preview.append({
                    "type": "variant",
                    "index": i,
                    "text": variant[:100] + "..." if len(variant) > 100 else variant
                })
        
        return {
            "has_questions": question_count > 0,
            "question_count": question_count,
            "questions_preview": questions_preview
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Error getting questions info for {doc_id}: {e}")
        return {
            "has_questions": False,
            "question_count": 0,
            "error": str(e)
        }

async def _get_forms_info(path_config, collection_name: str, doc_id: str) -> Dict[str, Any]:
    """Get forms information for a document"""
    try:
        forms_dir = path_config.get_document_dir(collection_name, doc_id) / "forms"
        
        if not forms_dir.exists():
            return {
                "has_forms": False,
                "form_count": 0
            }
        
        # Count form files
        form_files = []
        for file_path in forms_dir.iterdir():
            if file_path.is_file():
                form_files.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "download_url": f"/api/forms/download/{collection_name}/{doc_id}/{file_path.name}"
                })
        
        return {
            "has_forms": len(form_files) > 0,
            "form_count": len(form_files),
            "form_files": form_files
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Error getting forms info for {doc_id}: {e}")
        return {
            "has_forms": False,
            "form_count": 0,
            "error": str(e)
        }

async def _get_files_info(path_config, collection_name: str, doc_id: str) -> Dict[str, Any]:
    """Get file information for a document"""
    try:
        doc_dir = path_config.get_document_dir(collection_name, doc_id)
        
        files_info = {
            "json_files": [],
            "doc_files": [],
            "other_files": []
        }
        
        if doc_dir.exists():
            for file_path in doc_dir.iterdir():
                if file_path.is_file():
                    file_info = {
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    }
                    
                    if file_path.suffix == ".json":
                        files_info["json_files"].append(file_info)
                    elif file_path.suffix in [".doc", ".docx"]:
                        files_info["doc_files"].append(file_info)
                    else:
                        files_info["other_files"].append(file_info)
        
        return files_info
        
    except Exception as e:
        logger.warning(f"⚠️ Error getting files info for {doc_id}: {e}")
        return {"error": str(e)}

def _extract_filename_from_source(source_path: str) -> str:
    """Extract filename from source path"""
    if not source_path:
        return ""
    
    # Handle both Windows and Unix paths
    if "\\" in source_path:
        return source_path.split("\\")[-1]
    elif "/" in source_path:
        return source_path.split("/")[-1]
    else:
        return source_path


# ============================================================================
# DOCUMENT PREVIEW ENDPOINTS
# ============================================================================

@router.get("/collections/{collection_name}/documents/{doc_id}/preview/{doc_type}")
async def preview_document(
    collection_name: str,
    doc_id: str,
    doc_type: str  # "docx" or "json"
):
    """
    Preview document content - renders DOCX to HTML or returns JSON data
    
    **ARCHITECTURE (Corrected)**:
    - RAG Service (Data Layer): Serves raw DOCX/JSON files
    - Admin Service (Presentation Layer): Renders DOCX → HTML using mammoth locally
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
        doc_type: Type of preview ("docx" or "json")
        
    Returns:
        - For DOCX: HTML content rendered locally by Admin Service
        - For JSON: Parsed JSON data from RAG Service
        
    Example URLs:
        GET /collections/Bo_thu_tuc/documents/123/preview/docx
        GET /collections/Bo_thu_tuc/documents/123/preview/json
    """
    try:
        # Validate doc_type
        if doc_type not in ["docx", "json"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid doc_type '{doc_type}'. Must be 'docx' or 'json'"
            )
        
        logger.info(f"📄 Preview request: {collection_name}/{doc_id} ({doc_type})")
        
        # Get document renderer service
        renderer = get_document_renderer()
        
        try:
            if doc_type == "docx":
                # Render DOCX to HTML locally (Admin Service = Presentation Layer)
                logger.info(f"🎨 Rendering DOCX to HTML in Admin Service (Presentation Layer)")
                html_content = await renderer.render_docx_to_html(
                    collection=collection_name,
                    doc_id=doc_id
                )
                
                result = {
                    "success": True,
                    "html": html_content,
                    "doc_id": doc_id,
                    "collection": collection_name,
                    "type": "docx",
                    "rendered_by": "Admin Service (mammoth local)"
                }
                
                logger.info(f"✅ DOCX preview ready: {doc_id} ({len(html_content)} chars)")
                return JSONResponse(content=result)
                
            elif doc_type == "json":
                # Get JSON data from RAG Service
                logger.info(f"📋 Fetching JSON from RAG Service")
                json_content = await renderer.get_json_content(
                    collection=collection_name,
                    doc_id=doc_id
                )
                
                result = {
                    "success": True,
                    "data": json_content,
                    "doc_id": doc_id,
                    "collection": collection_name,
                    "type": "json"
                }
                
                logger.info(f"✅ JSON preview ready: {doc_id}")
                return JSONResponse(content=result)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error rendering document: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to render document: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in preview endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
