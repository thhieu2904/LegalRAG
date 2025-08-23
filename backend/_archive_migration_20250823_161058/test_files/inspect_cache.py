#!/usr/bin/env python3
"""
🔍 INSPECT CACHE FILE 
Check cache content & embedding status
"""

import pickle
import os

def inspect_cache():
    cache_file = "data/cache/router_embeddings.pkl"
    
    print("🔍 CACHE FILE INSPECTION")
    print("=" * 40)
    
    if not os.path.exists(cache_file):
        print("❌ Cache file không tồn tại")
        return
    
    file_size = os.path.getsize(cache_file)
    print(f"📁 File: {cache_file}")
    print(f"📊 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print(f"✅ Loaded successfully")
        print(f"📝 Type: {type(cache_data)}")
        
        if isinstance(cache_data, dict):
            print(f"🔑 Keys: {list(cache_data.keys())}")
            
            # Check metadata
            if 'metadata' in cache_data:
                metadata = cache_data['metadata']
                print(f"\\n📋 METADATA:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
            
            # Check collections
            if 'collections' in cache_data:
                collections = cache_data['collections']
                print(f"\\n📦 COLLECTIONS: {len(collections)}")
                
                for col_name, docs in collections.items():
                    print(f"   📂 {col_name}: {len(docs)} docs")
                    
                    # Check first doc for embedding
                    if docs:
                        first_doc = list(docs.values())[0]
                        has_embedding = 'embedding' in first_doc or 'embeddings' in first_doc
                        has_questions = 'main_question' in first_doc
                        
                        print(f"      - Has questions: {has_questions}")
                        print(f"      - Has embeddings: {has_embedding}")
                        
                        if has_embedding:
                            if 'embedding' in first_doc:
                                emb_shape = len(first_doc['embedding']) if first_doc['embedding'] else 0
                                print(f"      - Embedding size: {emb_shape}")
                            if 'embeddings' in first_doc:
                                emb_count = len(first_doc['embeddings']) if first_doc['embeddings'] else 0
                                print(f"      - Embeddings count: {emb_count}")
            
            # Check embeddings
            if 'embeddings' in cache_data:
                embeddings = cache_data['embeddings']
                print(f"\\n🧠 EMBEDDINGS: {len(embeddings)} items")
            
        print(f"\\n🎯 SUMMARY:")
        print(f"   Cache format: {'New questions.json' if 'metadata' in cache_data else 'Legacy'}")
        has_embeddings = any('embedding' in str(cache_data).lower() for _ in [1])
        print(f"   Has embeddings: {has_embeddings}")
        print(f"   Cache working: ✅")
        
    except Exception as e:
        print(f"❌ Error loading cache: {e}")

if __name__ == "__main__":
    inspect_cache()
