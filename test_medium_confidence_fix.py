#!/usr/bin/env python3
"""
TEST MEDIUM CONFIDENCE CLARIFICATION FIX
=========================================

Test để verify rằng medium confidence (0.5-0.8) giờ trigger clarification
thay vì route sai như trước đây.

Case Study: Query "lập di chúc" trước đây bị route sai thành marriage registration
với confidence 0.673 (medium) mà không hỏi clarification.
"""

import asyncio
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from app.services.rag_engine import RAGService
from app.core.config import Settings

async def test_medium_confidence_clarification():
    """Test medium confidence queries trigger clarification"""
    
    print("🧪 TESTING MEDIUM CONFIDENCE CLARIFICATION FIX")
    print("=" * 60)
    
    settings = Settings()
    rag_service = RAGService(settings)
    
    # Test cases với expected medium confidence (0.5-0.8)
    test_queries = [
        {
            "query": "lập di chúc như thế nào",
            "description": "Query về will/testament - trước đây bị route sai thành marriage",
            "expected": "clarification (not routing to marriage)"
        },
        {
            "query": "thủ tục visa du lịch", 
            "description": "Query về visa - có thể confuse với passport/travel docs",
            "expected": "clarification (ambiguous travel document type)"
        },
        {
            "query": "xin phép xây nhà",
            "description": "Construction permit - có thể confuse với multiple permit types",
            "expected": "clarification (many construction permit types)"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🔍 TEST {i}: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        print(f"Expected: {test_case['expected']}")
        print("-" * 50)
        
        try:
            result = await rag_service.process_query(
                query=test_case['query'],
                session_id=f"test_medium_confidence_{i}"
            )
            
            # Check if clarification was triggered
            if result.get('status') == 'clarification_needed':
                print(f"✅ PASS: Clarification triggered correctly")
                print(f"   Clarification type: {result.get('clarification_type')}")
                if 'options' in result:
                    print(f"   Options provided: {len(result['options'])}")
            elif result.get('status') == 'success':
                print(f"❌ FAIL: Query was routed instead of clarification")
                print(f"   Response length: {len(result.get('response', ''))}")
                print(f"   Router confidence: {result.get('debug_info', {}).get('router_confidence')}")
            else:
                print(f"⚠️ UNKNOWN: Unexpected result status: {result.get('status')}")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
            
    print("\n" + "=" * 60)
    print("🎯 SUMMARY: Medium confidence queries should now trigger clarification")
    print("   instead of proceeding with potentially incorrect routing.")

if __name__ == "__main__":
    asyncio.run(test_medium_confidence_clarification())
