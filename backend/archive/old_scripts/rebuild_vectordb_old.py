#!/usr/bin/env python3
"""
Rebuild VectorDB with Content-Aware Chunking
"""

import sys
import shutil
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.services.rag_service import RAGService
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService

def rebuild_vectordb():
    print("🔄 REBUILDING VECTORDB WITH CONTENT-AWARE CHUNKING")
    print("=" * 60)
    
    # Remove old vectordb
    vectordb_path = Path(settings.chroma_persist_directory)
    if vectordb_path.exists():
        print(f"🗑️  Removing old vectordb: {vectordb_path}")
        shutil.rmtree(vectordb_path)
    
    # Initialize services
    vectordb_service = VectorDBService(
        persist_directory=settings.chroma_persist_directory,
        embedding_model=settings.embedding_model
    )
    
    llm_service = LLMService(
        model_path=settings.llm_model_path,
        context_length=settings.context_length
    )
    
    # Initialize RAG service
    rag_service = RAGService(
        documents_dir=str(settings.documents_dir),
        vectordb_service=vectordb_service,
        llm_service=llm_service
    )
    
    # Rebuild with force
    print("🏗️  Building new index with content-aware chunking...")
    result = rag_service.build_index(force_rebuild=True)
    
    if result.get('status') == 'success':
        print("✅ SUCCESS!")
        print(f"📊 Collections processed: {len(result.get('collections', {}))}")
        
        collections = result.get('collections', {})
        for collection_name, chunk_count in collections.items():
            print(f"   - {collection_name}: {chunk_count} chunks")
        
        # Test search immediately
        print(f"\n🎯 TESTING SEARCH WITH NEW CHUNKS:")
        print("-" * 40)
        
        test_queries = ['khai sinh', 'chứng thực', 'nuôi con nuôi']
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            try:
                search_results = rag_service.search_relevant_documents(query, top_k=3)
                
                if search_results:
                    print(f"  ✅ Found {len(search_results)} results")
                    best_result = search_results[0]
                    print(f"     Best score: {best_result.get('similarity', 0):.3f}")
                    print(f"     Collection: {best_result.get('collection', 'unknown')}")
                    preview = best_result.get('content', '')[:100].replace('\n', ' ')
                    print(f"     Preview: {preview}...")
                else:
                    print(f"  ❌ No results found")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    rebuild_vectordb()
