#!/usr/bin/env python3
"""
Rebuild VectorDB Script - Updated for Current Architecture
Tái xây dựng VectorDB với cấu trúc hiện tại
"""

import sys
import shutil
import argparse
from pathlib import Path
import logging

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.optimized_enhanced_rag_service import OptimizedEnhancedRAGService
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def rebuild_vectordb(force_rebuild: bool = False):
    """
    Rebuild VectorDB với cấu trúc mới
    
    Args:
        force_rebuild: Có force rebuild hay không
    """
    print("🔄 REBUILDING VECTORDB WITH NEW ARCHITECTURE")
    print("=" * 60)
    print(f"Force rebuild: {'Yes' if force_rebuild else 'No'}")
    print()
    
    try:
        # Setup environment
        settings.setup_environment()
        
        # Paths
        vectordb_path = settings.vectordb_path
        documents_path = settings.documents_path
        
        print(f"📁 VectorDB Path: {vectordb_path}")
        print(f"📁 Documents Path: {documents_path}")
        print(f"🔧 Embedding Model: {settings.embedding_model_name}")
        print()
        
        # Remove old vectordb if force rebuild
        if force_rebuild and vectordb_path.exists():
            print(f"🗑️  Removing old vectordb: {vectordb_path}")
            shutil.rmtree(vectordb_path)
            print("   ✅ Old vectordb removed")
        
        # Check documents exist
        if not documents_path.exists():
            print(f"❌ Documents directory not found: {documents_path}")
            return False
            
        # Initialize services
        print("🚀 Initializing services...")
        
        # VectorDB Service
        vectordb_service = VectorDBService(
            persist_directory=str(vectordb_path),
            embedding_model=settings.embedding_model_name,
            default_collection_name=settings.chroma_collection_name
        )
        print("   ✅ VectorDB service initialized")
        
        # LLM Service 
        llm_service = LLMService()
        print("   ✅ LLM service initialized")
        
        # RAG Service
        rag_service = RAGService(
            documents_dir=str(documents_path),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        print("   ✅ RAG service initialized")
        print()
        
        # Build index
        print("🏗️  Building index with content-aware chunking...")
        result = rag_service.build_index(
            force_rebuild=force_rebuild,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap
        )
        
        if result.get('status') == 'success':
            print("✅ REBUILD SUCCESSFUL!")
            print(f"⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"📊 Collections processed: {result.get('collections_processed', 0)}")
            print()
            
            # Show collection details
            collections = result.get('processed_collections', {})
            if collections:
                print("📈 Collection Details:")
                for collection_name, stats in collections.items():
                    status = stats.get('status', 'unknown')
                    documents = stats.get('documents', 0)
                    chunks = stats.get('chunks', 0)
                    
                    print(f"   - {collection_name}: {status}")
                    print(f"     Documents: {documents}, Chunks: {chunks}")
                print()
            
            # Test search functionality
            print("🎯 TESTING SEARCH FUNCTIONALITY:")
            print("-" * 40)
            
            test_queries = [
                'thủ tục khai sinh',
                'chứng thực giấy tờ', 
                'quy trình nuôi con nuôi',
                'hồ sơ cần thiết'
            ]
            
            for query in test_queries:
                print(f"\nQuery: '{query}'")
                try:
                    # Test basic search using vectordb service
                    search_results = vectordb_service.search_across_collections(
                        query, 
                        top_k=3,
                        similarity_threshold=0.3
                    )
                    
                    if search_results:
                        print(f"  ✅ Found {len(search_results)} results")
                        best_result = search_results[0]
                        similarity = best_result.get('similarity', 0)
                        collection = best_result.get('collection', 'unknown')
                        print(f"     Best score: {similarity:.3f}")
                        print(f"     Collection: {collection}")
                        
                        # Test metadata includes chunk_index_num
                        metadata = best_result.get('metadata', {})
                        if 'chunk_index_num' in metadata:
                            print(f"     ✅ chunk_index_num found: {metadata['chunk_index_num']}")
                        else:
                            print("     ⚠️  chunk_index_num missing in metadata")
                        
                        # Show preview
                        content = best_result.get('content', '')
                        preview = content[:100].replace('\n', ' ')
                        print(f"     Preview: {preview}...")
                    else:
                        print("  ❌ No results found")
                except Exception as e:
                    print(f"  ❌ Search error: {e}")
                    logger.error(f"Search error for '{query}': {e}", exc_info=True)
            
            print("\n" + "="*60)
            print("🎉 VECTORDB REBUILD COMPLETED SUCCESSFULLY!")
            return True
            
        else:
            print("❌ REBUILD FAILED!")
            error = result.get('error', 'Unknown error')
            print(f"Error: {error}")
            logger.error(f"Rebuild failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        logger.error(f"Critical error during rebuild: {e}", exc_info=True)
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Rebuild LegalRAG VectorDB')
    parser.add_argument(
        '--force-rebuild', 
        action='store_true',
        help='Force rebuild by removing existing vectordb first'
    )
    
    args = parser.parse_args()
    
    success = rebuild_vectordb(force_rebuild=args.force_rebuild)
    
    if success:
        print("\n✨ Ready to answer legal questions!")
        sys.exit(0)
    else:
        print("\n💥 Rebuild failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
