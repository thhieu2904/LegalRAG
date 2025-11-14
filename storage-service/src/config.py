"""
Storage Service Configuration
All configuration loaded from .env file
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict


class Settings(BaseSettings):
    """Application settings - loaded from .env"""
    
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    # ============= SERVICE INFO =============
    SERVICE_NAME: str = "storage-service"
    SERVICE_PORT: int = 8001
    
    # ============= MINIO CONFIGURATION =============
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "legal-documents"
    
    # ============= SERVICE URLS (for inter-service communication) =============
    VECTOR_SERVICE_URL: str = "http://vector-service:8003"
    EMBEDDING_SERVICE_URL: str = "http://embedding-service:8004"
    
    # ============= FILE UPLOAD LIMITS =============
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB for legal documents
    
    # ============= CORS =============
    CORS_ORIGINS: str = "*"  # Will be split by comma if needed
    
    @field_validator("MINIO_SECURE", mode="before")
    @classmethod
    def parse_minio_secure(cls, v):
        """Convert string 'false'/'true' to boolean"""
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


settings = Settings()
