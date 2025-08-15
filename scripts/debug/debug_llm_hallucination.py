"""
Debug script để kiểm tra LLM output và system prompt
Sẽ test với các query đã bị lỗi để tìm nguyên nhân
"""

import os
import sys
import logging
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_llm_response():
    """Debug LLM response với các test cases đã bị lỗi"""
    
    print("🔍 DEBUGGING LLM HALLUCINATION ISSUES")
    print("=" * 60)
    
    # Initialize services
    print("🚀 Initializing services...")
    vectordb_service = VectorDBService()
    llm_service = LLMService()
    
    # Initialize RAG service với dependencies
    rag_service = OptimizedEnhancedRAGService(
        documents_dir=str(settings.documents_dir),
        vectordb_service=vectordb_service,
        llm_service=llm_service
    )
    
    # Test cases đã bị lỗi
    test_cases = [
        {
            "query": "muốn hỏi về thủ tục nhận nuôi con á",
            "expected": "Thông tin chi tiết về thủ tục nhận nuôi con",
            "issue": "LLM hỏi lại thay vì trả lời trực tiếp"
        },
        {
            "query": "đăng ký khai sinh cho con cần giấy tờ gì vậy",
            "expected": "Danh sách giấy tờ cần thiết cho trường hợp thông thường",
            "issue": "LLM trả lời rối rắm, trộn lẫn nhiều trường hợp"
        },
        {
            "query": "muốn đăng ký khai sinh thì có cần đóng tiền không",
            "expected": "Thông tin về lệ phí đăng ký khai sinh", 
            "issue": "LLM trả lời hoàn toàn sai chủ đề (về xác định cha con)"
        },
        {
            "query": "mình muốn hỏi phí khi mà đăng ký khai sinh á",
            "expected": "Thông tin về phí đăng ký khai sinh",
            "issue": "Router sai + LLM tóm tắt sai"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 TEST CASE {i}: {test_case['query']}")
        print(f"🎯 Expected: {test_case['expected']}")
        print(f"⚠️  Issue: {test_case['issue']}")
        print("-" * 50)
        
        try:
            # Get response từ RAG
            result = rag_service.enhanced_query(
                query=test_case['query'],
                session_id=f"debug_session_{i}"
            )
            
            if result.get('type') == 'answer':
                print(f"🤖 LLM Response:")
                print(f"   {result['answer'][:200]}...")
                print()
                
                # Check context info
                context_info = result.get('context_info', {})
                print(f"📚 Context Info:")
                print(f"   - Nucleus chunks: {context_info.get('nucleus_chunks', 0)}")
                print(f"   - Context length: {context_info.get('context_length', 0)}")
                print(f"   - Source docs: {context_info.get('source_documents', [])}")
                
                # Check routing info
                routing_info = result.get('routing_info', {})
                print(f"🎯 Routing Info:")
                print(f"   - Best collections: {routing_info.get('best_collections', [])}")
                
                # KIỂM TRA CONTEXT CỤ THỂ - ĐÂY LÀ PHẦN QUAN TRỌNG NHẤT
                session = rag_service.get_session(f"debug_session_{i}")
                if session and session.query_history:
                    last_query = session.query_history[-1]
                    if 'debug_context' in last_query:
                        print(f"\n📋 RAW CONTEXT SENT TO LLM:")
                        context_preview = last_query['debug_context'][:500] + "..." if len(last_query['debug_context']) > 500 else last_query['debug_context']
                        print(context_preview)
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("\n" + "=" * 60)
        
        # Wait for user input để xem kết quả
        input("Press Enter để tiếp tục test case tiếp theo...")

if __name__ == "__main__":
    debug_llm_response()
