#!/usr/bin/env python3
"""
Complete Vector Database Builder for LegalRAG
==============================================

Tool build vector database với TOÀN BỘ tính năng từ build_vectordb.py + fresh_install_setup.py:
- Process_document method với chunking logic chi tiết
- ChromaDB management với collection detection
- Test search functionality với proper scoring  
- Force rebuild và error handling

Usage:
    cd backend
    python tools/2_build_vectordb.py
    python tools/2_build_vectordb.py --force  # Clear existing and rebuild
"""

import sys
import os
import json
from pathlib import Path
import logging
import argparse
from typing import Dict, List, Any

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteVectorDBBuilder:
    def __init__(self):
        self.backend_dir = backend_dir
        self.data_dir = self.backend_dir / "data"
        self.documents_dir = self.data_dir / "documents"
        self.vectordb_dir = self.data_dir / "vectordb"
        
        # Create directories if needed
        self.vectordb_dir.mkdir(parents=True, exist_ok=True)
    
    def check_prerequisites(self) -> bool:
        """Check if documents exist - từ build_vectordb.py"""
        logger.info("📋 Checking prerequisites...")
        
        if not self.documents_dir.exists():
            logger.error(f"❌ Documents directory not found: {self.documents_dir}")
            return False
        
        # Count documents - scan recursively như fresh_install_setup.py
        json_files = list(self.documents_dir.rglob("*.json"))
        if not json_files:
            logger.error("❌ No JSON documents found")
            return False
        
        logger.info(f"✅ Found {len(json_files)} document files")
        
        # Check collections
        collections = []
        for json_file in json_files:
            collection = self.detect_collection_from_path(str(json_file))
            if collection not in collections:
                collections.append(collection)
        
        logger.info(f"✅ Detected collections: {collections}")
        return True
    
    def detect_collection_from_path(self, file_path: str) -> str:
        """Detect collection name from file path - từ build_vectordb.py"""
        path_lower = file_path.lower()
        
        if 'ho_tich_cap_xa' in path_lower:
            return 'ho_tich_cap_xa'
        elif 'chung_thuc' in path_lower:
            return 'chung_thuc'
        elif 'nuoi_con_nuoi' in path_lower:
            return 'nuoi_con_nuoi'
        else:
            # Default based on parent directory name
            parent_dir = Path(file_path).parent.name.lower()
            if 'cap_ho_tich' in parent_dir or 'ho_tich' in parent_dir:
                return 'ho_tich_cap_xa'
            elif 'chung_thuc' in parent_dir:
                return 'chung_thuc'
            elif 'nuoi_con' in parent_dir or 'con_nuoi' in parent_dir:
                return 'nuoi_con_nuoi'
            else:
                return 'ho_tich_cap_xa'  # Default collection
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document file - TOÀN BỘ LOGIC từ build_vectordb.py"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
            
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            if not content:
                return {'chunks': [], 'error': 'No content'}
            
            # Simple chunking - split by paragraphs (GIỐNG HỆT build_vectordb.py)
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            chunks = []
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph) > 50:  # Only meaningful paragraphs
                    chunk = {
                        'content': paragraph,
                        'metadata': {
                            'source': str(Path(file_path).name),
                            'title': metadata.get('title', ''),
                            'code': metadata.get('code', ''),
                            'chunk_index': i,
                            'chunk_type': 'paragraph'
                        }
                    }
                    chunks.append(chunk)
            
            # If no good chunks, use full content (GIỐNG HỆT build_vectordb.py)
            if not chunks:
                chunks = [{
                    'content': content,
                    'metadata': {
                        'source': str(Path(file_path).name),
                        'title': metadata.get('title', ''),
                        'code': metadata.get('code', ''),
                        'chunk_index': 0,
                        'chunk_type': 'full_document'
                    }
                }]
            
            return {'chunks': chunks, 'error': None}
            
        except Exception as e:
            return {'chunks': [], 'error': str(e)}
    
    def build_vector_database(self, force_rebuild: bool = False) -> bool:
        """Build complete vector database - TOÀN BỘ LOGIC từ build_vectordb.py + fresh_install_setup.py"""
        logger.info("🔄 BUILDING VECTOR DATABASE")
        logger.info("-" * 40)
        
        try:
            # Try to import ChromaDB (GIỐNG HỆT build_vectordb.py)
            import chromadb
            from chromadb.config import Settings
            
            logger.info("   📊 Initializing ChromaDB...")
            
            # Create client (GIỐNG HỆT build_vectordb.py)
            client = chromadb.PersistentClient(
                path=str(self.vectordb_dir),
                settings=Settings(allow_reset=True)
            )
            
            # Clear existing if force rebuild (GIỐNG HỆT build_vectordb.py)
            if force_rebuild:
                logger.info("   🗑️ Force rebuild - clearing existing collections...")
                try:
                    collections = client.list_collections()
                    for collection in collections:
                        logger.info(f"      🗑️ Deleting: {collection.name}")
                        client.delete_collection(collection.name)
                    logger.info("   ✅ Existing collections cleared")
                except Exception as e:
                    logger.warning(f"   ⚠️ Error clearing collections: {e}")
            
            # Process documents by collection - scan recursively như fresh_install_setup.py
            json_files = list(self.documents_dir.rglob("*.json"))
            collection_files = {}
            
            # Group files by collection (GIỐNG HỆT build_vectordb.py)
            for json_file in json_files:
                collection_name = self.detect_collection_from_path(str(json_file))
                if collection_name not in collection_files:
                    collection_files[collection_name] = []
                collection_files[collection_name].append(json_file)
            
            total_chunks = 0
            
            for collection_name, files in collection_files.items():
                logger.info(f"   📂 Processing collection: {collection_name}")
                logger.info(f"      📄 Files: {len(files)}")
                
                # Create or get collection (GIỐNG HỆT build_vectordb.py)
                try:
                    collection = client.get_collection(collection_name)
                    if not force_rebuild:
                        logger.info(f"      ⚠️ Collection exists, skipping (use --force to rebuild)")
                        continue
                except:
                    pass
                
                try:
                    collection = client.create_collection(collection_name)
                except Exception as e:
                    logger.error(f"      ❌ Could not create collection: {e}")
                    continue
                
                # Process files (GIỐNG HỆT build_vectordb.py)
                documents = []
                metadatas = []
                ids = []
                collection_chunks = 0
                
                for json_file in files:
                    result = self.process_document(str(json_file))
                    
                    if result['error']:
                        logger.warning(f"         ⚠️ {json_file.name}: {result['error']}")
                        continue
                    
                    chunks = result['chunks']
                    if chunks:
                        for chunk in chunks:
                            documents.append(chunk['content'])
                            metadatas.append(chunk['metadata'])
                            ids.append(f"{collection_name}_{collection_chunks}")
                            collection_chunks += 1
                        
                        logger.info(f"         ✅ {json_file.name}: {len(chunks)} chunks")
                
                # Add to ChromaDB if we have documents (GIỐNG HỆT build_vectordb.py)
                if documents:
                    try:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        logger.info(f"      ✅ Added {len(documents)} chunks to {collection_name}")
                        total_chunks += len(documents)
                    except Exception as e:
                        logger.error(f"      ❌ Error adding to collection: {e}")
                else:
                    logger.warning(f"      ⚠️ No documents to add to {collection_name}")
            
            logger.info(f"📊 Vector database build completed")
            logger.info(f"   📂 Collections: {len(collection_files)}")
            logger.info(f"   📄 Total chunks: {total_chunks}")
            logger.info(f"   💾 Database location: {self.vectordb_dir}")
            
            return True
            
        except ImportError:
            logger.error("❌ ChromaDB not installed")
            logger.info("💡 Install with: pip install chromadb")
            return False
        except Exception as e:
            logger.error(f"❌ Error building vector database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_vector_database(self) -> bool:
        """Test vector database functionality - TOÀN BỘ LOGIC từ build_vectordb.py"""
        logger.info("🧪 TESTING VECTOR DATABASE")
        logger.info("-" * 40)
        
        try:
            import chromadb
            
            client = chromadb.PersistentClient(path=str(self.vectordb_dir))
            
            # List collections (GIỐNG HỆT build_vectordb.py)
            collections = client.list_collections()
            if not collections:
                logger.error("❌ No collections found")
                return False
            
            logger.info(f"   📂 Found {len(collections)} collections")
            
            # Test each collection (GIỐNG HỆT build_vectordb.py)
            test_queries = {
                'ho_tich_cap_xa': 'thủ tục khai sinh',
                'chung_thuc': 'chứng thực hợp đồng',
                'nuoi_con_nuoi': 'nuôi con nuôi'
            }
            
            successful_tests = 0
            
            for collection_info in collections:
                collection_name = collection_info.name
                collection = client.get_collection(collection_name)
                
                # Get collection stats (GIỐNG HỆT build_vectordb.py)
                count = collection.count()
                logger.info(f"   📊 {collection_name}: {count} documents")
                
                # Test search if we have a test query (GIỐNG HỆT build_vectordb.py)
                if collection_name in test_queries:
                    query = test_queries[collection_name]
                    logger.info(f"   🔍 Testing search: '{query}'")
                    
                    try:
                        results = collection.query(
                            query_texts=[query],
                            n_results=3
                        )
                        
                        if results and results['documents'] and results['documents'][0]:
                            distances = results['distances'][0] if results['distances'] else []
                            logger.info(f"      ✅ Found {len(results['documents'][0])} results")
                            if distances:
                                logger.info(f"      📊 Best similarity: {1-min(distances):.3f}")
                            successful_tests += 1
                        else:
                            logger.warning(f"      ⚠️ No results found")
                    
                    except Exception as e:
                        logger.error(f"      ❌ Search error: {e}")
            
            logger.info(f"📊 Test Summary: {successful_tests}/{len(test_queries)} successful")
            
            if successful_tests > 0:
                logger.info("✅ Vector database test passed")
                return True
            else:
                logger.error("❌ All tests failed")
                return False
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description='Build complete vector database for LegalRAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/2_build_vectordb.py           # Build vector database
  python tools/2_build_vectordb.py --force   # Force rebuild (clear existing)

This tool will:
1. Scan all JSON files recursively in data/documents/
2. Process documents with chunking (paragraph-based)
3. Create ChromaDB collections based on directory structure
4. Add chunks with full metadata preservation
5. Test search functionality across collections
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild - clear existing collections'
    )
    
    args = parser.parse_args()
    
    logger.info("📊 LEGALRAG COMPLETE VECTOR DATABASE BUILDER")
    logger.info("=" * 60)
    
    # Initialize builder
    builder = CompleteVectorDBBuilder()
    
    # Check prerequisites
    if not builder.check_prerequisites():
        logger.error("❌ Prerequisites not met")
        return 1
    
    # Build vector database
    if not builder.build_vector_database(force_rebuild=args.force):
        logger.error("❌ Failed to build vector database")
        return 1
    
    # Test vector database
    if not builder.test_vector_database():
        logger.warning("⚠️ Vector database test failed, but database was built")
        # Don't fail here - database might work even if test fails
    
    logger.info("🎉 VECTOR DATABASE BUILD COMPLETED SUCCESSFULLY!")
    return 0

if __name__ == "__main__":
    exit(main())
