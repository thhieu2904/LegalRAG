"""
Document Manager Service - Collection-First Architecture
Quản lý documents theo collection với support cho form files

Architecture:
- Each collection has its own folder and registry
- Documents organized by collection/documents/document_id/
- Support for multiple file types: source, processed, form, router
"""

import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

class DocumentManagerService:
    """
    Service để quản lý documents theo collection-first architecture
    """
    
    def __init__(self, storage_root: Optional[str] = None):
        self.storage_root = Path(storage_root or settings.data_root_dir) / "storage"
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Mapping collection names
        self.collection_mappings = {
            'quy_trinh_cap_ho_tich_cap_xa': 'ho_tich_cap_xa',
            'ho_tich_cap_xa_moi_nhat': 'ho_tich_cap_xa',
            'quy_trinh_chung_thuc': 'chung_thuc', 
            'quy_trinh_nb_chung_thuc_dung_chung': 'chung_thuc',
            'quy_trinh_nuoi_con_nuoi': 'nuoi_con_nuoi',
            'iso_ncn_moi': 'nuoi_con_nuoi',
        }
    
    def get_collection_path(self, collection_id: str) -> Path:
        """Lấy đường dẫn thư mục collection"""
        return self.storage_root / collection_id
    
    def get_document_path(self, collection_id: str, document_id: str) -> Path:
        """Lấy đường dẫn thư mục document"""
        return self.get_collection_path(collection_id) / "documents" / document_id
    
    def get_registry_path(self, collection_id: str) -> Path:
        """Lấy đường dẫn file registry của collection"""
        return self.get_collection_path(collection_id) / "registry.json"
    
    def _generate_document_id(self, title: str, code: Optional[str] = None) -> str:
        """Tạo document ID từ title và code"""
        # Normalize title
        normalized = title.lower()
        normalized = normalized.replace(" ", "_").replace(",", "").replace(".", "")
        
        # Remove Vietnamese accents (simplified)
        replacements = {
            'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd'
        }
        
        for vn_char, latin_char in replacements.items():
            normalized = normalized.replace(vn_char, latin_char)
        
        # Extract number prefix if exists (e.g., "01. Đăng ký khai sinh" -> "01")
        parts = normalized.split("_")
        if parts[0].isdigit():
            return f"doc_{parts[0].zfill(3)}_{'_'.join(parts[1:])}"
        
        return f"doc_{normalized[:50]}"  # Limit length
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Tính checksum của file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def load_collection_registry(self, collection_id: str) -> Dict[str, Any]:
        """Load registry của collection"""
        registry_path = self.get_registry_path(collection_id)
        
        if not registry_path.exists():
            # Tạo registry mới
            registry = {
                "collection_id": collection_id,
                "name": self._get_collection_display_name(collection_id),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "document_count": 0,
                "documents": []
            }
            self.save_collection_registry(collection_id, registry)
            return registry
        
        with open(registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_collection_registry(self, collection_id: str, registry: Dict[str, Any]) -> None:
        """Lưu registry của collection"""
        registry_path = self.get_registry_path(collection_id)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        registry["updated_at"] = datetime.now().isoformat()
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
    
    def _get_collection_display_name(self, collection_id: str) -> str:
        """Lấy tên hiển thị của collection"""
        display_names = {
            "ho_tich_cap_xa": "Hộ tịch cấp xã",
            "chung_thuc": "Chứng thực", 
            "nuoi_con_nuoi": "Nuôi con nuôi"
        }
        return display_names.get(collection_id, collection_id.replace("_", " ").title())
    
    def create_document(
        self,
        collection_id: str,
        title: str,
        code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Tạo document mới trong collection
        
        Returns:
            document_id: ID của document được tạo
        """
        # Generate document ID
        document_id = self._generate_document_id(title, code)
        
        # Ensure unique ID
        registry = self.load_collection_registry(collection_id)
        existing_ids = [doc["id"] for doc in registry["documents"]]
        counter = 1
        original_id = document_id
        while document_id in existing_ids:
            document_id = f"{original_id}_{counter}"
            counter += 1
        
        # Create document folder
        doc_path = self.get_document_path(collection_id, document_id)
        doc_path.mkdir(parents=True, exist_ok=True)
        
        # Create document metadata
        doc_metadata = {
            "id": document_id,
            "title": title,
            "code": code,
            "collection_id": collection_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "files": {},
            "metadata": metadata or {}
        }
        
        # Add to registry
        registry["documents"].append(doc_metadata)
        registry["document_count"] = len(registry["documents"])
        self.save_collection_registry(collection_id, registry)
        
        logger.info(f"Created document {document_id} in collection {collection_id}")
        return document_id
    
    def add_file(
        self,
        collection_id: str,
        document_id: str,
        file_type: str,  # 'source', 'processed', 'form', 'router'
        file_path: Union[str, Path],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Thêm file vào document
        
        Args:
            collection_id: ID collection
            document_id: ID document  
            file_type: Loại file (source, processed, form, router)
            file_path: Đường dẫn file nguồn
            filename: Tên file đích (optional)
        
        Returns:
            Dict chứa thông tin file đã thêm
        """
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # Generate destination filename
        if not filename:
            extension_map = {
                'source': '.doc',
                'processed': '.json', 
                'form': '.pdf',
                'router': '.json'
            }
            filename = f"{file_type}{extension_map.get(file_type, source_path.suffix)}"
        
        # Copy file to document folder
        doc_path = self.get_document_path(collection_id, document_id)
        dest_path = doc_path / filename
        
        shutil.copy2(source_path, dest_path)
        
        # Calculate file info
        file_info = {
            "filename": filename,
            "path": str(dest_path.relative_to(self.storage_root)),
            "size": dest_path.stat().st_size,
            "checksum": self._calculate_file_checksum(dest_path),
            "added_at": datetime.now().isoformat()
        }
        
        # Update registry
        registry = self.load_collection_registry(collection_id)
        for doc in registry["documents"]:
            if doc["id"] == document_id:
                doc["files"][file_type] = file_info
                doc["updated_at"] = datetime.now().isoformat()
                break
        
        self.save_collection_registry(collection_id, registry)
        
        logger.info(f"Added {file_type} file to {collection_id}/{document_id}: {filename}")
        return file_info
    
    def get_document_info(self, collection_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin document"""
        registry = self.load_collection_registry(collection_id)
        
        for doc in registry["documents"]:
            if doc["id"] == document_id:
                return doc
        
        return None
    
    def list_documents(self, collection_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List documents, có thể filter theo collection
        
        Returns:
            Dict chứa danh sách documents, grouped by collection
        """
        result = {
            "collections": [],
            "total_documents": 0
        }
        
        if collection_id:
            collections = [collection_id]
        else:
            # Get all collections
            collections = [p.name for p in self.storage_root.iterdir() if p.is_dir()]
        
        for coll_id in collections:
            try:
                registry = self.load_collection_registry(coll_id)
                collection_info = {
                    "collection_id": coll_id,
                    "name": registry.get("name", coll_id),
                    "document_count": registry.get("document_count", 0),
                    "documents": registry.get("documents", [])
                }
                result["collections"].append(collection_info)
                result["total_documents"] += collection_info["document_count"]
            except Exception as e:
                logger.error(f"Error loading collection {coll_id}: {e}")
                continue
        
        return result
    
    def get_file_path(self, collection_id: str, document_id: str, file_type: str) -> Optional[Path]:
        """Lấy đường dẫn file"""
        doc_info = self.get_document_info(collection_id, document_id)
        if not doc_info or file_type not in doc_info.get("files", {}):
            return None
        
        file_info = doc_info["files"][file_type]
        return self.storage_root / file_info["path"]
    
    def has_form_file(self, collection_id: str, document_id: str) -> bool:
        """Kiểm tra document có form file không"""
        doc_info = self.get_document_info(collection_id, document_id)
        if not doc_info:
            return False
        
        return "form" in doc_info.get("files", {})
    
    def get_documents_with_forms(self, collection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy danh sách documents có form files"""
        all_docs = self.list_documents(collection_id)
        docs_with_forms = []
        
        for collection in all_docs["collections"]:
            for doc in collection["documents"]:
                if "form" in doc.get("files", {}):
                    docs_with_forms.append({
                        "collection_id": collection["collection_id"],
                        "collection_name": collection["name"],
                        **doc
                    })
        
        return docs_with_forms
    
    def delete_document(self, collection_id: str, document_id: str) -> bool:
        """Xóa document và tất cả files"""
        try:
            # Remove from registry
            registry = self.load_collection_registry(collection_id)
            registry["documents"] = [doc for doc in registry["documents"] if doc["id"] != document_id]
            registry["document_count"] = len(registry["documents"])
            self.save_collection_registry(collection_id, registry)
            
            # Remove folder
            doc_path = self.get_document_path(collection_id, document_id)
            if doc_path.exists():
                shutil.rmtree(doc_path)
            
            logger.info(f"Deleted document {collection_id}/{document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {collection_id}/{document_id}: {e}")
            return False
    
    def normalize_collection_name(self, collection_name: str) -> str:
        """Normalize collection name từ old structure"""
        return self.collection_mappings.get(collection_name, collection_name)
