"""
Questions API Endpoints
=======================

Handles questions management using PathConfig service.
Loads and processes questions.json files with proper encoding.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging
import json
from pathlib import Path

from ..core.path_config_adapter import get_path_config

logger = logging.getLogger(__name__)
router = APIRouter()

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
        path_config = get_path_config()
        
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
        path_config = get_path_config()
        
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
        path_config = get_path_config()
        
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