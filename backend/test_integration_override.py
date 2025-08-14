#!/usr/bin/env python3
"""
Test Stateful Router với integration test hoàn chính
Mô phỏng full flow với confidence override
"""

import sys
import os
sys.path.append('.')

import logging
import time
from app.services.rag_engine import OptimizedEnhancedRAGService, OptimizedChatSession
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_integration():
    """Test full integration với mock high confidence"""
    
    print("🚀 Initializing services for integration test...")
    
    try:
        # Initialize services
        vectordb_service = VectorDBService()
        llm_service = LLMService()
        rag_service = OptimizedEnhancedRAGService(
            documents_dir="data/documents",
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        print("✅ Services initialized successfully")
        
        # Test with integration
        print("\n" + "="*60)
        print("🧪 INTEGRATION TEST: Confidence Override Flow")
        print("="*60)
        
        session_id = rag_service.create_session({"test": "integration"})
        session = rag_service.get_session(session_id)
        
        if not session:
            print(f"❌ Failed to create/get session {session_id}")
            return
            
        # Step 1: Manually set up high confidence state (simulate successful previous query)
        print("Step 1: Setup high confidence context")
        session.update_successful_routing(
            collection="ho_tich_cap_xa",
            confidence=0.92,
            rag_content={"simulated": "content"}
        )
        print(f"✅ Session state set: {session.last_successful_collection} (confidence: {session.last_successful_confidence:.3f})")
        
        # Step 2: Test với low confidence query để trigger override
        print("\nStep 2: Test low confidence query with override")
        low_confidence_query = "tôi muốn hỏi"  # Câu hỏi rất mơ hồ để có confidence thấp
        
        # Test routing với session
        routing_result = rag_service.smart_router.route_query(low_confidence_query, session)
        
        print(f"Query: '{low_confidence_query}'")
        print(f"Routing result:")
        print(f"  - Confidence level: {routing_result.get('confidence_level', 'unknown')}")
        print(f"  - Current confidence: {routing_result.get('confidence', 0):.3f}")
        print(f"  - Original confidence: {routing_result.get('original_confidence', routing_result.get('confidence', 0)):.3f}")
        print(f"  - Was overridden: {routing_result.get('was_overridden', False)}")
        print(f"  - Target collection: {routing_result.get('target_collection', 'None')}")
        
        # Step 3: Test without session context
        print("\nStep 3: Same query without session (control test)")
        routing_result_no_session = rag_service.smart_router.route_query(low_confidence_query, None)
        
        print(f"Without session:")
        print(f"  - Confidence level: {routing_result_no_session.get('confidence_level', 'unknown')}")
        print(f"  - Confidence: {routing_result_no_session.get('confidence', 0):.3f}")
        print(f"  - Target collection: {routing_result_no_session.get('target_collection', 'None')}")
        
        # Step 4: Show difference
        print(f"\n📊 COMPARISON:")
        print(f"With session override:    {routing_result.get('confidence', 0):.3f} -> {routing_result.get('target_collection', 'None')}")
        print(f"Without session (normal): {routing_result_no_session.get('confidence', 0):.3f} -> {routing_result_no_session.get('target_collection', 'None')}")
        
        if routing_result.get('was_overridden', False):
            print("🔥 SUCCESS: Confidence override working!")
        else:
            print("⚠️  Override not triggered - checking conditions...")
            print(f"   Session has successful collection: {session.last_successful_collection is not None}")
            print(f"   Should override (current confidence): {session.should_override_confidence(routing_result.get('confidence', 0))}")
        
        print("\n✅ Integration test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_integration()
