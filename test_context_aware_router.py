#!/usr/bin/env python3
"""
TEST: Context-Aware Router Fix
Kiểm tra router đã nhớ context trong conversation chưa
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_context_aware_router():
    """Test context-aware router fix"""
    
    print("=== TEST CONTEXT-AWARE ROUTER FIX ===")
    
    try:
        from app.services.rag_engine import OptimizedEnhancedRAGService
        
        # Initialize service
        rag_service = OptimizedEnhancedRAGService()
        
        print("✅ RAG Service initialized")
        
        # Test conversation flow
        print("\n📝 CONVERSATION SIMULATION:")
        
        # Query 1: Initial question about marriage registration
        print("\n--- QUERY 1 ---")
        query1 = "đăng ký kết hôn có tốn phí không"
        result1 = rag_service.enhanced_query(query1, session_id="test_context_session")
        
        print(f"Q1: {query1}")
        print(f"A1: {result1.get('answer', 'No answer')[:100]}...")
        print(f"Routing: {result1.get('routing_info', {}).get('target_collection')}")
        print(f"Confidence: {result1.get('routing_info', {}).get('confidence', 0):.3f}")
        
        # Query 2: Follow-up question (should maintain context)
        print("\n--- QUERY 2 (FOLLOW-UP) ---")
        query2 = "ủa vậy khi nào thì phải đóng phí"
        result2 = rag_service.enhanced_query(query2, session_id="test_context_session")
        
        print(f"Q2: {query2}")
        print(f"A2: {result2.get('answer', 'No answer')[:100]}...")
        print(f"Routing: {result2.get('routing_info', {}).get('target_collection')}")
        print(f"Confidence: {result2.get('routing_info', {}).get('confidence', 0):.3f}")
        
        # Check if router maintained context
        collection1 = result1.get('routing_info', {}).get('target_collection')
        collection2 = result2.get('routing_info', {}).get('target_collection')
        
        print(f"\n🔍 ANALYSIS:")
        print(f"Collection 1: {collection1}")
        print(f"Collection 2: {collection2}")
        
        if collection1 == collection2:
            print("✅ SUCCESS: Router maintained context! Same collection for follow-up.")
        else:
            print("❌ ISSUE: Router lost context. Different collections.")
            
        # Check if second query was recognized as follow-up
        is_followup = result2.get('routing_info', {}).get('is_followup', False)
        confidence_level = result2.get('routing_info', {}).get('confidence_level', '')
        
        print(f"Is follow-up detected: {is_followup}")
        print(f"Confidence level: {confidence_level}")
        
        if 'followup' in confidence_level.lower() or is_followup:
            print("✅ EXCELLENT: Follow-up detection worked!")
        else:
            print("⚠️ Follow-up detection may need improvement")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_aware_router()
