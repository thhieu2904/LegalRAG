#!/usr/bin/env python3
"""
Test Script for show_document_questions Action
==============================================

This script tests the specific issue with "Không chính xác, cho tôi xem các lựa chọn khác" action.

Author: LegalRAG Team
"""

import sys
import os

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'rag_service'))

def test_show_document_questions():
    """Test the show_document_questions action specifically"""
    print("🧪 Testing show_document_questions Action...")
    
    try:
        from app.services.clarification import ClarificationService
        
        # Initialize the service
        clarification_service = ClarificationService(
            embedding_model=None,
            config_path=None,
            storage_path="data/storage/collections"
        )
        
        print(f"✅ ClarificationService initialized successfully")
        
        # Simulate the "show_document_questions" action that user clicks
        print("\n" + "="*60)
        print("🧪 TEST: show_document_questions Action")
        print("="*60)
        
        # This represents the option that user clicks from Smart Confirmation
        selected_option = {
            "action": "show_document_questions",
            "collection": "quy_trinh_cap_ho_tich_cap_xa",
            "document": "DOC_001", 
            "procedure": "Đăng ký khai sinh cần gì?",
            "original_query": "muốn hỏi dụ đăng ký",  # Original user query
            "id": "show_all",
            "title": "Không chính xác, cho tôi xem các lựa chọn khác"
        }
        
        # Handle the user selection
        result = clarification_service.handle_user_selection(
            selected_option=selected_option,
            session_id="test_session_show_doc"
        )
        
        print(f"📝 Result type: {result.get('type', 'Unknown')}")
        print(f"💬 Message: {result.get('message', 'No message')[:100]}...")
        
        options = result.get('options', [])
        print(f"🔢 Number of questions returned: {len(options)}")
        
        if options:
            print(f"🎯 First 3 questions:")
            for i, option in enumerate(options[:3]):
                print(f"  {i+1}. {option.get('title', 'No title')[:60]}...")
                print(f"     Action: {option.get('action', 'Unknown')}")
                print(f"     Confidence: {option.get('confidence_percent', 'N/A')}%")
        
        # Check if the result is correct
        if result.get('type') == 'clarification_needed' and len(options) > 0:
            print("✅ SUCCESS: show_document_questions returned question list correctly")
        else:
            print("❌ FAILED: show_document_questions did not return expected result")
            
        return True
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 STARTING show_document_questions TEST")
    print("=" * 80)
    
    success = test_show_document_questions()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 TEST COMPLETED")
    else:
        print("❌ TEST FAILED")
    print("=" * 80)