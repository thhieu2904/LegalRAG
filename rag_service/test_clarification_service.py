#!/usr/bin/env python3
"""
Test script cho Clarification Service sau khi refactor
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.clarification import ClarificationService
from app.models.schemas import StandardClarificationResponse

def test_clarification_service():
    """Test basic functionality của ClarificationService"""
    
    print("🧪 Testing ClarificationService...")
    
    try:
        # Initialize service
        service = ClarificationService(
            storage_path="data/storage/collections",
            config_path="config/clarification_config.json"
        )
        print("✅ Service initialized successfully")
        
        # Test generate_clarification với mock data
        mock_routing_result = {
            'confidence': 0.85,
            'target_collection': 'quy_trinh_cap_ho_tich_cap_xa',
            'best_match': {
                'question': 'Thủ tục khai sinh',
                'document': 'ho_tich_khai_sinh.pdf'
            },
            'all_scores': {
                'quy_trinh_cap_ho_tich_cap_xa': 0.85,
                'quy_trinh_chung_thuc': 0.65
            }
        }
        
        result = service.generate_clarification(
            query="Tôi muốn làm giấy khai sinh cho con",
            confidence=0.85,
            routing_result=mock_routing_result
        )
        
        print("✅ generate_clarification completed")
        print(f"Response type: {type(result)}")
        
        if isinstance(result, StandardClarificationResponse):
            print(f"✅ Correct response type: StandardClarificationResponse")
            print(f"   - Type: {result.type}")
            print(f"   - Confidence level: {result.confidence_level}")
            print(f"   - Options count: {len(result.options)}")
            print(f"   - Target collection: {result.target_collection}")
        else:
            print(f"❌ Wrong response type: {type(result)}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clarification_service()