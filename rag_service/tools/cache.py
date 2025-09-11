#!/usr/bin/env python3
"""
🔄 SAFE CACHE REBUILD FOR NEW QUESTIONS.JSON STRUCTURE

Fixed version để handle PyTorch compatibility issues
"""

import sys
import os
import json
import pickle
import glob
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_old_cache():
    """Clean old cache files"""
    cache_dir = "../data/cache"  # Fixed path from tools directory
    if os.path.exists(cache_dir):
        cache_files = glob.glob(f"{cache_dir}/*")
        for cache_file in cache_files:
            if os.path.isfile(cache_file) and cache_file.endswith('.pkl'):
                try:
                    os.remove(cache_file)
                    logger.info(f"🗑️  Removed old cache: {cache_file}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not remove {cache_file}: {e}")
    
    logger.info("✅ Old cache cleaned")

def load_new_structure():
    """Load questions from new structure"""
    questions_data = {}
    
    # Find all questions.json files - FIXED PATH from tools directory
    questions_files = glob.glob("../data/storage/collections/*/documents/*/questions.json", recursive=True)
    
    logger.info(f"📁 Found {len(questions_files)} questions.json files")
    
    for questions_file in questions_files:
        try:
            # Extract collection and document info from path
            path_parts = os.path.normpath(questions_file).split(os.sep)
            
            # Find collection and document
            collection_name = None
            document_name = None
            
            collection_idx = path_parts.index('collections') if 'collections' in path_parts else -1
            if collection_idx != -1 and collection_idx + 1 < len(path_parts):
                collection_name = path_parts[collection_idx + 1]

            documents_idx = path_parts.index('documents') if 'documents' in path_parts else -1
            if documents_idx != -1 and documents_idx + 1 < len(path_parts):
                document_name = path_parts[documents_idx + 1]
                    
            if collection_name and document_name:
                # Load questions
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                # Load corresponding document content (document.json)
                doc_dir = os.path.dirname(questions_file)
                doc_files = [f for f in os.listdir(doc_dir) 
                           if f.endswith('.json') and f != 'questions.json']
                
                metadata = {}
                content_data = {}
                if doc_files:
                    doc_path = os.path.join(doc_dir, doc_files[0])
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        metadata = doc_data.get('metadata', {})
                        content_data = doc_data  # Store full content data
                
                # 🚀 PHASE 1: CREATE FUSED TEXT EXACTLY LIKE VECTOR DB
                fused_text = _create_fused_text_like_vectordb(questions, metadata, content_data)
                
                # Store in structure with fused text
                if collection_name not in questions_data:
                    questions_data[collection_name] = {}
                
                questions_data[collection_name][document_name] = {
                    'questions': questions,
                    'metadata': metadata,
                    'content_data': content_data,  # Store full content
                    'fused_text': fused_text,     # Store fused text
                    'file_path': questions_file
                }
                
        except Exception as e:
            logger.error(f"❌ Error loading {questions_file}: {e}")
    
    logger.info(f"✅ Loaded {len(questions_data)} collections")
    return questions_data

def _create_fused_text_like_vectordb(questions, metadata, content_data):
    """
    🚀 CREATE FUSED TEXT EXACTLY LIKE VECTOR DB
    Format: questions + metadata + content
    """
    try:
        # Step 1: Extract text content (same as vector DB)
        text_content = ""
        
        # Format 1: Direct content field
        if isinstance(content_data.get("content"), str):
            text_content = content_data["content"]
        elif isinstance(content_data.get("content"), list):
            text_content = " ".join(str(item) for item in content_data["content"])
        
        # Format 2: Content chunks (legal documents format)
        elif content_data.get("content_chunks"):
            chunks = []
            for chunk in content_data["content_chunks"]:
                if isinstance(chunk, dict) and chunk.get("content"):
                    chunks.append(chunk["content"])
            text_content = " ".join(chunks)
        
        # Format 3: Summary or text fields
        elif content_data.get("summary"):
            text_content = content_data["summary"]
        elif content_data.get("text"):
            text_content = content_data["text"]
        
        if not text_content.strip():
            logger.warning(f"⚠️ Empty text content for document")
            text_content = ""
        
        # Step 2: Create WEIGHTED fused text (title priority)
        fused_text = ""
        
        # 🎯 TITLE FIRST (highest priority)
        if metadata and 'title' in metadata:
            fused_text = f"TITLE: {metadata['title']}"
        
        # Add questions second (main_question gets priority)
        if questions.get("main_question"):
            if fused_text:
                fused_text += f" | {questions['main_question']}"
            else:
                fused_text = questions["main_question"]
                
            if questions.get("question_variants"):
                fused_text += " | " + " | ".join(questions["question_variants"][:3])  # Limit variants
        
        # Add ONLY important metadata fields (reduce noise)
        important_fields = ['title', 'code', 'requirements_conditions']
        if metadata:
            metadata_items = []
            
            # Title gets highest priority (first position)
            if 'title' in metadata and str(metadata['title']).strip():
                metadata_items.append(f"TITLE: {metadata['title']}")
            
            # Add other important fields
            for field in ['code', 'requirements_conditions']:
                if field in metadata and str(metadata[field]).strip():
                    metadata_items.append(f"{field}: {metadata[field]}")
            
            if metadata_items:
                metadata_str = " | ".join(metadata_items)
                if fused_text:
                    fused_text += " | " + metadata_str
                else:
                    fused_text = metadata_str
        
        # Add content last
        if fused_text and text_content:
            fused_text += " | CONTENT: " + text_content
        elif text_content:
            fused_text = text_content
        
        # Limit fused text length (same as vector DB)
        original_length = len(fused_text)
        if len(fused_text) > 2000:
            fused_text = fused_text[:2000]
            logger.info(f"✅ Created fused text: {original_length} chars (truncated to {len(fused_text)})")
        else:
            logger.info(f"✅ Created fused text: {len(fused_text)} chars")
        return fused_text
        
    except Exception as e:
        logger.error(f"❌ Error creating fused text: {e}")
        return ""

