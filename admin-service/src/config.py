"""
Admin Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "admin-service"
    SERVICE_PORT: int = 8007
    
    # Database
    POSTGRES_HOST: str = "postgres-vector"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "legalrag"
    POSTGRES_PASSWORD: str = "legalrag123"
    POSTGRES_DB: str = "legalrag"
    
    # Service URLs
    STORAGE_SERVICE_URL: str = "http://storage-service:8001"
    EMBEDDING_SERVICE_URL: str = "http://embedding-service:8004"
    VECTOR_SERVICE_URL: str = "http://vector-service:8003"
    
    # Chunking
    CHUNK_SIZE: int = 500  # characters per chunk
    CHUNK_OVERLAP: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
