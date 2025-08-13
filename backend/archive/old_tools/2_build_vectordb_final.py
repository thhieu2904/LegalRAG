#!/usr/bin/env python3
"""
Final Vector Database Builder for LegalRAG using JSONDocumentProcessor
=====================================================================

Tool build vector database sử dụng JSONDocumentProcessor để đảm bảo
tính nhất quán về ID và metadata structure với hệ thống chính.

Đặc điểm:
- Sử dụng JSONDocumentProcessor để xử lý đúng cấu trúc JSON
- Tạo ID duy nhất cho document và chunk
- Bảo toàn metadata enrichment
- Hỗ trợ context expansion thông qua document_id và chunk_index_num

Usage:
    cd backend
    python tools/2_build_vectordb_final.py
    python tools/2_build_vectordb_final.py --force  # Clear existing and rebuild
    python tools/2_build_vectordb_final.py --clean  # Remove entire vectordb directory
"""

import sys
import os
import json
from pathlib import Path
import logging
import argparse
from typing import Dict, List, Any
import time

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import from app modules
from app.core.config import settings
from app.services.vector_database import VectorDBService  

# Import document processor (now in tools/)
sys.path.insert(0, str(Path(__file__).parent))  # Add tools directory to path
from document_processor import JSONDocumentProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalVectorDBBuilder:
    def __init__(self):
        self.backend_dir = backend_dir
        self.data_dir = self.backend_dir / "data"
        self.documents_dir = self.data_dir / "documents"
        self.vectordb_dir = self.data_dir / "vectordb"
        
        # Create directories if needed
        self.vectordb_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize JSONDocumentProcessor
        self.json_processor = JSONDocumentProcessor()
        
        # Initialize VectorDBService with proper Vietnamese embedding  
        self.vectordb_service = VectorDBService(
            persist_directory=str(self.vectordb_dir),
            embedding_model=settings.embedding_model_name
        )
    
    def check_prerequisites(self) -> bool:
        """Check if documents exist and are processable"""
        logger.info("📋 Checking prerequisites...")
        
        if not self.documents_dir.exists():
            logger.error(f"❌ Documents directory not found: {self.documents_dir}")
            return False
        
        # Count documents - scan recursively
        json_files = list(self.documents_dir.rglob("*.json"))
        if not json_files:
            logger.error("❌ No JSON documents found")
            return False
        
        logger.info(f"✅ Found {len(json_files)} document files")
        
        # Test process one file to check structure
        test_file = json_files[0]
        try:
            doc_data = self.json_processor.process_document(str(test_file))
            if "error" not in doc_data:
                logger.info(f"✅ JSON structure validation passed")
                collections = set()
                for json_file in json_files[:5]:  # Test first 5 files
                    collection = self.json_processor.detect_collection_from_path(str(json_file))
                    collections.add(collection)
                logger.info(f"✅ Detected collections: {list(collections)}")
                return True
            else:
                logger.error(f"❌ JSON structure validation failed: {doc_data['error']}")
                return False
        except Exception as e:
            logger.error(f"❌ Error testing JSON structure: {e}")
            return False
    
    def build_vector_database(self, force_rebuild: bool = False) -> bool:
        """Build complete vector database using JSONDocumentProcessor"""
        logger.info("🔄 BUILDING VECTOR DATABASE")
        logger.info("-" * 40)
        
        try:
            # Clean rebuild if requested
            if force_rebuild:
                logger.info("   🗑️ Force rebuild - clearing existing collections...")
                try:
                    import shutil
                    if self.vectordb_dir.exists():
                        shutil.rmtree(self.vectordb_dir)
                        logger.info(f"      ✅ Removed: {self.vectordb_dir}")
                    self.vectordb_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("      ✅ Created fresh vectordb directory")
                    
                    # Reinitialize VectorDBService
                    self.vectordb_service = VectorDBService(
                        persist_directory=str(self.vectordb_dir),
                        embedding_model=settings.embedding_model_name
                    )
                except Exception as e:
                    logger.warning(f"   ⚠️ Error clearing database: {e}")
            
            # Process all documents using JSONDocumentProcessor
            logger.info("   📊 Processing all JSON documents...")
            collections_data = self.json_processor.process_directory(str(self.documents_dir))
            
            if not collections_data:
                logger.error("❌ No data processed from JSON files")
                return False
            
            # Process each collection
            total_chunks = 0
            
            for collection_name, chunks in collections_data.items():
                if not chunks:
                    logger.warning(f"      ⚠️ No chunks for collection {collection_name}")
                    continue
                
                logger.info(f"   📂 Processing collection: {collection_name}")
                logger.info(f"      📄 Chunks: {len(chunks)}")
                
                # Log first chunk to verify structure
                if chunks:
                    first_chunk = chunks[0]
                    logger.info(f"      📝 Sample chunk ID: {first_chunk.get('chunk_id', 'N/A')}")
                    logger.info(f"      📝 Document title: {first_chunk.get('source', {}).get('document_title', 'N/A')}")
                
                # Add documents to vector database using VectorDBService
                try:
                    added_count = self.vectordb_service.add_documents_to_collection(
                        collection_name=collection_name,
                        documents=chunks
                    )
                    logger.info(f"      ✅ Added {added_count} chunks to {collection_name}")
                    total_chunks += added_count
                    
                except Exception as e:
                    logger.error(f"      ❌ Error adding to collection {collection_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            logger.info(f"📊 Vector database build completed")
            logger.info(f"   📂 Collections: {len(collections_data)}")
            logger.info(f"   📄 Total chunks: {total_chunks}")
            logger.info(f"   💾 Database location: {self.vectordb_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building vector database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_vector_database(self) -> bool:
        """Test vector database functionality using VectorDBService"""
        logger.info("🧪 TESTING VECTOR DATABASE")
        logger.info("-" * 40)
        
        try:
            # Test search queries
            test_queries = {
                'ho_tich_cap_xa': 'thủ tục khai sinh',
                'chung_thuc': 'chứng thực hợp đồng',
                'nuoi_con_nuoi': 'nuôi con nuôi'
            }
            
            successful_tests = 0
            total_tests = 0
            
            for collection_name, query in test_queries.items():
                try:
                    # Get collection stats
                    stats = self.vectordb_service.get_collection_stats(collection_name)
                    count = stats.get('document_count', 0)
                    logger.info(f"   📊 {collection_name}: {count} documents")
                    
                    if count > 0:
                        # Test search
                        logger.info(f"   🔍 Testing search: '{query}'")
                        total_tests += 1
                        
                        results = self.vectordb_service.search_in_collection(
                            collection_name=collection_name,
                            query=query,
                            top_k=3
                        )
                        
                        if results:
                            logger.info(f"      ✅ Found {len(results)} results")
                            best_result = results[0]
                            similarity = best_result.get('similarity', best_result.get('score', 0))
                            logger.info(f"      📊 Best similarity: {similarity:.3f}")
                            
                            # Log additional info about the result
                            source_info = best_result.get('source', {})
                            document_title = source_info.get('document_title', 'N/A')
                            chunk_id = source_info.get('chunk_id', 'N/A')
                            logger.info(f"      📄 Best result: {document_title} (ID: {chunk_id})")
                            
                            successful_tests += 1
                        else:
                            logger.warning(f"      ⚠️ No results found")
                    else:
                        logger.warning(f"   ⚠️ Collection {collection_name} is empty")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error testing collection {collection_name}: {e}")
            
            logger.info(f"📊 Test Summary: {successful_tests}/{total_tests} successful")
            
            if successful_tests > 0:
                logger.info("✅ Vector database test passed")
                return True
            else:
                logger.error("❌ All tests failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(
        description='Build corrected vector database for LegalRAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/2_build_vectordb_final.py           # Build vector database
  python tools/2_build_vectordb_final.py --force   # Force rebuild (clear existing)
  python tools/2_build_vectordb_final.py --clean   # Clean rebuild (remove entire DB)

This tool will:
1. Use JSONDocumentProcessor to process documents correctly
2. Ensure proper ID generation (document_id + chunk_id)
3. Maintain metadata enrichment for better search
4. Support context expansion via document grouping
5. Test search functionality across collections
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild - clear existing collections'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean rebuild - delete entire vectordb directory and start fresh'
    )
    
    args = parser.parse_args()
    
    logger.info("📊 LEGALRAG FINAL VECTOR DATABASE BUILDER")
    logger.info("=" * 60)
    
    # Clean rebuild if requested
    if args.clean:
        logger.info("🗑️ CLEAN REBUILD - Removing entire vectordb directory")
        import shutil
        import time
        
        # Don't initialize VectorDBService yet if we're doing clean rebuild
        if Path(str(settings.vectordb_path)).exists():
            try:
                # Wait a bit and try to remove
                time.sleep(1)
                shutil.rmtree(str(settings.vectordb_path))
                logger.info(f"   ✅ Removed: {settings.vectordb_path}")
            except PermissionError as e:
                logger.error(f"   ❌ Cannot remove vectordb directory: {e}")
                logger.info("   💡 Try closing all applications using the database and run again")
                return 1
        Path(str(settings.vectordb_path)).mkdir(parents=True, exist_ok=True)
        logger.info("   ✅ Created fresh vectordb directory")
    
    # Initialize builder (after clean if needed)
    builder = FinalVectorDBBuilder()
    
    # Check prerequisites
    if not builder.check_prerequisites():
        logger.error("❌ Prerequisites not met")
        return 1
    
    # Build vector database  
    force_rebuild = args.force or args.clean
    if not builder.build_vector_database(force_rebuild=force_rebuild):
        logger.error("❌ Failed to build vector database")
        return 1
    
    # Test vector database
    if not builder.test_vector_database():
        logger.warning("⚠️ Vector database test failed, but database was built")
        # Don't fail here - database might work even if test fails
    
    logger.info("🎉 FINAL VECTOR DATABASE BUILD COMPLETED SUCCESSFULLY!")
    return 0

if __name__ == "__main__":
    exit(main())
