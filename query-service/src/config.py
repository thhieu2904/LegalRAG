"""
Query Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "query-service"
    SERVICE_PORT: int = 8005
    
    # Service URLs
    EMBEDDING_SERVICE_URL: str = "http://embedding-service:8004"
    VECTOR_SERVICE_URL: str = "http://vector-service:8003"
    LLM_SERVICE_URL: str = "http://llm-service:8006"
    
    # Search parameters
    TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
