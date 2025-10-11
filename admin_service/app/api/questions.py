"""
Questions API Endpoints
=======================

Handles questions management using PathConfig service.
Loads and processes questions.json files with proper encoding.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
import logging
import json
from pathlib import Path
from pydantic import BaseModel

from ..core.admin_path_config import get_admin_path_config
from ..services.rag_client import get_rag_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Pydantic Models for Request Validation ==========

class QuestionsCreateRequest(BaseModel):
    """Request model for creating questions"""
    main_question: str
    question_variants: Optional[List[str]] = []


class QuestionsUpdateRequest(BaseModel):
    """Request model for updating questions"""
    main_question: str
    question_variants: Optional[List[str]] = []


class VariantsUpdateRequest(BaseModel):
    """Request model for updating only variants"""
    question_variants: List[str]


class RestoreRequest(BaseModel):
    """Request model for restoring from backup"""
    backup_filename: str


class RebuildRequest(BaseModel):
    """Request model for triggering rebuild"""
    trigger_rebuild: bool = False
    rebuild_scope: str = "document"  # document, collection, all


# ========== READ Endpoints (Existing) ==========

@router.get("/questions")
async def list_all_questions(
    q: Optional[str] = None,
    collection: Optional[str] = None, 
    limit: Optional[int] = None
):
    """
    Get all questions across collections with optional search and filtering
    
    Args:
        q: Search query for questions
        collection: Filter by collection name
        limit: Maximum number of results to return
        
    Returns:
        List of questions with metadata
    """
    try:
        path_config = get_admin_path_config()
        logger.info(f"❓ Listing questions with filters: q='{q}', collection='{collection}', limit={limit}")
        
        available_collections = path_config.list_collections()
        logger.info(f"📁 Available collections: {available_collections}")
        
        all_questions = []
        
        # Filter collections if specified
        collections_to_process = [collection] if collection and collection in available_collections else available_collections
        
        for collection_name in collections_to_process:
            try:
                logger.info(f"📂 Processing collection: {collection_name}")
                
                # Get collection directory
                collection_dir = path_config.get_collection_dir(collection_name)
                documents_dir = collection_dir / "documents"
                
                if not documents_dir.exists():
                    logger.warning(f"⚠️ Documents directory not found for {collection_name}")
                    continue
                
                # Scan all document directories for questions.json files
                for doc_dir in documents_dir.iterdir():
                    if not doc_dir.is_dir():
                        continue
                    
                    doc_id = doc_dir.name
                    questions_file = doc_dir / "questions.json"
                    
                    if not questions_file.exists():
                        continue
                    
                    try:
                        # Load and normalize questions
                        with open(questions_file, 'r', encoding='utf-8') as f:
                            questions_data = json.load(f)
                        
                        normalized_questions = _normalize_questions_format(questions_data)
                        
                        # Add metadata to each question
                        for i, question in enumerate(normalized_questions):
                            question_with_meta = {
                                "id": f"{collection_name}_{doc_id}_{i}",
                                "main_question": question.get("main_question", ""),
                                "variants": question.get("variants", []),
                                "collection": collection_name,
                                "doc_id": doc_id,
                                "category": question.get("category", "general")
                            }
                            
                            # Apply search filter if specified
                            if q:
                                search_text = q.lower()
                                question_text = question_with_meta["main_question"].lower()
                                variants_text = " ".join(question_with_meta["variants"]).lower()
                                
                                if search_text not in question_text and search_text not in variants_text:
                                    continue
                            
                            all_questions.append(question_with_meta)
                            
                    except Exception as e:
                        logger.error(f"❌ Error processing questions for {doc_id}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Error processing collection {collection_name}: {e}")
                continue
        
        # Apply limit if specified
        if limit and limit > 0:
            all_questions = all_questions[:limit]
        
        logger.info(f"✅ Found {len(all_questions)} questions total")
        
        return {
            "success": True,
            "data": all_questions,
            "total": len(all_questions),
            "filters": {
                "search_query": q,
                "collection_filter": collection,
                "limit": limit
            },
            "message": f"Found {len(all_questions)} questions"
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing questions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list questions: {str(e)}"
        )

@router.get("/questions/collections/{collection_name}/documents/{doc_id}")
async def get_document_questions(collection_name: str, doc_id: str):
    """
    Get questions for a specific document
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID (e.g., DOC_001)  
        
    Returns:
        Questions data with normalized format
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
        
        logger.info(f"❓ Getting questions for: {collection_name}/{doc_id}")
        
        # Get questions file path
        questions_file = path_config.get_document_dir(collection_name, doc_id) / "questions.json"
        
        if not questions_file.exists():
            logger.info(f"📝 No questions file found for {doc_id}")
            return {
                "success": True,
                "data": {
                    "collection": collection_name,
                    "doc_id": doc_id,
                    "questions": [],
                    "total": 0,
                    "has_questions": False
                },
                "message": "No questions found for this document"
            }
        
        # Load questions.json
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        logger.info(f"📋 Loaded questions data keys: {list(questions_data.keys()) if isinstance(questions_data, dict) else 'not dict'}")
        
        # Normalize questions format
        normalized_questions = _normalize_questions_format(questions_data)
        
        # Get document title from metadata
        document_title = await _get_document_title(path_config, collection_name, doc_id)
        
        response_data = {
            "collection": collection_name,
            "doc_id": doc_id,
            "document_title": document_title,
            "questions": normalized_questions,
            "total": len(normalized_questions),
            "has_questions": len(normalized_questions) > 0,
            "raw_format_info": {
                "has_main_question": "main_question" in questions_data if isinstance(questions_data, dict) else False,
                "has_variants": "question_variants" in questions_data if isinstance(questions_data, dict) else False,
                "variants_count": len(questions_data.get("question_variants", [])) if isinstance(questions_data, dict) else 0
            }
        }
        
        logger.info(f"✅ Returning {len(normalized_questions)} questions for {doc_id}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting questions for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get questions: {str(e)}"
        )

