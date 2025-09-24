#!/usr/bin/env python3
"""
Debug script to check the actual response structure
"""

import os
import sys
import json
from pathlib import Path

# Add the rag_service directory to Python path
rag_service_path = Path(__file__).parent.parent / "rag_service"
sys.path.insert(0, str(rag_service_path))

os.chdir(rag_service_path)

from app.services.clarification import ClarificationService

def debug_confirmation_response():
    """Debug the actual response structure"""
    print("🔍 Debugging confirmation response structure...")
    
    clarification_service = ClarificationService()
    
    routing_result = {
        "best_match": {
            "collection": "quy_trinh_cap_ho_tich_cap_xa",
            "document": "DOC_011",
            "question": "Thủ tục đăng ký kết hôn được thực hiện như thế nào?",
            "confidence": 0.746
        },
        "target_collection": "quy_trinh_cap_ho_tich_cap_xa",
        "query": "Thủ tục đăng ký kết hôn được thực hiện như thế nào?",
        "confidence": 0.746,
        "status": "found"
    }
    
    result = clarification_service.generate_clarification(
        confidence=0.746,
        routing_result=routing_result,
        query="Thủ tục đăng ký kết hôn được thực hiện như thế nào?",
        session_id="debug_001"
    )
    
    print(f"Result type: {type(result)}")
    
    if hasattr(result, 'model_dump'):
        result_dict = result.model_dump()
    elif hasattr(result, 'dict'):
        result_dict = result.dict()
    else:
        result_dict = result
    
    print("\\n📋 Full Response Structure:")
    print(json.dumps(result_dict, indent=2, ensure_ascii=False, default=str))
    
    print("\\n🔍 Key Analysis:")
    print(f"Type: {result_dict.get('type')}")
    print(f"Style: {result_dict.get('style')}")
    print(f"Has clarification: {'clarification' in result_dict}")
    
    if 'clarification' in result_dict:
        clarification = result_dict['clarification']
        print(f"Clarification style: {clarification.get('style')}")
        print(f"Options count: {len(clarification.get('options', []))}")
    
    if 'options' in result_dict:
        options = result_dict['options']
        print(f"Direct options count: {len(options)}")
        for i, option in enumerate(options[:2]):  # First 2 options
            print(f"  Option {i+1}: {option.get('title', '')[:50]}...")
            print(f"    Document: '{option.get('document', '')}'")
            print(f"    Procedure: '{option.get('procedure', '')}'")

if __name__ == "__main__":
    debug_confirmation_response()