"""
Simple cache manager for OCR Microservice testing
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .config import get_settings
from ..models.schemas import OCRSession

logger = logging.getLogger(__name__)


class SimpleCacheManager:
    """Simple in-memory cache manager for testing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.sessions: Dict[str, OCRSession] = {}
        self.images: Dict[str, bytes] = {}
        
    async def initialize(self):
        """Initialize cache manager"""
        logger.info("Simple cache manager initialized")
        
    async def cleanup(self):
        """Cleanup cache manager"""
        self.sessions.clear()
        self.images.clear()
        logger.info("Simple cache manager cleaned up")
        
    async def store_session(self, session: OCRSession) -> bool:
        """Store session in memory"""
        try:
            self.sessions[session.session_id] = session
            return True
        except Exception as e:
            logger.error(f"Failed to store session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[OCRSession]:
        """Get session from memory"""
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from memory"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    async def store_image(self, session_id: str, side: str, image_data: bytes, format: str) -> str:
        """Store image data in memory"""
        try:
            key = f"{session_id}:{side}"
            self.images[key] = image_data
            return key
        except Exception as e:
            logger.error(f"Failed to store image: {e}")
            raise Exception(f"Image storage failed: {e}")
    
    async def get_image(self, image_key: str) -> Optional[bytes]:
        """Get image data from memory"""
        return self.images.get(image_key)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_type": "in_memory",
            "total_sessions": len(self.sessions),
            "total_images": len(self.images)
        }


# Global cache manager instance
_cache_manager = None


async def get_cache_manager():
    """Get or create global cache manager instance"""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = SimpleCacheManager()
        await _cache_manager.initialize()
    
    return _cache_manager


async def cleanup_cache_manager():
    """Cleanup global cache manager"""
    global _cache_manager
    
    if _cache_manager is not None:
        await _cache_manager.cleanup()
        _cache_manager = None
