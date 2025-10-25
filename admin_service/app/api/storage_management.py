"""
📦 STORAGE MANAGEMENT API
Quản lý danh sách các form đã tải xuống (được lưu từ identifill_service)
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

# Database configuration
DB_PATH = "data/legalrag.db"

class StoredFormInfo(BaseModel):
    """Thông tin form đã lưu"""
    form_id: int
    scan_cccd: str
    scan_ho_ten: str
    filename: str
    file_size: int
    created_at: str
    updated_at: str
    form_path: Optional[str] = None


class StorageStats(BaseModel):
    """Thống kê lưu trữ"""
    total_forms: int
    total_users: int
    total_size_mb: float
    cccd_list: List[dict]


@router.get("/list", response_model=List[StoredFormInfo])
async def get_all_stored_forms(
    cccd: Optional[str] = Query(None, description="Filter by CCCD (optional)")
):
    """
    📋 Lấy danh sách tất cả form đã lưu
    - Nếu có cccd: filter theo CCCD
    - Nếu không: trả về tất cả
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if cccd:
            # Filter by specific CCCD
            cursor.execute("""
                SELECT form_id, scan_cccd, scan_ho_ten, filename, file_size,
                       created_at, updated_at
                FROM stored_forms
                WHERE scan_cccd = ?
                ORDER BY created_at DESC
            """, (cccd,))
        else:
            # Get all forms
            cursor.execute("""
                SELECT form_id, scan_cccd, scan_ho_ten, filename, file_size,
                       created_at, updated_at
                FROM stored_forms
                ORDER BY created_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        forms = [
            StoredFormInfo(
                form_id=row["form_id"],
                scan_cccd=row["scan_cccd"],
                scan_ho_ten=row["scan_ho_ten"],
                filename=row["filename"],
                file_size=row["file_size"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                form_path=f"data/scanned_documents/{row['scan_cccd']}/forms/{row['filename']}"
            )
            for row in rows
        ]

        logger.info(f"✅ Retrieved {len(forms)} stored forms")
        return forms

    except Exception as e:
        logger.error(f"❌ Error retrieving forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StorageStats)
async def get_storage_stats():
    """
    📊 Lấy thống kê lưu trữ
    - Tổng số form
    - Tổng số users
    - Tổng dung lượng
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Total forms
        cursor.execute("SELECT COUNT(*) as count FROM stored_forms")
        total_forms = cursor.fetchone()["count"]

        # Total users
        cursor.execute("SELECT COUNT(DISTINCT scan_cccd) as count FROM stored_forms")
        total_users = cursor.fetchone()["count"]

        # Total size
        cursor.execute("SELECT SUM(file_size) as total FROM stored_forms")
        total_size = cursor.fetchone()["total"] or 0
        total_size_mb = total_size / (1024 * 1024)

        # CCCD list with count
        cursor.execute("""
            SELECT scan_cccd, scan_ho_ten, COUNT(*) as form_count,
                   SUM(file_size) as total_size
            FROM stored_forms
            GROUP BY scan_cccd
            ORDER BY form_count DESC
        """)

        cccd_list = [
            {
                "scan_cccd": row["scan_cccd"],
                "scan_ho_ten": row["scan_ho_ten"],
                "form_count": row["form_count"],
                "total_size_mb": (row["total_size"] or 0) / (1024 * 1024)
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        logger.info(f"✅ Storage stats: {total_forms} forms from {total_users} users")
        return StorageStats(
            total_forms=total_forms,
            total_users=total_users,
            total_size_mb=total_size_mb,
            cccd_list=cccd_list
        )

    except Exception as e:
        logger.error(f"❌ Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    🏥 Health check
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stored_forms")
        count = cursor.fetchone()[0]
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "forms_count": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/download/{form_id}")
async def download_stored_form(form_id: int):
    """
    📥 Tải xuống file form đã lưu
    - Lấy thông tin form từ database
    - Trả về file .docx
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT form_id, scan_cccd, filename, file_size
            FROM stored_forms
            WHERE form_id = ?
        """, (form_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Construct file path
        file_path = Path(f"data/scanned_documents/{row['scan_cccd']}/forms/{row['filename']}")
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        logger.info(f"✅ Downloading form: {row['filename']}")
        return FileResponse(
            path=file_path,
            filename=row['filename'],
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{form_id}")
async def delete_stored_form(form_id: int):
    """
    🗑️ Xóa form đã lưu
    - Xóa record từ database
    - Xóa file từ disk
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get form info
        cursor.execute("""
            SELECT form_id, scan_cccd, filename
            FROM stored_forms
            WHERE form_id = ?
        """, (form_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Delete file from disk
        file_path = Path(f"data/scanned_documents/{row['scan_cccd']}/forms/{row['filename']}")
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"✅ File deleted: {file_path}")
        
        # Delete from database
        cursor.execute("DELETE FROM stored_forms WHERE form_id = ?", (form_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Form deleted: {row['filename']}")
        return {
            "status": "success",
            "message": "Form deleted successfully",
            "form_id": form_id,
            "filename": row['filename']
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
