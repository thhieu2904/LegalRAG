"""
Simple Form Detection Service - Đơn giản và hiệu quả
Chỉ cần check metadata has_form và đường dẫn forms/

Updated for Docker compatibility with PathConfig service
"""

import json
import logging
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

from ..models.schemas import FormAttachment
from ..core.path_config import PathConfig

logger = logging.getLogger(__name__)

class SimpleFormDetectionService:
    """
    Service đơn giản để detect và attach form files
    Logic: 
    1. Check metadata.has_form = true
    2. Check thư mục forms/ có file không
    3. Generate download URL và attach vào response
    """
    
    def __init__(self, storage_base_path: Optional[str] = None):
        if storage_base_path is None:
            # Use PathConfig service for Docker compatibility
            path_config = PathConfig()
            self.storage_base_path = path_config.collections_dir
            self.path_config = path_config
            logger.info(f"Using PathConfig service - Environment: {path_config.environment}")
        else:
            self.storage_base_path = Path(storage_base_path)
            self.path_config = None
            logger.info("Using provided storage_base_path")
        
        logger.info(f"SimpleFormDetectionService initialized with storage: {self.storage_base_path}")
        
        # Verify path exists
        if not self.storage_base_path.exists():
            logger.warning(f"Storage path does not exist: {self.storage_base_path}")
            logger.info("This may be normal if collections haven't been created yet")
    
    def extract_documents_from_context(self, context_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract document information từ RAG context
        
        Args:
            context_info: Context từ RAG response
            
        Returns:
            List of documents with collection and title info
        """
        documents = []
        
        # Extract from source_documents
        source_documents = context_info.get("source_documents", [])
        source_collections = context_info.get("source_collections", [])
        
        for i, doc_path in enumerate(source_documents):
            if isinstance(doc_path, str):
                # 🔧 FIX: Extract document info từ actual JSON file thay vì filename
                doc_info = self._extract_document_info_from_json_path(doc_path)
                
                # Get collection (dùng first collection làm default)
                collection_id = source_collections[0] if source_collections else "unknown"
                
                if doc_info:
                    documents.append({
                        "title": doc_info["title"],
                        "collection_id": collection_id,
                        "source_path": doc_path,
                        "doc_id": doc_info["doc_id"]  # Add doc_id for easier lookup
                    })
        
        return documents
    
    def _extract_document_title_from_path(self, file_path: str) -> Optional[str]:
        """Extract clean document title từ file path"""
        try:
            # Handle different path formats
            if "\\" in file_path:
                filename = file_path.split("\\")[-1]
            elif "/" in file_path:
                filename = file_path.split("/")[-1]
            else:
                filename = file_path
            
            # Remove extension
            title = filename.replace(".json", "").replace(".doc", "")
            
            # Remove numbering prefix (e.g., "01. " -> "")
            if ". " in title and title.split(". ")[0].replace(" ", "").isdigit():
                title = title.split(". ", 1)[1]
            
            return title.strip() if title.strip() else None
            
        except Exception as e:
            logger.error(f"Error extracting title from path {file_path}: {e}")
            return None
    
    def _extract_document_info_from_json_path(self, json_file_path: str) -> Optional[Dict[str, str]]:
        """
        Extract document info (title, doc_id) từ actual JSON file
        
        Args:
            json_file_path: Đường dẫn đến file JSON
            
        Returns:
            Dict với title và doc_id hoặc None nếu lỗi
        """
        try:
            from pathlib import Path
            import json
            
            json_path = Path(json_file_path)
            if not json_path.exists():
                logger.debug(f"JSON file not found: {json_file_path}")
                return None
            
            # Extract doc_id from path (DOC_XXX)
            doc_id = json_path.parent.name  # e.g., DOC_002
            
            # Load metadata từ JSON file
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            title = metadata.get("title", "")
            
            if not title:
                logger.debug(f"No title found in metadata for {json_file_path}")
                return None
            
            return {
                "title": title,
                "doc_id": doc_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting document info from {json_file_path}: {e}")
            return None
    
    def check_document_has_form(self, collection_id: str, document_title: Optional[str] = None, doc_json_path: Optional[str] = None) -> bool:
        """
        Check nếu document có form bằng cách:
        1. Load metadata từ JSON file
        2. Check has_form = true
        3. Check thư mục forms/ có file không
        
        Args:
            collection_id: ID của collection
            document_title: Title của document (optional nếu có doc_json_path)
            doc_json_path: Đường dẫn trực tiếp đến JSON file (ưu tiên)
        """
        try:
            # 🔧 FIX: Ưu tiên sử dụng đường dẫn trực tiếp nếu có
            if doc_json_path:
                from pathlib import Path
                json_path = Path(doc_json_path)
            else:
                # Fallback to find by title
                json_path = self._find_document_json_path(collection_id, document_title)
                
            if not json_path or not json_path.exists():
                logger.debug(f"Document JSON not found for {collection_id}/{document_title}")
                return False
            
            # Load metadata
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            has_form_flag = metadata.get("has_form", False)
            
            if not has_form_flag:
                logger.debug(f"Document {document_title or json_path.name} has has_form=false")
                return False
            
            # Check forms directory có file không
            forms_dir = json_path.parent / "forms"
            if not forms_dir.exists():
                logger.debug(f"Forms directory not found: {forms_dir}")
                return False
            
            # Check có file nào trong forms/ không
            form_files = list(forms_dir.glob("*"))
            form_files = [f for f in form_files if f.is_file()]
            
            if not form_files:
                logger.debug(f"No form files found in: {forms_dir}")
                return False
            
            logger.debug(f"✅ Document {document_title or json_path.name} has form: {len(form_files)} files")
            return True
            
        except Exception as e:
            logger.error(f"Error checking form for {collection_id}/{document_title}: {e}")
            return False
    
    def get_form_files(self, collection_id: str, document_title: str) -> List[Path]:
        """
        Get list of form files cho document
        """
        try:
            doc_json_path = self._find_document_json_path(collection_id, document_title)
            if not doc_json_path:
                return []
            
            forms_dir = doc_json_path.parent / "forms"
            if not forms_dir.exists():
                return []
            
            # Get all files trong forms directory
            form_files = []
            for file_path in forms_dir.glob("*"):
                if file_path.is_file():
                    form_files.append(file_path)
            
            return form_files
            
        except Exception as e:
            logger.error(f"Error getting form files for {collection_id}/{document_title}: {e}")
            return []
    
    def _get_form_files_from_path(self, json_file_path: str) -> List[Path]:
        """
        Get form files directly từ JSON file path
        
        Args:
            json_file_path: Đường dẫn đến JSON file
            
        Returns:
            List of form file paths
        """
        try:
            from pathlib import Path
            
            json_path = Path(json_file_path)
            if not json_path.exists():
                return []
            
            forms_dir = json_path.parent / "forms"
            if not forms_dir.exists():
                return []
            
            # Get all files trong forms directory
            form_files = []
            for file_path in forms_dir.glob("*"):
                if file_path.is_file():
                    form_files.append(file_path)
            
            return form_files
            
        except Exception as e:
            logger.error(f"Error getting form files from path {json_file_path}: {e}")
            return []
    
    def _find_document_json_path(self, collection_id: str, document_title: Optional[str]) -> Optional[Path]:
        """
        Find JSON file path cho document
        """
        try:
            if not document_title:
                return None
                
            collection_dir = self.storage_base_path / collection_id / "documents"
            if not collection_dir.exists():
                return None
            
            # Tìm trong các thư mục DOC_*
            for doc_dir in collection_dir.glob("DOC_*"):
                if not doc_dir.is_dir():
                    continue
                
                # Tìm file JSON có title matching
                for json_file in doc_dir.glob("*.json"):
                    try:
                        import json
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        file_title = data.get("metadata", {}).get("title", "")
                        if file_title == document_title:
                            return json_file
                            
                    except Exception:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding document JSON path: {e}")
            return None
    
    def generate_form_download_url(self, collection_id: str, document_title: str, form_file_path: Path) -> str:
        """
        Generate download URL cho form file
        """
        # Find document ID (DOC_XXX)
        doc_id = form_file_path.parent.parent.name  # forms/ -> DOC_XXX/
        
        # Generate API URL
        form_filename = form_file_path.name
        download_url = f"/api/documents/{collection_id}/{doc_id}/files/form/{form_filename}"
        
        return download_url
    
    def detect_forms_in_response(self, rag_response: Dict[str, Any]) -> List[FormAttachment]:
        """
        Main function: Detect form attachments từ RAG response
        
        Args:
            rag_response: Complete RAG response
            
        Returns:
            List of FormAttachment objects
        """
        form_attachments = []
        
        try:
            # Extract documents từ context
            context_info = rag_response.get("context_info", {})
            documents = self.extract_documents_from_context(context_info)
            
            for doc_info in documents:
                collection_id = doc_info["collection_id"]
                doc_title = doc_info["title"]
                source_path = doc_info["source_path"]
                
                # 🔧 FIX: Sử dụng đường dẫn trực tiếp thay vì title lookup
                if self.check_document_has_form(collection_id, doc_title, source_path):
                    # Get form files directly từ source_path
                    form_files = self._get_form_files_from_path(source_path)
                    
                    for form_file_path in form_files:
                        # Generate download URL
                        download_url = self.generate_form_download_url(collection_id, doc_title, form_file_path)
                        
                        # Create FormAttachment
                        form_attachment = FormAttachment(
                            document_id=doc_info.get('doc_id', 'unknown'),
                            document_title=doc_title,
                            form_filename=form_file_path.name,
                            form_url=download_url,
                            collection_id=collection_id
                        )
                        
                        form_attachments.append(form_attachment)
                        logger.info(f"✅ Form detected: {doc_title} -> {form_file_path.name}")
        
        except Exception as e:
            logger.error(f"Error detecting forms in response: {e}")
        
        return form_attachments
    
    def enhance_rag_response_with_forms(self, rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function: Enhance RAG response với form attachments
        
        Args:
            rag_response: Original RAG response
            
        Returns:
            Enhanced response với form_attachments field
        """
        try:
            # Detect forms
            form_attachments = self.detect_forms_in_response(rag_response)
            
            # Add to response
            enhanced_response = rag_response.copy()
            enhanced_response["form_attachments"] = [
                form.dict() for form in form_attachments
            ]
            
            # Add form count to context_info
            if "context_info" in enhanced_response:
                enhanced_response["context_info"]["form_count"] = len(form_attachments)
            
            # Log results
            if form_attachments:
                logger.info(f"✅ Enhanced response with {len(form_attachments)} form attachments")
                for form in form_attachments:
                    logger.info(f"   - {form.document_title}: {form.form_filename}")
                    
                # Update answer để mention forms nếu chưa có
                if enhanced_response.get("answer") and "form" not in enhanced_response["answer"].lower():
                    enhanced_response["answer"] += "\n\n📋 Xem biểu mẫu đính kèm bên dưới."
                    
            else:
                logger.info("ℹ️ No form attachments detected")
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response with forms: {e}")
            # Return original response nếu có lỗi
            return rag_response


# Convenience function for easy integration
def detect_and_attach_forms(rag_response: Dict[str, Any], storage_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function để detect và attach forms to RAG response
    
    Args:
        rag_response: RAG response to enhance
        storage_path: Path to storage directory
        
    Returns:
        Enhanced response with form attachments
    """
    form_service = SimpleFormDetectionService(storage_path)
    return form_service.enhance_rag_response_with_forms(rag_response)
