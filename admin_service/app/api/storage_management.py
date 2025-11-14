"""
📦 STORAGE MANAGEMENT API
Quản lý danh sách các form đã tải xuống (được lưu từ identifill_service)
Proxy to identifill_service database
"""
from fastapi import APIRouter, HTTPException, Query, Form, UploadFile, File
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

# 🔗 Use SAME database as identifill_service (shared location)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "legalrag.db"

class StoredFormInfo(BaseModel):
    """Thông tin form đã lưu"""
    file_id: str
    scan_cccd: str
    form_name: str
    file_name: str
    file_size: int
    created_at: str


class StorageStats(BaseModel):
    """Thống kê lưu trữ"""
    total_forms: int
    total_users: int
    total_size_mb: float
    cccd_list: List[dict]


@router.get("/list")
async def get_all_stored_forms(
    cccd: Optional[str] = Query(None, description="Filter by CCCD (optional)")
):
    """
    📋 Lấy danh sách tất cả form đã lưu
    - Nếu có cccd: filter theo CCCD
    - Nếu không: trả về tất cả
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if cccd:
            # Filter by specific CCCD
            cursor.execute("""
                SELECT file_id, scan_cccd, form_name, file_name, file_size, created_at
                FROM stored_forms
                WHERE scan_cccd = ?
                ORDER BY created_at DESC
            """, (cccd,))
        else:
            # Get all forms
            cursor.execute("""
                SELECT file_id, scan_cccd, form_name, file_name, file_size, created_at
                FROM stored_forms
                ORDER BY created_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        forms = [
            {
                "file_id": row["file_id"],
                "scan_cccd": row["scan_cccd"],
                "form_name": row["form_name"],
                "file_name": row["file_name"],
                "file_size": row["file_size"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

        logger.info(f"✅ Retrieved {len(forms)} stored forms")
        return {
            "success": True,
            "data": forms,
            "message": f"Retrieved {len(forms)} forms"
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_storage_stats():
    """
    📊 Lấy thống kê lưu trữ
    - Tổng số form
    - Tổng số users
    - Tổng dung lượng
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
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

        # CCCD list with count and user name
        cursor.execute("""
            SELECT f.scan_cccd, u.scan_ho_ten, COUNT(*) as form_count,
                   SUM(f.file_size) as total_size
            FROM stored_forms f
            LEFT JOIN cccd_users u ON f.scan_cccd = u.scan_cccd
            GROUP BY f.scan_cccd
            ORDER BY form_count DESC
        """)

        cccd_list = [
            {
                "scan_cccd": row["scan_cccd"],
                "scan_ho_ten": row["scan_ho_ten"] or "Unknown",
                "form_count": row["form_count"],
                "total_size_mb": (row["total_size"] or 0) / (1024 * 1024)
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        logger.info(f"✅ Storage stats: {total_forms} forms from {total_users} users")
        return {
            "success": True,
            "data": {
                "total_forms": total_forms,
                "total_users": total_users,
                "total_size_mb": total_size_mb,
                "cccd_list": cccd_list
            },
            "message": f"Retrieved stats for {total_forms} forms from {total_users} users"
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    🏥 Health check
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
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


@router.get("/download/{file_id}")
async def download_stored_form(file_id: str):
    """
    📥 Tải xuống file form đã lưu
    - Lấy thông tin form từ database
    - Trả về file .docx
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_id, scan_cccd, file_name, file_size
            FROM stored_forms
            WHERE file_id = ?
        """, (file_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Construct file path
        file_path = Path(f"data/scanned_documents/{row['scan_cccd']}/forms/{row['file_name']}")
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        logger.info(f"✅ Downloading form: {row['file_name']}")
        return FileResponse(
            path=file_path,
            filename=row['file_name'],
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{file_id}")
async def delete_stored_form(file_id: str):
    """
    🗑️ Xóa form đã lưu
    - Xóa record từ database
    - Xóa file từ disk
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get form info
        cursor.execute("""
            SELECT file_id, scan_cccd, file_name
            FROM stored_forms
            WHERE file_id = ?
        """, (file_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Delete file from disk
        file_path = Path(f"data/scanned_documents/{row['scan_cccd']}/forms/{row['file_name']}")
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"✅ File deleted: {file_path}")
        
        # Delete from database
        cursor.execute("DELETE FROM stored_forms WHERE file_id = ?", (file_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Form deleted: {row['file_name']}")
        return {
            "success": True,
            "data": {
                "file_id": file_id,
                "filename": row['file_name']
            },
            "message": "Form deleted successfully"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
