"""
In-Memory Cache Implementation for OCR Microservice
Simple alternative to Redis for development and testing
"""
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

from ..models.schemas import OCRSession, ProcessingStatus

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self):
        self._sessions: Dict[str, OCRSession] = {}
        self._images: Dict[str, bytes] = {}
        self._results: Dict[str, Any] = {}
        
    async def connect(self) -> bool:
        """Connect to cache (no-op for in-memory)"""
        logger.info("In-memory cache initialized")
        return True
        
    async def disconnect(self) -> None:
        """Disconnect from cache (no-op for in-memory)"""
        logger.info("In-memory cache disconnected")
        
    async def is_connected(self) -> bool:
        """Check if cache is connected"""
        return True
        
    # Session operations
    async def store_session(self, session: OCRSession) -> bool:
        """Store session data"""
        self._sessions[session.session_id] = session
        return True
        
    async def get_session(self, session_id: str) -> Optional[OCRSession]:
        """Get session by ID"""
        return self._sessions.get(session_id)
        
    async def update_session(self, session: OCRSession) -> bool:
        """Update existing session"""
        if session.session_id in self._sessions:
            self._sessions[session.session_id] = session
            return True
        return False
        
    async def delete_session(self, session_id: str) -> bool:
        """Delete session by ID"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            # Clean up related images and results
            front_key = f"{session_id}_front"
            back_key = f"{session_id}_back"
            if front_key in self._images:
                del self._images[front_key]
            if back_key in self._images:
                del self._images[back_key]
            if session_id in self._results:
                del self._results[session_id]
            return True
        return False
        
    # Image operations
    async def store_image(self, key: str, image_data: bytes, ttl_seconds: int = 14400) -> bool:
        """Store image data"""
        self._images[key] = image_data
        return True
        
    async def get_image(self, key: str) -> Optional[bytes]:
        """Get image by key"""
        return self._images.get(key)
        
    # Result operations
    async def store_result(self, session_id: str, result: Dict[str, Any], ttl_seconds: int = 14400) -> bool:
        """Store OCR result"""
        self._results[session_id] = result
        return True
        
    async def get_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get OCR result by session ID"""
        return self._results.get(session_id)

    # Cleanup expired sessions
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and their related data"""
        now = datetime.utcnow()
        expired_count = 0
        
        # Find and remove expired sessions
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if session.expires_at < now
        ]
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
            expired_count += 1
            
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")
            
        return expired_count


# Singleton instance
_memory_cache = InMemoryCache()


async def get_cache_manager():
    """Get the cache manager instance"""
    return _memory_cache


async def init_cache() -> bool:
    """Initialize the cache"""
    return await _memory_cache.connect()


async def close_cache() -> None:
    """Close the cache connection"""
    await _memory_cache.disconnect()


async def cleanup_task(interval_seconds: int = 900) -> None:
    """Background task to clean up expired sessions"""
    while True:
        try:
            await _memory_cache.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")
            
        await asyncio.sleep(interval_seconds)
