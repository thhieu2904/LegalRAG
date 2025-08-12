#!/usr/bin/env python3
"""
Test Context Expansion với chunk_index_num mới
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.rag_service import RAGService
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService

def test_context_expansion():
    """Test context expansion functionality"""
    print("🧪 TESTING CONTEXT EXPANSION")
    print("=" * 50)
    
    # Setup services
    settings.setup_environment()
    
    vectordb_service = VectorDBService()
    llm_service = LLMService()
    
    rag_service = RAGService(
        documents_dir=str(settings.documents_path),
        vectordb_service=vectordb_service,
        llm_service=llm_service
    )
    
    # Test query
    test_query = "thủ tục đăng ký khai sinh"
    
    print(f"Query: '{test_query}'")
    print()
    
    # Run full RAG query to test context expansion
    try:
        result = rag_service.query(
            question=test_query,
            broad_search_k=10,
            similarity_threshold=0.3,
            context_expansion_size=1  # Test context expansion
        )
        
        print("✅ RAG Query successful!")
        print(f"Answer length: {len(result.get('answer', ''))}")
        print()
        
        # Show search details
        search_results = result.get('search_results', [])
        print(f"🔍 Search found {len(search_results)} results")
        
        # Show rerank details
        reranked_results = result.get('reranked_results', [])
        print(f"🎯 Reranker selected {len(reranked_results)} results")
        
        # Show context expansion details
        expanded_context = result.get('expanded_context', [])
        print(f"📖 Context expansion: {len(expanded_context)} chunks")
        
        if expanded_context:
            print("\n📋 Context expansion details:")
            for i, chunk in enumerate(expanded_context):
                metadata = chunk.get('metadata', {})
                chunk_index_num = metadata.get('chunk_index_num', 'N/A')
                document_id = metadata.get('document_id', 'N/A')
                chunk_id = metadata.get('chunk_id', 'N/A')
                
                print(f"  {i+1}. Document: {document_id}")
                print(f"     chunk_index_num: {chunk_index_num}")
                print(f"     chunk_id: {chunk_id}")
                
                content_preview = chunk.get('content', '')[:80].replace('\n', ' ')
                print(f"     Content: {content_preview}...")
                print()
        
        # Show final answer preview
        answer = result.get('answer', '')
        if answer:
            print("💬 Answer preview:")
            print(answer[:200] + "..." if len(answer) > 200 else answer)
        
        print("\n" + "="*50)
        print("🎉 CONTEXT EXPANSION TEST COMPLETED!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_expansion()
