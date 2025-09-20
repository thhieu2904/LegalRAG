"""
Collections API - Cung cấp danh sách collections cho frontend mapping
"""
import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from ..core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/collections", response_model=Dict[str, List[str]])
async def get_collections():
    """
    Lấy danh sách tất cả collections có sẵn
    Frontend sử dụng để mapping display names
    """
    try:
        # Path to collections directory
        collections_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
        
        if not collections_path.exists():
            logger.error(f"Collections directory not found: {collections_path}")
            raise HTTPException(status_code=500, detail="Collections directory not found")
        
        # Get list of collection directories
        collections = []
        for item in collections_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                collections.append(item.name)
        
        # Sort for consistency
        collections.sort()
        
        logger.info(f"✅ Found {len(collections)} collections")
        
        return {
            "collections": collections,
            "total_count": len(collections)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """
    Lấy thông tin chi tiết của một collection
    """
    try:
        collections_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
        collection_path = collections_path / collection_name
        
        if not collection_path.exists():
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
        # Count documents
        documents_path = collection_path / "documents"
        document_count = 0
        if documents_path.exists():
            document_count = len([d for d in documents_path.iterdir() if d.is_dir() and d.name.startswith("DOC_")])
        
        # Basic collection info
        collection_info = {
            "name": collection_name,
            "document_count": document_count,
            "path": str(collection_path),
            "exists": collection_path.exists()
        }
        
        return collection_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting collection info for '{collection_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))