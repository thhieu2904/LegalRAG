#!/usr/bin/env python3
"""
Test Clarification System with Fixed Mappings
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_clarification():
    """Test clarification system with di chúc query"""
    
    print("🧪 TESTING CLARIFICATION SYSTEM")
    print("=" * 50)
    
    try:
        from app.services.clarification import ClarificationService
        
        # Initialize clarification service
        clarification_service = ClarificationService()
        
        # Simulate routing result với scores như trong debug
        routing_result = {
            'target_collection': 'quy_trinh_nuoi_con_nuoi',  # Wrong match
            'confidence': 0.599,
            'all_scores': {
                'quy_trinh_nuoi_con_nuoi': 0.599,
                'quy_trinh_cap_ho_tich_cap_xa': 0.583,
                'quy_trinh_chung_thuc': 0.568  # Should be correct
            },
            'matched_example': 'Tôi muốn nhận con nuôi thì cần những điều kiện gì?',
            'source_procedure': 'Đăng ký việc nuôi con nuôi trong nước'
        }
        
        test_query = "Xin chào tôi muốn hỏi lập di chúc thì cần phải đón..."
        confidence = 0.599
        
        print(f"📝 Query: {test_query}")
        print(f"🎯 Confidence: {confidence:.3f} (Medium confidence)")
        print(f"🎯 Best match (wrong): {routing_result['target_collection']}")
        print()
        
        # Generate clarification
        result = clarification_service.generate_clarification(
            confidence=confidence,
            routing_result=routing_result,
            query=test_query
        )
        
        print("📋 CLARIFICATION RESULT:")
        print("-" * 30)
        print(f"Type: {result.get('type')}")
        print(f"Confidence Level: {result.get('confidence_level')}")
        print(f"Strategy: {result.get('strategy')}")
        
        clarification = result.get('clarification', {})
        print(f"Message: {clarification.get('message')}")
        
        print("\n🎯 OPTIONS:")
        options = clarification.get('options', [])
        
        correct_option_found = False
        
        for i, option in enumerate(options, 1):
            title = option.get('title', 'N/A')
            description = option.get('description', 'N/A')
            collection = option.get('collection', 'N/A')
            
            print(f"{i}. {title}")
            print(f"   Collection: {collection}")
            print(f"   Description: {description}")
            
            # Check if chung_thuc option is available
            if collection == 'quy_trinh_chung_thuc':
                correct_option_found = True
                print(f"   ✅ CORRECT OPTION FOUND!")
            
            print()
        
        if correct_option_found:
            print("✅ SUCCESS: Clarification includes the correct collection (quy_trinh_chung_thuc)")
        else:
            print("❌ FAIL: Clarification missing the correct collection")
        
        # Check if all top 3 collections are included
        collections_in_options = [opt.get('collection') for opt in options if opt.get('collection')]
        expected_collections = ['quy_trinh_nuoi_con_nuoi', 'quy_trinh_cap_ho_tich_cap_xa', 'quy_trinh_chung_thuc']
        
        print(f"\n📊 COVERAGE CHECK:")
        print(f"Expected top 3: {expected_collections}")
        print(f"In options: {collections_in_options}")
        
        missing = [col for col in expected_collections if col not in collections_in_options]
        if not missing:
            print("✅ All top collections included in clarification")
        else:
            print(f"❌ Missing collections: {missing}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in clarification test: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🚀 CLARIFICATION SYSTEM TEST")
    print("=" * 60)
    
    result = test_clarification()
    
    if result:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    main()