@router.get("/questions/collections/{collection_name}")
async def get_collection_questions(collection_name: str, limit: Optional[int] = None):
    """
    Get all questions from all documents in a collection (aggregated view)
    
    Args:
        collection_name: Name of the collection
        limit: Optional limit on number of questions to return
        
    Returns:
        Aggregated questions from all documents in the collection
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
        
        logger.info(f"📚 Getting all questions for collection: {collection_name}")
        
        # Get all documents in collection
        documents = path_config.list_documents(collection_name)
        
        all_questions = []
        documents_with_questions = 0
        total_questions = 0
        
        for doc in documents:
            doc_id = doc["doc_id"]
            
            try:
                # Get questions for this document
                questions_file = path_config.get_document_dir(collection_name, doc_id) / "questions.json"
                
                if not questions_file.exists():
                    continue
                
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                
                # Normalize questions
                normalized_questions = _normalize_questions_format(questions_data)
                
                if normalized_questions:
                    documents_with_questions += 1
                    total_questions += len(normalized_questions)
                    
                    # Add document context to each question
                    for question in normalized_questions:
                        question["source_doc_id"] = doc_id
                        question["source_collection"] = collection_name
                        
                        # Get document title if available
                        document_title = await _get_document_title(path_config, collection_name, doc_id)
                        question["source_document_title"] = document_title
                    
                    all_questions.extend(normalized_questions)
                    
                    # Apply limit if specified
                    if limit and len(all_questions) >= limit:
                        all_questions = all_questions[:limit]
                        break
                        
            except Exception as e:
                logger.warning(f"⚠️ Error loading questions for {doc_id}: {e}")
                continue
        
        logger.info(f"📊 Collection {collection_name}: {documents_with_questions} docs with questions, {total_questions} total questions")
        
        return {
            "success": True,
            "data": {
                "collection": collection_name,
                "questions": all_questions,
                "total": len(all_questions),
                "statistics": {
                    "total_documents": len(documents),
                    "documents_with_questions": documents_with_questions,
                    "total_questions": total_questions,
                    "questions_returned": len(all_questions)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting collection questions for {collection_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection questions: {str(e)}"
        )

@router.get("/questions/search")
async def search_questions(
    q: str,
    collection: Optional[str] = None,
    limit: int = 50
):
    """
    Search questions across collections or within a specific collection
    
    Args:
        q: Search query
        collection: Optional collection to search within
        limit: Maximum number of results
        
    Returns:
        Matching questions with relevance information
    """
    try:
        path_config = get_admin_path_config()
        
        if not q.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        query_lower = q.lower().strip()
        logger.info(f"🔍 Searching questions for: '{q}'" + (f" in collection '{collection}'" if collection else " across all collections"))
        
        # Determine collections to search
        if collection:
            available_collections = path_config.list_collections()
            if collection not in available_collections:
                raise HTTPException(
                    status_code=404,
                    detail=f"Collection '{collection}' not found"
                )
            search_collections = [collection]
        else:
            search_collections = path_config.list_collections()
        
        matching_questions = []
        
        for coll_name in search_collections:
            try:
                documents = path_config.list_documents(coll_name)
                
                for doc in documents:
                    doc_id = doc["doc_id"]
                    
                    try:
                        questions_file = path_config.get_document_dir(coll_name, doc_id) / "questions.json"
                        
                        if not questions_file.exists():
                            continue
                        
                        with open(questions_file, 'r', encoding='utf-8') as f:
                            questions_data = json.load(f)
                        
                        normalized_questions = _normalize_questions_format(questions_data)
                        
                        for question in normalized_questions:
                            question_text = question["text"].lower()
                            
                            # Simple text matching (can be enhanced with fuzzy matching)
                            if query_lower in question_text:
                                # Calculate relevance score (simple)
                                relevance_score = _calculate_relevance_score(query_lower, question_text)
                                
                                question["source_collection"] = coll_name
                                question["source_doc_id"] = doc_id
                                question["relevance_score"] = relevance_score
                                question["source_document_title"] = await _get_document_title(path_config, coll_name, doc_id)
                                
                                matching_questions.append(question)
                                
                                # Apply limit
                                if len(matching_questions) >= limit:
                                    break
                        
                        if len(matching_questions) >= limit:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error searching in {coll_name}/{doc_id}: {e}")
                        continue
                
                if len(matching_questions) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️ Error searching collection {coll_name}: {e}")
                continue
        
        # Sort by relevance score (descending)
        matching_questions.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        logger.info(f"🎯 Found {len(matching_questions)} matching questions")
        
        return {
            "success": True,
            "data": {
                "query": q,
                "search_collections": search_collections,
                "questions": matching_questions,
                "total": len(matching_questions),
                "limited": len(matching_questions) >= limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error searching questions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search questions: {str(e)}"
        )

def _normalize_questions_format(questions_data: Any) -> List[Dict[str, Any]]:
    """
    Normalize questions data to unified format
    
    Args:
        questions_data: Raw questions data from JSON
        
    Returns:
        List of normalized question objects
    """
    normalized = []
    
    if isinstance(questions_data, dict):
        # Handle standard format: main_question + question_variants
        if "main_question" in questions_data and questions_data["main_question"]:
            normalized.append({
                "id": "main",
                "text": questions_data["main_question"],
                "type": "main",
                "order": 0
            })
        
        variants = questions_data.get("question_variants", [])
        for i, variant in enumerate(variants):
            if variant and variant.strip():
                normalized.append({
                    "id": f"variant_{i}",
                    "text": variant,
                    "type": "variant", 
                    "variant_index": i,
                    "order": i + 1
                })
    
    elif isinstance(questions_data, list):
        # Handle list format (legacy or alternative format)
        for i, item in enumerate(questions_data):
            if isinstance(item, dict):
                text = item.get("text") or item.get("question", "")
                question_type = item.get("type", "unknown")
            else:
                text = str(item)
                question_type = "unknown"
            
            if text and text.strip():
                normalized.append({
                    "id": f"question_{i}",
                    "text": text,
                    "type": question_type,
                    "order": i
                })
    
    else:
        # Handle other formats (string, etc.)
        if questions_data and str(questions_data).strip():
            normalized.append({
                "id": "single",
                "text": str(questions_data),
                "type": "single",
                "order": 0
            })
    
    return normalized

async def _get_document_title(path_config, collection_name: str, doc_id: str) -> str:
    """Get document title from metadata"""
    try:
        # Try to get title from collection metadata first
        metadata_file = path_config.get_collection_metadata(collection_name)
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            documents = metadata.get("documents", [])
            for doc in documents:
                if doc.get("id") == doc_id:
                    return doc.get("title", doc_id)
        
        # Fallback to doc_id
        return doc_id
        
    except Exception as e:
        logger.warning(f"⚠️ Error getting document title for {doc_id}: {e}")
        return doc_id

def _calculate_relevance_score(query: str, text: str) -> float:
    """
    Calculate simple relevance score for search results
    
    Args:
        query: Search query (lowercase)
        text: Question text (lowercase)
        
    Returns:
        Relevance score (0-1)
    """
    if not query or not text:
        return 0.0
    
    # Simple scoring based on:
    # 1. Exact match bonus
    # 2. Word match count
    # 3. Position of match
    
    score = 0.0
    
    # Exact phrase match (high score)
    if query in text:
        score += 0.8
        
        # Bonus for match at beginning
        if text.startswith(query):
            score += 0.2
    
    # Individual word matches
    query_words = query.split()
    text_words = text.split()
    
    matching_words = 0
    for word in query_words:
        if word in text_words:
            matching_words += 1
    
    if query_words:
        word_match_ratio = matching_words / len(query_words)
        score += word_match_ratio * 0.3
    
    # Normalize score to 0-1 range
    return min(score, 1.0)


# ========== CREATE/UPDATE/DELETE Endpoints (New - HTTP Communication) ==========

@router.post("/questions/collections/{collection_name}/documents/{doc_id}")
async def create_questions(
    collection_name: str,
    doc_id: str,
    request: QuestionsCreateRequest
):
    """
    Create new questions for a document (via RAG Service HTTP API)
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        request: Questions data (main_question, question_variants)
        
    Returns:
        Success response from RAG Service
    """
    try:
        logger.info(f"📝 Creating questions for {collection_name}/{doc_id}")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.create_questions(
            collection=collection_name,
            doc_id=doc_id,
            main_question=request.main_question,
            question_variants=request.question_variants
        )
        
        logger.info(f"✅ Questions created successfully for {doc_id}")
        
        return {
            "success": True,
            "data": result,
            "message": f"Questions created for {doc_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating questions for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create questions: {str(e)}"
        )


@router.put("/questions/collections/{collection_name}/documents/{doc_id}")
async def update_questions(
    collection_name: str,
    doc_id: str,
    request: QuestionsUpdateRequest,
    rebuild: bool = False
):
    """
    Update questions for a document (via RAG Service HTTP API)
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        request: Updated questions data
        rebuild: Whether to trigger VectorDB rebuild after update
        
    Returns:
        Success response with optional rebuild status
    """
    try:
        logger.info(f"✏️ Updating questions for {collection_name}/{doc_id} (rebuild={rebuild})")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.update_questions(
            collection=collection_name,
            doc_id=doc_id,
            main_question=request.main_question,
            question_variants=request.question_variants
        )
        
        logger.info(f"✅ Questions updated successfully for {doc_id}")
        
        # Trigger rebuild if requested
        rebuild_status = None
        if rebuild:
            try:
                logger.info(f"🔄 Triggering rebuild for {collection_name}/{doc_id}")
                rebuild_result = await rag_client.trigger_rebuild(
                    scope="document",
                    collection=collection_name,
                    doc_id=doc_id
                )
                rebuild_status = {
                    "triggered": True,
                    "pid": rebuild_result.get("pid"),
                    "message": rebuild_result.get("message")
                }
                logger.info(f"🚀 Rebuild triggered: PID {rebuild_result.get('pid')}")
            except Exception as e:
                logger.error(f"⚠️ Rebuild trigger failed: {e}")
                rebuild_status = {
                    "triggered": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": {
                "update_result": result,
                "rebuild_status": rebuild_status
            },
            "message": f"Questions updated for {doc_id}" + (" and rebuild triggered" if rebuild else "")
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating questions for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update questions: {str(e)}"
        )


@router.delete("/questions/collections/{collection_name}/documents/{doc_id}")
async def delete_questions(
    collection_name: str,
    doc_id: str,
    rebuild: bool = False
):
    """
    Delete questions file for a document (via RAG Service HTTP API)
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        rebuild: Whether to trigger VectorDB rebuild after deletion
        
    Returns:
        Success response with backup information
    """
    try:
        logger.info(f"🗑️ Deleting questions for {collection_name}/{doc_id} (rebuild={rebuild})")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.delete_questions(
            collection=collection_name,
            doc_id=doc_id
        )
        
        logger.info(f"✅ Questions deleted successfully for {doc_id}")
        
        # Trigger rebuild if requested
        rebuild_status = None
        if rebuild:
            try:
                logger.info(f"🔄 Triggering rebuild for {collection_name}/{doc_id}")
                rebuild_result = await rag_client.trigger_rebuild(
                    scope="document",
                    collection=collection_name,
                    doc_id=doc_id
                )
                rebuild_status = {
                    "triggered": True,
                    "pid": rebuild_result.get("pid"),
                    "message": rebuild_result.get("message")
                }
                logger.info(f"🚀 Rebuild triggered: PID {rebuild_result.get('pid')}")
            except Exception as e:
                logger.error(f"⚠️ Rebuild trigger failed: {e}")
                rebuild_status = {
                    "triggered": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": {
                "delete_result": result,
                "rebuild_status": rebuild_status
            },
            "message": f"Questions deleted for {doc_id}" + (" and rebuild triggered" if rebuild else "")
        }
        
    except Exception as e:
        logger.error(f"❌ Error deleting questions for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete questions: {str(e)}"
        )


@router.patch("/questions/collections/{collection_name}/documents/{doc_id}/variants")
async def update_variants(
    collection_name: str,
    doc_id: str,
    request: VariantsUpdateRequest,
    rebuild: bool = False
):
    """
    Update only question variants (keep main_question unchanged)
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        request: New variants list
        rebuild: Whether to trigger VectorDB rebuild after update
        
    Returns:
        Success response with optional rebuild status
    """
    try:
        logger.info(f"🔄 Updating variants for {collection_name}/{doc_id} (rebuild={rebuild})")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.update_variants(
            collection=collection_name,
            doc_id=doc_id,
            question_variants=request.question_variants
        )
        
        logger.info(f"✅ Variants updated successfully for {doc_id}")
        
        # Trigger rebuild if requested
        rebuild_status = None
        if rebuild:
            try:
                logger.info(f"🔄 Triggering rebuild for {collection_name}/{doc_id}")
                rebuild_result = await rag_client.trigger_rebuild(
                    scope="document",
                    collection=collection_name,
                    doc_id=doc_id
                )
                rebuild_status = {
                    "triggered": True,
                    "pid": rebuild_result.get("pid"),
                    "message": rebuild_result.get("message")
                }
                logger.info(f"🚀 Rebuild triggered: PID {rebuild_result.get('pid')}")
            except Exception as e:
                logger.error(f"⚠️ Rebuild trigger failed: {e}")
                rebuild_status = {
                    "triggered": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": {
                "update_result": result,
                "rebuild_status": rebuild_status
            },
            "message": f"Variants updated for {doc_id}" + (" and rebuild triggered" if rebuild else "")
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating variants for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update variants: {str(e)}"
        )


@router.post("/questions/collections/{collection_name}/documents/{doc_id}/restore")
async def restore_questions(
    collection_name: str,
    doc_id: str,
    request: RestoreRequest
):
    """
    Restore questions from backup file
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        request: Backup filename to restore from
        
    Returns:
        Success response
    """
    try:
        logger.info(f"♻️ Restoring questions for {collection_name}/{doc_id} from {request.backup_filename}")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.restore_questions(
            collection=collection_name,
            doc_id=doc_id,
            backup_filename=request.backup_filename
        )
        
        logger.info(f"✅ Questions restored successfully for {doc_id}")
        
        return {
            "success": True,
            "data": result,
            "message": f"Questions restored from backup for {doc_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error restoring questions for {collection_name}/{doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore questions: {str(e)}"
        )


# ========== Rebuild Management Endpoints ==========

@router.post("/questions/rebuild/trigger")
async def trigger_rebuild(
    scope: str = "all",
    collection: Optional[str] = None,
    doc_id: Optional[str] = None
):
    """
    Trigger VectorDB rebuild
    
    Args:
        scope: Rebuild scope (document, collection, all)
        collection: Collection name (required for document/collection scope)
        doc_id: Document ID (required for document scope)
        
    Returns:
        Rebuild trigger response with PID
    """
    try:
        logger.info(f"🚀 Triggering rebuild: scope={scope}, collection={collection}, doc_id={doc_id}")
        
        # Validate scope-specific requirements
        if scope == "document" and (not collection or not doc_id):
            raise HTTPException(
                status_code=400,
                detail="collection and doc_id are required for document scope"
            )
        
        if scope == "collection" and not collection:
            raise HTTPException(
                status_code=400,
                detail="collection is required for collection scope"
            )
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.trigger_rebuild(
            scope=scope,
            collection=collection,
            doc_id=doc_id
        )
        
        logger.info(f"✅ Rebuild triggered: PID {result.get('pid')}")
        
        return {
            "success": True,
            "data": result,
            "message": f"Rebuild triggered with scope '{scope}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error triggering rebuild: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger rebuild: {str(e)}"
        )


@router.get("/questions/rebuild/status")
async def get_rebuild_status():
    """
    Get rebuild process status
    
    Returns:
        Current rebuild status with progress
    """
    try:
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.get_rebuild_status()
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting rebuild status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get rebuild status: {str(e)}"
        )


@router.post("/questions/rebuild/cancel")
async def cancel_rebuild():
    """
    Cancel running rebuild process
    
    Returns:
        Success response
    """
    try:
        logger.info(f"⛔ Canceling rebuild process")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.cancel_rebuild()
        
        logger.info(f"✅ Rebuild canceled successfully")
        
        return {
            "success": True,
            "data": result,
            "message": "Rebuild process canceled"
        }
        
    except Exception as e:
        logger.error(f"❌ Error canceling rebuild: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel rebuild: {str(e)}"
        )


@router.delete("/questions/rebuild/status")
async def clear_rebuild_status():
    """
    Clear rebuild status file
    
    Returns:
        Success response
    """
    try:
        logger.info(f"🗑️ Clearing rebuild status")
        
        # Call RAG Service Internal API via HTTP
        rag_client = get_rag_client()
        result = await rag_client.clear_rebuild_status()
        
        logger.info(f"✅ Rebuild status cleared successfully")
        
        return {
            "success": True,
            "data": result,
            "message": "Rebuild status cleared"
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing rebuild status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear rebuild status: {str(e)}"
        )
