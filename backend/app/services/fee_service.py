"""
Fee Service - Intelligent Fee Information Processing
"""

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class FeeQuery:
    """Represents a fee-related query"""
    query_text: str
    is_fee_query: bool = False
    fee_keywords: List[str] = field(default_factory=list)
    context_keywords: List[str] = field(default_factory=list)

class FeeService:
    """
    Intelligent service for processing fee-related queries
    """
    
    def __init__(self):
        self.fee_keywords = [
            "phi", "le phi", "muc phi", "chi phi", "thu phi",
            "nop phi", "tra phi", "mien phi", "giam phi",
            "bao nhieu tien", "phi la bao nhieu"
        ]
        
        logger.info("FeeService initialized")
    
    def detect_fee_query(self, query: str) -> FeeQuery:
        """
        Detect if query is related to fees
        """
        query_lower = query.lower()
        fee_query = FeeQuery(query_text=query)
        
        # Check for fee keywords
        for keyword in self.fee_keywords:
            if keyword in query_lower:
                fee_query.is_fee_query = True
                fee_query.fee_keywords.append(keyword)
        
        return fee_query
    
    def extract_fee_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fee information from document metadata
        """
        fee_info = {
            "has_fee_structure": False,
            "fee_summary": "",
            "main_fee": {},
            "additional_fees": [],
            "exemptions": []
        }
        
        if "fee_structure" not in metadata:
            return fee_info
        
        fee_structure = metadata["fee_structure"]
        fee_info["has_fee_structure"] = True
        
        # Process main fee
        if "main_fee" in fee_structure:
            main_fee = fee_structure["main_fee"]
            fee_info["main_fee"] = {
                "type": main_fee.get("type", ""),
                "description": main_fee.get("description", ""),
                "fee_amounts": main_fee.get("fee_amounts", [])
            }
            
            # Create summary for main fee
            amounts_text = []
            for amount_info in main_fee.get("fee_amounts", []):
                condition = amount_info.get("condition", "")
                amount = amount_info.get("amount", 0)
                currency = amount_info.get("currency", "VND")
                
                amount_str = f"{amount:,} {currency}" if amount > 0 else "Mien phi"
                if condition:
                    amounts_text.append(f"- {condition}: {amount_str}")
                else:
                    amounts_text.append(amount_str)
            
            fee_info["fee_summary"] += f"**{main_fee.get('description', 'Phi chinh')}:**\n" + "\n".join(amounts_text) + "\n\n"
        
        return fee_info
    
    def generate_fee_response(self, query: str, metadata: Dict[str, Any], 
                            context_chunks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive fee response
        """
        fee_query = self.detect_fee_query(query)
        
        if not fee_query.is_fee_query:
            return {"is_fee_response": False, "fee_info": None}
        
        fee_info = self.extract_fee_info(metadata)
        
        if not fee_info["has_fee_structure"]:
            fee_text = metadata.get("fee_text", "")
            if fee_text:
                fee_info["fee_summary"] = f"Thong tin phi tu tai lieu:\n{fee_text}"
            else:
                fee_info["fee_summary"] = "Khong co thong tin cu the ve phi trong tai lieu nay."
        
        # Create response
        response = {
            "is_fee_response": True,
            "fee_info": fee_info,
            "answer": f"**Thong tin ve phi/le phi:**\n\n{fee_info['fee_summary']}",
            "detected_keywords": fee_query.fee_keywords,
            "context_keywords": fee_query.context_keywords
        }
        
        return response
    
    def enhance_rag_response_with_fee_info(self, response: Dict[str, Any], 
                                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing RAG response with fee information
        """
        query = response.get("query", "")
        fee_response = self.generate_fee_response(query, metadata, 
                                                response.get("context_chunks", []))
        
        if fee_response["is_fee_response"]:
            # Merge fee info into response
            response["fee_info"] = fee_response["fee_info"]
            
            # Add fee information to answer if not already present
            if "phi" not in response["answer"].lower() and "le phi" not in response["answer"].lower():
                response["answer"] += f"\n\n{fee_response['answer']}"
            
            logger.info("Enhanced response with fee information")
        
        return response
