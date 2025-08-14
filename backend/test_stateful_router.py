#!/usr/bin/env python3
"""
Test Stateful Router functionality
Kiểm tra xem Router có nhớ context và override confidence thấp không
"""

import sys
import os
sys.path.append('.')

import logging
import time
from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stateful_router():
    """Test các scenario cho Stateful Router"""
    
    print("🚀 Initializing services...")
    
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
        
        # Test Case 1: High confidence query để establish context
        print("\n" + "="*60)
        print("🧪 TEST CASE 1: High Confidence Query (Establish Context)")
        print("="*60)
        
        session_id = rag_service.create_session({"test": "stateful_router"})
        session = rag_service.get_session(session_id)
        
        if not session:
            print(f"❌ Failed to create/get session {session_id}")
            return
        
        query1 = "Làm thẻ căn cước công dân cho con"
        print(f"Query 1: '{query1}'")
        
        # Test routing trước
        routing_result1 = rag_service.smart_router.route_query(query1, session)
        print(f"Routing result 1: {routing_result1['confidence_level']} (confidence: {routing_result1['confidence']:.3f})")
        print(f"Target collection: {routing_result1.get('target_collection', 'None')}")
        
        if routing_result1['confidence'] >= 0.85:
            # Manually update session state để test
            session.update_successful_routing(
                collection=routing_result1['target_collection'],
                confidence=routing_result1['confidence']
            )
            print(f"✅ Updated session state: {session.last_successful_collection}")
        
        # Test Case 2: Low confidence follow-up query
        print("\n" + "="*60)
        print("🧪 TEST CASE 2: Low Confidence Follow-up (Should Override)")
        print("="*60)
        
        query2 = "nộp ở đâu"  # Câu hỏi mơ hồ, confidence thấp
        print(f"Query 2: '{query2}'")
        
        routing_result2 = rag_service.smart_router.route_query(query2, session)
        print(f"Routing result 2: {routing_result2['confidence_level']} (confidence: {routing_result2['confidence']:.3f})")
        print(f"Original confidence: {routing_result2.get('original_confidence', routing_result2['confidence']):.3f}")
        print(f"Was overridden: {routing_result2.get('was_overridden', False)}")
        print(f"Target collection: {routing_result2.get('target_collection', 'None')}")
        
        # Test Case 3: Test without session context
        print("\n" + "="*60)
        print("🧪 TEST CASE 3: Same Query Without Session Context")
        print("="*60)
        
        routing_result3 = rag_service.smart_router.route_query(query2, None)  # No session
        print(f"Routing result 3 (no session): {routing_result3['confidence_level']} (confidence: {routing_result3['confidence']:.3f})")
        print(f"Target collection: {routing_result3.get('target_collection', 'None')}")
        
        # Test Case 4: Test session state persistence
        print("\n" + "="*60)
        print("🧪 TEST CASE 4: Session State Info")
        print("="*60)
        
        print(f"Session ID: {session.session_id}")
        print(f"Last successful collection: {session.last_successful_collection}")
        print(f"Last successful confidence: {session.last_successful_confidence:.3f}")
        print(f"Consecutive low confidence count: {session.consecutive_low_confidence_count}")
        print(f"Should override confidence (0.4): {session.should_override_confidence(0.4)}")
        print(f"Should override confidence (0.6): {session.should_override_confidence(0.6)}")
        
        print("\n✅ Stateful Router test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stateful_router()
