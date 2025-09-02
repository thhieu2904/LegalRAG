#!/usr/bin/env python3
"""
Script to fix wrong metadata paths in JSON files
From: "data/documents/collection/DOC_XXX/file.doc"
To: "data/storage/collections/collection/documents/DOC_XXX/file.json"
"""

import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_json_file(json_file_path: Path):
    """Fix metadata.source path in a single JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if metadata.source needs fixing
        if 'metadata' in data and 'source' in data['metadata']:
            source_path = data['metadata']['source']
            
            # Skip if already fixed
            if isinstance(source_path, str) and source_path.startswith("data/storage/collections/"):
                return False
            
            # Check if it has wrong format: "data/documents/..."
            if isinstance(source_path, str) and "data/documents/" in source_path:
                logger.info(f"Fixing path in: {json_file_path}")
                logger.info(f"  Old path: {source_path}")
                
                # Extract the collection name from the current file path
                # Format: .../collections/collection_name/documents/DOC_XXX/file.json
                current_path = str(json_file_path)
                path_parts = current_path.split(os.sep)
                collection_idx = path_parts.index("collections") if "collections" in path_parts else -1
                
                if collection_idx >= 0 and collection_idx + 1 < len(path_parts):
                    collection_name = path_parts[collection_idx + 1]
                    
                    # Extract current file structure for the target path
                    current_file = json_file_path.name
                    
                    # Extract subfolders from current path
                    subfolders = []
                    if "documents" in path_parts:
                        doc_idx = path_parts.index("documents")
                        if doc_idx + 1 < len(path_parts):
                            # Get all folders between 'documents' and the file
                            subfolders = path_parts[doc_idx+1:-1]  # Skip the filename
                    
                    # Special case for quy_trinh_cong_chung with different structure
                    if collection_name == "quy_trinh_cong_chung" and "QUY TRÌNH CÔNG CHỨNG" in source_path:
                        doc_name = source_path.split("/")[-1].replace(".doc", ".json")
                        new_path = f"data/storage/collections/{collection_name}/documents/QUY TRÌNH CÔNG CHỨNG/{doc_name}"
                    # Special case for collections with documents in subdirectories
                    elif len(subfolders) > 0:
                        # Create path preserving the subfolder structure
                        subfolder_path = "/".join(subfolders)
                        doc_name = source_path.split("/")[-1].replace(".doc", ".json")
                        new_path = f"data/storage/collections/{collection_name}/documents/{subfolder_path}/{current_file}"
                    else:
                        # Default case: extract original filename and replace extension
                        original_filename = source_path.split("/")[-1]
                        new_filename = original_filename.replace(".doc", ".json")
                        new_path = f"data/storage/collections/{collection_name}/documents/{new_filename}"
                    
                    # Update data
                    data['metadata']['source'] = new_path
                    
                    logger.info(f"  New path: {new_path}")
                    
                    # Write back
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    return True
                    
        return False
        
    except Exception as e:
        logger.error(f"Error fixing {json_file_path}: {e}")
        return False

def main():
    """Fix all JSON files in collections"""
    base_dir = Path(__file__).parent.parent
    collections_dir = base_dir / "data" / "storage" / "collections"
    
    if not collections_dir.exists():
        logger.error(f"Collections directory not found: {collections_dir}")
        return
    
    fixed_count = 0
    total_count = 0
    
    # Get a list of all json files in the collections
    all_json_files = []
    for collection_dir in collections_dir.iterdir():
        if not collection_dir.is_dir():
            continue
            
        docs_dir = collection_dir / "documents"
        if not docs_dir.exists():
            continue
            
        logger.info(f"Processing collection: {collection_dir.name}")
        
        # Use recursive glob to find all JSON files, regardless of depth
        json_files = list(docs_dir.glob("**/*.json"))
        all_json_files.extend(json_files)
    
    # Process all JSON files
    for json_file in all_json_files:
        if "questions.json" in str(json_file):
            continue
            
        total_count += 1
        if fix_json_file(json_file):
            fixed_count += 1
    
    logger.info(f"✅ Fixed {fixed_count}/{total_count} JSON files")

if __name__ == "__main__":
    main()
