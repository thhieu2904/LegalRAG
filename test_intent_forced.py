#!/usr/bin/env python3
"""
TEST SMART INTENT với BYPASS ROUTER
Test cải tiến system với forced routing để test intent detection logic
"""

import os
import sys
import logging
import time

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_intent_with_forced_routing():
    """Test intent detection với forced routing để bypass router issues"""
    print("🧪 TESTING INTENT DETECTION WITH FORCED ROUTING")
    print("=" * 70)
    
    # Setup environment and services
    settings.setup_environment()
    
    vectordb_service = VectorDBService()
    llm_service = LLMService()
    rag_service = OptimizedEnhancedRAGService(
        vectordb_service=vectordb_service,
        llm_service=llm_service,
        documents_dir=str(settings.documents_path)
    )
    
    # Test cases với forced routing để bypass router
    test_cases = [
        {
            "name": "Query về LỆ PHÍ (forced ho_tich_cap_xa)",
            "query": "Lệ phí đăng ký khai sinh là bao nhiêu tiền?",
            "expected_intent": "query_fee",
            "forced_collection": "ho_tich_cap_xa"
        },
        {
            "name": "Query về THỜI GIAN (forced ho_tich_cap_xa)",
            "query": "Thủ tục đăng ký khai sinh mất bao lâu?",
            "expected_intent": "query_time",
            "forced_collection": "ho_tich_cap_xa"
        }
    ]
    
    session_id = None
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 50)
        print(f"📝 Query: {test_case['query']}")
        print(f"🎯 Forced Collection: {test_case['forced_collection']}")
        
        start_time = time.time()
        
        try:
            # Test intent detection directly
            detected_intent = rag_service._detect_specific_intent(test_case['query'])
            print(f"🎯 Detected Intent: {detected_intent or 'None'}")
            print(f"✅ Expected Intent: {test_case['expected_intent'] or 'None'}")
            
            intent_correct = detected_intent == test_case['expected_intent']
            print(f"📊 Intent Detection: {'✅ CORRECT' if intent_correct else '❌ INCORRECT'}")
            
            # Run query với forced routing để bypass router issues
            result = rag_service.enhanced_query(
                query=test_case['query'],
                session_id=session_id,
                forced_collection=test_case['forced_collection']  # Force routing
            )
            
            if not session_id:
                session_id = result.get('session_id')
            
            processing_time = time.time() - start_time
            
            # Analyze response  
            answer = result.get('answer', '')
            response_type = result.get('type', 'unknown')
            
            print(f"⏱️  Processing Time: {processing_time:.2f}s")
            print(f"📋 Response Type: {response_type}")
            print(f"📏 Answer Length: {len(answer)} chars")
            
            # Show answer
            if response_type == 'answer':
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"💬 Answer:\n{answer_preview}")
                
                # Check for metadata-specific information
                if test_case['expected_intent'] == 'query_fee':
                    has_fee_info = any(word in answer.lower() for word in ['miễn phí', 'phí', 'tiền', 'đồng', 'vnd'])
                    print(f"💰 Contains Fee Info: {'✅ YES' if has_fee_info else '❌ NO'}")
                    
                elif test_case['expected_intent'] == 'query_time':
                    has_time_info = any(word in answer.lower() for word in ['thời gian', 'ngày', 'lâu', 'hạn', 'khi'])
                    print(f"⏰ Contains Time Info: {'✅ YES' if has_time_info else '❌ NO'}")
                    
            elif response_type == 'clarification_request':
                questions = result.get('clarification_questions', [])
                print(f"🤔 Clarification Questions ({len(questions)}):")
                for q in questions[:3]:  # Show first 3
                    print(f"  • {q}")
                    
            # Quality assessment
            quality_score = 0
            if intent_correct: quality_score += 1
            if response_type == 'answer': quality_score += 1
            if processing_time < 15: quality_score += 1
            
            quality = "EXCELLENT" if quality_score >= 3 else "GOOD" if quality_score >= 2 else "NEEDS_IMPROVEMENT"
            print(f"🏆 Quality: {quality} ({quality_score}/3)")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎉 INTENT DETECTION TEST WITH FORCED ROUTING COMPLETED!")

if __name__ == "__main__":
    test_intent_with_forced_routing()
