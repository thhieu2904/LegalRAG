#!/usr/bin/env python3
"""
Collection Utilities for LegalRAG
=================================

Utilities to dynamically access and manage collections from storage

Author: LegalRAG Team
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class CollectionManager:
    """
    Collection Manager để lấy thông tin động về collections và documents
    Thay thế hardcode mapping bằng cách đọc trực tiếp từ file system
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Khởi tạo Collection Manager với đường dẫn đến thư mục storage
        """
        # Nếu storage_path đã chứa /collections thì không thêm nữa
        if storage_path and storage_path.endswith('collections'):
            self.collections_path = storage_path
            self.storage_path = os.path.dirname(storage_path)
        else:
            self.storage_path = storage_path or os.getenv("STORAGE_PATH", "data/storage")
            self.collections_path = os.path.join(self.storage_path, "collections")
        
        self.collections_cache = None
        self._load_collections()
    
    def _load_collections(self) -> Dict[str, Any]:
        """
        Load danh sách collection từ thư mục storage/collections
        """
        try:
            collections = {}
            
            # Kiểm tra thư mục tồn tại
            if not os.path.exists(self.collections_path):
                logger.error(f"❌ Collections path not found: {self.collections_path}")
                return {}
            
            # Lặp qua các thư mục con (mỗi thư mục là một collection)
            for collection_name in os.listdir(self.collections_path):
                collection_path = os.path.join(self.collections_path, collection_name)
                
                if os.path.isdir(collection_path):
                    # Đọc metadata.json nếu có
                    metadata_path = os.path.join(collection_path, "metadata.json")
                    metadata = {}
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                        except Exception as e:
                            logger.warning(f"⚠️ Error reading metadata for collection {collection_name}: {str(e)}")
                    
                    # Đọc danh sách documents
                    documents_path = os.path.join(collection_path, "documents")
                    documents = []
                    
                    if os.path.exists(documents_path):
                        documents = [
                            doc for doc in os.listdir(documents_path) 
                            if os.path.isdir(os.path.join(documents_path, doc))
                        ]
                    
                    # Thêm vào cache
                    collections[collection_name] = {
                        "name": collection_name,
                        "path": collection_path,
                        "metadata": metadata,
                        "documents": documents,
                        "document_count": len(documents),
                        "display_name": metadata.get("display_name", self._format_collection_name(collection_name)),
                        "description": metadata.get("description", f"Thủ tục liên quan đến {self._format_collection_name(collection_name).lower()}")
                    }
            
            self.collections_cache = collections
            logger.info(f"✅ Loaded {len(collections)} collections from {self.collections_path}")
            return collections
            
        except Exception as e:
            logger.error(f"❌ Error loading collections: {str(e)}")
            self.collections_cache = {}
            return {}
    
    def get_all_collections(self) -> Dict[str, Any]:
        """
        Lấy danh sách tất cả collection
        """
        if self.collections_cache is None:
            return self._load_collections()
        
        return self.collections_cache
    
    def get_collection(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết của một collection
        """
        collections = self.get_all_collections()
        return collections.get(collection_name)
    
    def get_document_info(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin về một document cụ thể
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return None
        
        if document_id not in collection.get("documents", []):
            return None
        
        # Đọc thông tin document từ file nếu có
        document_path = os.path.join(self.collections_path, collection_name, "documents", document_id)
        info_path = os.path.join(document_path, "info.json")
        document_info = {
            "id": document_id,
            "collection": collection_name,
            "path": document_path
        }
        
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                document_info.update(info)
            except Exception as e:
                logger.warning(f"⚠️ Error reading document info: {str(e)}")
        
        return document_info
    
    def get_collection_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tất cả documents trong một collection
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return []
        
        documents = []
        for doc_id in collection.get("documents", []):
            doc_info = self.get_document_info(collection_name, doc_id)
            if doc_info:
                documents.append(doc_info)
        
        return documents
    
    def get_document_questions(self, collection_name: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách câu hỏi của một document
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return []
        
        questions_path = os.path.join(
            self.collections_path, collection_name, "documents", document_id, "questions.json"
        )
        
        if not os.path.exists(questions_path):
            return []
        
        try:
            with open(questions_path, "r", encoding="utf-8") as f:
                questions_data = json.load(f)
            
            if isinstance(questions_data, list):
                return questions_data
            elif isinstance(questions_data, dict) and "questions" in questions_data:
                return questions_data["questions"]
            else:
                return []
                
        except Exception as e:
            logger.warning(f"⚠️ Error reading questions for document {document_id}: {str(e)}")
            return []
    
    def get_collection_questions(self, collection_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Lấy danh sách câu hỏi của toàn bộ collection
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return []
        
        all_questions = []
        for doc_id in collection.get("documents", []):
            questions = self.get_document_questions(collection_name, doc_id)
            for q in questions:
                q["document_id"] = doc_id
                all_questions.append(q)
            
            if len(all_questions) >= limit:
                break
        
        return all_questions[:limit]
    
    def _format_collection_name(self, collection_name: str) -> str:
        """
        Format tên collection để hiển thị thân thiện hơn
        """
        name = collection_name
        if name.startswith("quy_trinh_"):
            name = name[10:]  # Remove "quy_trinh_" prefix
        
        # Convert snake_case to Title Case
        words = name.split("_")
        return " ".join(word.capitalize() for word in words)
    
    def get_example_questions_for_collection(self, collection_name: str, limit: int = 10) -> List[str]:
        """
        Lấy danh sách câu hỏi mẫu cho một collection
        """
        questions = self.get_collection_questions(collection_name, limit)
        return [q.get("text", "") for q in questions if "text" in q]