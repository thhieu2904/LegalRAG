#!/usr/bin/env python3
"""
Test Stateful Router với manual simulation
Mô phỏng kịch bản confidence cao để test override logic
"""

import sys
import os
sys.path.append('.')

import logging
import time
from app.services.rag_engine import OptimizedChatSession

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_session_state_logic():
    """Test Session State logic trực tiếp"""
    
    print("🚀 Testing OptimizedChatSession state logic...")
    
    # Create session
    session = OptimizedChatSession(
        session_id="test-session",
        created_at=time.time(),
        last_accessed=time.time()
    )
    
    print("\n" + "="*60)
    print("🧪 TEST CASE 1: Initial State")
    print("="*60)
    print(f"Last successful collection: {session.last_successful_collection}")
    print(f"Last successful confidence: {session.last_successful_confidence}")
    print(f"Should override confidence (0.4): {session.should_override_confidence(0.4)}")
    
    print("\n" + "="*60) 
    print("🧪 TEST CASE 2: Update Successful Routing")
    print("="*60)
    
    # Simulate successful routing
    session.update_successful_routing(
        collection="ho_tich_cap_xa",
        confidence=0.92,
        rag_content={"test": "content"}
    )
    
    print(f"Last successful collection: {session.last_successful_collection}")
    print(f"Last successful confidence: {session.last_successful_confidence:.3f}")
    print(f"Last successful timestamp: {session.last_successful_timestamp}")
    print(f"Has cached content: {session.cached_rag_content is not None}")
    
    print("\n" + "="*60)
    print("🧪 TEST CASE 3: Should Override Logic")
    print("="*60)
    print(f"Should override confidence (0.4): {session.should_override_confidence(0.4)}")  # Should be True
    print(f"Should override confidence (0.6): {session.should_override_confidence(0.6)}")  # Should be False (>= 0.5)
    print(f"Should override confidence (0.3): {session.should_override_confidence(0.3)}")  # Should be True
    
    print("\n" + "="*60)
    print("🧪 TEST CASE 4: Low Confidence Counter")
    print("="*60)
    print(f"Initial consecutive low confidence count: {session.consecutive_low_confidence_count}")
    
    session.increment_low_confidence()
    print(f"After 1 increment: {session.consecutive_low_confidence_count}")
    
    session.increment_low_confidence()
    session.increment_low_confidence()
    print(f"After 3 increments total: {session.consecutive_low_confidence_count}")
    
    # Should still have state
    print(f"Still has last successful collection: {session.last_successful_collection}")
    
    # Clear state (simulate too many failures)
    session.clear_routing_state()
    print(f"After clearing state: {session.last_successful_collection}")
    print(f"After clearing, consecutive count: {session.consecutive_low_confidence_count}")
    
    print("\n" + "="*60)
    print("🧪 TEST CASE 5: Time-based Expiration")
    print("="*60)
    
    # Set up state again
    session.update_successful_routing("ho_tich_cap_xa", 0.92)
    print(f"Updated state, should override (0.4): {session.should_override_confidence(0.4)}")
    
    # Simulate old timestamp (> 10 minutes ago)
    session.last_successful_timestamp = time.time() - 700  # 11 minutes ago
    print(f"With old timestamp, should override (0.4): {session.should_override_confidence(0.4)}")  # Should be False
    
    print("\n✅ Session state logic test completed!")

if __name__ == "__main__":
    test_session_state_logic()
