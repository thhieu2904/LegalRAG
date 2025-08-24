"""
🔧 SIMPLIFIED ROUTER API - BACKEND PURE BUSINESS LOGIC

This module provides CLEAN backend APIs that only return business data.
All presentation logic moved to frontend for better scalability.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import os
import json

from ..services.router import QueryRouter
from ..core.config import settings

# Setup router
router = APIRouter(prefix="/router", tags=["Router Business API"])

# Global router instance
_router_instance = None
_embedding_model = None

def get_router_instance() -> QueryRouter:
    """Get router instance for business operations"""
    global _router_instance, _embedding_model
    
    if _router_instance is None:
        try:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
            
            _router_instance = QueryRouter(_embedding_model)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize router: {e}")
    
    return _router_instance

@router.get("/health", summary="Router Health Check")
async def router_health():
    """Health check for router service - business data only"""
    try:
        router_instance = get_router_instance()
        return {
            "status": "healthy", 
            "collection_count": len(router_instance.collection_mappings),
            "question_count": len(router_instance.example_questions),
            "cache_loaded": bool(router_instance.example_questions)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/collections", summary="Get Collections - Business Data Only")
async def get_collections_business_data(router_instance: QueryRouter = Depends(get_router_instance)):
    """
    Get collections with PURE BUSINESS DATA only.
    NO display logic, NO UI concerns - frontend handles all presentation.
    """
    try:
        # Get raw collections from file system
        collections = []
        base_path = "data/storage/collections"
        
        if os.path.exists(base_path):
            for collection_name in os.listdir(base_path):
                collection_path = os.path.join(base_path, collection_name)
                
                if os.path.isdir(collection_path):
                    # Count documents
                    documents_path = os.path.join(collection_path, "documents")
                    document_count = 0
                    question_count = 0
                    
                    if os.path.exists(documents_path):
                        for doc_name in os.listdir(documents_path):
                            doc_path = os.path.join(documents_path, doc_name)
                            if os.path.isdir(doc_path):
                                questions_file = os.path.join(doc_path, "questions.json")
                                if os.path.exists(questions_file):
                                    document_count += 1
                                    # Count questions in this document
                                    try:
                                        with open(questions_file, 'r', encoding='utf-8') as f:
                                            doc_data = json.load(f)
                                            variants = doc_data.get('question_variants', [])
                                            question_count += 1 + len(variants)  # main + variants
                                    except:
                                        question_count += 1  # fallback count
                    
                    # Get metadata if available
                    metadata_file = os.path.join(collection_path, "metadata.json")
                    metadata = {}
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    collections.append({
                        "id": collection_name,  # Pure backend identifier
                        "document_count": document_count,
                        "question_count": question_count,
                        "status": "active" if document_count > 0 else "empty",
                        "last_updated": metadata.get('last_updated'),
                        "data_version": metadata.get('version', '1.0'),
                        "path": collection_path
                    })
        
        return {
            "collections": collections,
            "total": len(collections),
            "api_version": "2.0",
            "response_type": "business_data"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collections: {e}")

@router.get("/collections/{collection_id}/questions", summary="Get Questions - Business Data Only")
async def get_collection_questions_business_data(
    collection_id: str,
    router_instance: QueryRouter = Depends(get_router_instance)
):
    """
    Get questions with PURE BUSINESS DATA only.
    NO display formatting, NO UI mapping - frontend handles all presentation.
    """
    try:
        # Get raw questions from router with optimization
        questions = []
        
        # 🚀 OPTIMIZATION: Sử dụng method mới thay vì truy cập trực tiếp
        try:
            # Sử dụng method mới với limit
            raw_questions = router_instance.get_example_questions_for_collection(collection_id)
            
            # Giới hạn số lượng để tránh performance issues
            limited_questions = raw_questions[:100]  # Chỉ trả về 100 questions đầu tiên
            
            for question_data in limited_questions:
                # Return pure business data
                questions.append({
                    "id": question_data.get('id'),
                    "text": question_data.get('text'),
                    "type": question_data.get('type', 'main'),
                    "document": question_data.get('document'),
                    "source_file": question_data.get('source'),
                    "category": question_data.get('category', 'general'),
                    "metadata": question_data.get('metadata', {})
                })
            
            logger.info(f"🚀 OPTIMIZATION: Retrieved {len(questions)} questions from {collection_id} (limited from {len(raw_questions)})")
            
        except Exception as e:
            logger.warning(f"⚠️ Error using optimized method, falling back to direct access: {e}")
            # Fallback: Truy cập trực tiếp nhưng giới hạn
            for question_data in list(router_instance.example_questions.items())[:50]:  # Chỉ 50 items
                if question_data[0] == collection_id:
                    # Return pure business data
                    questions.append({
                        "id": question_data[1].get('id'),
                        "text": question_data[1].get('text'),
                        "type": question_data[1].get('type', 'main'),
                        "document": question_data[1].get('document'),
                        "source_file": question_data[1].get('source'),
                        "category": question_data[1].get('category', 'general'),
                        "metadata": question_data[1].get('metadata', {})
                    })
        
        return {
            "collection_id": collection_id,
            "questions": questions,
            "total": len(questions),
            "api_version": "2.0",
            "response_type": "business_data"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting questions for {collection_id}: {e}")

@router.get("/collections/{collection_id}/stats", summary="Collection Statistics")
async def get_collection_stats(
    collection_id: str,
    router_instance: QueryRouter = Depends(get_router_instance)
):
    """Get detailed statistics for a collection"""
    try:
        # Count different types of questions with optimization
        main_questions = 0
        variant_questions = 0
        documents = set()
        
        # 🚀 OPTIMIZATION: Sử dụng method mới thay vì truy cập trực tiếp
        try:
            raw_questions = router_instance.get_example_questions_for_collection(collection_id)
            
            for question_data in raw_questions:
                if question_data.get('type') == 'main':
                    main_questions += 1
                else:
                    variant_questions += 1
                
                if question_data.get('document'):
                    documents.add(question_data.get('document'))
            
            logger.info(f"🚀 OPTIMIZATION: Counted stats from {len(raw_questions)} questions for {collection_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error using optimized method, falling back to direct access: {e}")
            # Fallback: Truy cập trực tiếp nhưng giới hạn
            for question_data in list(router_instance.example_questions.items())[:50]:  # Chỉ 50 items
                if question_data[0] == collection_id:
                    if question_data[1].get('type') == 'main':
                        main_questions += 1
                    else:
                        variant_questions += 1
                    
                    if question_data[1].get('document'):
                        documents.add(question_data[1].get('document'))
        
        return {
            "collection_id": collection_id,
            "statistics": {
                "total_questions": main_questions + variant_questions,
                "main_questions": main_questions,
                "variant_questions": variant_questions,
                "document_count": len(documents),
                "avg_questions_per_document": round((main_questions + variant_questions) / max(len(documents), 1), 2)
            },
            "documents": list(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats for {collection_id}: {e}")
