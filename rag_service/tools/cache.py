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

def load_structure_absolute_path():
    """
    Load questions from new structure using absolute paths.
    Created for rebuild_selective.py to work in Docker environment.
    Original load_new_structure() uses relative paths for backward compatibility.
    """
    questions_data = {}
    
    # Get absolute path - works in Docker and local
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # Parent of tools/ is rag_service/
    collections_path = os.path.join(base_dir, "data", "storage", "collections")
    
    # Construct glob pattern from absolute path
    pattern = os.path.join(collections_path, "*/documents/*/questions.json")
    questions_files = glob.glob(pattern)
    
    logger.info(f"📁 Found {len(questions_files)} questions.json files from {collections_path}")
    
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
                fused_text = content_data.get('fused_text', '')
                
                # Initialize collection if not exists
                if collection_name not in questions_data:
                    questions_data[collection_name] = {
                        'collection_id': collection_name,
                        'documents': []
                    }
                
                # Add document
                questions_data[collection_name]['documents'].append({
                    'doc_id': document_name,
                    'metadata': metadata,
                    'questions': questions,
                    'fused_text': fused_text  # Add fused_text for embedding
                })
                
        except Exception as e:
            logger.error(f"❌ Error loading {questions_file}: {e}")
            continue
    
    # Convert to list format
    result = list(questions_data.values())
    logger.info(f"✅ Loaded {len(result)} collections")
    
    return result

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

def build_clarify_cache():
    """
    🔄 BUILD CLARIFY CACHE
    Cache riêng cho clarify flow với format tối ưu
    Format: {collection: {document_id: {embeddings, title, metadata, confidence_data}}}
    """
    try:
        logger.info("🔄 Building Clarify Cache...")
        
        # Load collections từ metadata.json (thay vì questions.json)
        clarify_data = load_clarify_structure()
        
        if not clarify_data:
            logger.error("❌ No clarify data loaded")
            return None
        
        # Generate embeddings cho clarify
        clarify_cache = generate_clarify_embeddings(clarify_data)
        
        if not clarify_cache:
            logger.error("❌ Failed to create clarify cache")
            return None
        
        # Save clarify cache
        if not save_clarify_cache(clarify_cache):
            logger.error("❌ Failed to save clarify cache")
            return None
        
        logger.info("✅ Clarify cache built successfully")
        return clarify_cache
        
    except Exception as e:
        logger.error(f"❌ Error building clarify cache: {e}")
        return None

def load_clarify_structure():
    """Load documents từ metadata.json của mỗi collection"""
    clarify_data = {}
    
    # Find all metadata.json files
    metadata_files = glob.glob("../data/storage/collections/*/metadata.json", recursive=True)
    
    logger.info(f"📁 Found {len(metadata_files)} metadata.json files")
    
    for metadata_file in metadata_files:
        try:
            # Extract collection name
            path_parts = os.path.normpath(metadata_file).split(os.sep)
            collection_idx = path_parts.index('collections') if 'collections' in path_parts else -1
            
            if collection_idx != -1 and collection_idx + 1 < len(path_parts):
                collection_name = path_parts[collection_idx + 1]
                
                # Load metadata.json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Extract documents từ metadata
                documents = metadata.get('documents', [])
                
                if documents:
                    clarify_data[collection_name] = {}
                    
                    for doc in documents:
                        doc_id = doc.get('id', '')
                        doc_title = doc.get('title', '')
                        doc_source = doc.get('source', '')
                        has_form = doc.get('has_form', False)
                        
                        if doc_id and doc_title:
                            # Load questions.json cho document này (để lấy fused text)
                            questions_file = f"../data/storage/collections/{collection_name}/documents/{doc_id}/questions.json"
                            questions_data = {}
                            
                            if os.path.exists(questions_file):
                                try:
                                    with open(questions_file, 'r', encoding='utf-8') as f:
                                        questions_data = json.load(f)
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not load questions for {doc_id}: {e}")
                            
                            # Create fused text for clarify (tối ưu cho document selection)
                            fused_text = _create_clarify_fused_text(doc, questions_data)
                            
                            clarify_data[collection_name][doc_id] = {
                                'title': doc_title,
                                'source': doc_source,
                                'has_form': has_form,
                                'metadata': doc,
                                'questions_data': questions_data,
                                'fused_text': fused_text,
                                'collection': collection_name
                            }
                            
                        logger.info(f"✅ Loaded clarify data for {collection_name}/{doc_id}")
                
        except Exception as e:
            logger.error(f"❌ Error loading {metadata_file}: {e}")
    
    logger.info(f"✅ Loaded clarify data for {len(clarify_data)} collections")
    return clarify_data

