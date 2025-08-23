#!/usr/bin/env python3
"""
Test Medium-High Confidence Flow
================================

Simulates the exact user scenario:
1. Query: "Tôi muốn hỏi khi lập di chúc thì có phần phải đóng phí khi chứng thực không"
2. Should get medium-high confidence (~0.74-0.80)
3. Should show questions about "Thủ tục chứng thực di chúc"
4. User selects "show_document_questions" action
5. Should get list of specific questions about di chúc
"""

import sys
import json
import time
sys.path.append('.')

from app.services.rag_engine import RAGService
from app.core.config import settings

def test_medium_high_flow():
    print("🧪 Testing Medium-High Confidence Flow...")
    print("=" * 60)
    
    # Initialize services
    rag_service = RAGService()
    
    # Test query
    query = "Tôi muốn hỏi khi lập di chúc thì có phần phải đóng phí khi chứng thực không"
    session_id = f"test_session_{int(time.time())}"
    
    print(f"📝 Query: {query}")
    print(f"🔑 Session ID: {session_id}")
    print()
    
    # Step 1: Initial query processing
    print("🚀 Step 1: Processing initial query...")
    try:
        response1 = rag_service.process_query(
            query=query,
            session_id=session_id
        )
        
        print(f"✅ Response type: {response1.get('type')}")
        print(f"📊 Confidence level: {response1.get('confidence_level')}")
        print(f"🎯 Confidence score: {response1.get('confidence', 0):.3f}")
        
        if response1.get('type') == 'clarification_needed':
            print(f"💭 Clarification message: {response1.get('clarification', {}).get('message', 'N/A')}")
            
            options = response1.get('clarification', {}).get('options', [])
            print(f"📋 Available options ({len(options)}):")
            for i, opt in enumerate(options):
                print(f"  {i+1}. {opt.get('title', 'N/A')} (action: {opt.get('action', 'N/A')})")
            
            # Step 2: Select the first option (show_document_questions)
            if options and options[0].get('action') == 'show_document_questions':
                print("\\n🎯 Step 2: User selects 'show_document_questions'...")
                selected_option = options[0]
                
                response2 = rag_service.handle_clarification(
                    session_id=session_id,
                    selected_option=selected_option,
                    original_query=query
                )
                
                print(f"✅ Step 2 Response type: {response2.get('type')}")
                if response2.get('type') == 'clarification_needed':
                    print(f"💭 Message: {response2.get('clarification', {}).get('message', 'N/A')}")
                    
                    step2_options = response2.get('clarification', {}).get('options', [])
                    print(f"📋 Question options ({len(step2_options)}):")
                    for i, opt in enumerate(step2_options):
                        title = opt.get('title', 'N/A')
                        action = opt.get('action', 'N/A')
                        print(f"  {i+1}. {title[:80]}... (action: {action})")
                        
                elif response2.get('type') == 'error':
                    print(f"❌ Error: {response2.get('answer', 'N/A')}")
                else:
                    print(f"📄 Answer: {response2.get('answer', 'N/A')[:100]}...")
            else:
                print("❌ No show_document_questions option found")
        else:
            print(f"📄 Direct answer: {response1.get('answer', 'N/A')[:100]}...")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_medium_high_flow()
