#!/usr/bin/env python3
"""
Test end-to-end Stateful Router trong enhanced_query flow
Mô phỏng conversation hoàn chỉnh
"""

import sys
import os
sys.path.append('.')

import logging
from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_conversation_flow():
    """Test conversation flow với stateful router"""
    
    print("🚀 Testing End-to-End Conversation Flow...")
    
    try:
        # Initialize services
        vectordb_service = VectorDBService()
        llm_service = LLMService()
        rag_service = OptimizedEnhancedRAGService(
            documents_dir="data/documents",
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        print("✅ Services initialized")
        
        # Create session
        session_id = rag_service.create_session({"test": "conversation_flow"})
        session = rag_service.get_session(session_id)
        
        if not session:
            print(f"❌ Failed to create/get session")
            return
        
        print("\n" + "="*60)
        print("🎬 CONVERSATION SIMULATION")
        print("="*60)
        
        # Query 1: High confidence query để establish context
        print("\n👤 User: Làm thủ tục khai sinh cho con")
        
        # Để tránh query thực tế (chậm), chỉ test routing logic
        routing1 = rag_service.smart_router.route_query("Làm thủ tục khai sinh cho con", session)
        
        print(f"🤖 System Routing: {routing1['confidence_level']} (confidence: {routing1['confidence']:.3f})")
        print(f"🎯 Target: {routing1.get('target_collection', 'None')}")
        
        # Simulate successful query by manually updating session
        if routing1['confidence'] > 0.7:  # Simulate high enough confidence
            session.update_successful_routing(
                collection=routing1['target_collection'],
                confidence=0.90  # Simulate high confidence result
            )
            print("✅ Session state updated (simulated successful query)")
        
        # Query 2: Follow-up với confidence thấp
        print(f"\n👤 User: cần giấy tờ gì?")
        
        routing2 = rag_service.smart_router.route_query("cần giấy tờ gì?", session)
        
        print(f"🤖 System Routing: {routing2['confidence_level']} (confidence: {routing2['confidence']:.3f})")
        print(f"🔄 Original confidence: {routing2.get('original_confidence', routing2['confidence']):.3f}")
        print(f"🔥 Was overridden: {routing2.get('was_overridden', False)}")
        print(f"🎯 Target: {routing2.get('target_collection', 'None')}")
        
        # Query 3: Another follow-up
        print(f"\n👤 User: phí bao nhiêu?")
        
        routing3 = rag_service.smart_router.route_query("phí bao nhiêu?", session)
        
        print(f"🤖 System Routing: {routing3['confidence_level']} (confidence: {routing3['confidence']:.3f})")
        print(f"🔄 Original confidence: {routing3.get('original_confidence', routing3['confidence']):.3f}")
        print(f"🔥 Was overridden: {routing3.get('was_overridden', False)}")
        print(f"🎯 Target: {routing3.get('target_collection', 'None')}")
        
        # Query 4: Completely different topic (should clear state)
        print(f"\n👤 User: tôi muốn hỏi về nuôi con nuôi")
        
        routing4 = rag_service.smart_router.route_query("tôi muốn hỏi về nuôi con nuôi", session)
        
        print(f"🤖 System Routing: {routing4['confidence_level']} (confidence: {routing4['confidence']:.3f})")
        print(f"🎯 Target: {routing4.get('target_collection', 'None')}")
        
        # Show session state
        print(f"\n📊 FINAL SESSION STATE:")
        print(f"Last successful collection: {session.last_successful_collection}")
        print(f"Last successful confidence: {session.last_successful_confidence:.3f}")
        print(f"Consecutive low confidence: {session.consecutive_low_confidence_count}")
        
        print("\n✅ Conversation flow test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversation_flow()
