#!/usr/bin/env python3
"""
Debug Context Expansion - Test từng bước
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.vectordb_service import VectorDBService
from app.services.context_expansion_service import ContextExpansionService

def debug_context_expansion():
    """Debug context expansion step by step"""
    print("🔧 DEBUGGING CONTEXT EXPANSION")
    print("=" * 50)
    
    # Setup services
    settings.setup_environment()
    vectordb_service = VectorDBService()
    context_expansion_service = ContextExpansionService(vectordb_service)
    
    # Test query
    test_query = "thủ tục đăng ký khai sinh"
    print(f"Query: '{test_query}'")
    print()
    
    # Step 1: Test search
    print("🔍 Step 1: Testing basic search...")
    search_results = vectordb_service.search_across_collections(
        query=test_query,
        top_k=5,
        similarity_threshold=0.3
    )
    
    print(f"Found {len(search_results)} results")
    
    if search_results:
        # Show first result details
        best_result = search_results[0]
        print(f"Best result similarity: {best_result.get('similarity', 0):.3f}")
        print(f"Collection: {best_result.get('collection', 'unknown')}")
        
        metadata = best_result.get('metadata', {})
        print(f"chunk_index_num: {metadata.get('chunk_index_num', 'N/A')}")
        print(f"document_id: {metadata.get('document_id', 'N/A')}")
        print(f"chunk_id: {metadata.get('chunk_id', 'N/A')}")
        
        content_preview = best_result.get('content', '')[:100].replace('\n', ' ')
        print(f"Content: {content_preview}...")
        print()
        
        # Step 2: Test context expansion
        print("📖 Step 2: Testing context expansion...")
        try:
            expanded_chunks = context_expansion_service.expand_context(
                core_document=best_result,
                expansion_size=1
            )
            
            print(f"Expanded to {len(expanded_chunks)} chunks")
            
            if expanded_chunks:
                print("\n📋 Expanded chunks:")
                for i, chunk in enumerate(expanded_chunks):
                    chunk_metadata = chunk.get('metadata', {})
                    chunk_index_num = chunk_metadata.get('chunk_index_num', 'N/A')
                    document_id = chunk_metadata.get('document_id', 'N/A')
                    
                    print(f"  {i+1}. chunk_index_num: {chunk_index_num}, doc: {document_id}")
                    
                    content_preview = chunk.get('content', '')[:60].replace('\n', ' ')
                    print(f"     Content: {content_preview}...")
                
                print("\n✅ Context expansion working!")
            else:
                print("❌ No chunks in expansion")
                
        except Exception as e:
            print(f"❌ Context expansion error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ No search results found - cannot test context expansion")
    
    print("\n" + "="*50)
    print("🎉 DEBUG COMPLETED!")

if __name__ == "__main__":
    debug_context_expansion()
