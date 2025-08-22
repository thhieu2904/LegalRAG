"""
Hybrid Document Service - Backward compatible service during migration
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

from ..services.document_manager import DocumentManagerService
from ..core.config import settings

logger = logging.getLogger(__name__)

class HybridDocumentService:
    """
    Service that can read from both old and new structure during migration
    
    Migration phases:
    1. Read from old structure primarily, new structure as fallback
    2. Read from both structures, prefer new structure
    3. Read from new structure only
    """
    
    def __init__(self, migration_phase: int = 1):
        self.migration_phase = migration_phase
        
        # New structure manager
        self.new_manager = DocumentManagerService()
        
        # Old structure paths
        self.old_documents_dir = Path(settings.data_root_dir) / "documents"
        self.old_router_dir = Path(settings.data_root_dir) / "router_examples_smart_v3"
        
        # Collection mappings
        self.collection_mappings = {
            'quy_trinh_cap_ho_tich_cap_xa': 'ho_tich_cap_xa',
            'ho_tich_cap_xa_moi_nhat': 'ho_tich_cap_xa',
            'quy_trinh_chung_thuc': 'chung_thuc',
            'quy_trinh_nb_chung_thuc_dung_chung': 'chung_thuc',
            'quy_trinh_nuoi_con_nuoi': 'nuoi_con_nuoi',
            'iso_ncn_moi': 'nuoi_con_nuoi',
        }
        
        logger.info(f"HybridDocumentService initialized - Phase {migration_phase}")
    
    def get_document_by_title(self, collection_id: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Find document by title, checking both old and new structure
        """
        logger.info(f"🔍 Searching for document: '{title}' in collection: '{collection_id}' (phase: {self.migration_phase})")
        
        # Phase 2+: Check new structure first
        if self.migration_phase >= 2:
            logger.info(f"🔍 Phase {self.migration_phase}: Checking new structure first")
            new_doc = self._get_document_from_new_structure(collection_id, title)
            if new_doc:
                logger.info(f"✅ Found in new structure: {new_doc.get('title')}")
                return new_doc
        
        # Check old structure
        logger.info(f"🔍 Checking old structure...")
        old_doc = self._get_document_from_old_structure(collection_id, title)
        if old_doc:
            logger.info(f"✅ Found in old structure: {old_doc.get('title')}")
            return old_doc
        
        # Phase 1: Check new structure as fallback
        if self.migration_phase == 1:
            logger.info(f"🔍 Phase 1: Checking new structure as fallback")
            new_doc = self._get_document_from_new_structure(collection_id, title)
            if new_doc:
                logger.info(f"✅ Found in new structure fallback: {new_doc.get('title')}")
                return new_doc
        
        logger.warning(f"❌ Document '{title}' not found in any structure")
        return None
    
    def _get_document_from_new_structure(self, collection_id: str, title: str) -> Optional[Dict[str, Any]]:
        """Get document from new collection-first structure"""
        try:
            registry = self.new_manager.load_collection_registry(collection_id)
            
            for doc in registry.get("documents", []):
                if doc.get("title", "").lower() == title.lower():
                    # Enhance with file paths
                    doc_copy = doc.copy()
                    doc_copy["files_info"] = {}
                    
                    for file_type in doc.get("files", {}):
                        file_path = self.new_manager.get_file_path(collection_id, doc["id"], file_type)
                        if file_path and file_path.exists():
                            doc_copy["files_info"][file_type] = {
                                "path": str(file_path),
                                "exists": True,
                                "size": file_path.stat().st_size
                            }
                    
                    doc_copy["source"] = "new_structure"
                    return doc_copy
        except Exception as e:
            logger.error(f"Error reading from new structure: {e}")
        
        return None
    
    def _get_document_from_old_structure(self, collection_id: str, title: str) -> Optional[Dict[str, Any]]:
        """Get document from old structure"""
        try:
            # Find in old documents directory
            source_file = None
            processed_file = None
            
            # Search in old documents structure
            for old_collection_name, new_collection_name in self.collection_mappings.items():
                if new_collection_name == collection_id:
                    collection_path = self.old_documents_dir / old_collection_name
                    if collection_path.exists():
                        # Look for matching title
                        for doc_file in collection_path.rglob("*.doc"):
                            if doc_file.stem.lower() == title.lower():
                                source_file = doc_file
                                processed_file = doc_file.with_suffix('.json')
                                break
                        if source_file:
                            break
            
            if not source_file or not source_file.exists():
                return None
            
            # Load metadata from JSON if exists
            metadata = {}
            if processed_file and processed_file.exists():
                try:
                    with open(processed_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    metadata = json_data.get("metadata", {})
                except Exception as e:
                    logger.error(f"Error reading JSON metadata: {e}")
            
            # Look for router file
            router_file = None
            for old_collection_name, new_collection_name in self.collection_mappings.items():
                if new_collection_name == collection_id:
                    router_collection_path = self.old_router_dir / old_collection_name
                    if router_collection_path.exists():
                        for router_candidate in router_collection_path.rglob("*.json"):
                            if router_candidate.stem.lower() == title.lower():
                                router_file = router_candidate
                                break
                    if router_file:
                        break
            
            # Build document info
            doc_info = {
                "id": f"old_{title.lower().replace(' ', '_')}",
                "title": title,
                "collection_id": collection_id,
                "metadata": metadata,
                "source": "old_structure",
                "files_info": {}
            }
            
            if source_file and source_file.exists():
                doc_info["files_info"]["source"] = {
                    "path": str(source_file),
                    "exists": True,
                    "size": source_file.stat().st_size
                }
            
            if processed_file and processed_file.exists():
                doc_info["files_info"]["processed"] = {
                    "path": str(processed_file),
                    "exists": True,
                    "size": processed_file.stat().st_size
                }
            
            if router_file and router_file.exists():
                doc_info["files_info"]["router"] = {
                    "path": str(router_file),
                    "exists": True,
                    "size": router_file.stat().st_size
                }
            
            return doc_info
            
        except Exception as e:
            logger.error(f"Error reading from old structure: {e}")
        
        return None
    
    def has_form_file(self, collection_id: str, document_title: str) -> bool:
        """Check if document has form file"""
        doc_info = self.get_document_by_title(collection_id, document_title)
        if not doc_info:
            return False
        
        # Check metadata for has_form flag
        metadata = doc_info.get("metadata", {})
        return metadata.get("has_form", False)
    
    def get_form_file_path(self, collection_id: str, document_title: str) -> Optional[str]:
        """Get form file path if exists"""
        doc_info = self.get_document_by_title(collection_id, document_title)
        if not doc_info:
            return None
        
        # Check if has form in new structure
        if doc_info.get("source") == "new_structure":
            form_info = doc_info.get("files_info", {}).get("form")
            if form_info and form_info.get("exists"):
                return form_info["path"]
        
        # For old structure, form files might be in a separate location
        # This is placeholder - implement based on actual form file location
        return None
    
    def list_all_documents(self, collection_id: Optional[str] = None) -> Dict[str, Any]:
        """List documents from both structures"""
        result = {
            "collections": [],
            "total_documents": 0,
            "sources": {
                "new_structure": 0,
                "old_structure": 0
            }
        }
        
        collections_to_check = []
        if collection_id:
            collections_to_check = [collection_id]
        else:
            # Get all possible collections
            collections_to_check = list(set(self.collection_mappings.values()))
        
        for coll_id in collections_to_check:
            collection_info = {
                "collection_id": coll_id,
                "name": self._get_collection_display_name(coll_id),
                "documents": [],
                "document_count": 0
            }
            
            # Get from new structure
            if self.migration_phase >= 2:
                new_docs = self._list_documents_from_new_structure(coll_id)
                collection_info["documents"].extend(new_docs)
                result["sources"]["new_structure"] += len(new_docs)
            
            # Get from old structure
            old_docs = self._list_documents_from_old_structure(coll_id)
            
            # Filter out duplicates if checking both structures
            if self.migration_phase >= 2:
                new_titles = {doc["title"].lower() for doc in collection_info["documents"]}
                old_docs = [doc for doc in old_docs if doc["title"].lower() not in new_titles]
            
            collection_info["documents"].extend(old_docs)
            result["sources"]["old_structure"] += len(old_docs)
            
            # Get from new structure as fallback (Phase 1)
            if self.migration_phase == 1:
                new_docs = self._list_documents_from_new_structure(coll_id)
                existing_titles = {doc["title"].lower() for doc in collection_info["documents"]}
                new_docs = [doc for doc in new_docs if doc["title"].lower() not in existing_titles]
                collection_info["documents"].extend(new_docs)
                result["sources"]["new_structure"] += len(new_docs)
            
            collection_info["document_count"] = len(collection_info["documents"])
            result["total_documents"] += collection_info["document_count"]
            
            if collection_info["document_count"] > 0:
                result["collections"].append(collection_info)
        
        return result
    
    def _list_documents_from_new_structure(self, collection_id: str) -> List[Dict[str, Any]]:
        """List documents from new structure"""
        try:
            registry = self.new_manager.load_collection_registry(collection_id)
            documents = []
            
            for doc in registry.get("documents", []):
                doc_copy = doc.copy()
                doc_copy["source"] = "new_structure"
                documents.append(doc_copy)
            
            return documents
        except Exception as e:
            logger.error(f"Error listing from new structure: {e}")
            return []
    
    def _list_documents_from_old_structure(self, collection_id: str) -> List[Dict[str, Any]]:
        """List documents from old structure"""
        documents = []
        
        try:
            # Search in old documents directory
            for old_collection_name, new_collection_name in self.collection_mappings.items():
                if new_collection_name == collection_id:
                    collection_path = self.old_documents_dir / old_collection_name
                    if collection_path.exists():
                        for doc_file in collection_path.rglob("*.doc"):
                            json_file = doc_file.with_suffix('.json')
                            
                            metadata = {}
                            if json_file.exists():
                                try:
                                    with open(json_file, 'r', encoding='utf-8') as f:
                                        json_data = json.load(f)
                                    metadata = json_data.get("metadata", {})
                                except Exception:
                                    pass
                            
                            doc_info = {
                                "id": f"old_{doc_file.stem.lower().replace(' ', '_')}",
                                "title": doc_file.stem,
                                "collection_id": collection_id,
                                "metadata": metadata,
                                "source": "old_structure",
                                "files": {
                                    "source": {"exists": True},
                                    "processed": {"exists": json_file.exists()}
                                }
                            }
                            
                            documents.append(doc_info)
        except Exception as e:
            logger.error(f"Error listing from old structure: {e}")
        
        return documents
    
    def _get_collection_display_name(self, collection_id: str) -> str:
        """Get display name for collection"""
        display_names = {
            "ho_tich_cap_xa": "Hộ tịch cấp xã",
            "chung_thuc": "Chứng thực",
            "nuoi_con_nuoi": "Nuôi con nuôi"
        }
        return display_names.get(collection_id, collection_id.replace("_", " ").title())
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status and statistics"""
        status = {
            "migration_phase": self.migration_phase,
            "new_structure_exists": self.new_manager.storage_root.exists(),
            "old_structure_exists": self.old_documents_dir.exists(),
            "collections": {}
        }
        
        for collection_id in ["ho_tich_cap_xa", "chung_thuc", "nuoi_con_nuoi"]:
            collection_status = {
                "new_structure": {
                    "exists": False,
                    "document_count": 0
                },
                "old_structure": {
                    "exists": False,
                    "document_count": 0
                }
            }
            
            # Check new structure
            try:
                registry = self.new_manager.load_collection_registry(collection_id)
                collection_status["new_structure"]["exists"] = True
                collection_status["new_structure"]["document_count"] = len(registry.get("documents", []))
            except Exception:
                pass
            
            # Check old structure
            old_doc_count = 0
            for old_collection_name, new_collection_name in self.collection_mappings.items():
                if new_collection_name == collection_id:
                    collection_path = self.old_documents_dir / old_collection_name
                    if collection_path.exists():
                        collection_status["old_structure"]["exists"] = True
                        old_doc_count += len(list(collection_path.rglob("*.doc")))
            
            collection_status["old_structure"]["document_count"] = old_doc_count
            status["collections"][collection_id] = collection_status
        
        return status
