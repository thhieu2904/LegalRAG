"""
LLM Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    SERVICE_NAME: str = "llm-service"
    SERVICE_PORT: int = 8006
    
    # Model configuration
    MODEL_NAME: str = "google/gemma-2-9b-it"  # or meta-llama/Llama-3.1-8B-Instruct
    MODEL_CACHE_DIR: str = "/app/models"
    DEVICE: str = "cuda"  # requires GPU
    
    # Generation parameters
    MAX_LENGTH: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    TOP_K: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
