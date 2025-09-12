#!/usr/bin/env python3
"""
Test to ensure clarification service returns correct schema format
that frontend expects
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.clarification import ClarificationService
from app.models.schemas import StandardClarificationResponse
import json

def test_frontend_compatibility():
    """Test để đảm bảo response format tương thích với frontend"""
    
    print("🧪 Testing frontend compatibility...")
    
    try:
        # Initialize service
        service = ClarificationService(
            storage_path="data/storage/collections",
            config_path="config/clarification_config.json"
        )
        
        # Test với các confidence level khác nhau
        test_cases = [
            {
                'confidence': 0.85,
                'case': 'High confidence (auto route)',
                'routing_result': {
                    'confidence': 0.85,
                    'target_collection': 'quy_trinh_cap_ho_tich_cap_xa',
                    'best_match': {
                        'question': 'Thủ tục khai sinh',
                        'document': 'ho_tich_khai_sinh.pdf'
                    }
                }
            },
            {
                'confidence': 0.70,
                'case': 'Medium-high confidence (confirmation)',
                'routing_result': {
                    'confidence': 0.70,
                    'target_collection': 'quy_trinh_cap_ho_tich_cap_xa',
                    'best_match': {
                        'question': 'Thủ tục khai sinh',
                        'document': 'ho_tich_khai_sinh.pdf'
                    },
                    'all_scores': {
                        'quy_trinh_cap_ho_tich_cap_xa': 0.70,
                        'quy_trinh_chung_thuc': 0.55
                    }
                }
            },
            {
                'confidence': 0.25,
                'case': 'Low confidence (context gathering)',
                'routing_result': {
                    'confidence': 0.25,
                    'target_collection': None,
                    'all_scores': {}
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🔍 Testing {test_case['case']}...")
            
            result = service.generate_clarification(
                query="Test query",
                confidence=test_case['confidence'],
                routing_result=test_case['routing_result']
            )
            
            # Verify result is StandardClarificationResponse
            assert isinstance(result, StandardClarificationResponse), f"Expected StandardClarificationResponse, got {type(result)}"
            
            # Convert to dict for frontend consumption
            result_dict = result.model_dump()
            
            # Check required fields for frontend
            required_fields = ['type', 'confidence_level', 'message', 'options']
            for field in required_fields:
                assert field in result_dict, f"Missing required field: {field}"
            
            # Check options format
            assert isinstance(result_dict['options'], list), "Options should be a list"
            
            for option in result_dict['options']:
                assert 'id' in option, "Option missing 'id'"
                assert 'title' in option, "Option missing 'title'"
                assert 'action' in option, "Option missing 'action'"
            
            print(f"✅ {test_case['case']} - OK")
            print(f"   Type: {result_dict['type']}")
            print(f"   Confidence level: {result_dict['confidence_level']}")
            print(f"   Options count: {len(result_dict['options'])}")
            
            # Print sample for manual inspection
            if test_case['confidence'] == 0.70:  # Medium-high case
                print("📋 Sample response structure:")
                print(json.dumps(result_dict, indent=2, ensure_ascii=False)[:500] + "...")
        
        print("\n✅ All tests passed! Frontend compatibility confirmed.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_compatibility()