import os
import logging
from typing import Dict, List, Any
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_json_processor import ImprovedJSONProcessor
from app.services.vectordb_service import VectorDBService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rebuild_vectordb_from_optimized_processor():
    """Rebuild vector database using the optimized JSON processor"""
    try:
        # Initialize processor and vector service
        logger.info("=== Starting Optimized Vector Database Rebuild ===")
        
        processor = ImprovedJSONProcessor()
        vectordb_service = VectorDBService(
            persist_directory="./data/vectordb",
            embedding_model="AITeamVN/Vietnamese_Embedding_v2",
            default_collection_name="default"
        )
        
        # Process all JSON documents
        logger.info("Processing JSON documents...")
        collections_data = processor.process_all_json_documents()
        
        if not collections_data:
            logger.error("No data processed from JSON files")
            return
        
        # Process each collection
        total_chunks_added = 0
        
        for collection_name, chunks in collections_data.items():
            if not chunks:
                logger.warning(f"No chunks for collection {collection_name}")
                continue
                
            logger.info(f"\n=== Processing collection: {collection_name} ===")
            logger.info(f"Adding {len(chunks)} chunks to collection '{collection_name}'")
            
            # Prepare documents for vectordb - match VectorDBService expected format
            vectordb_documents = []
            
            for chunk in chunks:
                # Transform to format expected by VectorDBService
                vectordb_document = {
                    'content': chunk['content'],
                    'metadata': chunk['metadata'],  # fee_info, processing_time, legal_basis, etc.
                    'source': {
                        'file_path': chunk['metadata']['file_path'],
                        'document_title': chunk['metadata']['document_title'],
                        'document_code': chunk['metadata']['document_code'], 
                        'section_title': chunk['metadata']['section_title'],
                        'source_reference': chunk['metadata']['source_reference'],
                        'chunk_id': chunk['metadata']['chunk_id'],
                        'issuing_authority': chunk['metadata']['issuing_authority'],
                        'executing_agency': chunk['metadata']['executing_agency'],
                        'effective_date': chunk['metadata']['effective_date']
                    },
                    'type': chunk['metadata']['type'],
                    'keywords': []  # Simplified for now, will be handled by metadata
                }
                vectordb_documents.append(vectordb_document)
            
            # Add to vector database
            try:
                added_count = vectordb_service.add_documents_to_collection(
                    collection_name=collection_name,
                    documents=vectordb_documents
                )
                
                total_chunks_added += added_count
                logger.info(f"Successfully added {added_count} chunks to collection '{collection_name}'")
                
            except Exception as e:
                logger.error(f"Error adding documents to collection '{collection_name}': {e}")
                continue
        
        # Final summary
        logger.info(f"\n=== Rebuild Complete ===")
        logger.info(f"Total chunks added: {total_chunks_added}")
        
        # Log collection counts
        for collection_name in collections_data.keys():
            try:
                stats = vectordb_service.get_collection_stats(collection_name)
                count = stats.get('document_count', 0)
                logger.info(f"Collection '{collection_name}': {count} documents")
            except Exception as e:
                logger.error(f"Error getting count for collection '{collection_name}': {e}")
        
        logger.info("Vector database rebuild completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during vector database rebuild: {e}")
        raise

if __name__ == "__main__":
    rebuild_vectordb_from_optimized_processor()
