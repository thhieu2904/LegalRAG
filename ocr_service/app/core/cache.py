"""
Redis Cache Management for OCR Microservice
Handles session data, image storage, and caching
"""
import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4

import redis.asyncio as redis

from .config import get_settings
from ..models.schemas import OCRSession, ProcessingStatus, CCCDSide


logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base cache error"""
    pass


class RedisManager:
    """Redis connection and operations manager"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.settings = get_settings()
        
    def _get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.settings.redis_password:
            return f"redis://:{self.settings.redis_password}@{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}"
        return f"redis://{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}"
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            redis_url = get_redis_url()
            logger.info(f"Connecting to Redis: {redis_url}")
            
            self.redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=settings.redis_socket_timeout,
                max_connections=settings.redis_connection_pool_max_connections
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("✅ Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("✅ Redis connection closed")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


class OCRCacheManager:
    """Cache manager for OCR operations"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        
        # Cache key prefixes
        self.SESSION_PREFIX = "ocr:session:"
        self.IMAGE_PREFIX = "ocr:image:"
        self.RESULT_PREFIX = "ocr:result:"
        self.LOCK_PREFIX = "ocr:lock:"
        self.STATS_PREFIX = "ocr:stats:"
    
    @property
    def redis(self):
        return self.redis_manager.redis
        
    async def create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new OCR session"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=settings.session_expiry_hours)
        
        session = {
            "session_id": session_id,
            "front_image_key": None,
            "back_image_key": None,
            "extracted_data": None,
            "confidence_scores": None,
            "processing_status": "pending",
            "error_message": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "processing_time": None
        }
        
        # Store session in Redis
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = json.dumps(session, default=str)
        
        expiry_seconds = settings.session_expiry_hours * 3600
        await self.redis.setex(session_key, expiry_seconds, session_data)
        
        logger.info(f"📝 Created new OCR session: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get OCR session by ID"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = await self.redis.get(session_key)
        
        if not session_data:
            logger.warning(f"Session {session_id} not found")
            return None
            
        try:
            return json.loads(session_data)
        except Exception as e:
            logger.error(f"Failed to deserialize session {session_id}: {str(e)}")
            return None
    
    async def update_session(self, session: Dict[str, Any]) -> bool:
        """Update OCR session"""
        session["updated_at"] = datetime.utcnow().isoformat()
        
        session_key = f"{self.SESSION_PREFIX}{session['session_id']}"
        session_data = json.dumps(session, default=str)
        
        # Update expiry time
        expiry_seconds = settings.session_expiry_hours * 3600
        result = await self.redis.setex(session_key, expiry_seconds, session_data)
        
        return bool(result)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete OCR session and associated data"""
        # Get session to find associated images
        session = await self.get_session(session_id)
        
        # Delete associated images
        if session:
            if session.get("front_image_key"):
                await self.delete_image(session["front_image_key"])
            if session.get("back_image_key"):
                await self.delete_image(session["back_image_key"])
        
        # Delete session
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        result = await self.redis.delete(session_key)
        
        # Delete result cache
        result_key = f"{self.RESULT_PREFIX}{session_id}"
        await self.redis.delete(result_key)
        
        # Release any locks
        await self.release_lock(session_id)
        
        logger.info(f"🗑️ Deleted OCR session: {session_id}")
        return bool(result)
    
    async def store_image(self, session_id: str, side: str, image_data: bytes) -> str:
        """Store image data in Redis"""
        image_key = f"{self.IMAGE_PREFIX}{session_id}:{side}"
        
        # Encode image as base64 for storage
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        expiry_seconds = settings.session_expiry_hours * 3600
        await self.redis.setex(image_key, expiry_seconds, image_b64)
        
        logger.info(f"📸 Stored {len(image_data)} bytes image for session {session_id}, side {side}")
        return image_key
    
    async def get_image(self, image_key: str) -> Optional[bytes]:
        """Get image data from Redis"""
        image_b64 = await self.redis.get(image_key)
        
        if not image_b64:
            logger.warning(f"Image {image_key} not found")
            return None
            
        try:
            return base64.b64decode(image_b64.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decode image {image_key}: {str(e)}")
            return None
    
    async def delete_image(self, image_key: str) -> bool:
        """Delete image from Redis"""
        result = await self.redis.delete(image_key)
        if result:
            logger.info(f"🗑️ Deleted image: {image_key}")
        return bool(result)
    
    async def cache_ocr_result(self, session_id: str, result_data: Dict[str, Any]) -> bool:
        """Cache OCR processing result"""
        result_key = f"{self.RESULT_PREFIX}{session_id}"
        result_json = json.dumps(result_data, default=str)
        
        expiry_seconds = settings.cache_ttl_seconds
        result = await self.redis.setex(result_key, expiry_seconds, result_json)
        
        logger.info(f"💾 Cached OCR result for session {session_id}")
        return bool(result)
    
    async def get_cached_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached OCR result"""
        result_key = f"{self.RESULT_PREFIX}{session_id}"
        result_data = await self.redis.get(result_key)
        
        if not result_data:
            return None
            
        try:
            return json.loads(result_data)
        except Exception as e:
            logger.error(f"Failed to deserialize cached result for {session_id}: {str(e)}")
            return None
    
    async def acquire_lock(self, session_id: str, timeout: int = 60) -> bool:
        """Acquire processing lock for session"""
        lock_key = f"{self.LOCK_PREFIX}{session_id}"
        
        # Try to set lock with expiry
        result = await self.redis.set(lock_key, "locked", nx=True, ex=timeout)
        if result:
            logger.info(f"🔒 Acquired lock for session {session_id}")
        return bool(result)
    
    async def release_lock(self, session_id: str) -> bool:
        """Release processing lock for session"""
        lock_key = f"{self.LOCK_PREFIX}{session_id}"
        result = await self.redis.delete(lock_key)
        if result:
            logger.info(f"🔓 Released lock for session {session_id}")
        return bool(result)
    
    async def is_locked(self, session_id: str) -> bool:
        """Check if session is locked for processing"""
        lock_key = f"{self.LOCK_PREFIX}{session_id}"
        lock_status = await self.redis.get(lock_key)
        return lock_status is not None
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        pattern = f"{self.SESSION_PREFIX}*"
        keys = await self.redis.keys(pattern)
        
        session_ids = []
        for key in keys:
            session_id = key.replace(self.SESSION_PREFIX, "")
            session_ids.append(session_id)
            
        return session_ids
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and associated data"""
        cleaned_count = 0
        active_sessions = await self.get_active_sessions()
        
        current_time = datetime.utcnow()
        
        for session_id in active_sessions:
            session = await self.get_session(session_id)
            
            if not session:
                continue
                
            # Check if session is expired
            try:
                expires_at = datetime.fromisoformat(session["expires_at"])
                if current_time > expires_at:
                    await self.delete_session(session_id)
                    cleaned_count += 1
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid session data for {session_id}: {e}")
                await self.delete_session(session_id)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = await self.redis.info()
            
            # Count different types of keys
            session_keys = await self.redis.keys(f"{self.SESSION_PREFIX}*")
            image_keys = await self.redis.keys(f"{self.IMAGE_PREFIX}*")
            result_keys = await self.redis.keys(f"{self.RESULT_PREFIX}*")
            lock_keys = await self.redis.keys(f"{self.LOCK_PREFIX}*")
            
            return {
                "redis_info": {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                },
                "ocr_cache_stats": {
                    "active_sessions": len(session_keys),
                    "stored_images": len(image_keys),
                    "cached_results": len(result_keys),
                    "active_locks": len(lock_keys),
                    "cache_hit_ratio": "N/A",  # TODO: Implement hit ratio tracking
                }
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {"error": str(e)}


# Global instances
redis_manager = RedisManager()
cache_manager = OCRCacheManager(redis_manager)


async def init_cache():
    """Initialize cache connection"""
    logger.info("🔧 Initializing Redis cache...")
    await redis_manager.connect()
    logger.info("✅ Redis cache initialized")


async def close_cache():
    """Close cache connection"""
    logger.info("🔄 Closing Redis cache...")
    await redis_manager.disconnect()


def get_cache_manager() -> OCRCacheManager:
    """Get the global cache manager instance"""
    return cache_manager


# Background cleanup task
async def cleanup_task():
    """Background task for cleaning up expired sessions"""
    logger.info("🧹 Starting cleanup task...")
    
    while True:
        try:
            await asyncio.sleep(settings.cleanup_interval_minutes * 60)
            await cache_manager.cleanup_expired_sessions()
        except asyncio.CancelledError:
            logger.info("🛑 Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Error in cleanup task: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
