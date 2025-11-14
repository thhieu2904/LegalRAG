"""
Lightweight PathConfig for Admin Service
========================================

Simplified version of RAG service PathConfig focused on admin operations.
Handles Docker/Local path resolution without complex imports.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AdminPathConfig:
    """Simplified PathConfig for Admin Service operations"""
    
    def __init__(self):
        # Environment detection
        self.environment = self._detect_environment()
        self.base_data_dir = self._configure_base_data_dir()
        
        # Storage paths
        # NOTE: In Docker, base_data_dir already points to storage directory
        #       In local, base_data_dir points to rag_service/data/storage
        if self.base_data_dir.name == "storage":
            # Already pointing to storage directory
            self.storage_dir = self.base_data_dir
        else:
            # Legacy path structure (should not happen with new config)
            self.storage_dir = self.base_data_dir / "storage"
        
        self.collections_dir = self.storage_dir / "collections"
        
        logger.info(f"AdminPathConfig initialized:")
        logger.info(f"  Environment: {self.environment}")
        logger.info(f"  Base data dir: {self.base_data_dir}")
        logger.info(f"  Storage dir: {self.storage_dir}")
        logger.info(f"  Collections dir: {self.collections_dir}")
        logger.info(f"  ✅ Admin service: Lightweight read-only mode (NO models, NO vectordb)")
    
    def _detect_environment(self) -> str:
        """Auto-detect if running in Docker or local environment"""
        # Method 1: Check for ENVIRONMENT variable
        if os.getenv("ENVIRONMENT") == "docker":
            return "docker"
        
        # Method 2: Check for PYTHONPATH=/app (Docker)
        if os.getenv("PYTHONPATH") == "/app":
            return "docker"
        
        # Method 3: Check if we're in /app/ directory
        current_file = Path(__file__).resolve()
        if str(current_file).startswith("/app/"):
            return "docker"
        
        # Default: local
        return "local"
    
    def _configure_base_data_dir(self) -> Path:
        """Configure base data directory based on environment
        
        IMPORTANT: This path should point to the storage directory
        - In Docker: /app/data/storage (mounted from RAG service data/storage)
        - Local: rag_service/data/storage
        
        This ensures admin service only accesses storage (collections, documents)
        and NOT models, vectordb, or cache.
        """
        if self.environment == "docker":
            # In Docker, storage is mounted at /app/data/storage
            # This is the only data admin service needs to access
            return Path("/app/data/storage")
        else:
            # Local: relative to admin_service directory
            admin_service_dir = Path(__file__).parent.parent.parent
            rag_service_dir = admin_service_dir.parent / "rag_service"
            return rag_service_dir / "data" / "storage"
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        if not self.collections_dir.exists():
            logger.warning(f"Collections directory not found: {self.collections_dir}")
            return []
        
        collections = []
        for item in self.collections_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                collections.append(item.name)
        
        return sorted(collections)
    
    def list_documents(self, collection_name: str) -> List[Dict]:
        """List documents in a collection"""
        collection_dir = self.collections_dir / collection_name / "documents"
        
        if not collection_dir.exists():
            logger.warning(f"Collection documents directory not found: {collection_dir}")
            return []
        
        documents = []
        for doc_dir in collection_dir.iterdir():
            if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                continue
            
            # Find JSON and DOC files
            json_files = list(doc_dir.glob("*.json"))
            json_files = [f for f in json_files if f.name != "questions.json"]
            doc_files = list(doc_dir.glob("*.doc")) + list(doc_dir.glob("*.docx"))
            
            documents.append({
                "doc_id": doc_dir.name,
                "json_file": json_files[0].name if json_files else None,
                "doc_file": doc_files[0].name if doc_files else None,
                "has_questions": (doc_dir / "questions.json").exists(),
                "has_forms": (doc_dir / "forms").exists(),
                "json_path": str(json_files[0]) if json_files else None,
                "doc_path": str(doc_files[0]) if doc_files else None
            })
        
        return documents
    
    def get_collection_dir(self, collection_name: str) -> Path:
        """Get collection directory path"""
        return self.collections_dir / collection_name
    
    def get_collection_metadata(self, collection_name: str) -> Path:
        """Get collection metadata file path"""
        return self.collections_dir / collection_name / "metadata.json"
    
    def get_document_dir(self, collection_name: str, doc_id: str) -> Path:
        """Get document directory path"""
        return self.collections_dir / collection_name / "documents" / doc_id
    
    def load_document_json(self, collection_name: str, doc_id: str) -> Optional[Dict]:
        """Load document JSON data"""
        doc_dir = self.get_document_dir(collection_name, doc_id)
        
        # Find JSON file (exclude questions.json)
        json_files = [f for f in doc_dir.glob("*.json") if f.name != "questions.json"]
        
        if not json_files:
            return None
        
        try:
            with open(json_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading document JSON: {e}")
            return None

# Global instance
_admin_path_config = None

def get_admin_path_config() -> AdminPathConfig:
    """Get global AdminPathConfig instance"""
    global _admin_path_config
    
    if _admin_path_config is None:
        _admin_path_config = AdminPathConfig()
    
    return _admin_path_config