def generate_embeddings_safe(questions_data):
    """Generate embeddings cho questions with safe model loading - sử dụng cùng logic như app/services/vector.py"""
    try:
        logger.info("🔄 Attempting to load embedding model safely...")
        
        # Import settings và vector service
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        
        from app.core.config import settings
        from sentence_transformers import SentenceTransformer
        
        model = None
        
        # 🎮 GPU OPTIMIZATION - Use GPU for faster embedding generation
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:
            device = 'cpu'
        
        logger.info(f"🎮 Using {device.upper()} for embedding generation")
        
        # Strategy 1: Load từ explicit local cache path (same as VectorDBService)
        try:
            cache_path = settings.hf_cache_path / "hub"
            embedding_model_name = settings.embedding_model_name
            model_folders = list(cache_path.glob(f"models--{embedding_model_name.replace('/', '--')}"))
            
            if model_folders:
                model_folder = model_folders[0]
                snapshots = list((model_folder / "snapshots").iterdir())
                
                if snapshots:
                    snapshot_path = str(snapshots[0])
                    logger.info(f"Loading embedding model from local cache: {embedding_model_name}")
                    logger.info(f"Loading from explicit path: {snapshot_path}")
                    model = SentenceTransformer(snapshot_path, device=device)
                    logger.info(f"✅ Loaded local Vietnamese_Embedding_v2 from snapshot on {device.upper()}")
                else:
                    raise FileNotFoundError(f"No snapshots found in {model_folder}")
            else:
                raise FileNotFoundError(f"No cached model found for {embedding_model_name}")
                
        except Exception as e1:
            logger.warning(f"⚠️  Local cache load failed: {e1}")
            
            # Strategy 2: Try loading with local_files_only (same as VectorDBService)
            try:
                model = SentenceTransformer(settings.embedding_model_name, local_files_only=True, device=device)
                logger.info(f"✅ Fallback: loaded with local_files_only on {device.upper()}")
            except Exception as e2:
                logger.warning(f"⚠️  Local files only failed: {e2}")
                
                # Strategy 3: Final fallback to CPU
                try:
                    model = SentenceTransformer(settings.embedding_model_name, device='cpu')
                    logger.info("✅ Final fallback: loaded on CPU")
                except Exception as e3:
                    logger.error(f"❌ All loading strategies failed: {e3}")
                    return None
                # Strategy 3: Create simple text-based cache without embeddings
                logger.info("🔄 Creating text-based cache without embeddings...")
                return create_text_based_cache(questions_data)
        
        if not model:
            logger.error("❌ No embedding model available")
            return None
        
        embeddings_data = {}
        
        for collection_name, documents in questions_data.items():
            embeddings_data[collection_name] = {}
            
            for doc_name, doc_data in documents.items():
                questions = doc_data['questions']
                
                # 🚀 PHASE 1: Use pre-created fused text (same as vector DB)
                fused_text = doc_data.get('fused_text', '')
                
                if not fused_text:
                    logger.warning(f"⚠️ No fused text for {collection_name}/{doc_name}")
                    continue
                
                # Prepare texts for individual embeddings (for backward compatibility)
                texts = [questions.get('main_question', '')]
                texts.extend(questions.get('question_variants', []))
                texts = [t for t in texts if t and t.strip()]
                
                if texts:
                    # Generate embeddings
                    embeddings = model.encode(texts) if texts else None
                    fused_embedding = model.encode([fused_text])[0] if fused_text else None
                    
                    # Lưu vào cache_data với fused text
                    embeddings_data[collection_name][doc_name] = {
                        'embeddings': embeddings,
                        'texts': texts,
                        'metadata': doc_data['metadata'],
                        'fused_embedding': fused_embedding,
                        'fused_text': fused_text,  # Store fused text for exact matching
                        'content_data': doc_data.get('content_data', {}),  # Store full content
                        'cache_type': 'fused_text_embeddings'
                    }
                    
                    logger.info(f"✅ Generated embeddings for {collection_name}/{doc_name} (fused: {len(fused_text)} chars)")
                else:
                    logger.warning(f"⚠️ No valid texts for {collection_name}/{doc_name}")
        
        logger.info(f"✅ Generated embeddings for all collections")
        return embeddings_data
        
    except Exception as e:
        logger.error(f"❌ Error generating embeddings: {e}")
        return create_text_based_cache(questions_data)

