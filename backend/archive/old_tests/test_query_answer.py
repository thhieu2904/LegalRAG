#!/usr/bin/env python3
"""
TEST QUERY & ANSWER - HỆ THỐNG RAG CHÍNH THỨC
============================================
File này để test các câu hỏi và câu trả lời từ hệ thống RAG
Đây là file chính để test query/answer của hệ thống
"""

import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.vectordb_service import VectorDBService
from app.services.rag_service import RAGService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGTestSuite:
    """Test suite for RAG system query and answer functionality"""
    
    def __init__(self):
        self.setup_services()
        
    def setup_services(self):
        """Initialize all required services"""
        logger.info("🚀 Initializing RAG Test Suite...")
        
        # Initialize services
        self.llm_service = LLMService(
            model_path=str(settings.llm_model_file_path),
            model_url=settings.llm_model_url,
            n_ctx=settings.n_ctx
        )
        
        self.vectordb_service = VectorDBService(
            persist_directory=str(settings.vectordb_path),
            embedding_model=settings.embedding_model_name
        )
        
        self.rag_service = RAGService(
            documents_dir=str(settings.documents_path),
            vectordb_service=self.vectordb_service,
            llm_service=self.llm_service
        )
        
        logger.info("✅ All services initialized successfully")
    
    def test_single_query(self, question: str, expected_collection: str = None):
        """Test a single query with detailed output"""
        print("\n" + "="*80)
        print(f"🔍 TESTING QUERY: {question}")
        print("="*80)
        
        try:
            # Run the query
            result = self.rag_service.query(
                question=question,
                broad_search_k=settings.broad_search_k,  # Use config default
                similarity_threshold=settings.similarity_threshold,
                context_expansion_size=settings.context_expansion_size,
                use_routing=settings.use_routing
            )
            
            # Display results
            print(f"✅ Query successful!")
            print(f"📊 Processing time: {result.get('processing_time', 'N/A'):.2f}s")
            print(f"📋 Method used: {result.get('method', 'N/A')}")
            
            # Search results summary
            search_results = result.get('search_results', [])
            print(f"🔍 Search results: {len(search_results)} documents found")
            
            if search_results:
                # Show collection distribution
                collections = {}
                for doc in search_results:
                    collection = doc.get('metadata', {}).get('collection', 'unknown')
                    collections[collection] = collections.get(collection, 0) + 1
                
                print("📚 Collection distribution:")
                for collection, count in collections.items():
                    print(f"   - {collection}: {count} documents")
                    
                # Show top 3 results
                print("\n📋 Top 3 search results:")
                for i, doc in enumerate(search_results[:3]):
                    metadata = doc.get('metadata', {})
                    score = doc.get('score', 0)
                    title = metadata.get('document_title', 'N/A')
                    section = metadata.get('section_title', 'N/A')
                    print(f"   {i+1}. [{score:.3f}] {title} - {section}")
            
            # Answer preview
            answer = result.get('answer', '')
            if answer:
                print(f"\n💬 ANSWER ({len(answer)} chars):")
                print("-" * 60)
                # Show first 300 characters
                preview = answer[:400] + "..." if len(answer) > 400 else answer
                print(preview)
                print("-" * 60)
            else:
                print("❌ No answer generated")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return None
    
    def run_test_suite(self):
        """Run comprehensive test suite with various queries"""
        print("\n🧪 RUNNING COMPREHENSIVE RAG TEST SUITE")
        print("="*80)
        
        # Test cases covering different scenarios
        test_cases = [
            {
                "question": "thủ tục đăng ký khai sinh",
                "description": "Test basic birth registration (should favor basic over special)",
                "expected_collection": "ho_tich_cap_xa"
            },
            {
                "question": "đăng ký khai sinh lưu động",
                "description": "Test mobile birth registration (specific procedure)",
                "expected_collection": "ho_tich_cap_xa"
            },
            {
                "question": "chứng thực bản sao giấy tờ",
                "description": "Test document notarization",
                "expected_collection": "chung_thuc"
            },
            {
                "question": "thủ tục nuôi con nuôi",
                "description": "Test adoption procedures",
                "expected_collection": "nuoi_con_nuoi"
            },
            {
                "question": "hồ sơ cần thiết kết hôn",
                "description": "Test marriage documentation requirements",
                "expected_collection": "ho_tich_cap_xa"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 TEST CASE {i}: {test_case['description']}")
            result = self.test_single_query(
                test_case["question"], 
                test_case.get("expected_collection", "")
            )
            results.append({
                "test_case": test_case,
                "result": result,
                "success": result is not None
            })
        
        # Summary
        print(f"\n📊 TEST SUITE SUMMARY")
        print("="*80)
        successful = sum(1 for r in results if r["success"])
        print(f"✅ Successful queries: {successful}/{len(results)}")
        
        for i, result_data in enumerate(results, 1):
            status = "✅ PASS" if result_data["success"] else "❌ FAIL"
            test_case = result_data["test_case"]
            print(f"   Test {i}: {status} - {test_case['description']}")
        
        return results

def main():
    """Main test function"""
    print("🎯 RAG SYSTEM QUERY & ANSWER TEST")
    print("="*80)
    
    # Check if vector database exists
    if not settings.vectordb_path.exists():
        print("❌ Vector database not found. Please run rebuild script first:")
        print("   python scripts/rebuild.py")
        return
    
    # Initialize test suite
    test_suite = RAGTestSuite()
    
    # Option 1: Run single query (good for quick testing)
    print("\n🔧 SINGLE QUERY TEST MODE")
    single_question = "thủ tục đăng ký khai sinh"
    test_suite.test_single_query(single_question)
    
    # Option 2: Run full test suite (comment out if you just want single query)
    print("\n🔧 FULL TEST SUITE MODE")
    test_suite.run_test_suite()

if __name__ == "__main__":
    main()
