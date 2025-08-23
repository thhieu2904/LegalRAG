#!/usr/bin/env python3
"""
🔧 QUICK CACHE REBUILD - SIMPLE VERSION

Simple cache rebuild để test new structure
"""

import os
import json
import pickle
import glob
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_cache_rebuild():
    """Simple cache rebuild without embeddings"""
    
    logger.info("🔄 SIMPLE CACHE REBUILD")
    
    # Clean old cache
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = os.path.join(cache_dir, "router_embeddings.pkl")
    if os.path.exists(cache_file):
        os.remove(cache_file)
        logger.info("🗑️  Old cache removed")
    
    # Find questions.json files
    questions_files = glob.glob("data/**/*questions.json", recursive=True)
    logger.info(f"📁 Found {len(questions_files)} questions.json files")
    
    # Group by collection
    collections_data = {}
    
    for questions_file in questions_files:
        try:
            # Debug path parsing
            normalized_path = questions_file.replace('\\\\', '/').replace('\\', '/')
            logger.info(f"Processing: {normalized_path}")
            
            # Simple parsing
            if '/storage/collections/' in normalized_path:
                parts = normalized_path.split('/storage/collections/')[1].split('/')
                if len(parts) >= 3:  # collection/documents/doc_id/questions.json
                    collection_name = parts[0]
                    doc_id = parts[2]
                    
                    logger.info(f"   Collection: {collection_name}, Doc: {doc_id}")
                    
                    # Load questions
                    with open(questions_file, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                    
                    # Store
                    if collection_name not in collections_data:
                        collections_data[collection_name] = {}
                    
                    collections_data[collection_name][doc_id] = {
                        'main_question': questions.get('main_question', ''),
                        'question_variants': questions.get('question_variants', []),
                        'file_path': questions_file
                    }
                    
        except Exception as e:
            logger.error(f"Error processing {questions_file}: {e}")
    
    logger.info(f"✅ Grouped into {len(collections_data)} collections")
    for collection, docs in collections_data.items():
        logger.info(f"   {collection}: {len(docs)} documents")
    
    # Create simple cache
    cache_data = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'structure_version': '3.0',
            'source': 'questions.json',
            'cache_type': 'text_only',
            'total_collections': len(collections_data),
            'total_documents': sum(len(docs) for docs in collections_data.values())
        },
        'collections': collections_data
    }
    
    # Save cache
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    cache_size = os.path.getsize(cache_file)
    logger.info(f"✅ Cache saved: {cache_file} ({cache_size:,} bytes)")
    
    # Test cache
    with open(cache_file, 'rb') as f:
        test_cache = pickle.load(f)
    
    logger.info(f"✅ Cache test: {test_cache['metadata']['total_collections']} collections")
    
    return True

if __name__ == "__main__":
    success = simple_cache_rebuild()
    if success:
        logger.info("🎉 SIMPLE CACHE REBUILD COMPLETE!")
    else:
        logger.error("❌ Cache rebuild failed")