def create_text_based_cache(questions_data):
    """Create text-based cache without embeddings as fallback"""
    logger.info("🔄 Creating text-based cache (no embeddings)...")
    
    cache_data = {}
    
    for collection_name, documents in questions_data.items():
        cache_data[collection_name] = {}
        
        for doc_name, doc_data in documents.items():
            questions = doc_data['questions']
            
            # 🚀 PHASE 1: Use pre-created fused text (same as vector DB)
            fused_text = doc_data.get('fused_text', '')
            
            # Store text data
            texts = [questions.get('main_question', '')]
            texts.extend(questions.get('question_variants', []))
            texts = [t for t in texts if t and t.strip()]
            
            cache_data[collection_name][doc_name] = {
                'texts': texts,
                'metadata': doc_data['metadata'],
                'fused_text': fused_text,  # Store fused text for exact matching
                'content_data': doc_data.get('content_data', {}),  # Store full content
                'embeddings': None,  # Will be generated on-demand
                'cache_type': 'fused_text_text_only'
            }
            
            logger.info(f"✅ Cached text for {collection_name}/{doc_name} (fused: {len(fused_text)} chars)")
    
    logger.info("✅ Text-based cache created")
    return cache_data

def save_cache(cache_data):
    """Save cache to file"""
    try:
        cache_dir = "../data/cache"  # Fixed path from tools directory
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, "router_embeddings.pkl")
        
        # Add metadata
        cache_with_metadata = {
            'data': cache_data,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'structure_version': '4.0',  # Updated version
                'source': 'questions.json + document.json + fused_text',
                'cache_type': 'embeddings' if any(
                    doc.get('embeddings') is not None 
                    for collection in cache_data.values() 
                    for doc in collection.values()
                ) else 'text_only',
                'fused_text_enabled': True,  # New feature
                'content_synchronization': 'vector_db_compatible'  # New feature
            }
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_with_metadata, f)
        
        cache_size = os.path.getsize(cache_file)
        logger.info(f"✅ Cache saved: {cache_file} ({cache_size:,} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving cache: {e}")
        return False

def validate_cache():
    """Validate cache integrity"""
    try:
        cache_file = "../data/cache/router_embeddings.pkl"  # Fixed path from tools directory
        
        if not os.path.exists(cache_file):
            logger.error("❌ Cache file not found")
            return False
        
        with open(cache_file, 'rb') as f:
            cache_container = pickle.load(f)
        
        # Handle both old and new cache formats
        if isinstance(cache_container, dict) and 'data' in cache_container:
            cache_data = cache_container['data']
            metadata = cache_container.get('metadata', {})
            logger.info(f"📋 Cache metadata: {metadata}")
        else:
            cache_data = cache_container
            logger.info("📋 Legacy cache format detected")
        
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
    logger.info("🔄 STARTING SAFE CACHE REBUILD FOR NEW STRUCTURE")
    
    # Step 1: Clean old cache
    clean_old_cache()
    
    # Step 2: Load new structure
    questions_data = load_new_structure()
    
    if not questions_data:
        logger.error("❌ No questions data loaded")
        exit(1)
    
    # Step 3: Generate embeddings (with fallback)
    cache_data = generate_embeddings_safe(questions_data)
    
    if not cache_data:
        logger.error("❌ Failed to create cache")
        exit(1)
    
    # Step 4: Save cache
    if not save_cache(cache_data):
        logger.error("❌ Failed to save cache")
        exit(1)
    
    # Step 5: Validate cache
    if not validate_cache():
        logger.error("❌ Cache validation failed")
        exit(1)
    
    logger.info("🎉 SAFE CACHE REBUILD COMPLETE!")
    logger.info("✅ New questions.json structure cached successfully")
    logger.info("💡 Cache will work with new router service")
