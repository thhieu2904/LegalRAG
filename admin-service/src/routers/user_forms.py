"""
User Forms Router - Manage user-filled forms stored in MinIO

These endpoints allow admins to:
- List all user-filled forms by session
- Download specific filled forms
- Delete user-filled forms

Storage pattern: user_forms/{session_id}/{cccd}_{form_name}.docx
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/user-forms", tags=["User Forms"])

# Storage service URL
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8010")


# ============= MODELS =============

class UserFormItem(BaseModel):
    """A single user-filled form"""
    file_path: str  # Full path in MinIO
    filename: str  # Just the filename
    session_id: str
    cccd_number: Optional[str] = None  # Extracted from filename if present
    form_name: str  # Form name without CCCD prefix
    file_size: Optional[int] = None
    created_at: Optional[str] = None


class UserFormListResponse(BaseModel):
    """Response for listing user forms"""
    success: bool
    message: str
    forms: List[UserFormItem]
    total: int


class UserFormDeleteResponse(BaseModel):
    """Response for deleting user form"""
    success: bool
    message: str
    deleted_path: Optional[str] = None


# ============= HELPER FUNCTIONS =============

def parse_user_form_filename(filename: str) -> tuple:
    """
    Parse user form filename to extract CCCD and form name.
    
    Pattern: {cccd}_{form_name}.docx or {form_name}.docx
    
    Returns:
        (cccd_number or None, form_name)
    """
    # Remove .docx extension
    name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Check if has CCCD prefix (12 digits)
    parts = name.split('_', 1)
    if len(parts) == 2 and len(parts[0]) == 12 and parts[0].isdigit():
        return parts[0], parts[1]
    else:
        return None, name


# ============= ENDPOINTS =============

@router.get("", response_model=UserFormListResponse)
async def list_user_forms(session_id: Optional[str] = None):
    """
    List all user-filled forms.
    
    Args:
        session_id: Optional filter by session ID
        
    Returns:
        List of user-filled forms
    """
    try:
        async with httpx.AsyncClient() as client:
            # List files in user_forms folder
            if session_id:
                folder = f"user_forms/{session_id}"
            else:
                folder = "user_forms"
            
            response = await client.get(
                f"{STORAGE_SERVICE_URL}/list",
                params={"prefix": folder, "recursive": True},
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.warning(f"Storage list returned {response.status_code}")
                return UserFormListResponse(
                    success=True,
                    message="No user forms found",
                    forms=[],
                    total=0
                )
            
            data = response.json()
            files = data.get("files", [])
            
            # Parse files into UserFormItem
            forms = []
            for file_info in files:
                # storage-service returns "name" not "path"
                file_path = file_info.get("name", "")
                
                # Skip if not a docx file
                if not file_path.endswith(".docx"):
                    continue
                
                # Extract session_id and filename from path
                # Path format: user_forms/{session_id}/{filename}
                parts = file_path.split("/")
                if len(parts) >= 3:
                    sess_id = parts[1]
                    filename = parts[-1]
                    
                    # Parse filename
                    cccd, form_name = parse_user_form_filename(filename)
                    
                    forms.append(UserFormItem(
                        file_path=file_path,
                        filename=filename,
                        session_id=sess_id,
                        cccd_number=cccd,
                        form_name=form_name,
                        file_size=file_info.get("size"),
                        created_at=str(file_info.get("last_modified")) if file_info.get("last_modified") else None
                    ))
            
            # Sort by created_at descending
            forms.sort(key=lambda x: x.created_at or "", reverse=True)
            
            return UserFormListResponse(
                success=True,
                message=f"Found {len(forms)} user forms",
                forms=forms,
                total=len(forms)
            )
            
    except Exception as e:
        logger.error(f"Error listing user forms: {e}")
        return UserFormListResponse(
            success=False,
            message=f"Error: {str(e)}",
            forms=[],
            total=0
        )


@router.get("/{session_id}", response_model=UserFormListResponse)
async def list_session_forms(session_id: str):
    """
    List forms for a specific session.
    
    Args:
        session_id: Session ID to filter by
        
    Returns:
        List of user-filled forms for this session
    """
    return await list_user_forms(session_id=session_id)


@router.get("/{session_id}/download/{filename:path}")
async def download_user_form(session_id: str, filename: str):
    """
    Download a specific user-filled form.
    
    Args:
        session_id: Session ID
        filename: Filename to download
        
    Returns:
        Redirect to storage-service download URL
    """
    try:
        file_path = f"user_forms/{session_id}/{filename}"
        
        async with httpx.AsyncClient() as client:
            # Get download URL from storage-service
            response = await client.get(
                f"{STORAGE_SERVICE_URL}/download",
                params={"file_path": file_path},
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Return the file content
                return response.content
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Form not found")
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Storage error: {response.text}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading user form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}/{filename:path}", response_model=UserFormDeleteResponse)
async def delete_user_form(session_id: str, filename: str):
    """
    Delete a specific user-filled form.
    
    Args:
        session_id: Session ID
        filename: Filename to delete
        
    Returns:
        Deletion confirmation
    """
    try:
        file_path = f"user_forms/{session_id}/{filename}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{STORAGE_SERVICE_URL}/delete",
                params={"file_path": file_path},
                timeout=30.0
            )
            
            if response.status_code == 200:
                logger.info(f"Deleted user form: {file_path}")
                return UserFormDeleteResponse(
                    success=True,
                    message="Form deleted successfully",
                    deleted_path=file_path
                )
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Form not found")
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Storage error: {response.text}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=UserFormDeleteResponse)
async def delete_session_forms(session_id: str):
    """
    Delete all forms for a session.
    
    Args:
        session_id: Session ID to delete all forms for
        
    Returns:
        Deletion confirmation with count
    """
    try:
        folder_path = f"user_forms/{session_id}/"
        
        async with httpx.AsyncClient() as client:
            # First list all files in session folder
            list_response = await client.get(
                f"{STORAGE_SERVICE_URL}/list",
                params={"prefix": folder_path},
                timeout=30.0
            )
            
            if list_response.status_code != 200:
                return UserFormDeleteResponse(
                    success=True,
                    message="No forms found for session",
                    deleted_path=folder_path
                )
            
            files = list_response.json().get("files", [])
            deleted_count = 0
            
            # Delete each file
            for file_info in files:
                # storage-service returns "name" not "path"
                file_path = file_info.get("name", "")
                if file_path:
                    del_response = await client.delete(
                        f"{STORAGE_SERVICE_URL}/delete",
                        params={"file_path": file_path},
                        timeout=10.0
                    )
                    if del_response.status_code == 200:
                        deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} forms for session: {session_id}")
            
            return UserFormDeleteResponse(
                success=True,
                message=f"Deleted {deleted_count} forms for session {session_id}",
                deleted_path=folder_path
            )
            
    except Exception as e:
        logger.error(f"Error deleting session forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))
