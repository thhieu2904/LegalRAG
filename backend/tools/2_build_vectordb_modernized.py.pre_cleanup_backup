"""
MODERNIZED VECTOR DATABASE BUILDER
=================================

Updated to work with new collection-based document structure:
data/storage/collections/{collection}/documents/DOC_XXX/
├── original_name.json          ← RAG content (what we index)
├── original_name.doc           ← Original document  
├── router_questions.json       ← Router questions (not indexed)
└── forms/                      ← Forms directory

This tool scans all collections and builds vector database from the JSON content files.
"""

#!/usr/bin/env python3

import sys
import os
import json
from pathlib import Path
import logging
import argparse
from typing import Dict, List, Any, Optional
import time

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import from app modules
from app.core.config import settings

# Setup logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vectordb_builder.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ModernizedVectorDBBuilder:
    """Vector database builder for new collection-based structure"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        
        # NEW STRUCTURE
        self.storage_dir = self.data_dir / "storage"
        self.collections_dir = self.storage_dir / "collections"
        
        # OLD STRUCTURE (fallback)
        self.old_documents_dir = self.data_dir / "documents"
        
        # OUTPUT
        self.vectordb_dir = self.data_dir / "vectordb"
        
    def check_structure(self) -> str:
        """Check which structure is available"""
        new_available = (self.collections_dir.exists() and 
                        any(self.collections_dir.iterdir()))
        old_available = (self.old_documents_dir.exists() and 
                        any(self.old_documents_dir.iterdir()))
        
        if new_available:
            return "new"
        elif old_available:
            return "old"
        else:
            return "none"
    
    def scan_new_structure(self) -> List[Dict]:
        """Scan new collection-based structure for JSON files"""
        logger.info("Scanning new collection-based structure...")
        
        documents = []
        
        for collection_dir in self.collections_dir.iterdir():
            if not collection_dir.is_dir():
                continue
                
            collection_name = collection_dir.name
            docs_dir = collection_dir / "documents"
            
            if not docs_dir.exists():
                continue
            
            logger.info(f"Processing collection: {collection_name}")
            
            for doc_dir in docs_dir.iterdir():
                if not doc_dir.is_dir():
                    continue
                
                # Find JSON content file (exclude router_questions.json)
                json_files = [f for f in doc_dir.glob("*.json") 
                             if f.name != "router_questions.json"]
                
                if not json_files:
                    logger.warning(f"No content JSON in {doc_dir}")
                    continue
                
                json_file = json_files[0]
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    # Validate content - check multiple possible content fields
                    has_content = False
                    if content.get('content'):
                        has_content = True
                    elif content.get('content_chunks'):
                        has_content = len(content['content_chunks']) > 0
                    elif content.get('summary') or content.get('text'):
                        has_content = True
                    
                    if not has_content:
                        logger.warning(f"Empty content in {json_file}")
                        continue
                    
                    documents.append({
                        "collection": collection_name,
                        "doc_id": doc_dir.name,
                        "file_path": str(json_file),
                        "file_name": json_file.name,
                        "content": content,
                        "structure": "new"
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading {json_file}: {e}")
        
        logger.info(f"Found {len(documents)} documents in new structure")
        return documents
    
    def scan_old_structure(self) -> List[Dict]:
        """Scan old documents structure for JSON files"""
        logger.info("🔍 Scanning old documents structure...")
        
        documents = []
        json_files = list(self.old_documents_dir.rglob("*.json"))
        
        for json_file in json_files:
            try:
                # Determine collection from path
                relative_path = json_file.relative_to(self.old_documents_dir)
                collection_name = relative_path.parts[0]
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                # Validate content
                if not content.get('content'):
                    logger.warning(f"⚠️ Empty content in {json_file}")
                    continue
                
                documents.append({
                    "collection": collection_name,
                    "doc_id": json_file.stem,
                    "file_path": str(json_file),
                    "file_name": json_file.name,
                    "content": content,
                    "structure": "old"
                })
                
            except Exception as e:
                logger.error(f"❌ Error reading {json_file}: {e}")
        
        logger.info(f"✅ Found {len(documents)} documents in old structure")
        return documents
    
    def build_vectordb(self, force_rebuild: bool = False):
        """Build vector database from available documents"""
        logger.info("🚀 Starting vector database build...")
        
        # Check structure
        structure_type = self.check_structure()
        
        if structure_type == "none":
            logger.error("❌ No document structure found!")
            return False
        
        # Scan documents
        if structure_type == "new":
            documents = self.scan_new_structure()
        else:
            documents = self.scan_old_structure()
        
        if not documents:
            logger.error("❌ No documents found to index!")
            return False
        
        # Group by collection
        collections_data = {}
        for doc in documents:
            collection = doc["collection"]
            if collection not in collections_data:
                collections_data[collection] = []
            collections_data[collection].append(doc)
        
        logger.info(f"📊 Found {len(collections_data)} collections with {len(documents)} total documents")
        
        # Build database
        try:
            from app.services.vector import VectorDBService
            
            # Initialize vector service
            vector_service = VectorDBService()
            
            for collection_name, collection_docs in collections_data.items():
                logger.info(f"🔨 Building collection: {collection_name} ({len(collection_docs)} docs)")
                
                # Prepare documents for indexing
                texts = []
                metadatas = []
                ids = []
                
                for doc in collection_docs:
                    content = doc["content"]
                    
                    # Extract text content - handle multiple content formats
                    text_content = ""
                    
                    # Format 1: Direct content field
                    if isinstance(content.get("content"), str):
                        text_content = content["content"]
                    elif isinstance(content.get("content"), list):
                        text_content = " ".join(str(item) for item in content["content"])
                    
                    # Format 2: Content chunks (legal documents format)
                    elif content.get("content_chunks"):
                        chunks = []
                        for chunk in content["content_chunks"]:
                            if isinstance(chunk, dict) and chunk.get("content"):
                                chunks.append(chunk["content"])
                        text_content = " ".join(chunks)
                    
                    # Format 3: Summary or text fields
                    elif content.get("summary"):
                        text_content = content["summary"]
                    elif content.get("text"):
                        text_content = content["text"]
                    
                    if not text_content.strip():
                        logger.warning(f"⚠️ Empty text content for {doc['file_name']}")
                        continue
                    
                    texts.append(text_content)
                    
                    # Prepare metadata
                    metadata = {
                        "source_file": doc["file_name"],
                        "collection": collection_name,
                        "doc_id": doc["doc_id"],
                        "structure_type": doc["structure"],
                        "file_path": doc["file_path"]
                    }
                    
                    # Add original metadata if available and extract document_title properly
                    if "metadata" in content:
                        metadata.update(content["metadata"])
                        
                        # Ensure document_title is set correctly for router filtering
                        if "title" in content["metadata"]:
                            metadata["document_title"] = content["metadata"]["title"]
                        elif "document_title" in content["metadata"]:
                            metadata["document_title"] = content["metadata"]["document_title"]
                    
                    # Fallback: use filename if no title found
                    if "document_title" not in metadata or not metadata["document_title"]:
                        metadata["document_title"] = doc["file_name"].replace(".json", "")
                    
                    metadatas.append(metadata)
                    ids.append(f"{collection_name}_{doc['doc_id']}")
                
                if not texts:
                    logger.warning(f"⚠️ No valid texts for collection {collection_name}")
                    continue
                
                # Add to vector database
                try:
                    # Clear collection if force rebuild
                    if force_rebuild and vector_service.collection_exists(collection_name):
                        logger.info(f"🧹 Clearing existing collection: {collection_name}")
                        vector_service.clear_collection(collection_name)
                    
                    # Add documents - Use correct format for VectorDBService
                    documents_for_indexing = [
                        {
                            "content": text,
                            "source": {
                                "document_title": metadata.get("document_title", ""),
                                "file_path": metadata.get("file_path", ""),
                                "document_code": metadata.get("code", ""),
                                "section_title": "",
                                "source_reference": "",
                                "chunk_id": doc_id,
                                "chunk_index_num": 0,
                                "document_id": metadata.get("doc_id", ""),
                                "issuing_authority": metadata.get("issuing_authority", ""),
                                "executing_agency": metadata.get("executing_agency", ""),
                                "effective_date": metadata.get("effective_date", "")
                            },
                            "metadata": {
                                "processing_time": metadata.get("processing_time_text", ""),
                                "fee_info": metadata.get("fee_text", ""),
                                "legal_basis": metadata.get("legal_basis_references", [])
                            },
                            "type": "json_document",
                            "keywords": []
                        }
                        for text, metadata, doc_id in zip(texts, metadatas, ids)
                    ]
                    
                    added_count = vector_service.add_documents_to_collection(
                        collection_name=collection_name,
                        documents=documents_for_indexing
                    )
                    
                    logger.info(f"✅ Added {added_count} documents to collection {collection_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error building collection {collection_name}: {e}")
                    continue
            
            logger.info("🎉 Vector database build completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building vector database: {e}")
            return False
    
    def clean_vectordb(self):
        """Clean entire vector database"""
        logger.info("🧹 Cleaning vector database...")
        
        if self.vectordb_dir.exists():
            import shutil
            shutil.rmtree(self.vectordb_dir)
            logger.info("✅ Vector database cleaned")
        else:
            logger.info("📁 Vector database directory not found")
    
    def get_status(self):
        """Get current status"""
        structure_type = self.check_structure()
        
        if structure_type == "new":
            documents = self.scan_new_structure()
        elif structure_type == "old":
            documents = self.scan_old_structure()
        else:
            documents = []
        
        # Group by collection
        collections_summary = {}
        for doc in documents:
            collection = doc["collection"]
            if collection not in collections_summary:
                collections_summary[collection] = 0
            collections_summary[collection] += 1
        
        status = {
            "structure_type": structure_type,
            "total_documents": len(documents),
            "collections": collections_summary,
            "vectordb_exists": self.vectordb_dir.exists()
        }
        
        return status

def main():
    parser = argparse.ArgumentParser(description='Modernized Vector Database Builder')
    parser.add_argument('--force', action='store_true', help='Force rebuild (clear existing)')
    parser.add_argument('--clean', action='store_true', help='Clean vector database')
    parser.add_argument('--status', action='store_true', help='Show current status')
    
    args = parser.parse_args()
    
    builder = ModernizedVectorDBBuilder()
    
    if args.clean:
        builder.clean_vectordb()
        return
    
    if args.status:
        status = builder.get_status()
        print("📊 VECTOR DATABASE STATUS")
        print("=" * 40)
        print(f"Structure Type: {status['structure_type']}")
        print(f"Total Documents: {status['total_documents']}")
        print(f"VectorDB Exists: {status['vectordb_exists']}")
        print(f"Collections:")
        for collection, count in status['collections'].items():
            print(f"  - {collection}: {count} documents")
        return
    
    # Build vector database
    success = builder.build_vectordb(force_rebuild=args.force)
    
    if success:
        logger.info("🎉 Vector database build completed!")
    else:
        logger.error("❌ Vector database build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
