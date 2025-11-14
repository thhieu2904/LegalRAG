"""
Rebuild API - Trigger and Monitor VectorDB Cache Rebuild
=========================================================
Provides endpoints to trigger selective cache rebuilds via subprocess.
Uses script-based approach for isolation and reliability.

Security: Internal endpoints - should only be accessible from Admin Service.
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional, Literal
from enum import Enum
import subprocess
import json
import os
import signal
from datetime import datetime
import logging

from app.core.config import Settings

# Initialize settings
settings = Settings()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/rebuild", tags=["internal-rebuild"])


# ============================================================================
# Constants
# ============================================================================

REBUILD_SCRIPT_PATH = Path(__file__).parent.parent.parent / "tools" / "rebuild_selective.py"
STATUS_FILE_PATH = Path(__file__).parent.parent.parent / "data" / "cache" / "rebuild_status.json"
REBUILD_TIMEOUT = 3600  # 1 hour max


# ============================================================================
# Models
# ============================================================================

class RebuildScope(str, Enum):
    """Scope of rebuild operation"""
    DOCUMENT = "document"      # Rebuild single document
    COLLECTION = "collection"  # Rebuild entire collection
    ALL = "all"                # Rebuild all collections


class RebuildStatus(str, Enum):
    """Status of rebuild process"""
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RebuildTriggerRequest(BaseModel):
    """Request to trigger rebuild"""
    scope: RebuildScope = Field(..., description="Scope of rebuild")
    collection: Optional[str] = Field(None, description="Collection name (required for document/collection scope)")
    doc_id: Optional[str] = Field(None, description="Document ID (required for document scope)")

    class Config:
        json_schema_extra = {
            "example": {
                "scope": "document",
                "collection": "hop_dong",
                "doc_id": "DOC_001"
            }
        }


class RebuildStatusResponse(BaseModel):
    """Current rebuild status"""
    status: RebuildStatus
    scope: Optional[str] = None
    collection: Optional[str] = None
    doc_id: Optional[str] = None
    pid: Optional[int] = None
    progress: Optional[float] = None  # 0-100
    message: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None


class RebuildTriggerResponse(BaseModel):
    """Response from trigger endpoint"""
    success: bool
    message: str
    pid: Optional[int] = None
    status_file: str


# ============================================================================
# Security Helper
# ============================================================================

async def verify_internal_api_key(x_internal_api_key: str = Header(None)):
    """Verify internal API key for security"""
    expected_key = getattr(settings, 'internal_api_key', 'dev-internal-key')
    
    if x_internal_api_key != expected_key:
        logger.warning(f"❌ Unauthorized rebuild attempt - invalid API key")
        raise HTTPException(
            status_code=403,
            detail="Forbidden - Invalid internal API key"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_status() -> RebuildStatusResponse:
    """
    Read current rebuild status from file
    
    Returns:
        Current rebuild status
    """
    if not STATUS_FILE_PATH.exists():
        return RebuildStatusResponse(status=RebuildStatus.IDLE)
    
    try:
        with open(STATUS_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return RebuildStatusResponse(**data)
    except Exception as e:
        logger.error(f"❌ Failed to read status file: {e}")
        return RebuildStatusResponse(status=RebuildStatus.IDLE)


def update_status(status_data: dict):
    """
    Update rebuild status file
    
    Args:
        status_data: Status data to write
    """
    try:
        # Ensure directory exists
        STATUS_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write status
        with open(STATUS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"📝 Updated rebuild status: {status_data.get('status')}")
    except Exception as e:
        logger.error(f"❌ Failed to update status file: {e}")


def is_process_running(pid: int) -> bool:
    """
    Check if process is still running (without psutil dependency)
    
    Args:
        pid: Process ID
    
    Returns:
        True if process is running
    """
    try:
        # Send signal 0 to check if process exists
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill_process(pid: int) -> bool:
    """
    Kill rebuild process (cross-platform)
    
    Args:
        pid: Process ID to kill
    
    Returns:
        True if process was killed
    """
    try:
        import platform
        
        if platform.system() == "Windows":
            # Windows: use taskkill
            import subprocess
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                          capture_output=True, check=False)
        else:
            # Unix: use SIGTERM/SIGKILL
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            import time
            for _ in range(10):
                if not is_process_running(pid):
                    logger.info(f"🛑 Process {pid} terminated gracefully")
                    return True
                time.sleep(0.5)
            
            # Force kill if still running (Unix only - SIGKILL = 9)
            if is_process_running(pid):
                os.kill(pid, 9)  # SIGKILL
        
        logger.info(f"🛑 Killed rebuild process: PID {pid}")
        return True
    except (OSError, ProcessLookupError) as e:
        logger.error(f"❌ Failed to kill process {pid}: {e}")
        return False


def validate_rebuild_request(request: RebuildTriggerRequest):
    """
    Validate rebuild request parameters
    
    Args:
        request: Rebuild trigger request
    
    Raises:
        HTTPException: If validation fails
    """
    if request.scope == RebuildScope.DOCUMENT:
        if not request.collection or not request.doc_id:
            raise HTTPException(
                status_code=400,
                detail="collection and doc_id required for document scope"
            )
    elif request.scope == RebuildScope.COLLECTION:
        if not request.collection:
            raise HTTPException(
                status_code=400,
                detail="collection required for collection scope"
            )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/status",
    response_model=RebuildStatusResponse,
    summary="Get rebuild status",
    description="Get current status of rebuild process"
)
async def get_rebuild_status():
    """
    Get current rebuild status
    
    **Usage:** Poll this endpoint to monitor rebuild progress
    
    **Status values:**
    - `idle`: No rebuild in progress
    - `queued`: Rebuild scheduled but not started
    - `running`: Rebuild in progress
    - `success`: Rebuild completed successfully
    - `failed`: Rebuild failed with error
    - `cancelled`: Rebuild was cancelled
    """
    status = get_current_status()
    
    # Check if process is still running
    if status.status == RebuildStatus.RUNNING and status.pid:
        if not is_process_running(status.pid):
            # Process died unexpectedly
            logger.warning(f"⚠️ Rebuild process {status.pid} died unexpectedly")
            update_status({
                **status.model_dump(),
                "status": RebuildStatus.FAILED,
                "error": "Rebuild process terminated unexpectedly",
                "completed_at": datetime.now().isoformat()
            })
            status = get_current_status()
    
    return status


@router.post(
    "/trigger",
    response_model=RebuildTriggerResponse,
    summary="Trigger rebuild",
    description="Trigger selective cache rebuild via subprocess"
)
async def trigger_rebuild(
    request: RebuildTriggerRequest,
    x_internal_api_key: str = Header(None)
):
    """
    Trigger cache rebuild
    
    **Usage:** Start rebuild process after CRUD operations
    
    **Scopes:**
    - `document`: Rebuild single document (fastest, ~1-2s)
    - `collection`: Rebuild entire collection (medium, ~10-30s)
    - `all`: Rebuild all collections (slowest, ~1-5min)
    
    **Example:**
    ```
    POST /internal/rebuild/trigger
    {
        "scope": "document",
        "collection": "hop_dong",
        "doc_id": "DOC_001"
    }
    ```
    
    **Returns:** PID of rebuild process and status file path
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        # Validate request
        validate_rebuild_request(request)
        
        # Check if rebuild already running
        current_status = get_current_status()
        if current_status.status == RebuildStatus.RUNNING:
            raise HTTPException(
                status_code=409,
                detail=f"Rebuild already in progress (PID: {current_status.pid})"
            )
        
        # Check if rebuild script exists
        if not REBUILD_SCRIPT_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Rebuild script not found: {REBUILD_SCRIPT_PATH}"
            )
        
        # Build command
        cmd = [
            'python',
            str(REBUILD_SCRIPT_PATH),
            '--scope', request.scope.value
        ]
        
        if request.collection:
            cmd.extend(['--collection', request.collection])
        
        if request.doc_id:
            cmd.extend(['--doc-id', request.doc_id])
        
        # Add status file path
        cmd.extend(['--status-file', str(STATUS_FILE_PATH)])
        
        logger.info(f"🚀 Triggering rebuild: {' '.join(cmd)}")
        
        # Update status to queued
        update_status({
            "status": RebuildStatus.QUEUED,
            "scope": request.scope.value,
            "collection": request.collection,
            "doc_id": request.doc_id,
            "started_at": datetime.now().isoformat(),
            "message": "Rebuild queued"
        })
        
        # Spawn subprocess (detached)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # Detach from parent
            cwd=str(REBUILD_SCRIPT_PATH.parent.parent)  # Run from rag_service root
        )
        
        # Update status with PID
        update_status({
            "status": RebuildStatus.RUNNING,
            "scope": request.scope.value,
            "collection": request.collection,
            "doc_id": request.doc_id,
            "pid": process.pid,
            "started_at": datetime.now().isoformat(),
            "message": f"Rebuild started (PID: {process.pid})"
        })
        
        logger.info(f"✅ Rebuild triggered: PID {process.pid}")
        
        return RebuildTriggerResponse(
            success=True,
            message=f"Rebuild triggered successfully (PID: {process.pid})",
            pid=process.pid,
            status_file=str(STATUS_FILE_PATH)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to trigger rebuild: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/cancel",
    response_model=RebuildTriggerResponse,
    summary="Cancel rebuild",
    description="Cancel running rebuild process"
)
async def cancel_rebuild(
    x_internal_api_key: str = Header(None)
):
    """
    Cancel running rebuild
    
    **Usage:** Stop rebuild if taking too long or triggered by mistake
    
    **Note:** Process will be terminated gracefully (SIGTERM), then killed (SIGKILL) if doesn't stop
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        # Get current status
        current_status = get_current_status()
        
        if current_status.status != RebuildStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail=f"No rebuild in progress (current status: {current_status.status})"
            )
        
        if not current_status.pid:
            raise HTTPException(
                status_code=500,
                detail="Rebuild PID not found in status file"
            )
        
        # Kill process
        if kill_process(current_status.pid):
            # Update status
            update_status({
                **current_status.model_dump(),
                "status": RebuildStatus.CANCELLED,
                "message": "Rebuild cancelled by user",
                "completed_at": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Rebuild cancelled: PID {current_status.pid}")
            
            return RebuildTriggerResponse(
                success=True,
                message=f"Rebuild cancelled (PID: {current_status.pid})",
                pid=current_status.pid,
                status_file=str(STATUS_FILE_PATH)
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to kill rebuild process (PID: {current_status.pid})"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to cancel rebuild: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/status",
    summary="Clear rebuild status",
    description="Clear rebuild status file (reset to idle)"
)
async def clear_rebuild_status(
    x_internal_api_key: str = Header(None)
):
    """
    Clear rebuild status
    
    **Usage:** Reset status after completed/failed rebuild
    
    **Warning:** Only clear status when no rebuild is running
    """
    await verify_internal_api_key(x_internal_api_key)
    
    try:
        # Check if rebuild is running
        current_status = get_current_status()
        if current_status.status == RebuildStatus.RUNNING:
            raise HTTPException(
                status_code=409,
                detail="Cannot clear status while rebuild is running. Cancel rebuild first."
            )
        
        # Delete status file
        if STATUS_FILE_PATH.exists():
            STATUS_FILE_PATH.unlink()
            logger.info("🗑️ Rebuild status cleared")
        
        return {
            "success": True,
            "message": "Rebuild status cleared"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to clear status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
