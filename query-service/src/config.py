"""
Query Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "query-service"
    SERVICE_PORT: int = 8002  # Public User-facing RAG API
    
    # Service URLs (updated port architecture)
    EMBEDDING_SERVICE_URL: str = "http://embedding-service:8011"
    VECTOR_SERVICE_URL: str = "http://vector-service:8012"
    RERANK_SERVICE_URL: str = "http://rerank-service:8013"
    LLM_SERVICE_URL: str = "http://llm-service:8006"
    STORAGE_SERVICE_URL: str = "http://storage-service:8010"
    
    # Search parameters
    TOP_K: int = 10
    
    # Confidence thresholds
    SIMILARITY_THRESHOLD: float = 0.5  # Minimum similarity to return results
    LOW_CONFIDENCE_THRESHOLD: float = 0.5  # Below this: show document grouping
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.65  # Below this: may need clarification
    HIGH_CONFIDENCE_THRESHOLD: float = 0.8  # Above this: auto-route
    
    # Reranking parameters
    RERANK_TOP_K: int = 5  # Number of chunks to rerank
    RERANK_THRESHOLD: float = 0.6  # Minimum rerank score
    RERANK_SAME_DOCUMENT_ONLY: bool = True  # Only return chunks from same document
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
