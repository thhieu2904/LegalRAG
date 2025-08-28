"""
Form Service - Intelligent Form Detection and Suggestion
"""

import logging
import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class FormQuery:
    """Represents a form-related query"""
    query_text: str
    is_form_query: bool = False
    form_keywords: List[str] = field(default_factory=list)
    context_keywords: List[str] = field(default_factory=list)
    procedure_type: str = ""

class FormService:
    """
    Intelligent service for detecting and suggesting relevant forms
    """
    
    def __init__(self, storage_base_path: str = "data/storage"):
        self.storage_base_path = storage_base_path
        self.form_keywords = [
            "mau", "bieu mau", "to khai", "don", "giay to", "ho so",
            "form", "application", "dang ky", "cap", "thay doi", "cap lai",
            "xac nhan", "chung thuc", "yeu cau", "nop", "dien", "download"
        ]
        
        logger.info(f"FormService initialized with storage: {self.storage_base_path}")
    
    def detect_form_query(self, query: str) -> FormQuery:
        """
        Detect if query is related to forms and extract context
        """
        query_lower = query.lower()
        form_query = FormQuery(query_text=query)
        
        # Check for form keywords
        for keyword in self.form_keywords:
            if keyword in query_lower:
                form_query.is_form_query = True
                form_query.form_keywords.append(keyword)
        
        # Extract context keywords
        context_patterns = [
            r"dang ky\s+(\w+)", r"cap\s+(\w+)", r"thay doi\s+(\w+)",
            r"cap lai\s+(\w+)", r"xac nhan\s+(\w+)", r"chung thuc\s+(\w+)",
            r"(\w+)\s+mau", r"(\w+)\s+to khai", r"(\w+)\s+don"
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, query_lower)
            form_query.context_keywords.extend(matches)
        
        return form_query
    
    def generate_form_response(self, query: str, collection: str, 
                             metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate form response with relevant forms
        """
        form_query = self.detect_form_query(query)
        
        if not form_query.is_form_query and not metadata.get("has_form", False):
            return {"is_form_response": False, "forms": []}
        
        # For now, return basic response
        response = {
            "is_form_response": form_query.is_form_query,
            "forms": [],
            "detected_keywords": form_query.form_keywords,
            "context_keywords": form_query.context_keywords,
            "procedure_type": form_query.procedure_type
        }
        
        return response
    
    def enhance_rag_response_with_forms(self, response: Dict[str, Any], 
                                       collection: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing RAG response with relevant forms
        """
        query = response.get("query", "")
        form_response = self.generate_form_response(query, collection, metadata)
        
        if form_response["is_form_response"]:
            # Add forms to response
            response["form_attachments"] = form_response["forms"]
            
            # Add form information to answer if not already present
            if "mau" not in response["answer"].lower() and "bieu mau" not in response["answer"].lower():
                response["answer"] += "\n\n**Bieu mau/to khai lien quan:**\n- Xem bieu mau dinh kem"
            
            logger.info("Enhanced response with form suggestions")
        
        return response
