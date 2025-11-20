"""
Rebuild VectorDB for JSON Document Changes
===========================================
Lightweight VectorDB rebuild specifically for JSON document edits.
Does NOT rebuild cache - only updates VectorDB chunks.

Usage:
    python rebuild_vectordb_json.py --collection <name> --doc-id <id>
"""

import sys
import os
from pathlib import Path
import json
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.vector import VectorDBService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rebuild_vectordb_for_json(collection_name: str, doc_id: str):
    """
    Rebuild VectorDB for a specific JSON document.
    
    Strategy:
    1. Load JSON document content
    2. Delete old chunks for this document from VectorDB
    3. Re-chunk and re-index the document
    
    Args:
        collection_name: Collection name
        doc_id: Document ID
    """
    try:
        logger.info(f"🔄 Rebuilding VectorDB for {collection_name}/{doc_id}")
        
        # Initialize VectorDB service
        vectordb = VectorDBService()
        
        # Find JSON file
        doc_dir = Path(f"data/storage/collections/{collection_name}/documents/{doc_id}")
        if not doc_dir.exists():
            logger.error(f"❌ Document directory not found: {doc_dir}")
            return False
        
        # Find JSON file (not questions.json)
        json_files = [f for f in doc_dir.glob("*.json") if f.name != "questions.json"]
        if not json_files:
            logger.error(f"❌ No JSON document found in {doc_dir}")
            return False
        
        json_file = json_files[0]
        logger.info(f"📄 Found JSON file: {json_file.name}")
        
        # Load JSON content
        with open(json_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        # Extract content for chunking
        metadata = doc_data.get('metadata', {})
        title = doc_data.get('title', '')
        
        # Build text from sections
        texts_to_index = []
        
        # Add title
        if title:
            texts_to_index.append(f"# {title}")
        
        # Add sections
        for section in doc_data.get('sections', []):
            section_title = section.get('title', '')
            if section_title:
                texts_to_index.append(f"## {section_title}")
            
            for item in section.get('items', []):
                content = item.get('content', '')
                if content:
                    texts_to_index.append(content)
        
        # Add required documents
        for req_doc in doc_data.get('required_documents', []):
            name = req_doc.get('name', '')
            desc = req_doc.get('description', '')
            if name or desc:
                texts_to_index.append(f"Hồ sơ yêu cầu: {name}. {desc}")
        
        # Add notes
        for note in doc_data.get('notes', []):
            if note:
                texts_to_index.append(f"Lưu ý: {note}")
        
        if not texts_to_index:
            logger.warning(f"⚠️ No content to index for {doc_id}")
            return True  # Not an error, just empty
        
        full_text = "\n\n".join(texts_to_index)
        logger.info(f"📝 Extracted {len(texts_to_index)} text chunks ({len(full_text)} chars)")
        
        # Delete old chunks for this document
        # ChromaDB uses collection per collection_name
        try:
            collection = vectordb.get_collection(collection_name)
            
            # Delete by document_id metadata filter
            existing_ids = collection.get(
                where={"document_id": doc_id}
            )['ids']
            
            if existing_ids:
                logger.info(f"🗑️ Deleting {len(existing_ids)} old chunks")
                collection.delete(ids=existing_ids)
        except Exception as e:
            logger.warning(f"⚠️ Could not delete old chunks: {e}")
        
        # Add new chunks
        logger.info(f"➕ Adding new chunks to VectorDB")
        
        # Prepare document for indexing
        doc_for_indexing = {
            "content": full_text,
            "source": {
                "document_title": title,
                "file_path": str(json_file),
                "document_code": metadata.get("code", ""),
                "section_title": "",
                "source_reference": "",
                "chunk_id": doc_id,
                "chunk_index_num": 0,
                "document_id": doc_id,
                "issuing_authority": metadata.get("issuing_authority", ""),
                "executing_agency": metadata.get("executing_agency", ""),
                "effective_date": metadata.get("effective_date", "")
            },
            "metadata": {
                "processing_time": doc_data.get("processing_time_text", ""),
                "fee_info": doc_data.get("fee_text", ""),
                "legal_basis": metadata.get("legal_basis_references", [])
            },
            "type": "json_document",
            "keywords": []
        }
        
        # Add to VectorDB
        added = vectordb.add_documents_to_collection(
            collection_name=collection_name,
            documents=[doc_for_indexing]
        )
        
        logger.info(f"✅ VectorDB rebuilt: {added} chunks added")
        return True
        
    except Exception as e:
        logger.error(f"❌ VectorDB rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebuild VectorDB for JSON document")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--doc-id", required=True, help="Document ID")
    
    args = parser.parse_args()
    
    success = rebuild_vectordb_for_json(args.collection, args.doc_id)
    sys.exit(0 if success else 1)
