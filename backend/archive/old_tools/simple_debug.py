import logging
from app.services.vectordb_service import VectorDBService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_debug():
    try:
        # Initialize VectorDB service
        vectordb = VectorDBService(
            persist_directory="./data/vectordb",
            embedding_model="AITeamVN/Vietnamese_Embedding_v2",
            default_collection_name="default"
        )
        
        # Test simple search with lower threshold
        collections = ["ho_tich_cap_xa", "chung_thuc", "nuoi_con_nuoi"]
        
        for collection_name in collections:
            logger.info(f"\n=== Testing {collection_name} ===")
            
            # Get collection count
            try:
                collection = vectordb._get_or_create_collection(collection_name)
                count = collection.count()
                logger.info(f"Collection has {count} documents")
                
                if count > 0:
                    # Try a simple search with very low threshold
                    results = vectordb.search_in_collection(
                        collection_name=collection_name,
                        query="khai sinh" if collection_name == "ho_tich_cap_xa" else "chứng thực" if collection_name == "chung_thuc" else "nuôi con",
                        top_k=5,
                        similarity_threshold=0.0  # No threshold
                    )
                    
                    logger.info(f"Found {len(results)} results with no threshold")
                    
                    for i, result in enumerate(results[:3]):
                        logger.info(f"Result {i+1}: Similarity={result['similarity']:.4f}, Title={result['metadata'].get('document_title', 'N/A')[:50]}...")
                        
            except Exception as e:
                logger.error(f"Error with collection {collection_name}: {str(e)}")
                
    except Exception as e:
        logger.error(f"General error: {str(e)}")

if __name__ == "__main__":
    simple_debug()
