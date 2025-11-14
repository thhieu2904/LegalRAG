"""
Vector Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "vector-service"
    SERVICE_PORT: int = 8003
    
    # PostgreSQL with pgvector
    POSTGRES_HOST: str = "postgres-vector"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "legalrag"
    POSTGRES_PASSWORD: str = "legalrag123"
    POSTGRES_DB: str = "legalrag"
    
    # Connection pool
    DB_POOL_SIZE: int = 5
    DB_POOL_MAX_OVERFLOW: int = 10
    
    # Vector search
    EMBEDDING_DIMENSION: int = 384  # sentence-transformers default
    VECTOR_SIMILARITY_THRESHOLD: float = 0.7
    TOP_K_RESULTS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
