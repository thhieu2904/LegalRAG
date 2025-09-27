"""
Analytics API Endpoints
=======================

Dashboard analytics endpoints for LegalRAG Admin
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import httpx
from datetime import datetime

from ..core.admin_path_config import get_admin_path_config

logger = logging.getLogger(__name__)
router = APIRouter()

import os

# Docker-aware RAG service URL
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8000")
if os.getenv("ENVIRONMENT") == "docker":
    RAG_SERVICE_URL = "http://rag-service:8000"  # Docker service name

@router.get("/analytics/dashboard")
async def get_dashboard_analytics():
    """
    Get dashboard analytics data
    
    Aggregates data from:
    - RAG service health endpoint (sessions, queries)
    - Local collections data (document counts)
    
    Returns:
        Dashboard statistics for frontend
    """
    try:
        # Get RAG service health data
        rag_data = {}
        rag_service_status = "unavailable"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{RAG_SERVICE_URL}/health", timeout=15.0)
                if response.status_code == 200:
                    rag_data = response.json()
                    rag_service_status = "healthy"
                    logger.info(f"✅ RAG service connected: {rag_data.get('active_sessions', 0)} sessions, {rag_data.get('metrics', {}).get('total_queries', 0)} queries")
                else:
                    logger.warning(f"⚠️ RAG service returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to RAG service: {e}")
            # Continue with empty rag_data
        
        # Get collections data using existing admin API logic
        # Use RAG service data for document count if available, otherwise fallback to admin counting
        total_collections = rag_data.get('total_collections', 0)
        total_documents = rag_data.get('total_documents', 0)
        
        # If RAG data not available, fallback to admin service counting
        if total_collections == 0 or total_documents == 0:
            try:
                path_config = get_admin_path_config()
                collection_names = path_config.list_collections()
                total_collections = len(collection_names)
                total_documents = 0
                
                # Use existing collections API to get accurate counts
                async with httpx.AsyncClient() as client:
                    collections_response = await client.get("http://localhost:8001/api/collections", timeout=5.0)
                    if collections_response.status_code == 200:
                        collections_data = collections_response.json()
                        if collections_data.get('success'):
                            total_documents = sum(col.get('document_count', 0) for col in collections_data.get('data', []))
                            logger.info(f"📊 Fallback count: {total_documents} documents from admin API")
            except Exception as e:
                logger.warning(f"⚠️ Error counting documents fallback: {e}")
                total_collections = 0
                total_documents = 0
        
        # Extract metrics from RAG service
        metrics = rag_data.get('metrics', {})
        active_sessions = rag_data.get('active_sessions', 0)
        total_queries = metrics.get('total_queries', 0)
        avg_response_time = metrics.get('avg_response_time', 0.0)
        
        # Try to get enhanced session data if available
        enhanced_session_data = {}
        try:
            async with httpx.AsyncClient() as client:
                session_response = await client.get(f"{RAG_SERVICE_URL}/api/v1/sessions/stats", timeout=3.0)
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    if session_data.get('success'):
                        enhanced_session_data = session_data.get('data', {})
                        logger.info(f"📊 Enhanced session data retrieved: {enhanced_session_data}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get enhanced session data: {e}")
            # Continue with basic data
        
        # Build dashboard response
        dashboard_data = {
            "success": True,
            "data": {
                "stats": {
                    "active_sessions": enhanced_session_data.get('total_active_sessions', active_sessions),
                    "total_queries_today": enhanced_session_data.get('today_session_count', total_queries),
                    "total_collections": total_collections,
                    "total_documents": total_documents,
                    "avg_response_time": round(avg_response_time, 2),
                    "session_format": enhanced_session_data.get('session_id_format', 'N/A'),
                    "next_session_id": enhanced_session_data.get('next_session_id', 'N/A')
                },
                "collections_summary": [
                    {
                        "name": f"collection_{i+1}",
                        "display_name": f"Bộ thủ tục {i+1}",
                        "document_count": "N/A"  # Simplified for dashboard
                    }
                    for i in range(min(5, total_collections))  # Top 5 for dashboard
                ],
                "system_status": {
                    "rag_service": rag_service_status,
                    "admin_service": "healthy", 
                    "total_collections": total_collections,
                    "collections_accessible": total_collections > 0,
                    "llm_loaded": rag_data.get('llm_loaded', False),
                    "embedding_device": rag_data.get('embedding_device', 'Unknown'),
                    "router_ready": rag_data.get('router_ready', False)
                },
                "timestamp": datetime.now().isoformat(),
                "rag_service_data": rag_data  # For debugging
            }
        }
        
        logger.info(f"📊 Dashboard analytics: {active_sessions} sessions, {total_queries} queries, {total_collections} collections, {total_documents} documents")
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@router.get("/analytics/collections-stats")
async def get_collections_stats():
    """
    Get detailed collection statistics
    
    Returns:
        Detailed stats per collection
    """
    try:
        path_config = get_admin_path_config()
        collection_names = path_config.list_collections()
        
        collections_stats = []
        
        for collection_name in collection_names:
            try:
                collection_dir = path_config.collections_dir / collection_name
                if collection_dir.exists():
                    # Count documents
                    doc_files = list(collection_dir.glob("*.json"))
                    doc_count = len([f for f in doc_files if not f.name.endswith('_metadata.json')])
                    
                    collections_stats.append({
                        "name": collection_name,
                        "display_name": collection_name.replace('_', ' ').title(),
                        "document_count": doc_count,
                        "query_count": 0  # Would need RAG service integration for query tracking
                    })
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing collection {collection_name}: {e}")
                collections_stats.append({
                    "name": collection_name,
                    "display_name": collection_name.replace('_', ' ').title(),
                    "document_count": 0,
                    "query_count": 0,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "data": collections_stats,
            "total": len(collections_stats)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting collections stats: {e}")
        raise HTTPException(status_code=500, detail=f"Collections stats error: {str(e)}")