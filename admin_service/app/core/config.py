"""
Admin Service Configuration
===========================

Configuration settings for the admin service.
"""

import os
from pathlib import Path

class AdminConfig:
    """Configuration settings for Admin Service"""
    
    # Service settings
    SERVICE_NAME = "LegalRAG Admin Service"
    VERSION = "1.0.0"
    
    # Server settings
    HOST = os.getenv("ADMIN_HOST", "0.0.0.0")
    PORT = int(os.getenv("ADMIN_PORT", "8001"))
    
    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:3000",   # React dev
        "http://localhost:5173",   # Vite dev
        "http://localhost:8080",   # Production
    ]
    
    # Path settings (managed by PathConfig)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "auto")  # auto, docker, local
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_environment_info(cls):
        """Get environment information"""
        return {
            "service": cls.SERVICE_NAME,
            "version": cls.VERSION,
            "host": cls.HOST,
            "port": cls.PORT,
            "environment": cls.ENVIRONMENT
        }