def _create_clarify_fused_text(doc_metadata, questions_data):
    """
    Create fused text tối ưu cho clarify flow
    Ưu tiên title và description để dễ matching
    """
    try:
        fused_parts = []
        
        # 1. Title (priority cao nhất)
        title = doc_metadata.get('title', '')
        if title:
            fused_parts.append(f"TITLE: {title}")
        
        # 2. Code (nếu có)
        code = doc_metadata.get('code', '')
        if code:
            fused_parts.append(f"CODE: {code}")
        
        # 3. Main question (từ questions.json)
        main_question = questions_data.get('main_question', '')
        if main_question:
            fused_parts.append(f"QUESTION: {main_question}")
        
        # 4. Question variants (top 2)
        variants = questions_data.get('question_variants', [])
        if variants:
            top_variants = variants[:2]  # Chỉ lấy 2 variants đầu
            fused_parts.append(f"VARIANTS: {' | '.join(top_variants)}")
        
        # 5. Requirements (nếu có)
        requirements = doc_metadata.get('requirements_conditions', '')
        if requirements:
            fused_parts.append(f"REQUIREMENTS: {requirements}")
        
        fused_text = " | ".join(fused_parts)
        
        # Limit length for efficiency
        if len(fused_text) > 1500:
            fused_text = fused_text[:1500]
            logger.info(f"✅ Created clarify fused text: {len(fused_text)} chars (truncated)")
        else:
            logger.info(f"✅ Created clarify fused text: {len(fused_text)} chars")
        
        return fused_text
        
    except Exception as e:
        logger.error(f"❌ Error creating clarify fused text: {e}")
        return ""

def generate_clarify_embeddings(clarify_data):
    """Generate embeddings cho clarify cache"""
    try:
        logger.info("🔄 Generating clarify embeddings...")
        
        # Reuse embedding model loading logic
        from app.core.config import settings
        from sentence_transformers import SentenceTransformer
        
        model = None
        
        # GPU optimization
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:
            device = 'cpu'
        
        logger.info(f"🎮 Using {device.upper()} for clarify embeddings")
        
        # Load model (same strategy as router cache)
        try:
            cache_path = settings.hf_cache_path / "hub"
            embedding_model_name = settings.embedding_model_name
            model_folders = list(cache_path.glob(f"models--{embedding_model_name.replace('/', '--')}"))
            
            if model_folders:
                model_folder = model_folders[0]
                snapshots = list((model_folder / "snapshots").iterdir())
                
                if snapshots:
                    snapshot_path = str(snapshots[0])
                    model = SentenceTransformer(snapshot_path, device=device)
                    logger.info(f"✅ Loaded embedding model for clarify cache on {device.upper()}")
                else:
                    raise FileNotFoundError(f"No snapshots found")
            else:
                raise FileNotFoundError(f"No cached model found")
                
        except Exception as e1:
            logger.warning(f"⚠️ Local cache load failed: {e1}")
            try:
                model = SentenceTransformer(settings.embedding_model_name, local_files_only=True, device=device)
                logger.info(f"✅ Fallback: loaded with local_files_only")
            except Exception as e2:
                logger.warning(f"⚠️ All embedding strategies failed: {e2}")
                return None
        
        if not model:
            logger.error("❌ No embedding model available for clarify cache")
            return None
        
        clarify_cache = {}
        
        for collection_name, documents in clarify_data.items():
            clarify_cache[collection_name] = {}
            
            for doc_id, doc_data in documents.items():
                fused_text = doc_data.get('fused_text', '')
                
                if fused_text:
                    # Generate embedding cho document
                    try:
                        doc_embedding = model.encode([fused_text])[0]
                        
                        clarify_cache[collection_name][doc_id] = {
                            'title': doc_data['title'],
                            'has_form': doc_data['has_form'],
                            'metadata': doc_data['metadata'],
                            'fused_text': fused_text,
                            'embedding': doc_embedding,
                            'cache_type': 'clarify_document_embedding'
                        }
                        
                        logger.info(f"✅ Generated clarify embedding for {collection_name}/{doc_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error generating embedding for {collection_name}/{doc_id}: {e}")
                else:
                    logger.warning(f"⚠️ No fused text for {collection_name}/{doc_id}")
        
        logger.info(f"✅ Generated clarify embeddings for all collections")
        return clarify_cache
        
    except Exception as e:
        logger.error(f"❌ Error generating clarify embeddings: {e}")
        return None

