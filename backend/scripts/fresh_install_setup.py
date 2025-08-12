#!/usr/bin/env python3
"""
Complete Fresh Installation Setup Script for LegalRAG Backend
=============================================================

Script này được thiết kế để setup hoàn chỉnh hệ thống trên máy mới lần đầu:
1. Kiểm tra và tạo cấu trúc thư mục
2. Download models cần thiết
3. Process documents và build vector database
4. Test hệ thống hoạt động đúng cách

Usage:
    python scripts/fresh_install_setup.py
    python scripts/fresh_install_setup.py --force-rebuild
"""

import sys
import os
import shutil
import json
import argparse
from pathlib import Path
import logging
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

def setup_directory_structure():
    """Tạo cấu trúc thư mục cần thiết"""
    print("📁 SETTING UP DIRECTORY STRUCTURE")
    print("-" * 40)
    
    required_dirs = [
        'data',
        'data/documents',
        'data/models',
        'data/models/hf_cache',
        'data/models/llm_dir', 
        'data/vectordb',
        'data/cache'
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {dir_path}")
        else:
            print(f"   ✅ Exists: {dir_path}")
    print()

def check_documents():
    """Kiểm tra documents có tồn tại không"""
    print("📄 CHECKING DOCUMENTS")
    print("-" * 40)
    
    docs_path = Path("data/documents")
    if not docs_path.exists():
        print("   ❌ Documents directory not found!")
        return False
    
    # Check các collection directories và subdirectories
    expected_collections = [
        'quy_trinh_cap_ho_tich_cap_xa',
        'quy_trinh_chung_thuc', 
        'quy_trinh_nuoi_con_nuoi'
    ]
    
    found_docs = 0
    for collection in expected_collections:
        collection_path = docs_path / collection
        if collection_path.exists():
            # Scan recursively for JSON files
            json_files = list(collection_path.glob('**/*.json'))
            print(f"   ✅ {collection}: {len(json_files)} JSON files (including subdirectories)")
            found_docs += len(json_files)
        else:
            print(f"   ⚠️  {collection}: Directory not found")
    
    print(f"   📊 Total documents found: {found_docs}")
    print()
    return found_docs > 0

def check_and_setup_models():
    """Kiểm tra và setup AI models"""
    print("🤖 CHECKING AI MODELS")
    print("-" * 40)
    
    try:
        from app.core.config import settings
        settings.setup_environment()
        
        # Check embedding model
        print("   📊 Embedding Model:")
        try:
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer(settings.embedding_model_name)
            print(f"      ✅ {settings.embedding_model_name} loaded successfully")
        except Exception as e:
            print(f"      ❌ Error loading embedding model: {e}")
            return False
        
        # Check reranker model  
        print("   🎯 Reranker Model:")
        try:
            from sentence_transformers import CrossEncoder
            reranker_model = CrossEncoder(settings.reranker_model_name)
            print(f"      ✅ {settings.reranker_model_name} loaded successfully")
        except Exception as e:
            print(f"      ❌ Error loading reranker model: {e}")
            return False
        
        # Check LLM model
        print("   🧠 LLM Model:")
        llm_path = Path(settings.llm_model_path)
        if llm_path.exists():
            print(f"      ✅ LLM model found: {llm_path}")
        else:
            print(f"      ❌ LLM model not found: {llm_path}")
            print("      💡 Run: python scripts/download_models.py")
            return False
        
        print("   ✅ All models available!")
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking models: {e}")
        return False

def build_vector_database(force_rebuild: bool = False):
    """Build vector database từ documents"""
    print("🔄 BUILDING VECTOR DATABASE")
    print("-" * 40)
    
    try:
        from app.core.config import settings
        from app.services.vectordb_service import VectorDBService
        from app.services.json_document_processor import JSONDocumentProcessor
        
        # Initialize VectorDB Service first
        print("   🔧 Initializing VectorDB Service...")
        vectordb_service = VectorDBService(
            persist_directory=str(settings.vectordb_path),
            embedding_model=settings.embedding_model_name,
            default_collection_name=settings.chroma_collection_name
        )
        
        # Clear existing collections if force rebuild
        if force_rebuild:
            print("   🗑️  Clearing existing collections...")
            try:
                collections = vectordb_service.list_collections()
                for collection_info in collections:
                    collection_name = collection_info["name"]
                    print(f"      🗑️  Deleting collection: {collection_name}")
                    try:
                        vectordb_service.delete_collection(collection_name)
                    except Exception as e:
                        print(f"         ⚠️  Could not delete {collection_name}: {e}")
                print("      ✅ Collections cleared")
            except Exception as e:
                print(f"      ⚠️  Error clearing collections: {e}")
                print("      💡 Continuing anyway...")
        
        document_processor = JSONDocumentProcessor()
        
        # Process documents by collection (scan recursively)
        docs_path = Path("data/documents")
        total_processed = 0
        
        for collection_dir in docs_path.iterdir():
            if not collection_dir.is_dir():
                continue
                
            collection_name = document_processor.detect_collection_from_path(str(collection_dir))
            print(f"   📂 Processing collection: {collection_name}")
            
            # Process all JSON files recursively in collection and subdirectories
            json_files = list(collection_dir.glob('**/*.json'))
            print(f"      📄 Found {len(json_files)} JSON files (including subdirectories)")
            
            for json_file in json_files:
                try:
                    # Process document
                    result = document_processor.process_document(str(json_file))
                    processed_chunks = result.get('chunks', [])
                    
                    if processed_chunks:
                        # Add to vector database
                        vectordb_service.add_documents_to_collection(
                            collection_name=collection_name,
                            documents=processed_chunks
                        )
                        total_processed += len(processed_chunks)
                        print(f"         ✅ {json_file.name}: {len(processed_chunks)} chunks")
                    else:
                        print(f"         ⚠️  {json_file.name}: No chunks generated")
                        
                except Exception as e:
                    print(f"         ❌ {json_file.name}: Error - {e}")
        
        print(f"   📊 Total chunks processed: {total_processed}")
        print("   ✅ Vector database build completed!")
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ Error building vector database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system():
    """Test hệ thống hoạt động đúng cách"""
    print("🧪 TESTING SYSTEM")
    print("-" * 40)
    
    try:
        from app.services.vectordb_service import VectorDBService
        from app.core.config import settings
        
        # Initialize vectordb service
        vectordb_service = VectorDBService(
            persist_directory=str(settings.vectordb_path),
            embedding_model=settings.embedding_model_name,
            default_collection_name=settings.chroma_collection_name
        )
        
        # Test search functionality 
        test_cases = [
            ("thủ tục khai sinh", "ho_tich_cap_xa"),
            ("chứng thực", "chung_thuc"), 
            ("nuôi con nuôi", "nuoi_con_nuoi")
        ]
        
        for query, collection_name in test_cases:
            print(f"   🔍 Testing query: '{query}' in collection '{collection_name}'")
            try:
                results = vectordb_service.search_in_collection(
                    collection_name=collection_name,
                    query=query,
                    top_k=3,
                    similarity_threshold=0.3
                )
                
                if results:
                    best_score = results[0].get('similarity', 0)
                    print(f"      ✅ Found {len(results)} results, best score: {best_score:.3f}")
                else:
                    print(f"      ⚠️  No results found (collection may be empty)")
                    
            except Exception as e:
                print(f"      ❌ Search error: {e}")
        
        print("   ✅ System test completed!")
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ System test failed: {e}")
        return False

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Fresh Installation Setup for LegalRAG')
    parser.add_argument('--force-rebuild', action='store_true', 
                       help='Force rebuild of vector database')
    args = parser.parse_args()
    
    print("🚀 FRESH INSTALLATION SETUP FOR LEGALRAG")
    print("=" * 60)
    print("This script will setup the complete system for first-time use")
    print()
    
    # Step 1: Directory structure
    setup_directory_structure()
    
    # Step 2: Check documents
    if not check_documents():
        print("❌ SETUP FAILED: No documents found!")
        print("💡 Please add JSON documents to data/documents/ directories")
        return False
    
    # Step 3: Check models
    if not check_and_setup_models():
        print("❌ SETUP FAILED: Models not available!")
        print("💡 Please run download_models.py first")
        return False
    
    # Step 4: Build vector database
    if not build_vector_database(force_rebuild=args.force_rebuild):
        print("❌ SETUP FAILED: Could not build vector database!")
        return False
    
    # Step 5: Test system
    if not test_system():
        print("❌ SETUP FAILED: System test failed!")
        return False
    
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ Directory structure created")
    print("✅ Documents processed") 
    print("✅ Models loaded")
    print("✅ Vector database built")
    print("✅ System tested")
    print()
    print("🚀 Your LegalRAG system is ready to use!")
    print("   Start the server: python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
