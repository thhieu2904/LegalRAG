#!/usr/bin/env python3
"""
🧠 BUILD CACHE WITH EMBEDDINGS
Rebuild cache với Vietnamese Embedding v2
"""

import os
import json
import pickle
import time
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_cache_with_embeddings():
    """Build cache with proper embeddings"""
    
    logger.info("🧠 BUILDING CACHE WITH EMBEDDINGS")
    logger.info("=" * 50)
    
    # Load embedding model
    try:
        logger.info("🔄 Loading Vietnamese Embedding v2...")
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
        logger.info("✅ Embedding model loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
        logger.info("💡 Using text-only cache instead")
        model = None
    
    # Load questions from new structure
    base_path = "data/storage/collections"
    collections_data = {}
    
    if not os.path.exists(base_path):
        logger.error(f"❌ Base path not found: {base_path}")
        return False
    
    total_docs = 0
    
    for collection_name in os.listdir(base_path):
        collection_path = os.path.join(base_path, collection_name)
        documents_path = os.path.join(collection_path, "documents")
        
        if not os.path.isdir(documents_path):
            continue
        
        logger.info(f"🔄 Processing collection: {collection_name}")
        
        collection_docs = {}
        
        for doc_name in os.listdir(documents_path):
            doc_path = os.path.join(documents_path, doc_name)
            questions_file = os.path.join(doc_path, "questions.json")
            
            if os.path.exists(questions_file):
                try:
                    with open(questions_file, 'r', encoding='utf-8') as f:
                        questions_data = json.load(f)
                    
                    main_question = questions_data.get('main_question', '')
                    variants = questions_data.get('question_variants', [])
                    
                    # Prepare document data
                    doc_data = {
                        'main_question': main_question,
                        'question_variants': variants
                    }
                    
                    # Generate embeddings if model available
                    if model is not None:
                        try:
                            all_questions = [main_question] + variants
                            all_questions = [q for q in all_questions if q.strip()]
                            
                            if all_questions:
                                embeddings = model.encode(all_questions, convert_to_tensor=False)
                                doc_data['embeddings'] = embeddings.tolist()
                                doc_data['embedding_main'] = embeddings[0].tolist()
                                logger.info(f"   ✅ {doc_name}: {len(embeddings)} embeddings")
                            else:
                                logger.warning(f"   ⚠️  {doc_name}: No valid questions")
                        except Exception as e:
                            logger.error(f"   ❌ {doc_name}: Embedding error: {e}")
                    else:
                        logger.info(f"   📝 {doc_name}: Text only")
                    
                    collection_docs[doc_name] = doc_data
                    total_docs += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {questions_file}: {e}")
        
        if collection_docs:
            collections_data[collection_name] = collection_docs
            logger.info(f"✅ {collection_name}: {len(collection_docs)} documents")
    
    # Build cache data
    cache_data = {
        'metadata': {
            'created_at': time.time(),
            'structure_version': '3.0',
            'source': 'questions.json', 
            'cache_type': 'with_embeddings' if model else 'text_only',
            'embedding_model': 'AITeamVN/Vietnamese_Embedding_v2' if model else None,
            'total_collections': len(collections_data),
            'total_documents': total_docs
        },
        'collections': collections_data
    }
    
    # Save cache
    cache_file = "data/cache/router_embeddings.pkl"
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        
        cache_size = os.path.getsize(cache_file)
        logger.info(f"💾 Cache saved: {cache_file}")
        logger.info(f"📊 Cache size: {cache_size:,} bytes ({cache_size/1024:.1f} KB)")
        
        # Summary
        logger.info("\\n🎯 CACHE BUILD SUMMARY:")
        logger.info(f"   Collections: {len(collections_data)}")
        logger.info(f"   Documents: {total_docs}")
        logger.info(f"   Has embeddings: {'✅' if model else '❌'}")
        logger.info(f"   Cache type: {cache_data['metadata']['cache_type']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save cache: {e}")
        return False

if __name__ == "__main__":
    success = build_cache_with_embeddings()
    
    if success:
        logger.info("\\n🎉 CACHE BUILD COMPLETED!")
        logger.info("✅ Cache ready with embeddings")
    else:
        logger.info("\\n❌ CACHE BUILD FAILED")
        logger.info("Check errors above")
