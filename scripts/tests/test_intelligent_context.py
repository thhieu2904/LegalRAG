#!/usr/bin/env python3
"""
TEST FULL DOCUMENT CONTEXT EXPAN        print(f"⏱️  Time: {ela          print(f"🎯 Quality: {keywords_found}/5 keywords found")
        expansion_strategy = context_info.get('expansion_strategy', 'unknown') if 'context_info' in locals() and context_info else 'no_context_info'
        print(f"📄 Context: Full document loaded ({'✅ CORRECT' if expansion_strategy == 'full_document_legal_context' else '⚠️ CHECK: ' + expansion_strategy})")    print(f"🎯 Quality: {keywords_found}/5 keywords found")
        expansion_strategy = context_info.get('expansion_strategy', 'unknown') if context_info else 'no_context_info'
        print(f"📄 Context: Full document loaded ({'✅ CORRECT' if expansion_strategy == 'full_document_legal_context' else '⚠️ CHECK: ' + expansion_strategy})")ed_time:.2f}s")
        print(f"📏 Answer Length: {len(result['answer'])} chars")
        
        # Initialize context_info safely
        context_info = {}
        if 'context_details' in result:
            context_info = result['context_details']
            print(f"📄 Context Length: {context_info.get('total_length', 0)} chars")
            print(f"📊 Expansion Strategy: {context_info.get('expansion_strategy', 'N/A')}")
            print(f"📁 Source Documents: {len(context_info.get('source_documents', []))}")ểm tra thiết kế gốc: Load TOÀN BỘ document để đảm bảo ngữ cảnh pháp luật đầy đủ
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService
from app.services.language_model import LLMService

async def test_full_document_context():
    """Test full document context expansion - THIẾT KẾ GỐC"""
    
    print("🧪 TESTING FULL DOCUMENT CONTEXT EXPANSION")
    print("=" * 60)
    print("📋 TRIẾT LÝ: Văn bản pháp luật cần được hiểu trong TOÀN BỘ ngữ cảnh")
    print("-" * 60)
    
    try:
        # Initialize services như trong main.py
        print("🔧 Initializing VectorDB service...")
        vectordb_service = VectorDBService()
        
        print("🔧 Initializing LLM service...")
        llm_service = LLMService()
        
        print("🔧 Initializing RAG service...")
        documents_dir = str(Path(__file__).parent / "data" / "documents")
        rag_service = OptimizedEnhancedRAGService(
            documents_dir=documents_dir,
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        # Test query với full document expansion
        test_query = "Thủ tục đăng ký doanh nghiệp có mất phí gì không?"
        
        print(f"📝 Test Query: {test_query}")
        print("-" * 40)
        
        # TEST: FULL DOCUMENT EXPANSION (thiết kế gốc)
        print("\n📄 TESTING: FULL DOCUMENT EXPANSION (THIẾT KẾ GỐC)")
        start_time = time.time()
        
        result = rag_service.enhanced_query(
            query=test_query,
            max_context_length=5000,  # Cho phép document dài để đảm bảo context đầy đủ
            use_full_document_expansion=True  # THIẾT KẾ GỐC
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Time: {elapsed_time:.2f}s")
        print(f"📏 Answer Length: {len(result['answer'])} chars")
        
        if 'context_details' in result:
            context_info = result['context_details']
            print(f"📄 Context Length: {context_info.get('total_length', 0)} chars")
            print(f"📊 Expansion Strategy: {context_info.get('expansion_strategy', 'N/A')}")
            print(f"� Source Documents: {len(context_info.get('source_documents', []))}")
        
        # Analyze answer quality
        key_info = ["phí", "lệ phí", "miễn", "giấy tờ", "thủ tục"]
        keywords_found = sum(1 for keyword in key_info if keyword in result['answer'].lower())
        
        print(f"🔍 Keywords Found: {keywords_found}/{len(key_info)}")
        print(f"� Answer Quality: {'EXCELLENT' if keywords_found >= 4 else 'GOOD' if keywords_found >= 3 else 'NEEDS_IMPROVEMENT'}")
        
        print(f"\n💭 Full Answer:\n{result['answer']}")
        
        # Validation
        print("\n✅ VALIDATION RESULTS")
        print("=" * 40)
        print(f"⚡ Performance: {elapsed_time:.2f}s ({'EXCELLENT' if elapsed_time < 5 else 'ACCEPTABLE' if elapsed_time < 10 else 'SLOW'})")
        print(f"🎯 Quality: {keywords_found}/5 keywords found")
        print(f"� Context: Full document loaded ({'✅ CORRECT' if context_info.get('expansion_strategy') == 'full_document_legal_context' else '⚠️ CHECK'})")
        
        if elapsed_time < 5 and keywords_found >= 3:
            print("\n🎉 SUCCESS: Thiết kế gốc hoạt động HOÀN HẢO!")
            print("✅ Fast response + Full legal context + High quality answer")
        else:
            print("\n⚠️  REVIEW: System cần review thêm")
        
        print("\n✅ TEST COMPLETED!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Full Document Context Test...")
    asyncio.run(test_full_document_context())
