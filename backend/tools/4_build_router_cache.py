#!/usr/bin/env python3
"""
Router Cache Builder for LegalRAG
=================================

Tool để build embeddings cache cho router examples:
- Load từ aggregated files trong router_examples_smart
- Generate embeddings và save cache
- Router startup sẽ nhanh hơn nhiều

Usage:
    cd backend && conda activate LegalRAG_v1 && python tools/4_build_router_cache.py
"""

import sys
import os
import json
import pickle
import numpy as np
from pathlib import Path
import logging
import argparse
import time

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RouterCacheBuilder:
    def __init__(self):
        self.data_dir = backend_dir / "data"
        self.router_dir = self.data_dir / "router_examples_smart_v3"  # Updated to V3
        self.cache_dir = self.data_dir / "cache"
        self.cache_file = self.cache_dir / "router_embeddings.pkl"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model = None
    
    def clean_incomplete_downloads(self, model_name, cache_dir):
        """Clean up incomplete model downloads"""
        try:
            model_path = cache_dir / f"models--{model_name.replace('/', '--')}"
            
            if not model_path.exists():
                return True
            
            # Remove incomplete blobs
            blobs_dir = model_path / "blobs"
            if blobs_dir.exists():
                incomplete_files = list(blobs_dir.glob("*.incomplete"))
                for file in incomplete_files:
                    logger.info(f"🗑️ Removing incomplete download: {file.name}")
                    file.unlink()
            
            # Check if any complete files exist
            complete_files = list(blobs_dir.glob("*")) if blobs_dir.exists() else []
            complete_files = [f for f in complete_files if not f.name.endswith('.incomplete')]
            
            if not complete_files:
                logger.info(f"🗑️ Removing empty model directory: {model_path}")
                import shutil
                shutil.rmtree(model_path, ignore_errors=True)
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean incomplete downloads: {e}")
            return False

    def check_model_completeness(self, model_name, cache_dir):
        """Check if model is completely downloaded"""
        model_path = cache_dir / f"models--{model_name.replace('/', '--')}"
        
        if not model_path.exists():
            return False, "Model directory not found"
        
        # Check for incomplete downloads
        blobs_dir = model_path / "blobs"
        if blobs_dir.exists():
            incomplete_files = list(blobs_dir.glob("*.incomplete"))
            if incomplete_files:
                return False, f"Found {len(incomplete_files)} incomplete download(s)"
        
        # Check for essential files in snapshots
        snapshots_dir = model_path / "snapshots"
        if not snapshots_dir.exists():
            return False, "No snapshots directory found"
        
        # Find the latest snapshot
        snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
        if not snapshot_dirs:
            return False, "No snapshots found"
        
        latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
        
        # Check for essential files
        essential_files = ["config.json", "config_sentence_transformers.json", "modules.json"]
        model_files = ["model.safetensors", "pytorch_model.bin"]
        
        for file in essential_files:
            if not (latest_snapshot / file).exists():
                return False, f"Missing essential file: {file}"
        
        # Check for at least one model file
        has_model_file = any((latest_snapshot / file).exists() for file in model_files)
        if not has_model_file:
            return False, "No model weights found (model.safetensors or pytorch_model.bin)"
        
        return True, "Model is complete"
    
    def initialize_model(self, allow_download=False):
        """Initialize embedding model with proper error handling"""
        try:
            from sentence_transformers import SentenceTransformer
            import os
            
            # Model config
            model_name = "AITeamVN/Vietnamese_Embedding_v2"
            cache_dir = self.data_dir / "models" / "hf_cache"
            
            logger.info(f"🔧 Loading embedding model...")
            logger.info(f"   📂 Cache dir: {cache_dir}")
            logger.info(f"   🤖 Model: {model_name}")
            
            # Check if model is complete
            is_complete, msg = self.check_model_completeness(model_name, cache_dir)
            
            if not is_complete:
                logger.warning(f"⚠️ Model check failed: {msg}")
                
                if not allow_download:
                    logger.error("❌ Model incomplete and download not allowed. Use --allow-download flag")
                    logger.info("💡 To fix the issue, you can:")
                    logger.info("   Option 1: python tools/4_build_router_cache.py --allow-download --force")
                    logger.info("   Option 2: Manually clean cache and re-run")
                    return False
                
                logger.info("🧹 Cleaning incomplete downloads...")
                self.clean_incomplete_downloads(model_name, cache_dir)
                
                logger.info("🔄 Downloading model (this may take a while)...")
                # Allow online download
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
                os.environ.pop('HF_HUB_OFFLINE', None)
            else:
                logger.info(f"✅ Model check passed: {msg}")
                # Use offline mode for complete models
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_HUB_OFFLINE'] = '1'
            
            # Common settings
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            self.embedding_model = SentenceTransformer(
                model_name,
                cache_folder=str(cache_dir),
                device='cuda'
            )
            
            logger.info("✅ Embedding model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_router_examples(self):
        """Load từ tất cả file JSON trong router_examples_smart"""
        logger.info("📚 Loading router examples...")
        
        collections_data = {}
        
        # Mapping thư mục -> collection name
        collection_mapping = {
            'quy_trinh_chung_thuc': 'chung_thuc',
            'quy_trinh_cap_ho_tich_cap_xa': 'ho_tich_cap_xa',
            'quy_trinh_nuoi_con_nuoi': 'nuoi_con_nuoi'
        }
        
        # Scan tất cả thư mục
        for subdir in self.router_dir.iterdir():
            if not subdir.is_dir():
                continue
            
            collection_name = collection_mapping.get(subdir.name, subdir.name)
            logger.info(f"   📂 Processing {subdir.name} -> {collection_name}")
            
            questions = []
            
            # Scan đệ quy tất cả file JSON
            json_files = list(subdir.rglob("*.json"))
            
            for json_file in json_files:
                logger.info(f"     📄 Loading {json_file.name}...")
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Xử lý format mới - có thể có nhiều examples trong 1 file
                    if isinstance(data, list):
                        # File chứa list examples
                        for item in data:
                            if isinstance(item, dict) and 'question' in item:
                                question_item = {
                                    'text': item.get('question', '').strip(),
                                    'collection': collection_name,
                                    'filters': item.get('filters', {}),
                                    'source': json_file.name,
                                    'type': 'individual',
                                    'answer': item.get('answer', '')
                                }
                                if question_item['text']:
                                    questions.append(question_item)
                    
                    elif isinstance(data, dict):
                        # File chứa smart router format
                        if 'main_question' in data:
                            # Smart router format mới
                            main_question = data.get('main_question', '').strip()
                            question_variants = data.get('question_variants', [])
                            metadata = data.get('metadata', {})
                            smart_filters = data.get('smart_filters', {})
                            
                            if main_question:
                                # Main question
                                question_item = {
                                    'text': main_question,
                                    'collection': metadata.get('collection', collection_name),
                                    'filters': smart_filters,
                                    'source': json_file.name,
                                    'type': 'smart_main',
                                    'metadata': metadata,
                                    'priority_score': data.get('priority_score', 1.0),
                                    'confidence_threshold': data.get('confidence_threshold', 0.75)
                                }
                                questions.append(question_item)
                            
                            # Question variants
                            for variant in question_variants:
                                if variant.strip():
                                    question_item = {
                                        'text': variant.strip(),
                                        'collection': metadata.get('collection', collection_name),
                                        'filters': smart_filters,
                                        'source': json_file.name,
                                        'type': 'smart_variant',
                                        'metadata': metadata,
                                        'priority_score': data.get('priority_score', 1.0),
                                        'confidence_threshold': data.get('confidence_threshold', 0.75)
                                    }
                                    questions.append(question_item)
                        
                        elif 'question' in data:
                            # Single example format cũ
                            question_item = {
                                'text': data.get('question', '').strip(),
                                'collection': collection_name,
                                'filters': data.get('filters', {}),
                                'source': json_file.name,
                                'type': 'individual',
                                'answer': data.get('answer', '')
                            }
                            if question_item['text']:
                                questions.append(question_item)
                        
                        elif 'examples' in data:
                            # Format aggregated cũ
                            examples = data.get('examples', [])
                            for example in examples:
                                question_item = {
                                    'text': example.get('question', '').strip(),
                                    'collection': data.get('collection', collection_name),
                                    'filters': example.get('filters', {}),
                                    'source': json_file.name,
                                    'type': 'aggregated',
                                    'answer': example.get('answer', '')
                                }
                                if question_item['text']:
                                    questions.append(question_item)
                        
                        else:
                            # Try to extract any text fields that might be questions
                            for key in ['text', 'query', 'input', 'question_text']:
                                if key in data and data[key].strip():
                                    question_item = {
                                        'text': data[key].strip(),
                                        'collection': collection_name,
                                        'filters': data.get('filters', {}),
                                        'source': json_file.name,
                                        'type': 'extracted',
                                        'answer': data.get('answer', data.get('response', ''))
                                    }
                                    questions.append(question_item)
                                    break
                    
                except Exception as e:
                    logger.warning(f"     ⚠️ Failed to load {json_file.name}: {e}")
                    continue
            
            if questions:
                collections_data[collection_name] = questions
                logger.info(f"     ✅ Loaded {len(questions)} questions for {collection_name}")
            else:
                logger.warning(f"     ⚠️ No questions found in {collection_name}")
        
        total = sum(len(q) for q in collections_data.values())
        logger.info(f"📚 Total: {total} questions, {len(collections_data)} collections")
        
        return collections_data
    
    def build_cache(self, collections_data, force=False):
        """Build embeddings cache"""
        if self.cache_file.exists() and not force:
            logger.info("📦 Cache exists, use --force to rebuild")
            return True
        
        if self.embedding_model is None:
            logger.error("❌ Embedding model not initialized")
            return False
        
        logger.info("🔄 Building embeddings cache...")
        start_time = time.time()
        
        cache_data = {
            'metadata': {
                'version': '1.0',
                'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_questions': 0,
                'collections': {}
            },
            'questions': {},
            'embeddings': {}
        }
        
        total_questions = 0
        
        for collection, questions in collections_data.items():
            logger.info(f"   🎯 Processing {collection}: {len(questions)} questions")
            
            # Extract texts
            texts = [q['text'] for q in questions if q['text'].strip()]
            
            if not texts:
                continue
            
            # Generate embeddings
            logger.info(f"   🔢 Generating embeddings...")
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Store
            cache_data['questions'][collection] = questions
            cache_data['embeddings'][collection] = embeddings
            cache_data['metadata']['collections'][collection] = len(questions)
            total_questions += len(questions)
            
            logger.info(f"     ✅ Cached {len(questions)} questions")
        
        cache_data['metadata']['total_questions'] = total_questions
        
        # Save cache
        logger.info(f"💾 Saving cache: {self.cache_file}")
        with open(self.cache_file, 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        elapsed = time.time() - start_time
        size_mb = self.cache_file.stat().st_size / (1024 * 1024)
        
        logger.info(f"🎉 Cache built successfully:")
        logger.info(f"   📄 Questions: {total_questions}")
        logger.info(f"   📂 Collections: {len(collections_data)}")
        logger.info(f"   💾 Size: {size_mb:.1f}MB")
        logger.info(f"   ⏱️ Time: {elapsed:.1f}s")
        
        return True
    
    def verify_cache(self):
        """Verify cache"""
        try:
            logger.info("🔍 Verifying cache...")
            
            if not self.cache_file.exists():
                logger.error("❌ Cache file not found")
                return False
            
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            metadata = cache_data.get('metadata', {})
            questions = cache_data.get('questions', {})
            embeddings = cache_data.get('embeddings', {})
            
            logger.info(f"   📋 Version: {metadata.get('version')}")
            logger.info(f"   📅 Created: {metadata.get('created')}")
            logger.info(f"   📄 Questions: {metadata.get('total_questions')}")
            logger.info(f"   📂 Collections: {len(questions)}")
            
            # Verify structure
            for collection in questions.keys():
                if collection not in embeddings:
                    logger.error(f"❌ Missing embeddings for {collection}")
                    return False
                
                q_count = len(questions[collection])
                e_shape = embeddings[collection].shape
                
                if e_shape[0] != q_count:
                    logger.error(f"❌ Size mismatch in {collection}")
                    return False
                
                logger.info(f"     ✅ {collection}: {q_count} questions, {e_shape}")
            
            logger.info("✅ Cache verification passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache verification failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Build router embeddings cache')
    parser.add_argument('--force', action='store_true', help='Force rebuild cache')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing cache')
    parser.add_argument('--allow-download', action='store_true', help='Allow downloading model if incomplete')
    parser.add_argument('--clean-model', action='store_true', help='Clean incomplete model downloads and exit')
    args = parser.parse_args()
    
    logger.info("🔧 LEGALRAG ROUTER CACHE BUILDER")
    logger.info("=" * 50)
    
    builder = RouterCacheBuilder()
    
    # Clean model only
    if args.clean_model:
        model_name = "AITeamVN/Vietnamese_Embedding_v2"
        cache_dir = builder.data_dir / "models" / "hf_cache"
        success = builder.clean_incomplete_downloads(model_name, cache_dir)
        if success:
            logger.info("✅ Model cleanup completed")
            return 0
        else:
            logger.error("❌ Model cleanup failed")
            return 1
    
    if args.verify_only:
        return 0 if builder.verify_cache() else 1
    
    # Initialize model
    if not builder.initialize_model(allow_download=args.allow_download):
        return 1
    
    # Load examples
    collections_data = builder.load_router_examples()
    if not collections_data:
        logger.error("❌ No router examples loaded")
        return 1
    
    # Build cache
    if not builder.build_cache(collections_data, args.force):
        return 1
    
    # Verify
    builder.verify_cache()
    
    logger.info("🎉 SUCCESS! Router will now start much faster!")
    return 0

if __name__ == "__main__":
    exit(main())
