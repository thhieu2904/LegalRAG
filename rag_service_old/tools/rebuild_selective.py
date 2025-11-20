"""
Selective VectorDB Rebuild Script
==================================
Rebuild cache for specific scope (document/collection/all).
Called by internal_rebuild API via subprocess for process isolation.

Usage:
    python rebuild_selective.py --scope document --collection hop_dong --doc-id DOC_001
    python rebuild_selective.py --scope collection --collection hop_dong
    python rebuild_selective.py --scope all
"""

import sys
import argparse
import json
import os
from pathlib import Path
from datetime import datetime
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Change working directory to rag_service root for correct path resolution
os.chdir(Path(__file__).parent.parent)

from tools.cache import (
    load_structure_absolute_path,  # Use new absolute path version
    generate_embeddings_safe,
    save_cache,
    build_clarify_cache
)


def convert_to_dict_format(list_data):
    """
    Convert list format to dict format for generate_embeddings_safe().
    
    Input (list format):
        [{'collection_id': 'coll1', 'documents': [{'doc_id': 'doc1', ...}]}]
    
    Output (dict format):
        {'coll1': {'doc1': {...}, 'doc2': {...}}}
    """
    dict_data = {}
    
    for collection in list_data:
        collection_name = collection['collection_id']
        dict_data[collection_name] = {}
        
        for doc in collection['documents']:
            doc_id = doc['doc_id']
            dict_data[collection_name][doc_id] = doc
    
    return dict_data


def update_status(status_file: Path, data: dict):
    """Update rebuild status file"""
    try:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"📝 Status updated: {data.get('status')}")
    except Exception as e:
        print(f"❌ Failed to update status: {e}")


def rebuild_document(collection: str, doc_id: str, status_file: Path):
    """Rebuild cache for single document"""
    try:
        update_status(status_file, {
            "status": "running",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "progress": 10,
            "message": "Loading document data..."
        })
        
        # Load document data
        print(f"📂 Loading document: {collection}/{doc_id}")
        all_data = load_structure_absolute_path()
        
        # Find specific document
        doc_data = None
        for coll_data in all_data:
            if coll_data['collection_id'] == collection:
                for doc in coll_data['documents']:
                    if doc['doc_id'] == doc_id:
                        doc_data = [{'collection_id': collection, 'documents': [doc]}]
                        break
                break
        
        if not doc_data:
            raise ValueError(f"Document {collection}/{doc_id} not found")
        
        update_status(status_file, {
            "status": "running",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "progress": 40,
            "message": "Generating embeddings..."
        })
        
        # Generate embeddings (convert to dict format first)
        print(f"🔢 Generating embeddings...")
        dict_data = convert_to_dict_format(doc_data)
        embeddings_data = generate_embeddings_safe(dict_data)
        
        update_status(status_file, {
            "status": "running",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "progress": 70,
            "message": "Saving cache..."
        })
        
        # Save cache
        print(f"💾 Saving cache...")
        save_cache(embeddings_data)
        
        update_status(status_file, {
            "status": "running",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "progress": 90,
            "message": "Building clarification cache..."
        })
        
        # Build clarify cache
        print(f"🔍 Building clarify cache...")
        build_clarify_cache()
        
        update_status(status_file, {
            "status": "running",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "progress": 95,
            "message": "Rebuilding VectorDB for document..."
        })
        
        # Rebuild VectorDB for this specific document
        print(f"🔄 Rebuilding VectorDB for {collection}/{doc_id}...")
        
        import subprocess
        vectordb_rebuild_result = subprocess.run(
            [
                'python',
                str(Path(__file__).parent / 'rebuild_vectordb_json.py'),
                '--collection', collection,
                '--doc-id', doc_id
            ],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout for single document
        )
        
        if vectordb_rebuild_result.returncode == 0:
            print(f"✅ VectorDB rebuilt successfully!")
            rebuild_message = f"Document {doc_id} rebuild completed (Cache + VectorDB)"
        else:
            print(f"⚠️ VectorDB rebuild warning:")
            print(vectordb_rebuild_result.stderr[:500])  # Show first 500 chars
            rebuild_message = f"Document {doc_id} rebuild completed (Cache only - VectorDB failed)"
        
        update_status(status_file, {
            "status": "success",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "progress": 100,
            "message": rebuild_message,
            "completed_at": datetime.now().isoformat()
        })
        
        print(f"✅ Document rebuild completed: {collection}/{doc_id}")

        
    except Exception as e:
        error_msg = f"Failed to rebuild document: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        update_status(status_file, {
            "status": "failed",
            "scope": "document",
            "collection": collection,
            "doc_id": doc_id,
            "error": error_msg,
            "completed_at": datetime.now().isoformat()
        })
        sys.exit(1)


