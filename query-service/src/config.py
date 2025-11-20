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
    LLM_SERVICE_URL: str = "http://llm-service:8006"
    STORAGE_SERVICE_URL: str = "http://storage-service:8010"
    
    # Search parameters
    TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
