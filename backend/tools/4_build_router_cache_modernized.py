#!/usr/bin/env python3
"""
Router Cache Builder for LegalRAG - MODERNIZED FOR NEW STRUCTURE
================================================================

Tool để build embeddings cache cho router examples:
- Load từ new collection-based structure hoặc fallback to old structure
- Generate embeddings và save cache
- Router startup sẽ nhanh hơn nhiều

Usage:
    cd backend && conda activate LegalRAG_v1 && python tools/4_build_router_cache_modernized.py
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

# Import path config
try:
    from app.core.path_config import path_config
    HAVE_PATH_CONFIG = True
except ImportError:
    path_config = None
    HAVE_PATH_CONFIG = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RouterCacheBuilderModernized:
    def __init__(self):
        self.data_dir = backend_dir / "data"
        self.router_dir = self.data_dir / "router_examples_smart_v3"  # Fallback to old structure
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
                
            # Check for incomplete download indicators
            incomplete_indicators = ['.lock', '.incomplete', '.tmp']
            for indicator in incomplete_indicators:
                if any(f.name.endswith(indicator) for f in model_path.rglob('*')):
                    logger.warning(f"Found incomplete download indicator in {model_path}")
                    import shutil
                    shutil.rmtree(model_path)
                    logger.info(f"Cleaned up incomplete download: {model_path}")
                    return True
                    
            return True
        except Exception as e:
            logger.error(f"Error cleaning incomplete downloads: {e}")
            return False

    def setup_embedding_model(self):
        """Setup embedding model with error handling"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # Use the same model as vector database builder for consistency
            model_name = "AITeamVN/Vietnamese_Embedding_v2"
            hf_cache_dir = backend_dir / "data" / "models" / "hf_cache"
            hf_cache_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Loading embedding model: {model_name}")
            logger.info(f"Cache directory: {hf_cache_dir}")
            
            # Clean incomplete downloads
            self.clean_incomplete_downloads(model_name, hf_cache_dir)
            
            # Force CPU usage for embedding model (memory optimization)
            device = "cpu"
            logger.info(f"Using device: {device}")
            
            # Load model with cache directory
            self.embedding_model = SentenceTransformer(
                model_name,
                cache_folder=str(hf_cache_dir),
                device=device
            )
            
            logger.info(f"✅ Embedding model loaded successfully on {device}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup embedding model: {e}")
            return False

    def load_router_examples_new_structure(self):
        """Load router examples from new collection-based structure"""
        if not HAVE_PATH_CONFIG or not path_config.is_new_structure_available():
            return None
            
        logger.info("📁 Loading router examples from NEW collection-based structure")
        
        all_examples = {}
        collection_stats = {}
        
        try:
            for collection_name in path_config.list_collections():
                logger.info(f"Processing collection: {collection_name}")
                collection_examples = []
                
                documents = path_config.list_documents(collection_name)
                for doc in documents:
                    if not doc.get("has_router"):
                        continue
                        
                    router_path = Path(doc["router_path"])
                    if not router_path.exists():
                        continue
                        
                    try:
                        with open(router_path, 'r', encoding='utf-8') as f:
                            router_data = json.load(f)
                            
                        # NEW FORMAT: Uses 'question_variants' instead of 'questions'
                        if "question_variants" in router_data:
                            for question in router_data["question_variants"]:
                                collection_examples.append({
                                    "text": question,
                                    "collection": collection_name,
                                    "source_document": doc["doc_id"],
                                    "document_title": router_data.get("metadata", {}).get("title", doc["doc_id"])
                                })
                        # FALLBACK: Old format compatibility
                        elif "questions" in router_data:
                            for question in router_data["questions"]:
                                collection_examples.append({
                                    "text": question,
                                    "collection": collection_name,
                                    "source_document": doc["doc_id"],
                                    "document_title": router_data.get("title", doc["doc_id"])
                                })
                                
                    except Exception as e:
                        logger.warning(f"Error loading router file {router_path}: {e}")
                        continue
                
                if collection_examples:
                    all_examples[collection_name] = collection_examples
                    collection_stats[collection_name] = len(collection_examples)
                    logger.info(f"✅ {collection_name}: {len(collection_examples)} examples")
        
            if all_examples:
                logger.info(f"📊 Total collections: {len(all_examples)}")
                logger.info(f"📊 Total examples: {sum(collection_stats.values())}")
                return all_examples
            else:
                logger.warning("No router examples found in new structure")
                return None
                
        except Exception as e:
            logger.error(f"Error loading from new structure: {e}")
            return None

    def load_router_examples_old_structure(self):
        """Load router examples from old router_examples_smart_v3 structure"""
        logger.info("📁 Loading router examples from OLD structure (fallback)")
        
        if not self.router_dir.exists():
            logger.error(f"Router directory not found: {self.router_dir}")
            return None
        
        all_examples = {}
        
        # Load aggregated files
        aggregated_file = self.router_dir / "llm_generation_summary_v3.json"
        if not aggregated_file.exists():
            logger.error(f"Aggregated file not found: {aggregated_file}")
            return None
        
        try:
            with open(aggregated_file, 'r', encoding='utf-8') as f:
                aggregated_data = json.load(f)
            
            # Process each collection
            for collection_name, collection_data in aggregated_data.items():
                if not isinstance(collection_data, dict):
                    continue
                    
                collection_examples = []
                for doc_name, doc_data in collection_data.items():
                    if isinstance(doc_data, dict) and "questions" in doc_data:
                        for question in doc_data["questions"]:
                            collection_examples.append({
                                "text": question,
                                "collection": collection_name,
                                "source_document": doc_name,
                                "document_title": doc_data.get("title", doc_name)
                            })
                
                if collection_examples:
                    all_examples[collection_name] = collection_examples
                    logger.info(f"✅ {collection_name}: {len(collection_examples)} examples")
            
            if all_examples:
                logger.info(f"📊 Total collections: {len(all_examples)}")
                logger.info(f"📊 Total examples: {sum(len(examples) for examples in all_examples.values())}")
                return all_examples
            else:
                logger.warning("No examples found in aggregated file")
                return None
                
        except Exception as e:
            logger.error(f"Error loading from old structure: {e}")
            return None

    def load_router_examples(self):
        """Load router examples with dual-mode support"""
        # Try new structure first
        examples = self.load_router_examples_new_structure()
        
        if examples:
            logger.info("✅ Successfully loaded from NEW structure")
            return examples
        
        # Fallback to old structure
        logger.info("⚠️  Falling back to OLD structure")
        examples = self.load_router_examples_old_structure()
        
        if examples:
            logger.info("✅ Successfully loaded from OLD structure")
            return examples
        
        logger.error("❌ Failed to load router examples from both structures")
        return None

    def generate_embeddings(self, examples_data):
        """Generate embeddings for router examples"""
        logger.info("🔄 Generating embeddings for router examples...")
        
        cache_data = {
            "embeddings": {},
            "metadata": {
                "model_name": "AITeamVN/Vietnamese_Embedding_v2",
                "creation_time": time.time(),
                "total_collections": len(examples_data),
                "structure_type": "new" if HAVE_PATH_CONFIG and path_config.is_new_structure_available() else "old"
            }
        }
        
        total_examples = 0
        
        for collection_name, examples in examples_data.items():
            logger.info(f"Processing {collection_name}: {len(examples)} examples")
            
            # Extract texts
            texts = [example["text"] for example in examples]
            
            # Generate embeddings in batches
            batch_size = 32
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.embedding_model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                embeddings.extend(batch_embeddings)
            
            cache_data["embeddings"][collection_name] = {
                "vectors": np.array(embeddings),
                "examples": examples,
                "count": len(examples)
            }
            
            total_examples += len(examples)
            logger.info(f"✅ {collection_name}: {len(examples)} embeddings generated")
        
        cache_data["metadata"]["total_examples"] = total_examples
        logger.info(f"🎯 Total embeddings generated: {total_examples}")
        
        return cache_data

    def save_cache(self, cache_data):
        """Save embeddings cache to file"""
        logger.info(f"💾 Saving embeddings cache to: {self.cache_file}")
        
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Verify cache file
            file_size = self.cache_file.stat().st_size
            logger.info(f"✅ Cache saved successfully: {file_size:,} bytes")
            
            # Test loading
            with open(self.cache_file, 'rb') as f:
                test_data = pickle.load(f)
            
            logger.info(f"✅ Cache verification passed")
            logger.info(f"📊 Cached collections: {list(test_data['embeddings'].keys())}")
            logger.info(f"📊 Total examples: {test_data['metadata']['total_examples']}")
            logger.info(f"📊 Structure type: {test_data['metadata']['structure_type']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save cache: {e}")
            return False

    def build_cache(self):
        """Main method to build router cache"""
        logger.info("🚀 Starting router cache building process...")
        
        # Setup embedding model
        if not self.setup_embedding_model():
            return False
        
        # Load router examples
        examples_data = self.load_router_examples()
        if not examples_data:
            return False
        
        # Generate embeddings
        cache_data = self.generate_embeddings(examples_data)
        if not cache_data:
            return False
        
        # Save cache
        if not self.save_cache(cache_data):
            return False
        
        logger.info("🎉 Router cache building completed successfully!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Build router embeddings cache")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if cache exists")
    args = parser.parse_args()
    
    builder = RouterCacheBuilderModernized()
    
    if builder.cache_file.exists() and not args.force:
        logger.info(f"Cache file already exists: {builder.cache_file}")
        logger.info("Use --force to rebuild")
        return
    
    success = builder.build_cache()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
