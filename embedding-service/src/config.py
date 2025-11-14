"""
Embedding Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "embedding-service"
    SERVICE_PORT: int = 8004
    
    # Model configuration
    MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    MODEL_CACHE_DIR: str = "/app/models"
    DEVICE: str = "cpu"  # cpu or cuda
    
    # Embedding configuration
    BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 384
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