def rebuild_collection(collection: str, status_file: Path):
    """Rebuild cache for entire collection"""
    try:
        update_status(status_file, {
            "status": "running",
            "scope": "collection",
            "collection": collection,
            "progress": 10,
            "message": f"Loading collection {collection}..."
        })
        
        # Load collection data
        print(f"📂 Loading collection: {collection}")
        all_data = load_structure_absolute_path()
        
        # Filter for specific collection
        coll_data = [c for c in all_data if c['collection_id'] == collection]
        
        if not coll_data:
            raise ValueError(f"Collection {collection} not found")
        
        update_status(status_file, {
            "status": "running",
            "scope": "collection",
            "collection": collection,
            "progress": 30,
            "message": "Generating embeddings..."
        })
        
        # Generate embeddings (convert to dict format first)
        print(f"🔢 Generating embeddings...")
        dict_data = convert_to_dict_format(coll_data)
        embeddings_data = generate_embeddings_safe(dict_data)
        
        update_status(status_file, {
            "status": "running",
            "scope": "collection",
            "collection": collection,
            "progress": 60,
            "message": "Saving cache..."
        })
        
        # Save cache
        print(f"💾 Saving cache...")
        save_cache(embeddings_data)
        
        update_status(status_file, {
            "status": "running",
            "scope": "collection",
            "collection": collection,
            "progress": 90,
            "message": "Building clarification cache..."
        })
        
        # Build clarify cache
        print(f"🔍 Building clarify cache...")
        build_clarify_cache()
        
        update_status(status_file, {
            "status": "success",
            "scope": "collection",
            "collection": collection,
            "progress": 100,
            "message": f"Collection {collection} rebuild completed",
            "completed_at": datetime.now().isoformat()
        })
        
        print(f"✅ Collection rebuild completed: {collection}")
        
    except Exception as e:
        error_msg = f"Failed to rebuild collection: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        update_status(status_file, {
            "status": "failed",
            "scope": "collection",
            "collection": collection,
            "error": error_msg,
            "completed_at": datetime.now().isoformat()
        })
        sys.exit(1)


def rebuild_all(status_file: Path):
    """Rebuild cache for all collections"""
    try:
        update_status(status_file, {
            "status": "running",
            "scope": "all",
            "progress": 10,
            "message": "Loading all collections..."
        })
        
        # Load all data
        print(f"📂 Loading all collections...")
        all_data = load_structure_absolute_path()
        
        update_status(status_file, {
            "status": "running",
            "scope": "all",
            "progress": 30,
            "message": "Generating embeddings for all collections..."
        })
        
        # Generate embeddings (convert to dict format first)
        print(f"🔢 Generating embeddings...")
        dict_data = convert_to_dict_format(all_data)
        embeddings_data = generate_embeddings_safe(dict_data)
        
        update_status(status_file, {
            "status": "running",
            "scope": "all",
            "progress": 60,
            "message": "Saving cache..."
        })
        
        # Save cache
        print(f"💾 Saving cache...")
        save_cache(embeddings_data)
        
        update_status(status_file, {
            "status": "running",
            "scope": "all",
            "progress": 90,
            "message": "Building clarification cache..."
        })
        
        # Build clarify cache
        print(f"🔍 Building clarify cache...")
        build_clarify_cache()
        
        update_status(status_file, {
            "status": "success",
            "scope": "all",
            "progress": 100,
            "message": "Full rebuild completed",
            "completed_at": datetime.now().isoformat()
        })
        
        print(f"✅ Full rebuild completed")
        
    except Exception as e:
        error_msg = f"Failed to rebuild all: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        update_status(status_file, {
            "status": "failed",
            "scope": "all",
            "error": error_msg,
            "completed_at": datetime.now().isoformat()
        })
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Selective VectorDB cache rebuild")
    parser.add_argument(
        '--scope',
        choices=['document', 'collection', 'all'],
        required=True,
        help="Rebuild scope"
    )
    parser.add_argument(
        '--collection',
        help="Collection name (required for document/collection scope)"
    )
    parser.add_argument(
        '--doc-id',
        help="Document ID (required for document scope)"
    )
    parser.add_argument(
        '--status-file',
        type=Path,
        required=True,
        help="Path to status file for progress tracking"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.scope == 'document':
        if not args.collection or not args.doc_id:
            print("❌ Error: --collection and --doc-id required for document scope")
            sys.exit(1)
    elif args.scope == 'collection':
        if not args.collection:
            print("❌ Error: --collection required for collection scope")
            sys.exit(1)
    
    # Run rebuild
    print(f"🚀 Starting rebuild: scope={args.scope}, collection={args.collection}, doc_id={args.doc_id}")
    
    if args.scope == 'document':
        rebuild_document(args.collection, args.doc_id, args.status_file)
    elif args.scope == 'collection':
        rebuild_collection(args.collection, args.status_file)
    elif args.scope == 'all':
        rebuild_all(args.status_file)


if __name__ == "__main__":
    main()
