#!/usr/bin/env python3
"""
TEST SMART INTENT DETECTION SYSTEM - Backend Version
Test cải tiến system dựa trên lời khuyên với cache đã sẵn sàng:
1. Enhanced system prompt với metadata awareness  
2. Context expander trả về structured metadata
3. Intent detection cho metadata fields phổ biến
"""

import logging
import time
import json
from app.core.config import settings
from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_smart_intent_detection():
    """Test enhanced intent detection và smart context building"""
    print("🧪 TESTING SMART INTENT DETECTION SYSTEM (Backend)")
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
    
    # Test cases với intent patterns khác nhau
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
        },
        {
            "name": "Query về BIỂU MẪU (forced ho_tich_cap_xa)",
            "query": "Có cần điền biểu mẫu gì không khi đăng ký khai sinh?",
            "expected_intent": "query_form",
            "forced_collection": "ho_tich_cap_xa"
        },
        {
            "name": "Query về CƠ QUAN (forced chung_thuc)",
            "query": "Đăng ký khai sinh ở đâu?",
            "expected_intent": "query_agency",
            "forced_collection": "chung_thuc"
        },
        {
            "name": "Query TỔNG QUÁT (forced ho_tich_cap_xa)",
            "query": "Thủ tục đăng ký khai sinh như thế nào?",
            "expected_intent": None,
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
            
            # Check structured metadata presence
            context_info = result.get('context_info', {})
            structured_metadata = context_info.get('structured_metadata', {}) if 'context_info' in result else {}
            print(f"📊 Structured Metadata Fields: {list(structured_metadata.keys()) if structured_metadata else 'None'}")
            
            # Show answer
            if response_type == 'answer':
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"💬 Answer:\n{answer_preview}")
                
                # Check for metadata-specific information
                if test_case['expected_intent'] == 'query_fee':
                    has_fee_info = any(word in answer.lower() for word in ['miễn phí', 'phí', 'tiền', 'đồng', 'vnd'])
                    print(f"💰 Contains Fee Info: {'✅ YES' if has_fee_info else '❌ NO'}")
                    
                    # Check if fee_text metadata was used
                    if structured_metadata and 'fee_text' in structured_metadata:
                        print(f"🎯 Fee Metadata Available: {structured_metadata['fee_text'][:50]}...")
                    
                elif test_case['expected_intent'] == 'query_time':
                    has_time_info = any(word in answer.lower() for word in ['thời gian', 'ngày', 'lâu', 'hạn', 'khi'])
                    print(f"⏰ Contains Time Info: {'✅ YES' if has_time_info else '❌ NO'}")
                    
                    # Check if processing_time_text metadata was used
                    if structured_metadata and 'processing_time_text' in structured_metadata:
                        print(f"🎯 Time Metadata Available: {structured_metadata['processing_time_text'][:50]}...")
                        
                elif test_case['expected_intent'] == 'query_form':
                    has_form_info = any(word in answer.lower() for word in ['biểu mẫu', 'form', 'tờ khai', 'mẫu'])
                    print(f"📋 Contains Form Info: {'✅ YES' if has_form_info else '❌ NO'}")
                    
                    # Check if has_form metadata was used
                    if structured_metadata and 'has_form' in structured_metadata:
                        print(f"🎯 Form Metadata Available: {structured_metadata['has_form']}")
                        
                elif test_case['expected_intent'] == 'query_agency':
                    has_agency_info = any(word in answer.lower() for word in ['ubnd', 'ủy ban', 'cơ quan', 'phường', 'xã'])
                    print(f"🏛️ Contains Agency Info: {'✅ YES' if has_agency_info else '❌ NO'}")
                    
                    # Check if executing_agency metadata was used
                    if structured_metadata and 'executing_agency' in structured_metadata:
                        print(f"🎯 Agency Metadata Available: {structured_metadata['executing_agency'][:50]}...")
                    
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
            if structured_metadata: quality_score += 0.5  # Bonus for metadata
            
            quality = "EXCELLENT" if quality_score >= 3.5 else "GOOD" if quality_score >= 2.5 else "NEEDS_IMPROVEMENT"
            print(f"🏆 Quality: {quality} ({quality_score}/4)")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎉 SMART INTENT DETECTION TEST COMPLETED!")
    
    print("\n📋 SUMMARY OF IMPROVEMENTS:")
    print("✅ Enhanced Context Expander: Returns structured metadata")
    print("✅ Intent Detection: Detects fee, time, form, agency queries") 
    print("✅ Smart Context Building: Prioritizes relevant metadata")
    print("✅ Enhanced System Prompt: Metadata-aware instructions")
    print("✅ Forced Routing: Bypasses router confidence issues for testing")

if __name__ == "__main__":
    test_smart_intent_detection()
