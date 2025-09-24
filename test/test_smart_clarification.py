"""Test Script for Smart Clarification System
==========================================

This script tests the new Smart Confirmation logic in clarification.py:
- Test different confidence levels
- Verify that high confidence leads to direct question suggestions
- Ensure fallback works when needed
- Test the proceed_with_question flow

Author: LegalRAG Team
"""

import sys
import os
import json
import time
from typing import Dict, Any

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'rag_service'))

def test_smart_clarification():
    """Test the Smart Clarification system"""
    print("🚀 Testing Smart Clarification System...")
    
    try:
        # Import the clarification service
        from app.services.clarification import ClarificationService
        
        # Initialize the service (without embedding model for now)
        clarification_service = ClarificationService(
            embedding_model=None,
            config_path=None,
            storage_path="data/storage/collections"
        )
        
        print(f"✅ ClarificationService initialized successfully")
        print(f"📊 Loaded {len(clarification_service.collections)} collections")
        
        # Test Case 1: High Confidence (should trigger Smart Confirmation)
        print("\n" + "="*60)
        print("🧪 TEST CASE 1: High Confidence (0.75) - Should suggest direct question")
        print("="*60)
        
        high_confidence_routing = {
            "query": "muốn hỏi dụ đăng ký",  # Use actual user input from the bug
            "target_collection": "quy_trinh_cap_ho_tich_cap_xa",
            "best_match": {
                "question": "Đăng ký khai sinh cần gì?",  # Router's suggested question
                "document": "DOC_001",
                "collection": "quy_trinh_cap_ho_tich_cap_xa"
            },
            "confidence": 0.737  # Actual confidence from the bug
        }
        
        result = clarification_service.generate_clarification(
            confidence=0.737,
            routing_result=high_confidence_routing,
            query="muốn hỏi dụ đăng ký"
        )
        
        print(f"📝 Result type: {getattr(result, 'type', 'Unknown')}")
        print(f"🎯 Confidence level: {getattr(result, 'confidence_level', 'Unknown')}")
        print(f"💬 Message: {getattr(result, 'message', 'No message')[:100]}...")
        
        options = getattr(result, 'options', [])
        print(f"🔢 Number of options: {len(options)}")
        
        if options:
            first_option = options[0]
            first_action = getattr(first_option, 'action', 'Unknown')
            first_title = getattr(first_option, 'title', 'No title')
            print(f"🥇 First option action: {first_action}")
            print(f"🥇 First option title: {first_title[:80]}...")
            
            # Check if it's the smart confirmation
            if first_action == 'proceed_with_question':
                print("✅ SUCCESS: Smart Confirmation is working! First option is 'proceed_with_question'")
            else:
                print("⚠️  WARNING: Smart Confirmation not triggered, first action is not 'proceed_with_question'")
        
        # Test Case 2: Medium Confidence (should use old behavior)
        print("\n" + "="*60)  
        print("🧪 TEST CASE 2: Medium Confidence (0.60) - Should use multiple choice")
        print("="*60)
        
        medium_confidence_routing = {
            "query": "Thủ tục gì đó",
            "target_collection": "quy_trinh_cap_ho_tich_cap_xa", 
            "all_scores": {
                "quy_trinh_cap_ho_tich_cap_xa": 0.60,
                "quy_trinh_chung_thuc": 0.55,
                "quy_trinh_boi_thuong_nn": 0.50
            },
            "confidence": 0.60
        }
        
        result2 = clarification_service.generate_clarification(
            confidence=0.60,
            routing_result=medium_confidence_routing,
            query="Thủ tục gì đó"
        )
        
        print(f"📝 Result type: {getattr(result2, 'type', 'Unknown')}")
        print(f"🎯 Confidence level: {getattr(result2, 'confidence_level', 'Unknown')}")
        options2 = getattr(result2, 'options', [])
        print(f"🔢 Number of options: {len(options2)}")
        
        if options2:
            first_action = getattr(options2[0], 'action', 'Unknown')
            print(f"🥇 First option action: {first_action}")
            if first_action == 'proceed_with_collection':
                print("✅ SUCCESS: Medium confidence correctly uses multiple choice")
            else:
                print(f"⚠️  WARNING: Unexpected action for medium confidence: {first_action}")
        
        # Test Case 3: Test handle_user_selection with proceed_with_question
        print("\n" + "="*60)
        print("🧪 TEST CASE 3: Testing handle_user_selection with proceed_with_question")
        print("="*60)
        
        if options and getattr(options[0], 'action', None) == 'proceed_with_question':
            selected_option = {
                "action": "proceed_with_question",
                "question_text": "Đăng ký kết hôn cần những giấy tờ gì?",
                "collection": "quy_trinh_cap_ho_tich_cap_xa",
                "document": "DOC_001",
                "procedure": "Đăng ký kết hôn",
                "confidence_percent": 75.0,
                "original_query": "Tôi muốn đăng ký kết hôn cần những giấy tờ gì?"
            }
            
            proceed_result = clarification_service.handle_user_selection(
                selected_option=selected_option,
                session_id="test_session_123"
            )
            
            print(f"📝 Proceed result type: {proceed_result.get('type', 'Unknown')}")
            print(f"❓ Final query: {proceed_result.get('final_query', 'No query')[:80]}...")
            print(f"📚 Collection: {proceed_result.get('collection', 'Unknown')}")
            print(f"📄 Document: {proceed_result.get('document', 'Unknown')}")
            
            if proceed_result.get('type') == 'proceed_with_question':
                print("✅ SUCCESS: proceed_with_question handling works correctly")
            else:
                print("⚠️  WARNING: proceed_with_question handling may have issues")
        else:
            print("⏭️  SKIPPED: No proceed_with_question option to test")
        
        # Test Case 4: Test fallback behavior when no questions found
        print("\n" + "="*60)
        print("🧪 TEST CASE 4: Testing fallback when no questions found")
        print("="*60)
        
        fallback_routing = {
            "query": "Câu hỏi về collection không tồn tại",
            "target_collection": "non_existent_collection",
            "best_match": {
                "question": "Unknown procedure",
                "document": "DOC_999",
                "collection": "non_existent_collection"
            },
            "confidence": 0.75
        }
        
        fallback_result = clarification_service.generate_clarification(
            confidence=0.75,
            routing_result=fallback_routing,
            query="Câu hỏi về collection không tồn tại"
        )
        
        print(f"📝 Fallback result type: {getattr(fallback_result, 'type', 'Unknown')}")
        fallback_options = getattr(fallback_result, 'options', [])
        print(f"🔢 Number of fallback options: {len(fallback_options)}")
        
        if fallback_options:
            fallback_first_action = getattr(fallback_options[0], 'action', 'Unknown')
            print(f"🥇 Fallback first option action: {fallback_first_action}")
            if fallback_first_action == 'show_document_questions':
                print("✅ SUCCESS: Fallback correctly uses show_document_questions when no smart questions found")
            else:
                print(f"⚠️  INFO: Fallback uses different action: {fallback_first_action}")
        
        print("\n" + "="*60)
        print("🎉 SMART CLARIFICATION TEST COMPLETED")
        print("="*60)
        print("✅ All tests executed successfully!")
        print("📊 Check the results above to verify Smart Confirmation is working")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_questions_for_clarify():
    """Test the _get_questions_for_clarify method independently"""
    print("\n🔍 Testing _get_questions_for_clarify method...")
    
    try:
        from app.services.clarification import ClarificationService
        
        clarification_service = ClarificationService()
        
        # Test with a real collection and document
        questions = clarification_service._get_questions_for_clarify(
            collection="quy_trinh_boi_thuong_nn",
            document="DOC_001", 
            original_query="Xác định cơ quan giải quyết bồi thường như thế nào?"
        )
        
        print(f"📊 Found {len(questions)} questions")
        for i, q in enumerate(questions[:3]):  # Show first 3
            if isinstance(q, dict):
                print(f"  {i+1}. {q.get('text', 'No text')[:60]}... (confidence: {q.get('confidence', 0):.2f})")
            else:
                print(f"  {i+1}. {str(q)[:60]}...")
        
        if questions:
            print("✅ _get_questions_for_clarify is working")
        else:
            print("⚠️  No questions found - check file paths")
            
    except Exception as e:
        print(f"❌ Error testing _get_questions_for_clarify: {e}")

if __name__ == "__main__":
    print("🧪 STARTING SMART CLARIFICATION TESTS")
    print("=" * 80)
    
    # Test 1: Main Smart Clarification logic
    success = test_smart_clarification()
    
    # Test 2: Questions helper method
    test_questions_for_clarify()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 TEST SUITE COMPLETED - Check results above for verification")
    else:
        print("❌ TEST SUITE FAILED - Check error messages above")
    print("=" * 80)