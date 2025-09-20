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
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..core.config import settings

logger = logging.getLogger(__name__)

class PathConfig:
    """Centralized path configuration for new document structure"""
    
    def __init__(self, base_data_dir: Optional[str] = None):
        self.base_data_dir = Path(base_data_dir or settings.data_root_dir)
        
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

# Global instance
path_config = PathConfig()
