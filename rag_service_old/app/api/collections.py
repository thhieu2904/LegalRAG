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

@router.get("/collections")
async def get_collections():
    """
    Lấy danh sách tất cả collections với metadata đầy đủ
    Sử dụng cho Admin Service dashboard
    """
    try:
        logger.info("🔍 Starting collections API call...")
        
        # Path to collections directory
        collections_path = Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
        logger.info(f"📁 Looking for collections in: {collections_path}")
        logger.info(f"📁 Collections path exists: {collections_path.exists()}")
        
        if not collections_path.exists():
            logger.error(f"❌ Collections directory not found: {collections_path}")
            # Return empty list instead of error for compatibility
            return []
        
        # Get detailed collection info
        collections = []
        logger.info(f"📂 Scanning directory contents...")
        
        directory_items = list(collections_path.iterdir())
        logger.info(f"📂 Found {len(directory_items)} items in collections directory")
        
        for item in directory_items:
            try:
                if item.is_dir() and not item.name.startswith('.'):
                    logger.info(f"📁 Processing collection: {item.name}")
                    collection_info = await _get_collection_metadata(item.name, collections_path)
                    collections.append(collection_info)
                    logger.info(f"✅ Collection {item.name} processed successfully")
                else:
                    logger.info(f"⏭️ Skipping non-directory item: {item.name}")
            except Exception as e:
                logger.error(f"❌ Error processing collection {item.name}: {e}")
                # Continue with other collections
                continue
        
        # Sort by name for consistency
        collections.sort(key=lambda x: x['name'])
        
        logger.info(f"✅ Successfully processed {len(collections)} collections")
        
        return collections
        
    except Exception as e:
        logger.error(f"❌ Fatal error in get_collections: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Return empty list instead of 500 error for better compatibility
        return []

async def _get_collection_metadata(collection_name: str, collections_path: Path) -> Dict[str, Any]:
    """Get detailed metadata for a single collection"""
    collection_dir = collections_path / collection_name
    
    # Basic info
    collection_info = {
        "name": collection_name,
        "display_name": _format_display_name(collection_name),
        "document_count": 0,
        "description": f"Bộ sưu tập {_format_display_name(collection_name)}",
        "metadata_exists": False,
        "last_updated": None
    }
    
    try:
        # Count documents
        documents_dir = collection_dir / "documents"
        if documents_dir.exists():
            doc_dirs = [d for d in documents_dir.iterdir() if d.is_dir() and d.name.startswith('DOC_')]
            collection_info["document_count"] = len(doc_dirs)
        
        # Load metadata.json if exists
        metadata_file = collection_dir / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            collection_info.update({
                "display_name": metadata.get("collection_name", collection_info["display_name"]),
                "description": metadata.get("description", collection_info["description"]),
                "document_count": len(metadata.get("documents", [])),
                "metadata_exists": True,
                "last_updated": metadata.get("last_updated")
            })
    
    except Exception as e:
        logger.warning(f"⚠️ Error loading metadata for {collection_name}: {e}")
    
    return collection_info

def _format_display_name(collection_name: str) -> str:
    """Format collection name for display"""
    # Convert snake_case to Title Case
    return collection_name.replace('_', ' ').title()

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