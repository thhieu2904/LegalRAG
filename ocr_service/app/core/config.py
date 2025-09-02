"""
Configuration for OCR Microservice
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """OCR Microservice Settings"""
    
    # Service Configuration
    app_name: str = "CCCD OCR Microservice"
    app_version: str = "1.0.0"
    SERVICE_VERSION: str = "1.0.0"  # Alias for compatibility
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8001  # Different port from main backend
    
    # For compatibility
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True
    
    # CORS Configuration
    allowed_origins: List[str] = [
        "http://localhost:3000",  # Frontend dev
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Main backend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    # For compatibility
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 2  # Different DB from main backend
    redis_password: str = ""
    redis_ssl: bool = False
    redis_decode_responses: bool = True
    redis_socket_timeout: int = 5
    redis_connection_pool_max_connections: int = 50
    
    # Uppercase aliases for compatibility
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: str = ""
    
    # Session Management
    session_expiry_hours: int = 2
    SESSION_EXPIRY_HOURS: int = 2
    image_cache_ttl_hours: int = 4
    IMAGE_CACHE_TTL_HOURS: int = 4
    
    # OCR Configuration
    vietocr_config: str = "vgg_transformer"  # vgg_transformer, vgg_seq2seq
    vietocr_device: str = "cpu"  # Force CPU usage
    ocr_confidence_threshold: float = 0.7
    text_detection_confidence: float = 0.8
    
    # Session Management
    session_expiry_hours: int = 2
    max_sessions_per_ip: int = 10
    cleanup_interval_minutes: int = 15
    
    # Image Processing
    max_image_size_mb: int = 10
    allowed_image_formats: List[str] = ["jpeg", "jpg", "png", "webp"]
    image_quality: int = 85
    max_image_dimensions: int = 4096
    min_image_dimensions: int = 100
    
    # Uppercase aliases
    MAX_IMAGE_SIZE_MB: int = 10
    TORCH_CPU_THREADS: int = 4
    
    # Processing Configuration
    max_processing_time_seconds: int = 60
    max_concurrent_processes: int = 5
    enable_preprocessing: bool = True
    enable_postprocessing: bool = True
    
    # Security Configuration
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 20
    max_request_size_mb: int = 15
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_access_logs: bool = True
    log_file_path: str = ""
    
    # Development Configuration
    save_debug_images: bool = False
    debug_image_path: str = "./debug_images"
    enable_detailed_errors: bool = True
    
    # Performance Configuration
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    preload_models: bool = True
    
    # Integration Configuration  
    main_backend_url: str = "http://localhost:8000"
    webhook_enabled: bool = False
    webhook_url: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = "OCR_"


# Global settings instance
settings = Settings()


def get_redis_url() -> str:
    """Get Redis connection URL"""
    auth_part = f":{settings.redis_password}@" if settings.redis_password else ""
    protocol = "rediss" if settings.redis_ssl else "redis"
    return f"{protocol}://{auth_part}{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def get_vietocr_config() -> dict:
    """Get VietOCR configuration optimized for CPU"""
    return {
        "config": settings.vietocr_config,
        "device": "cpu",  # Force CPU usage
        "confidence_threshold": settings.ocr_confidence_threshold,
        "workers": 1,  # Single worker for CPU
        "batch_size": 1,  # Process one image at a time
    }


def get_image_processing_config() -> dict:
    """Get image processing configuration"""
    return {
        "max_size_mb": settings.max_image_size_mb,
        "allowed_formats": settings.allowed_image_formats,
        "quality": settings.image_quality,
        "max_dimensions": settings.max_image_dimensions,
        "min_dimensions": settings.min_image_dimensions,
        "enable_preprocessing": settings.enable_preprocessing,
        "enable_postprocessing": settings.enable_postprocessing,
    }


def get_performance_config() -> dict:
    """Get performance configuration for CPU optimization"""
    return {
        "max_concurrent_processes": settings.max_concurrent_processes,
        "max_processing_time": settings.max_processing_time_seconds,
        "cache_enabled": settings.enable_caching,
        "cache_ttl": settings.cache_ttl_seconds,
        "preload_models": settings.preload_models,
        "cpu_optimized": True,
    }


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get or create global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
