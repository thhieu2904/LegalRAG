"""
Embedding Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "embedding-service"
    SERVICE_PORT: int = 8011  # 801X series: Internal microservices
    
    # Model configuration - Vietnamese Document Embedding
    MODEL_NAME: str = "dangvantuan/vietnamese-document-embedding"
    MODEL_CACHE_DIR: str = "/app/models"
    DEVICE: str = "cpu"  # cpu or cuda
    MAX_SEQ_LENGTH: int = 8192  # Model supports up to 8192 tokens
    
    # Embedding configuration
    BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 768  # Updated for Vietnamese model
    
    # GPU Swap Mode - for low VRAM environments (6-8GB)
    # When true: Force CPU for embedding to save VRAM for LLM+Rerank
    # When false: Use configured DEVICE (GPU if available)
    GPU_SWAP_MODE: bool = False
    
    # Chunking configuration (for legal documents)
    CHUNK_SIZE: int = 600  # tokens per chunk (well below 8192 limit)
    CHUNK_OVERLAP: int = 100  # token overlap between chunks
    
    # Authentication
    ADMIN_API_KEY: str = "admin-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
