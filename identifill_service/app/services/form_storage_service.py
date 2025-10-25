"""
Form Storage Service
Manages file storage and database integration for form documents
"""

import os
import uuid
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any

from app.core.database import db

logger = logging.getLogger(__name__)


class FormStorageService:
    """Service to manage form storage (file system + database)"""
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize form storage service
        
        Args:
            storage_dir: Base directory for storage (default: "data")
        """
        self.base_dir = Path(storage_dir) / "scanned_documents"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Form Storage Service initialized: {self.base_dir}")
    
    def save_form(
        self,
        scan_cccd: str,
        scan_ho_ten: str,
        form_name: str,
        form_content: bytes,
        form_type: str = "docx"
    ) -> Dict[str, Any]:
        """
        Save form file and track in database
        
        Args:
            scan_cccd: 12-digit CCCD number
            scan_ho_ten: User full name
            form_name: Form type (e.g., "contract", "request")
            form_content: Binary file content
            form_type: File type (default: "docx")
            
        Returns:
            Dict with success status, file_id, and message
        """
        try:
            # 1. Save user metadata to DB
            logger.info(f"💾 Saving form for CCCD: {scan_cccd}, User: {scan_ho_ten}")
            db.save_cccd_user(scan_cccd, scan_ho_ten)
            
            # 2. Create CCCD directory
            cccd_dir = self.base_dir / scan_cccd
            cccd_dir.mkdir(exist_ok=True)
            
            forms_dir = cccd_dir / "forms"
            forms_dir.mkdir(exist_ok=True)
            logger.info(f"📁 Created directory: {forms_dir}")
            
            # 3. Generate unique file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{form_name}_{timestamp}.{form_type}"
            file_path = forms_dir / file_name
            
            # 4. Save file
            with open(file_path, 'wb') as f:
                f.write(form_content)
            
            file_size = len(form_content)
            logger.info(f"✅ Saved form: {file_path} ({file_size} bytes)")
            
            # 5. Add record to database
            file_id = str(uuid.uuid4())
            db.add_form_record(
                file_id=file_id,
                scan_cccd=scan_cccd,
                form_name=form_name,
                file_name=file_name,
                file_type=form_type,
                file_size=file_size
            )
            
            return {
                "success": True,
                "file_id": file_id,
                "file_name": file_name,
                "message": "Form saved successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error saving form: {e}")
            return {
                "success": False,
                "message": f"Error saving form: {str(e)}"
            }
    
    def get_forms(self, scan_cccd: str) -> Dict[str, Any]:
        """
        Get all forms for a CCCD
        
        Args:
            scan_cccd: CCCD number
            
        Returns:
            Dict with forms list and metadata
        """
        try:
            # Get user info
            user = db.get_cccd_user(scan_cccd)
            if not user:
                logger.warning(f"⚠️ No user found for CCCD: {scan_cccd}")
                return {
                    "success": False,
                    "message": "No forms found for this CCCD"
                }
            
            # Get forms list
            forms = db.get_forms_by_cccd(scan_cccd)
            
            return {
                "success": True,
                "scan_cccd": scan_cccd,
                "scan_ho_ten": user.get("scan_ho_ten"),
                "forms": forms,
                "total_forms": len(forms)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting forms: {e}")
            return {
                "success": False,
                "message": f"Error retrieving forms: {str(e)}"
            }
    
    def download_form(
        self, 
        scan_cccd: str, 
        file_name: str
    ) -> Dict[str, Any]:
        """
        Download form from file system
        
        Args:
            scan_cccd: CCCD number
            file_name: File name to download
            
        Returns:
            Dict with success status and file content
        """
        try:
            file_path = self.base_dir / scan_cccd / "forms" / file_name
            
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return {
                    "success": False,
                    "message": "File not found"
                }
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            logger.info(f"✅ Downloaded form: {file_path}")
            
            return {
                "success": True,
                "file_name": file_name,
                "file_content": file_content
            }
            
        except Exception as e:
            logger.error(f"❌ Error downloading form: {e}")
            return {
                "success": False,
                "message": f"Error downloading form: {str(e)}"
            }
    
    def delete_form(
        self, 
        scan_cccd: str, 
        file_id: str,
        file_name: str
    ) -> Dict[str, Any]:
        """
        Delete form from file system and database
        
        Args:
            scan_cccd: CCCD number
            file_id: File ID to delete
            file_name: File name to delete
            
        Returns:
            Dict with success status and message
        """
        try:
            # 1. Delete file from filesystem
            file_path = self.base_dir / scan_cccd / "forms" / file_name
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️ Deleted file: {file_path}")
            else:
                logger.warning(f"⚠️ File already gone: {file_path}")
            
            # 2. Delete record from database
            db.delete_form_record(file_id)
            
            return {
                "success": True,
                "message": "Form deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting form: {e}")
            return {
                "success": False,
                "message": f"Error deleting form: {str(e)}"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dict with storage statistics
        """
        return db.get_database_stats()
