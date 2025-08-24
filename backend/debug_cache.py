#!/usr/bin/env python3
"""Debug cache structure"""
import pickle
import json

# Load cache file
cache_file = "data/cache/router_embeddings.pkl"
with open(cache_file, 'rb') as f:
    cache_container = pickle.load(f)

print("=== CACHE STRUCTURE ===")
print(f"Type: {type(cache_container)}")
print(f"Keys: {list(cache_container.keys()) if isinstance(cache_container, dict) else 'Not dict'}")

if isinstance(cache_container, dict):
    if 'data' in cache_container:
        print("\n=== DATA SECTION ===")
        cache_data = cache_container['data']
        print(f"Data type: {type(cache_data)}")
        print(f"Data keys: {list(cache_data.keys()) if isinstance(cache_data, dict) else 'Not dict'}")
        
        if isinstance(cache_data, dict):
            # Check first collection
            first_collection_name = next(iter(cache_data.keys()), None)
            if first_collection_name:
                print(f"\n=== FIRST COLLECTION: {first_collection_name} ===")
                first_collection = cache_data[first_collection_name]
                print(f"Collection type: {type(first_collection)}")
                print(f"Collection keys: {list(first_collection.keys()) if isinstance(first_collection, dict) else 'Not dict'}")
                
                # Check first document
                first_doc_name = next(iter(first_collection.keys()), None)
                if first_doc_name:
                    print(f"\n=== FIRST DOCUMENT: {first_doc_name} ===")
                    first_doc = first_collection[first_doc_name]
                    print(f"Document type: {type(first_doc)}")
                    print(f"Document keys: {list(first_doc.keys()) if isinstance(first_doc, dict) else 'Not dict'}")
                    
                    # Check specific fields
                    for key in ['embeddings', 'fused_embedding', 'texts', 'metadata']:
                        if key in first_doc:
                            value = first_doc[key]
                            if key == 'embeddings':
                                print(f"  {key}: {type(value)} - shape: {getattr(value, 'shape', 'No shape')}")
                            elif key == 'fused_embedding':
                                print(f"  {key}: {type(value)} - shape: {getattr(value, 'shape', 'No shape')}")
                            elif key == 'texts':
                                print(f"  {key}: {type(value)} - count: {len(value) if isinstance(value, list) else 'Not list'}")
                            else:
                                print(f"  {key}: {type(value)}")
    
    if 'metadata' in cache_container:
        print(f"\n=== METADATA ===")
        metadata = cache_container['metadata']
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
