import logging
import chromadb
from chromadb.config import Settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_vectordb():
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./data/vectordb",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # List all collections
        collections = client.list_collections()
        logger.info(f"Found {len(collections)} collections:")
        
        for collection in collections:
            logger.info(f"\nCollection: {collection.name}")
            count = collection.count()
            logger.info(f"Number of documents: {count}")
            
            if count > 0:
                # Get first few documents to inspect
                results = collection.get(
                    limit=3,
                    include=['documents', 'metadatas', 'embeddings']
                )
                
                logger.info(f"First few documents:")
                if results and results.get('documents') is not None:
                    documents = results['documents']
                    if documents:
                        ids = results.get('ids', [])
                        metadatas = results.get('metadatas', [])
                        embeddings = results.get('embeddings', [])
                        
                        for i, doc in enumerate(documents[:3]):
                            logger.info(f"Doc {i+1}:")
                            
                            logger.info(f"  ID: {ids[i] if ids and i < len(ids) else 'N/A'}")
                            logger.info(f"  Content length: {len(doc)}")
                            logger.info(f"  Content preview: {doc[:200]}...")
                            logger.info(f"  Metadata: {metadatas[i] if metadatas and i < len(metadatas) else 'N/A'}")
                            logger.info(f"  Has embedding: {'Yes' if embeddings and i < len(embeddings) and embeddings[i] else 'No'}")
                            if embeddings and i < len(embeddings) and embeddings[i]:
                                logger.info(f"  Embedding dimension: {len(embeddings[i])}")
                    else:
                        logger.info("  Documents list is empty")
                else:
                    logger.info("  No documents found")
                
    except Exception as e:
        logger.error(f"Error debugging vector database: {e}")
        raise

if __name__ == "__main__":
    debug_vectordb()
