"""
Form Service Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service config
    SERVICE_NAME: str = "form-service"
    SERVICE_PORT: int = 8015
    SERVICE_HOST: str = "0.0.0.0"
    
    # External service URLs
    STORAGE_SERVICE_URL: str = "http://storage-service:8010"
    
    # Request timeouts
    STORAGE_TIMEOUT: int = 30
    
    # CORS configuration
    CORS_ORIGINS: str = "*"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
