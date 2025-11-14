"""
Centralized Path Configuration for New Document Structure
=========================================================

Manages all paths for the new collection-based document structure while
maintaining backward compatibility with the old structure.

New Structure:
data/storage/collections/{collection}/documents/DOC_XXX/
├── original_name.json          ← RAG content  
├── original_name.doc           ← Original document
├── router_questions.json       ← Router questions
└── forms/                      ← Forms directory

Docker Compatibility:
- Auto-detects local vs Docker environment
- Handles path resolution for both Windows and Linux
- Supports environment variable overrides
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..core.config import settings

logger = logging.getLogger(__name__)

class PathConfig:
    """Centralized path configuration for new document structure with Docker support"""
    
    def __init__(self, base_data_dir: Optional[str] = None, force_environment: Optional[str] = None):
        # Environment detection and base path setup
        self.environment = self._detect_environment(force_environment)
        self.base_data_dir = self._configure_base_data_dir(base_data_dir)
        
        logger.info(f"PathConfig initialized for {self.environment} environment")
        logger.info(f"Base data dir: {self.base_data_dir}")
        
        # NEW STRUCTURE PATHS
        self.storage_dir = self.base_data_dir / "storage"
        self.collections_dir = self.storage_dir / "collections"
        self.registry_dir = self.storage_dir / "registry"
        
        # OLD STRUCTURE PATHS (for backward compatibility)
        self.old_documents_dir = self.base_data_dir / "documents"
        self.old_router_dir = self.base_data_dir / "router_examples_smart_v3"
        
        # REGISTRIES
        self.collections_registry = self.registry_dir / "collections.json"
        self.documents_registry = self.registry_dir / "documents.json"
        
        # CACHE
        self.cache_dir = self.base_data_dir / "cache"
        self.router_cache = self.cache_dir / "router_embeddings.pkl"
    
    def _detect_environment(self, force_environment: Optional[str] = None) -> str:
        """
        Auto-detect if running in Docker or local environment
        
        Returns:
            'docker' or 'local'
        """
        if force_environment:
            return force_environment
        
        # Method 1: Check for PYTHONPATH=/app (set in Docker)
        if os.getenv("PYTHONPATH") == "/app":
            return "docker"
        
        # Method 2: Check if we're in /app/ directory
        current_file = Path(__file__).resolve()
        if str(current_file).startswith("/app/"):
            return "docker"
        
        # Method 3: Check for Docker-specific environment variables
        if os.getenv("ENVIRONMENT") == "docker":
            return "docker"
        
        # Method 4: Check if settings.data_root_dir is Docker-like
        if hasattr(settings, 'data_root_dir') and str(settings.data_root_dir).startswith("/app/"):
            return "docker"
        
        # Default: assume local
        return "local"
    
    def _configure_base_data_dir(self, base_data_dir: Optional[str] = None) -> Path:
        """
        Configure base data directory based on environment
        
        Args:
            base_data_dir: Override base data directory
            
        Returns:
            Configured Path object
        """
        # Priority 1: Explicit parameter
        if base_data_dir:
            return Path(base_data_dir)
        
        # Priority 2: Environment variable
        env_data_path = os.getenv("LEGALRAG_DATA_PATH")
        if env_data_path:
            return Path(env_data_path)
        
        # Priority 3: Environment-specific defaults
        if self.environment == "docker":
            # Docker: data is mounted at /app/data
            return Path("/app/data")
        else:
            # Local: use settings or calculate from file location
            if hasattr(settings, 'data_root_dir') and not settings.data_root_dir.startswith("data"):
                # If data_root_dir is absolute path, use it
                return Path(settings.data_root_dir)
            else:
                # Calculate from current file: app/core/path_config.py -> rag_service/data
                base_service_dir = Path(__file__).parent.parent.parent
                return base_service_dir / "data"
    
    def resolve_cross_platform_path(self, path_str: str) -> Path:
        """
        Resolve path string to work across Windows/Linux and Docker/local
        
        Args:
            path_str: Path string that may contain platform-specific separators
            
        Returns:
            Resolved Path object
        """
        # Normalize separators
        normalized = path_str.replace("\\", "/")
        
        # 🔧 DOCKER FIX: Handle absolute Windows paths in Docker environment
        if self.environment == "docker":
            logger.info(f"🔧 DEBUG: Processing path in Docker: {normalized}")
            # Check for Windows absolute path patterns: D:\... or D:/...
            windows_patterns = [
                "Personal/LegalRAG_OCR/rag_service/data/",
                "Personal\\LegalRAG_OCR\\rag_service\\data\\",
            ]
            
            for pattern in windows_patterns:
                if pattern in normalized:
                    logger.info(f"🔧 DEBUG: Found pattern '{pattern}' in path")
                    # Extract relative path from Windows absolute path
                    # D:\Personal\LegalRAG_OCR\rag_service\data\storage\collections\...
                    # -> /app/data/storage/collections/...
                    parts = normalized.split(pattern)
                    if len(parts) > 1:
                        relative_path = parts[1]
                        docker_path = Path(f"/app/data/{relative_path}")
                        logger.info(f"🔧 Converted Windows absolute path to Docker: {path_str} -> {docker_path}")
                        return docker_path
        
        # Handle relative paths
        if normalized.startswith("../"):
            # Remove ../ and resolve from base
            relative_part = normalized[3:]
            if self.environment == "docker":
                # In Docker, go up from /app/app/services -> /app
                return Path("/app") / relative_part
            else:
                # In local, use parent of rag_service
                base_parent = Path(__file__).parent.parent.parent.parent
                return base_parent / relative_part
        
        elif normalized.startswith("data/"):
            # Relative to base data directory
            return self.base_data_dir.parent / normalized
        
        else:
            # Assume relative to data directory
            return self.base_data_dir / normalized
    
    def get_collection_dir(self, collection_name: str) -> Path:
        """Get collection directory path"""
        return self.collections_dir / collection_name
    
    def get_collection_documents_dir(self, collection_name: str) -> Path:
        """Get collection documents directory"""
        return self.get_collection_dir(collection_name) / "documents"
    
    def get_collection_metadata(self, collection_name: str) -> Path:
        """Get collection metadata file path"""
        return self.get_collection_dir(collection_name) / "metadata.json"
    
    def get_document_dir(self, collection_name: str, doc_id: str) -> Path:
        """Get specific document directory (DOC_XXX)"""
        return self.get_collection_documents_dir(collection_name) / doc_id
    
    def get_document_content(self, collection_name: str, doc_id: str) -> Tuple[Optional[Path], Optional[Path]]:
        """Get document content files (.json and .doc/.docx)"""
        doc_dir = self.get_document_dir(collection_name, doc_id)
        
        # Find JSON file (exclude router_questions.json)
        json_files = [f for f in doc_dir.glob("*.json") if f.name != "router_questions.json"]
        json_file = json_files[0] if json_files else None
        
        # Find DOC file
        doc_files = list(doc_dir.glob("*.doc*"))
        doc_file = doc_files[0] if doc_files else None
        
        return json_file, doc_file
    
    def load_document_json(self, collection_name: str, doc_id: str) -> Optional[Dict]:
        """Load document JSON content"""
        json_file, _ = self.get_document_content(collection_name, doc_id)
        if not json_file or not json_file.exists():
            return None
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON for {collection_name}/{doc_id}: {e}")
            return None
    
    def get_document_router(self, collection_name: str, doc_id: str) -> Path:
        """Get document router questions file"""
        return self.get_document_dir(collection_name, doc_id) / "router_questions.json"
    
    def get_document_forms_dir(self, collection_name: str, doc_id: str) -> Path:
        """Get document forms directory"""
        return self.get_document_dir(collection_name, doc_id) / "forms"
    
    def list_collections(self) -> List[str]:
        """List all available collections"""
        if not self.collections_dir.exists():
            return []
        
        collections = []
        for item in self.collections_dir.iterdir():
            if item.is_dir() and (item / "documents").exists():
                collections.append(item.name)
        
        return sorted(collections)
    
    def list_documents(self, collection_name: str) -> List[Dict]:
        """List all documents in a collection"""
        docs_dir = self.get_collection_documents_dir(collection_name)
        if not docs_dir.exists():
            return []
        
        documents = []
        for doc_dir in sorted(docs_dir.iterdir()):
            if not doc_dir.is_dir():
                continue
            
            json_file, doc_file = self.get_document_content(collection_name, doc_dir.name)
            router_file = self.get_document_router(collection_name, doc_dir.name)
            forms_dir = self.get_document_forms_dir(collection_name, doc_dir.name)
            
            documents.append({
                "doc_id": doc_dir.name,
                "json_file": json_file.name if json_file else None,
                "doc_file": doc_file.name if doc_file else None,
                "has_router": router_file.exists(),
                "has_forms": forms_dir.exists() and any(forms_dir.iterdir()),
                "json_path": str(json_file) if json_file else None,
                "doc_path": str(doc_file) if doc_file else None,
                "router_path": str(router_file) if router_file.exists() else None,
                "forms_path": str(forms_dir) if forms_dir.exists() else None
            })
        
        return documents
    
    def get_document_forms_path(self, collection_name: str, doc_id: str) -> Optional[Path]:
        """Get forms directory path for a document"""
        forms_dir = self.get_document_forms_dir(collection_name, doc_id)
        return forms_dir if forms_dir.exists() else None
    
    def find_document_by_name(self, collection_name: str, document_name: str) -> Optional[Dict]:
        """Find document by its original filename"""
        documents = self.list_documents(collection_name)
        
        for doc in documents:
            if doc["json_file"] and document_name in doc["json_file"]:
                return doc
            if doc["doc_file"] and document_name in doc["doc_file"]:
                return doc
        
        return None
    
    def get_all_document_contents(self) -> List[Dict]:
        """Get all document content files across all collections"""
        all_documents = []
        
        for collection in self.list_collections():
            documents = self.list_documents(collection)
            for doc in documents:
                if doc["json_path"]:
                    all_documents.append({
                        "collection": collection,
                        "doc_id": doc["doc_id"],
                        "json_path": doc["json_path"],
                        "doc_path": doc["doc_path"],
                        "router_path": doc["router_path"],
                        "document_name": doc["json_file"].replace(".json", "") if doc["json_file"] else doc["doc_id"]
                    })
        
        return all_documents
    
    def get_all_router_files(self) -> List[Dict]:
        """Get all router files across all collections"""
        router_files = []
        
        for collection in self.list_collections():
            documents = self.list_documents(collection)
            for doc in documents:
                if doc["router_path"]:
                    router_files.append({
                        "collection": collection,
                        "doc_id": doc["doc_id"],
                        "router_path": doc["router_path"],
                        "document_name": doc["json_file"].replace(".json", "") if doc["json_file"] else doc["doc_id"]
                    })
        
        return router_files
    
    def is_new_structure_available(self) -> bool:
        """Check if new structure is available and populated"""
        return (self.collections_dir.exists() and 
                len(self.list_collections()) > 0)
    
    def is_old_structure_available(self) -> bool:
        """Check if old structure still exists"""
        return (self.old_documents_dir.exists() and 
                any(self.old_documents_dir.iterdir()))
    
    def get_migration_status(self) -> Dict:
        """Get migration status information"""
        return {
            "new_structure_available": self.is_new_structure_available(),
            "old_structure_available": self.is_old_structure_available(),
            "collections_count": len(self.list_collections()),
            "total_documents": sum(len(self.list_documents(col)) for col in self.list_collections()),
            "registry_files_exist": self.collections_registry.exists() and self.documents_registry.exists()
        }

    def verify_paths(self) -> Dict:
        """
        Verify that all configured paths exist and are accessible
        
        Returns:
            Dictionary with verification results
        """
        results = {
            "environment": self.environment,
            "paths_status": {},
            "all_paths_exist": True,
            "warnings": []
        }
        
        paths_to_check = {
            "base_data_dir": self.base_data_dir,
            "storage_dir": self.storage_dir,
            "collections_dir": self.collections_dir,
            "registry_dir": self.registry_dir,
            "cache_dir": self.cache_dir
        }
        
        for name, path in paths_to_check.items():
            exists = path.exists()
            is_dir = path.is_dir() if exists else False
            
            results["paths_status"][name] = {
                "path": str(path),
                "exists": exists,
                "is_directory": is_dir
            }
            
            if not exists:
                results["all_paths_exist"] = False
                results["warnings"].append(f"Path does not exist: {path}")
            elif exists and not is_dir:
                results["warnings"].append(f"Path is not a directory: {path}")
        
        return results

# Global instance
path_config = PathConfig()
