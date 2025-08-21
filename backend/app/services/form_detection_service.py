"""
Form Detection Service - Tích hợp form detection vào RAG pipeline
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .hybrid_document_service import HybridDocumentService
from ..models.schemas import FormAttachment

logger = logging.getLogger(__name__)

class FormDetectionService:
    """
    Service để detect và attach form files vào RAG responses
    """
    
    def __init__(self, migration_phase: int = 1):
        self.hybrid_doc_service = HybridDocumentService(migration_phase)
        logger.info(f"FormDetectionService initialized - Phase {migration_phase}")
    
    def extract_documents_from_context(self, context_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract document information từ RAG context
        
        Args:
            context_info: Context information from RAG response
            
        Returns:
            List of documents with collection and title info
        """
        documents = []
        
        # Extract from source_documents (old format)
        source_documents = context_info.get("source_documents", [])
        source_collections = context_info.get("source_collections", [])
        
        for i, doc_path in enumerate(source_documents):
            if isinstance(doc_path, str):
                # Extract document title from file path
                doc_title = self._extract_document_title_from_path(doc_path)
                
                # Get collection (use first collection as default)
                collection_id = source_collections[0] if source_collections else "unknown"
                
                if doc_title:
                    documents.append({
                        "title": doc_title,
                        "collection_id": collection_id,
                        "source_path": doc_path
                    })
        
        # Extract from sources (new format) - FIX for test
        sources = context_info.get("sources", [])
        for source in sources:
            if isinstance(source, dict):
                doc_title = source.get("title", "")
                collection_id = source.get("collection", "unknown")
                
                if doc_title:
                    documents.append({
                        "title": doc_title,
                        "collection_id": collection_id,
                        "source_path": f"sources/{doc_title}"  # Mock path
                    })
        
        return documents
    
    def _extract_document_title_from_path(self, file_path: str) -> Optional[str]:
        """Extract clean document title from file path"""
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
    
    def detect_forms_in_response(self, rag_response: Dict[str, Any]) -> List[FormAttachment]:
        """
        Detect form attachments từ RAG response
        
        Args:
            rag_response: Complete RAG response
            
        Returns:
            List of FormAttachment objects
        """
        form_attachments = []
        
        try:
            # Extract documents from context
            context_info = rag_response.get("context_info", {})
            documents = self.extract_documents_from_context(context_info)
            
            for doc_info in documents:
                collection_id = doc_info["collection_id"]
                doc_title = doc_info["title"]
                
                # Check if document has form using hybrid service
                has_form = self.hybrid_doc_service.has_form_file(collection_id, doc_title)
                
                if has_form:
                    # Get form file path if exists
                    form_path = self.hybrid_doc_service.get_form_file_path(collection_id, doc_title)
                    
                    # Generate form URL (placeholder - implement based on your URL structure)
                    form_url = self._generate_form_download_url(collection_id, doc_title, form_path)
                    
                    if form_url:
                        form_attachment = FormAttachment(
                            document_id=f"{collection_id}_{doc_title}",
                            document_title=doc_title,
                            form_filename=self._get_form_filename(form_path) if form_path else "form.pdf",
                            form_url=form_url,
                            collection_id=collection_id
                        )
                        
                        form_attachments.append(form_attachment)
                        logger.info(f"✅ Form detected for document: {doc_title}")
                
        except Exception as e:
            logger.error(f"Error detecting forms in response: {e}")
        
        return form_attachments
    
    def _generate_form_download_url(self, collection_id: str, document_title: str, form_path: Optional[str]) -> Optional[str]:
        """
        Generate download URL for form file
        
        Args:
            collection_id: Collection ID
            document_title: Document title  
            form_path: Path to form file
            
        Returns:
            Download URL or None if no form
        """
        if not form_path:
            return None
        
        # For new structure: use document API
        doc_info = self.hybrid_doc_service.get_document_by_title(collection_id, document_title)
        if doc_info and doc_info.get("source") == "new_structure":
            document_id = doc_info["id"]
            return f"/api/documents/{collection_id}/{document_id}/files/form"
        
        # For old structure: serve directly from file path (placeholder)
        # You might need to implement a file serving endpoint for old structure
        return f"/api/files/legacy/forms/{collection_id}/{document_title}"
    
    def _get_form_filename(self, form_path: Optional[str]) -> str:
        """Extract filename from form path"""
        if not form_path:
            return "form.pdf"
        
        try:
            if isinstance(form_path, str):
                if "\\" in form_path:
                    return form_path.split("\\")[-1]
                elif "/" in form_path:
                    return form_path.split("/")[-1]
                return form_path
            return "form.pdf"
        except Exception:
            return "form.pdf"
    
    def enhance_rag_response_with_forms(self, rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance RAG response with form attachments
        
        Args:
            rag_response: Original RAG response
            
        Returns:
            Enhanced response with form_attachments field
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
            
            # Log form detection results
            if form_attachments:
                logger.info(f"✅ Enhanced response with {len(form_attachments)} form attachments")
                for form in form_attachments:
                    logger.info(f"   - {form.document_title}: {form.form_filename}")
            else:
                logger.info("ℹ️ No form attachments detected")
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response with forms: {e}")
            # Return original response on error
            return rag_response
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status from hybrid service"""
        return self.hybrid_doc_service.get_migration_status()
    
    def set_migration_phase(self, phase: int):
        """Update migration phase"""
        self.hybrid_doc_service.migration_phase = phase
        logger.info(f"Updated migration phase to: {phase}")

# Convenience function for easy integration
def detect_and_attach_forms(rag_response: Dict[str, Any], migration_phase: int = 1) -> Dict[str, Any]:
    """
    Convenience function to detect and attach forms to RAG response
    
    Args:
        rag_response: RAG response to enhance
        migration_phase: Current migration phase
        
    Returns:
        Enhanced response with form attachments
    """
    form_service = FormDetectionService(migration_phase)
    return form_service.enhance_rag_response_with_forms(rag_response)
