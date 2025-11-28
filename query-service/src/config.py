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
    RERANK_TOP_K: int = 10  # Number of chunks to get from rerank
    RERANK_THRESHOLD: float = 0.6  # Minimum rerank score
    
    # PostgreSQL for document metadata
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "legalrag"
    POSTGRES_PASSWORD: str = "legalrag"
    POSTGRES_DB: str = "legalrag"
    
    # Clarification thresholds (Smart clarification based on document score gap)
    CLARIFICATION_THRESHOLD: float = 0.7  # Below this: always clarify
    SCORE_GAP_THRESHOLD: float = 0.1  # If gap between top-1 and top-2 doc < this: clarify
    
    # Heuristics
    SPECIFIC_KEYWORDS: list = [
        "nước ngoài", "lưu động", "quá hạn", "lại", "thay đổi", 
        "cải chính", "bổ sung", "xác định lại", "nhận cha mẹ con"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
