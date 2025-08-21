#!/usr/bin/env python3
"""
TEST CLARIFICATION SYSTEM FIX
==============================

Test để verify rằng clarification system hoạt động đúng với cấu trúc mới:
- Router cache đã được rebuild
- Câu hỏi về "lập di chúc" should match với collection "quy_trinh_chung_thuc"
- Medium confidence sẽ hiển thị multiple choices đúng
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.rag_engine import RAGEngine

async def test_di_chuc_clarification():
    """Test câu hỏi về di chúc với clarification system mới"""
    
    print("🧪 TESTING CLARIFICATION SYSTEM WITH DI CHÚC QUERY")
    print("=" * 60)
    
    try:
        # Initialize RAG Engine
        print("🔄 Initializing RAG Engine...")
        rag_engine = RAGEngine()
        
        # Test query về lập di chúc
        test_query = "Xin chào tôi muốn hỏi lập di chúc thì cần phải đón..."
        session_id = "test_di_chuc_clarification"
        
        print(f"📝 Test Query: {test_query}")
        print(f"🆔 Session ID: {session_id}")
        print()
        
        # Process query
        print("🚀 Processing query...")
        result = await rag_engine.process_query(test_query, session_id)
        
        print("📊 RESULT ANALYSIS:")
        print("-" * 40)
        print(f"Type: {result.get('type')}")
        print(f"Status: {result.get('status', 'N/A')}")
        
        if result.get('type') == 'clarification_needed':
            clarification = result.get('clarification', {})
            print(f"Confidence Level: {result.get('confidence_level')}")
            print(f"Confidence Score: {result.get('confidence', 0):.3f}")
            print(f"Message: {clarification.get('message', 'N/A')}")
            
            print("\n🎯 CLARIFICATION OPTIONS:")
            options = clarification.get('options', [])
            for i, option in enumerate(options, 1):
                print(f"{i}. {option.get('title', 'N/A')}")
                print(f"   Description: {option.get('description', 'N/A')}")
                print(f"   Collection: {option.get('collection', 'N/A')}")
                print(f"   Action: {option.get('action', 'N/A')}")
                print()
            
            # Check if "chung_thuc" is in options
            collections_in_options = [opt.get('collection') for opt in options if opt.get('collection')]
            if 'quy_trinh_chung_thuc' in collections_in_options:
                print("✅ PASS: 'quy_trinh_chung_thuc' found in clarification options")
            else:
                print("❌ FAIL: 'quy_trinh_chung_thuc' NOT found in clarification options")
                print(f"Available collections: {collections_in_options}")
        
        elif result.get('type') == 'answer':
            print("⚠️  Query was directly answered (high confidence)")
            routing_info = result.get('routing_info', {})
            print(f"Routed to: {routing_info.get('target_collection')}")
            print(f"Confidence: {routing_info.get('confidence', 0):.3f}")
        
        else:
            print(f"❓ Unexpected result type: {result.get('type')}")
        
        print("\n" + "=" * 60)
        return result
        
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_router_scores():
    """Test router scores directly để hiểu matching behavior"""
    
    print("\n🔍 TESTING ROUTER SCORES DIRECTLY")
    print("=" * 50)
    
    try:
        from app.services.router import QueryRouter
        from sentence_transformers import SentenceTransformer
        
        # Initialize components
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
        router = QueryRouter(model)
        
        test_query = "Xin chào tôi muốn hỏi lập di chúc thì cần phải đón..."
        
        print(f"📝 Query: {test_query}")
        print()
        
        # Get routing result
        result = router.route_query(test_query, session=None)
        
        print("📊 ROUTER RESULT:")
        print(f"Status: {result.get('status')}")
        print(f"Confidence Level: {result.get('confidence_level')}")
        print(f"Target Collection: {result.get('target_collection')}")
        print(f"Confidence Score: {result.get('confidence', 0):.3f}")
        print(f"Matched Example: {result.get('matched_example', 'N/A')[:100]}...")
        print(f"Source Procedure: {result.get('source_procedure', 'N/A')}")
        
        # Show all scores
        all_scores = result.get('all_scores', {})
        if all_scores:
            print("\n🎯 ALL COLLECTION SCORES:")
            sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
            for collection, score in sorted_scores:
                print(f"  {collection}: {score:.3f}")
        
        print("\n" + "=" * 50)
        return result
        
    except Exception as e:
        print(f"❌ ERROR in router test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("🚀 CLARIFICATION SYSTEM COMPREHENSIVE TEST")
    print("=" * 70)
    
    # Test 1: Full RAG Engine flow
    rag_result = await test_di_chuc_clarification()
    
    # Test 2: Router scores directly
    router_result = await test_router_scores()
    
    print("\n📋 SUMMARY:")
    print("-" * 30)
    
    if rag_result and router_result:
        print("✅ Both tests completed")
        
        # Check if di chúc properly routes to chung_thuc
        router_target = router_result.get('target_collection')
        if router_target == 'quy_trinh_chung_thuc':
            print("✅ Router correctly identifies 'quy_trinh_chung_thuc' collection")
        else:
            print(f"❌ Router incorrectly routes to: {router_target}")
        
        # Check clarification
        if rag_result.get('type') == 'clarification_needed':
            print("✅ Clarification system triggered correctly")
        else:
            print("⚠️  Clarification not triggered")
    
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())
