#!/usr/bin/env python3
"""
🔄 REBUILD CACHE FOR NEW QUESTIONS.JSON STRUCTURE

Comprehensive cache rebuild script:
✅ Clean old cache
✅ Load new questions.json structure
✅ Generate embeddings 
✅ Save new cache
✅ Validate cache integrity
"""

import sys
import os
import json
import pickle
import glob
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_old_cache():
    """Clean old cache files"""
    cache_dir = "data/cache"
    if os.path.exists(cache_dir):
        cache_files = glob.glob(f"{cache_dir}/*")
        for cache_file in cache_files:
            if os.path.isfile(cache_file):
                os.remove(cache_file)
                logger.info(f"🗑️  Removed old cache: {cache_file}")
    
    logger.info("✅ Old cache cleaned")

def load_new_structure():
    """Load questions from new structure"""
    questions_data = {}
    
    # Find all questions.json files
    questions_files = glob.glob("data/**/*questions.json", recursive=True)
    
    logger.info(f"📁 Found {len(questions_files)} questions.json files")
    
    for questions_file in questions_files:
        try:
            # Extract collection and document info from path
            path_parts = questions_file.split(os.sep)
            
            # Find collection and document
            collection_idx = -1
            document_idx = -1
            
            for i, part in enumerate(path_parts):
                if part == "collections" and i + 1 < len(path_parts):
                    collection_name = path_parts[i + 1]
                    collection_idx = i + 1
                elif part == "documents" and i + 1 < len(path_parts):
                    document_name = path_parts[i + 1]
                    document_idx = i + 1
                    
            if collection_idx > 0 and document_idx > 0:
                # Load questions
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                # Load corresponding document metadata
                doc_dir = os.path.dirname(questions_file)
                doc_files = [f for f in os.listdir(doc_dir) 
                           if f.endswith('.json') and f != 'questions.json']
                
                metadata = {}
                if doc_files:
                    doc_path = os.path.join(doc_dir, doc_files[0])
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        metadata = doc_data.get('metadata', {})
                
                # Store in structure
                if collection_name not in questions_data:
                    questions_data[collection_name] = {}
                
                questions_data[collection_name][document_name] = {
                    'questions': questions,
                    'metadata': metadata,
                    'file_path': questions_file
                }
                
        except Exception as e:
            logger.error(f"❌ Error loading {questions_file}: {e}")
    
    logger.info(f"✅ Loaded {len(questions_data)} collections")
    return questions_data

def generate_embeddings(questions_data):
    """Generate embeddings cho questions"""
    try:
        # Import embedding model
        from sentence_transformers import SentenceTransformer
        
        logger.info("🔄 Loading embedding model...")
        model = SentenceTransformer('keepitreal/vietnamese-sbert')
        
        embeddings_data = {}
        
        for collection_name, documents in questions_data.items():
            embeddings_data[collection_name] = {}
            
            for doc_name, doc_data in documents.items():
                questions = doc_data['questions']
                
                # Prepare text for embedding
                texts = [questions.get('main_question', '')]
                texts.extend(questions.get('question_variants', []))
                
                # Generate embeddings
                embeddings = model.encode(texts)
                
                embeddings_data[collection_name][doc_name] = {
                    'embeddings': embeddings,
                    'texts': texts,
                    'metadata': doc_data['metadata']
                }
                
                logger.info(f"✅ Generated embeddings for {collection_name}/{doc_name}")
        
        logger.info(f"✅ Generated embeddings for all collections")
        return embeddings_data
        
    except Exception as e:
        logger.error(f"❌ Error generating embeddings: {e}")
        return None

def save_cache(embeddings_data):
    """Save cache to file"""
    try:
        cache_dir = "data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, "router_embeddings.pkl")
        
        with open(cache_file, 'wb') as f:
            pickle.dump(embeddings_data, f)
        
        cache_size = os.path.getsize(cache_file)
        logger.info(f"✅ Cache saved: {cache_file} ({cache_size:,} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving cache: {e}")
        return False

def validate_cache():
    """Validate cache integrity"""
    try:
        cache_file = "data/cache/router_embeddings.pkl"
        
        if not os.path.exists(cache_file):
            logger.error("❌ Cache file not found")
            return False
        
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Basic validation
        if not isinstance(cache_data, dict):
            logger.error("❌ Cache data invalid format")
            return False
        
        total_docs = sum(len(docs) for docs in cache_data.values())
        logger.info(f"✅ Cache validated: {len(cache_data)} collections, {total_docs} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cache validation error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔄 STARTING CACHE REBUILD FOR NEW STRUCTURE")
    
    # Step 1: Clean old cache
    clean_old_cache()
    
    # Step 2: Load new structure
    questions_data = load_new_structure()
    
    if not questions_data:
        logger.error("❌ No questions data loaded")
        exit(1)
    
    # Step 3: Generate embeddings
    embeddings_data = generate_embeddings(questions_data)
    
    if not embeddings_data:
        logger.error("❌ Failed to generate embeddings")
        exit(1)
    
    # Step 4: Save cache
    if not save_cache(embeddings_data):
        logger.error("❌ Failed to save cache")
        exit(1)
    
    # Step 5: Validate cache
    if not validate_cache():
        logger.error("❌ Cache validation failed")
        exit(1)
    
    logger.info("🎉 CACHE REBUILD COMPLETE!")
    logger.info("✅ New questions.json structure cached successfully")
