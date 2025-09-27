"""
Collections API Endpoints
=========================

Handles collections listing and information using PathConfig service.
No hardcoded paths - full Docker/Local compatibility.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import json
from pathlib import Path

from ..core.path_config_adapter import get_path_config

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/collections")
async def list_collections():
    """
    Get list of all collections with metadata
    
    Returns:
        List of collections with document counts and descriptions
    """
    try:
        path_config = get_path_config()
        logger.info(f"🔍 Listing collections from: {path_config.collections_dir}")
        
        # Use PathConfig's list_collections method
        collection_names = path_config.list_collections()
        logger.info(f"📁 Found {len(collection_names)} collections: {collection_names}")
        
        collections_data = []
        
        for collection_name in collection_names:
            try:
                # Get collection metadata
                metadata_file = path_config.get_collection_metadata(collection_name)
                collection_info = {
                    "name": collection_name,
                    "display_name": _format_collection_display_name(collection_name),
                    "document_count": 0,
                    "description": f"Bộ sưu tập {_format_collection_display_name(collection_name)}",
                    "metadata_exists": False
                }
                
                # Load metadata.json if exists
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        collection_info.update({
                            "document_count": len(metadata.get("documents", [])),
                            "description": metadata.get("description", collection_info["description"]),
                            "metadata_exists": True
                        })
                        
                        # Add additional metadata if available
                        if "collection_name" in metadata:
                            collection_info["display_name"] = metadata["collection_name"]
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error loading metadata for {collection_name}: {e}")
                
                collections_data.append(collection_info)
                logger.info(f"✅ Collection {collection_name}: {collection_info['document_count']} documents")
                
            except Exception as e:
                logger.error(f"❌ Error processing collection {collection_name}: {e}")
                # Add basic info even if error
                collections_data.append({
                    "name": collection_name,
                    "display_name": _format_collection_display_name(collection_name),
                    "document_count": 0,
                    "description": f"Lỗi khi tải thông tin {collection_name}",
                    "metadata_exists": False,
                    "error": str(e)
                })
        
        # Sort by document count (descending)
        collections_data.sort(key=lambda x: x["document_count"], reverse=True)
        
        logger.info(f"📊 Total collections returned: {len(collections_data)}")
        
        return {
            "success": True,
            "data": collections_data,
            "total": len(collections_data),
            "message": f"Found {len(collections_data)} collections"
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing collections: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list collections: {str(e)}"
        )

@router.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """
    Get detailed information about a specific collection
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Detailed collection information
    """
    try:
        path_config = get_path_config()
        
        # Verify collection exists
        available_collections = path_config.list_collections()
        if collection_name not in available_collections:
            raise HTTPException(
                status_code=404, 
                detail=f"Collection '{collection_name}' not found. Available: {available_collections}"
            )
        
        # Get collection metadata
        metadata_file = path_config.get_collection_metadata(collection_name)
        collection_info = {
            "name": collection_name,
            "display_name": _format_collection_display_name(collection_name),
            "document_count": 0,
            "documents": [],
            "metadata_exists": metadata_file.exists()
        }
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                documents = metadata.get("documents", [])
                collection_info.update({
                    "document_count": len(documents),
                    "description": metadata.get("description", ""),
                    "documents": documents[:5]  # Preview of first 5 documents
                })
                
                # Add collection-level metadata
                for field in ["collection_name", "created_date", "updated_date"]:
                    if field in metadata:
                        collection_info[field] = metadata[field]
                        
            except Exception as e:
                logger.warning(f"⚠️ Error loading metadata for {collection_name}: {e}")
                collection_info["error"] = str(e)
        
        logger.info(f"📋 Collection info for {collection_name}: {collection_info['document_count']} documents")
        
        return {
            "success": True,
            "data": collection_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting collection info for {collection_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection info: {str(e)}"
        )

def _format_collection_display_name(collection_name: str) -> str:
    """
    Format collection name for display
    
    Args:
        collection_name: Raw collection name (e.g., "quy_trinh_cap_ho_tich_cap_xa")
        
    Returns:
        Formatted display name (e.g., "Quy Trình Cấp Hộ Tịch Cấp Xã")
    """
    # Replace underscores with spaces and capitalize each word
    display_name = collection_name.replace('_', ' ').title()
    
    # Handle Vietnamese specific formatting
    vietnamese_replacements = {
        'Quy Trinh': 'Quy Trình',
        'Ho Tich': 'Hộ Tịch', 
        'Cong Chung': 'Công Chứng',
        'Chung Thuc': 'Chứng Thực',
        'Luat Su': 'Luật Sư',
        'Boi Thuong': 'Bồi Thường',
        'Dau Gia': 'Đấu Giá',
        'Tai San': 'Tài Sản',
        'Con Nuoi': 'Con Nuôi',
        'Quan Tai': 'Quan Tài',
        'Trong Tai': 'Trọng Tài',
        'Thuong Mai': 'Thương Mại',
        'Tu Van': 'Tư Vấn',
        'Phap Luat': 'Pháp Luật'
    }
    
    for old, new in vietnamese_replacements.items():
        display_name = display_name.replace(old, new)
    
    return display_name