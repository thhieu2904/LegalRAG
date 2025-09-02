"""
Simplified OCR Service Implementation for testing
"""
import asyncio
import logging
import base64
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4

# Configure logging
logger = logging.getLogger(__name__)

# Session management
sessions: Dict[str, Dict[Any, Any]] = {}

class OCRService:
    """Simple OCR service implementation"""
    
    def __init__(self):
        self.start_time = time.time()
        self.initialized = False
        
    async def initialize(self):
        """Initialize service"""
        self.initialized = True
        return True
    
    async def create_session(self, session_id: Optional[str] = None, expires_in_hours: int = 2):
        """Create a new session"""
        if not session_id:
            session_id = str(uuid4())
            
        # Check if session already exists
        if session_id in sessions:
            return {"success": False, "message": "Session already exists"}
            
        # Create new session
        now = datetime.utcnow()
        sessions[session_id] = {
            "session_id": session_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=expires_in_hours)).isoformat(),
            "processing_status": "pending",
            "front_image": None,
            "back_image": None,
            "extracted_data": None,
            "confidence_scores": None
        }
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=expires_in_hours)).isoformat()
            },
            "message": "Session created successfully"
        }
    
    async def upload_image(self, session_id: str, side: str, image_data: str):
        """Upload an image to a session"""
        if session_id not in sessions:
            return {"success": False, "message": "Session not found"}
            
        # Store image
        sessions[session_id][f"{side}_image"] = image_data
        sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "side": side,
                "image_key": f"{session_id}_{side}"
            },
            "message": f"{side.capitalize()} image uploaded successfully"
        }
    
    async def process_ocr(self, session_id: str, process_both_sides: bool = True):
        """Process OCR for a session"""
        if session_id not in sessions:
            return {"success": False, "message": "Session not found"}
            
        session = sessions[session_id]
        
        # Check if we have the required images
        if process_both_sides and (not session["front_image"] or not session["back_image"]):
            return {"success": False, "message": "Both front and back images are required for processing"}
            
        # Update status
        session["processing_status"] = "processing"
        session["updated_at"] = datetime.utcnow().isoformat()
        
        # For testing, we'll use a simulated extraction
        # In a real implementation, this would call VietOCR
        
        # Simulate processing delay
        await asyncio.sleep(2)
        
        # Set mock data
        session["extracted_data"] = {
            "id_number": "123456789012",
            "full_name": "NGUYỄN VĂN A",
            "date_of_birth": "01/01/1990",
            "gender": "Nam",
            "nationality": "Việt Nam",
            "hometown": "Hà Nội",
            "residence": "123 Đường ABC, Phường XYZ, Quận 123, TP. Hồ Chí Minh",
            "issue_date": "01/01/2020",
            "expiry_date": "01/01/2030"
        }
        
        session["confidence_scores"] = {
            "id_number": 0.95,
            "full_name": 0.98,
            "date_of_birth": 0.94,
            "gender": 0.99,
            "nationality": 0.99,
            "hometown": 0.92,
            "residence": 0.90,
            "issue_date": 0.93,
            "expiry_date": 0.91,
            "overall_confidence": 0.95
        }
        
        session["processing_status"] = "completed"
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "processing_status": "completed"
            },
            "message": "OCR processing completed"
        }
    
    async def get_results(self, session_id: str):
        """Get OCR results for a session"""
        if session_id not in sessions:
            return {"success": False, "message": "Session not found"}
            
        session = sessions[session_id]
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "processing_status": session["processing_status"],
                "extracted_data": session["extracted_data"],
                "confidence_scores": session["confidence_scores"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            },
            "message": "OCR results retrieved successfully"
        }
    
    async def get_session_status(self, session_id: str):
        """Get session status"""
        if session_id not in sessions:
            return {"success": False, "message": "Session not found"}
            
        session = sessions[session_id]
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "processing_status": session["processing_status"],
                "has_front_image": bool(session["front_image"]),
                "has_back_image": bool(session["back_image"]),
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
                "expires_at": session["expires_at"]
            },
            "message": "Session status retrieved successfully"
        }
    
    async def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id not in sessions:
            return {"success": False, "message": "Session not found"}
            
        del sessions[session_id]
        
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    
    async def get_service_stats(self):
        """Get service statistics"""
        return {
            "success": True,
            "data": {
                "total_sessions": len(sessions),
                "active_sessions": len([s for s in sessions.values() if s["processing_status"] != "expired"]),
                "completed_sessions": len([s for s in sessions.values() if s["processing_status"] == "completed"]),
                "failed_sessions": len([s for s in sessions.values() if s["processing_status"] == "failed"]),
                "uptime_seconds": int(time.time() - self.start_time)
            },
            "message": "Service statistics retrieved successfully"
        }

# Create singleton instance
_ocr_service = OCRService()

async def get_ocr_service():
    """Get OCR service instance"""
    return _ocr_service
