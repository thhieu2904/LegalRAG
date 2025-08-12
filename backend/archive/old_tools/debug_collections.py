import logging
from app.services.vectordb_service import VectorDBService
import chromadb

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_collections():
    # Initialize VectorDB service
    vectordb = VectorDBService(
        persist_directory="./data/vectordb",
        embedding_model="AITeamVN/Vietnamese_Embedding_v2",
        default_collection_name="default"
    )
    
    # Check collections info
    collections = ["ho_tich_cap_xa", "chung_thuc", "nuoi_con_nuoi"]
    
    for collection_name in collections:
        logger.info(f"\n{'='*50}")
        logger.info(f"Debugging collection: {collection_name}")
        logger.info(f"{'='*50}")
        
        try:
            # Get collection
            collection = vectordb._get_or_create_collection(collection_name)
            
            # Get collection info
            count = collection.count()
            logger.info(f"Collection {collection_name} contains {count} documents")
            
            if count > 0:
                # Get some sample documents
                results = collection.get(limit=3, include=['documents', 'metadatas'])
                
                logger.info(f"Sample documents from {collection_name}:")
                if results['documents'] and len(results['documents']) > 0:
                    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'] or [])):
                        if i < min(len(results['documents']), len(results.get('metadatas', [])) or 0):
                            logger.info(f"\nSample {i+1}:")
                            logger.info(f"  Document Title: {metadata.get('document_title', 'N/A') if metadata else 'N/A'}")
                            logger.info(f"  Source: {metadata.get('source', 'N/A') if metadata else 'N/A'}")
                            logger.info(f"  Content preview: {doc[:150] if doc else 'No content'}...")
                else:
                    logger.info("No documents found in sample")
                
                # Test raw search without threshold
                logger.info(f"\n--- Testing raw search in {collection_name} ---")
                query = "đăng ký"
                if collection_name == "chung_thuc":
                    query = "chứng thực"
                elif collection_name == "nuoi_con_nuoi":
                    query = "nuôi con"
                
                # Generate query embedding
                if vectordb.embedding_model:
                    query_embedding = vectordb.embedding_model.encode([query]).tolist()
                    
                    # Raw ChromaDB query
                    raw_results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=3,
                        include=['documents', 'metadatas', 'distances']
                    )
                    
                    logger.info(f"Raw query '{query}' results:")
                    if (raw_results.get('documents') and 
                        raw_results['documents'] and 
                        len(raw_results['documents']) > 0 and 
                        raw_results['documents'][0]):
                        
                        for i, (doc, metadata, distance) in enumerate(zip(
                            raw_results['documents'][0], 
                            raw_results['metadatas'][0] or [], 
                            raw_results['distances'][0] or []
                        )):
                            similarity = 1 - distance  # Convert distance to similarity
                            logger.info(f"\nRaw Result {i+1}:")
                            logger.info(f"  Distance: {distance:.4f}")
                            logger.info(f"  Similarity: {similarity:.4f}")
                            logger.info(f"  Title: {metadata.get('document_title', 'N/A') if metadata else 'N/A'}")
                            logger.info(f"  Content: {doc[:100] if doc else 'N/A'}...")
                    else:
                        logger.info("No raw results found")
                else:
                    logger.error("Embedding model not loaded")
            else:
                logger.warning(f"Collection {collection_name} is empty!")
                
        except Exception as e:
            logger.error(f"Error debugging collection {collection_name}: {str(e)}")

if __name__ == "__main__":
    debug_collections()
