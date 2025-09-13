#!/usr/bin/env python3

import sys, json
sys.path.append('rag_service')

from app.services.rag_engine import RAGService
from app.core.config import Settings

def test_forced_routing():
    print("🧪 TESTING FORCED ROUTING DIRECTLY")
    print("=" * 50)
    
    # Create engine
    config = Settings()
    engine = RAGService(config)
    print("✅ RAGService created")

    # Create session
    session = engine.session_manager.create_session('test-debug-1757788046')

    # Simulate routing info from clarification
    session.metadata = {
        'routing_info': {
            'force_collection': 'quy_trinh_cap_ho_tich_cap_xa',
            'force_document': 'DOC_001'
        }
    }

    print(f"✅ Session created: {session.session_id}")
    print(f"📋 Session metadata: {json.dumps(session.metadata, indent=2)}")

    print("\n🔍 Testing query with forced routing...")

    # Test query
    result = engine.process_query(
        query='Những điều kiện gì để đăng ký khai sinh?',
        session_id='test-debug-1757788046'
    )

    print(f"\n🎯 Result type: {result.get('type')}")
    print(f"📝 Answer: {result.get('answer', 'N/A')}")
    print(f"⏱️ Time: {result.get('processing_time', 0):.3f}s")
    
    if result.get('routing_info'):
        print(f"🚀 Routing: {json.dumps(result['routing_info'], indent=2)}")
    else:
        print("⚠️ No routing_info in result")
        
    if result.get('context_info'):
        print(f"📄 Context: {json.dumps(result['context_info'], indent=2)}")
    else:
        print("⚠️ No context_info in result")

if __name__ == "__main__":
    test_forced_routing()