def save_clarify_cache(clarify_cache):
    """Save clarify cache to separate file"""
    try:
        cache_dir = "../data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, "clarify_embeddings.pkl")
        
        # Add metadata
        cache_with_metadata = {
            'data': clarify_cache,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'structure_version': '1.0',
                'source': 'metadata.json + questions.json (clarify optimized)',
                'cache_type': 'clarify_embeddings',
                'purpose': 'document_selection_in_clarify_flow',
                'format': 'collection -> document_id -> {title, embedding, metadata}'
            }
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_with_metadata, f)
        
        cache_size = os.path.getsize(cache_file)
        logger.info(f"✅ Clarify cache saved: {cache_file} ({cache_size:,} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving clarify cache: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔄 STARTING COMPREHENSIVE CACHE REBUILD")
    logger.info("Building both Router Cache and Clarify Cache...")
    
    # Phase 1: Build Router Cache
    logger.info("\n" + "="*50)
    logger.info("📋 PHASE 1: BUILDING ROUTER CACHE")
    logger.info("="*50)
    
    # Step 1: Clean old cache
    clean_old_cache()
    
    # Step 2: Load new structure for router
    questions_data = load_new_structure()
    
    if not questions_data:
        logger.error("❌ No questions data loaded for router cache")
        exit(1)
    
    # Step 3: Generate embeddings for router (with fallback)
    router_cache_data = generate_embeddings_safe(questions_data)
    
    if not router_cache_data:
        logger.error("❌ Failed to create router cache")
        exit(1)
    
    # Step 4: Save router cache
    if not save_cache(router_cache_data):
        logger.error("❌ Failed to save router cache")
        exit(1)
    
    # Step 5: Validate router cache
    if not validate_cache():
        logger.error("❌ Router cache validation failed")
        exit(1)
    
    logger.info("✅ PHASE 1 COMPLETE: Router cache built successfully")
    
    # Phase 2: Build Clarify Cache
    logger.info("\n" + "="*50)
    logger.info("📋 PHASE 2: BUILDING CLARIFY CACHE")
    logger.info("="*50)
    
    clarify_cache_data = build_clarify_cache()
    
    if not clarify_cache_data:
        logger.error("❌ Failed to build clarify cache")
        exit(1)
    
    logger.info("✅ PHASE 2 COMPLETE: Clarify cache built successfully")
    
    # Final Summary
    logger.info("\n" + "="*50)
    logger.info("🎉 COMPREHENSIVE CACHE REBUILD COMPLETE!")
    logger.info("="*50)
    logger.info("✅ Router Cache: data/cache/router_embeddings.pkl")
    logger.info("✅ Clarify Cache: data/cache/clarify_embeddings.pkl")
    logger.info("💡 Both caches ready for production use")
    logger.info("🚀 System performance optimized for both routing and clarification")
