"""
OCR Service Implementation
Main service layer for OCR processing orchestration
"""
import asyncio
import logging
import base64
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image
import io

# Switch from Redis to in-memory cache
from ..core.memory_cache import get_cache_manager
from ..models.schemas import (
    OCRSession, CCCDExtractedData, ConfidenceScores, 
    ProcessingStatus, CCCDSide
)
from .ocr_engine import get_ocr_engine


logger = logging.getLogger(__name__)


class OCRServiceError(Exception):
    """Base OCR service exception"""
    pass


class SessionNotFoundError(OCRServiceError):
    """Session not found error"""
    pass


class ImageProcessingError(OCRServiceError):
    """Image processing error"""
    pass


class OCRProcessingService:
    """Main OCR processing service"""
    
    def __init__(self):
        self.cache_manager = None
        self.ocr_engine = None
        self._processing_tasks = {}  # Track ongoing processing tasks
        self._stats = {
            'sessions_created': 0,
            'images_uploaded': 0,
            'processing_requests': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_processing_time': 0.0
        }
    
    async def initialize(self):
        """Initialize service dependencies"""
        try:
            self.cache_manager = await get_cache_manager()
            self.ocr_engine = await get_ocr_engine()
            logger.info("OCR processing service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OCR service: {str(e)}")
            raise
    
    async def create_session(self, session_id: Optional[str] = None, expires_in_hours: int = 2) -> OCRSession:
        """Create a new OCR processing session"""
        if session_id is None:
            session_id = str(uuid4())
        
        # Check if session already exists
        existing_session = await self.cache_manager.get_session(session_id)
        if existing_session:
            raise OCRServiceError(f"Session {session_id} already exists")
        
        # Create new session
        now = datetime.utcnow()
        session = OCRSession(
            session_id=session_id,
            processing_status=ProcessingStatus.PENDING,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=expires_in_hours)
        )
        
        # Store session in cache
        await self.cache_manager.store_session(session)
        
        self._stats['sessions_created'] += 1
        logger.info(f"Created OCR session: {session_id}")
        
        return session
    
    async def upload_image(
        self, 
        session_id: str, 
        side: CCCDSide, 
        image_data: str,
        image_format: str = "jpeg"
    ) -> Tuple[str, int]:
        """Upload and store image for OCR processing"""
        
        # Get or create session
        session = await self.cache_manager.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image_size = len(image_bytes)
            
            # Validate image
            image_array = self._decode_image(image_bytes)
            
            # Store image in cache
            image_key = await self.cache_manager.store_image(session_id, side, image_bytes, image_format)
            
            # Update session
            if side == CCCDSide.FRONT:
                session.front_image_key = image_key
            else:
                session.back_image_key = image_key
            
            session.updated_at = datetime.utcnow()
            await self.cache_manager.store_session(session)
            
            self._stats['images_uploaded'] += 1
            logger.info(f"Uploaded {side} image for session {session_id}: {image_size} bytes")
            
            return image_key, image_size
            
        except Exception as e:
            logger.error(f"Failed to upload image for session {session_id}: {str(e)}")
            raise ImageProcessingError(f"Image upload failed: {str(e)}")
    
    def _decode_image(self, image_bytes: bytes) -> np.ndarray:
        """Decode image bytes to numpy array"""
        try:
            # Try PIL first
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(pil_image)
            
            # Convert RGB to BGR for OpenCV compatibility
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return image_array
            
        except Exception as e:
            logger.error(f"Failed to decode image: {str(e)}")
            raise ImageProcessingError(f"Invalid image format: {str(e)}")
    
    async def process_session(
        self, 
        session_id: str, 
        process_both_sides: bool = True, 
        force_reprocess: bool = False
    ) -> OCRSession:
        """Process OCR for a session"""
        
        # Get session
        session = await self.cache_manager.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Check if already processing
        if session_id in self._processing_tasks:
            logger.warning(f"Session {session_id} already being processed")
            return session
        
        # Check if already processed and not forcing reprocess
        if not force_reprocess and session.processing_status == ProcessingStatus.COMPLETED:
            logger.info(f"Session {session_id} already processed")
            return session
        
        # Validate images availability
        if not session.front_image_key:
            raise OCRServiceError("Front image not uploaded")
        
        if process_both_sides and not session.back_image_key:
            raise OCRServiceError("Back image required but not uploaded")
        
        # Update session status
        session.processing_status = ProcessingStatus.PROCESSING
        session.updated_at = datetime.utcnow()
        await self.cache_manager.store_session(session)
        
        # Start processing task
        task = asyncio.create_task(self._process_session_async(session, process_both_sides))
        self._processing_tasks[session_id] = task
        
        self._stats['processing_requests'] += 1
        logger.info(f"Started OCR processing for session {session_id}")
        
        return session
    
    async def _process_session_async(self, session: OCRSession, process_both_sides: bool):
        """Async OCR processing task"""
        session_id = session.session_id
        start_time = time.time()
        
        try:
            # Load images
            front_image = await self._load_image(session.front_image_key)
            back_image = None
            
            if process_both_sides and session.back_image_key:
                back_image = await self._load_image(session.back_image_key)
            
            # Process with OCR engine
            if back_image is not None:
                extracted_data, confidence_scores = await self.ocr_engine.process_both_sides(front_image, back_image)
            else:
                extracted_data, confidence_scores, _ = await self.ocr_engine.process_cccd_image(front_image, CCCDSide.FRONT)
            
            # Update session with results
            session.extracted_data = extracted_data
            session.confidence_scores = confidence_scores
            session.processing_status = ProcessingStatus.COMPLETED
            session.processing_time = time.time() - start_time
            session.updated_at = datetime.utcnow()
            
            await self.cache_manager.store_session(session)
            
            self._stats['successful_extractions'] += 1
            self._stats['total_processing_time'] += session.processing_time
            
            logger.info(f"OCR processing completed for session {session_id} in {session.processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"OCR processing failed for session {session_id}: {str(e)}")
            
            # Update session with error
            session.processing_status = ProcessingStatus.FAILED
            session.error_message = str(e)
            session.processing_time = time.time() - start_time
            session.updated_at = datetime.utcnow()
            
            await self.cache_manager.store_session(session)
            
            self._stats['failed_extractions'] += 1
            
        finally:
            # Remove from processing tasks
            if session_id in self._processing_tasks:
                del self._processing_tasks[session_id]
    
    async def _load_image(self, image_key: str) -> np.ndarray:
        """Load image from cache"""
        image_data = await self.cache_manager.get_image(image_key)
        if not image_data:
            raise ImageProcessingError(f"Image not found: {image_key}")
        
        return self._decode_image(image_data)
    
    async def get_session_status(self, session_id: str) -> OCRSession:
        """Get current session status"""
        session = await self.cache_manager.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        return session
    
    async def get_session_results(self, session_id: str) -> OCRSession:
        """Get session results"""
        session = await self.get_session_status(session_id)
        
        # Check if processing is complete
        if session.processing_status not in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            logger.info(f"Session {session_id} not ready - status: {session.processing_status}")
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and associated data"""
        try:
            # Cancel processing task if running
            if session_id in self._processing_tasks:
                task = self._processing_tasks[session_id]
                task.cancel()
                del self._processing_tasks[session_id]
            
            # Delete from cache
            success = await self.cache_manager.delete_session(session_id)
            
            if success:
                logger.info(f"Deleted session: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions"""
        try:
            count = await self.cache_manager.cleanup_expired_sessions()
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0
    
    def get_processing_status(self, session_id: str) -> Optional[ProcessingStatus]:
        """Get processing status for session"""
        if session_id in self._processing_tasks:
            task = self._processing_tasks[session_id]
            if task.done():
                return ProcessingStatus.COMPLETED
            else:
                return ProcessingStatus.PROCESSING
        return None
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        cache_stats = await self.cache_manager.get_cache_stats()
        ocr_stats = self.ocr_engine.get_stats()
        
        return {
            'service_stats': self._stats,
            'cache_stats': cache_stats,
            'ocr_engine_stats': ocr_stats,
            'active_processing_sessions': len(self._processing_tasks),
            'processing_sessions': list(self._processing_tasks.keys())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'service': 'healthy',
            'cache_connected': False,
            'ocr_engine_loaded': False,
            'timestamp': datetime.utcnow()
        }
        
        try:
            # Check cache connection
            if self.cache_manager:
                cache_stats = await self.cache_manager.get_cache_stats()
                health_status['cache_connected'] = True
            
            # Check OCR engine
            if self.ocr_engine and self.ocr_engine.is_loaded:
                health_status['ocr_engine_loaded'] = True
            
            # Overall health
            if health_status['cache_connected'] and health_status['ocr_engine_loaded']:
                health_status['service'] = 'healthy'
            else:
                health_status['service'] = 'degraded'
                
        except Exception as e:
            health_status['service'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    async def cleanup(self):
        """Cleanup service resources"""
        try:
            # Cancel all processing tasks
            for task in self._processing_tasks.values():
                task.cancel()
            
            self._processing_tasks.clear()
            
            # Cleanup cache manager
            if self.cache_manager:
                await self.cache_manager.cleanup()
            
            logger.info("OCR processing service cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup OCR service: {str(e)}")


# Global service instance
_ocr_service = None


async def get_ocr_service() -> OCRProcessingService:
    """Get or create global OCR service instance"""
    global _ocr_service
    
    if _ocr_service is None:
        _ocr_service = OCRProcessingService()
        await _ocr_service.initialize()
    
    return _ocr_service


async def cleanup_ocr_service():
    """Cleanup global OCR service"""
    global _ocr_service
    
    if _ocr_service is not None:
        await _ocr_service.cleanup()
        _ocr_service = None
