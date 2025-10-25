# 🏗️ CHỌN PHƯƠNG ÁN LƯU TRỮ PHẢI HỢP LÝ

## ❓ Câu Hỏi: Nơi Lưu Trữ Ở Đâu?

### 3 Phương Án Chính

| Phương Án              | Vị Trí                    | Ưu Điểm            | Nhược Điểm          | Khuyên?       |
| ---------------------- | ------------------------- | ------------------ | ------------------- | ------------- |
| **1. File System**     | `data/scanned_documents/` | Đơn giản, không DB | Khó backup, scaling | ⭐⭐ OK Local |
| **2. SQLite Database** | `data/legalrag.db`        | Có index, query dễ | Cần học SQL         | ⭐⭐⭐ BEST   |
| **3. PostgreSQL**      | Docker container          | Professional       | Overkill cho local  | ❌ Không cần  |

---

## 🎯 KHUYẾN CÁO: **SQLite + File System Hybrid** ⭐⭐⭐

### Tại Sao SQLite Tốt Nhất Cho Bạn?

```
Hiện tại:
- Dự án local
- Không có DB layer
- Kiến thức hạn hẹp

SQLite:
✅ Python có sẵn (built-in)
✅ Không cần cài gì thêm
✅ Dễ backup (1 file .db)
✅ Có transaction (đảm bảo data integrity)
✅ Dễ migrate sang PostgreSQL sau (SQL syntax giống)
✅ Fast enough cho local
```

### Kiến Trúc Hybrid (KHUYẾN CÁO):

```
┌─────────────────────────────────────────────┐
│         SQLite Database (data.db)           │
├─────────────────────────────────────────────┤
│ Lưu metadata + tracking:                    │
│  - scan_cccd, scan_ho_ten                   │
│  - file_id, file_name, created_at           │
│  - (Chỉ ~1-2 KB/record)                     │
└─────────────────────────────────────────────┘
            ↓ References ↓
┌─────────────────────────────────────────────┐
│    File System (data/scanned_documents/)    │
├─────────────────────────────────────────────┤
│ Lưu actual files:                           │
│  - *.docx files                             │
│  - (Large binary, 100-500 KB each)          │
└─────────────────────────────────────────────┘
```

### File Structure:

```
project/
├── data/
│   ├── legalrag.db              # SQLite database (metadata)
│   └── scanned_documents/       # File storage (forms)
│       └── 079123456789/
│           ├── contract_20251025_103000.docx
│           └── request_20251025_145500.docx
├── identifill_service/
└── ...
```

---

## 💾 CÁCH IMPLEMENT: SQLite + File System

### 1️⃣ **Database Schema (SQLite)**

```python
# identifill_service/app/core/database.py - TẠO FILE MỚI

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    """SQLite Database Manager"""

    DB_PATH = Path("data/legalrag.db")

    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
        logger.info(f"✅ Database initialized at: {self.DB_PATH}")

    def init_db(self):
        """Tạo tables nếu chưa có"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        # Table: CCCD Users (metadata)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cccd_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_cccd TEXT UNIQUE NOT NULL,
            scan_ho_ten TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # Table: Stored Forms (file tracking)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stored_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            scan_cccd TEXT NOT NULL,
            form_name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT DEFAULT 'docx',
            file_size INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(scan_cccd) REFERENCES cccd_users(scan_cccd)
            ON DELETE CASCADE
        )
        """)

        # Index for faster queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scan_cccd
        ON stored_forms(scan_cccd)
        """)

        conn.commit()
        conn.close()
        logger.info("✅ Database tables initialized")

    def get_connection(self):
        """Get SQLite connection"""
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row  # Return dict-like rows
        return conn

    def save_cccd_user(self, scan_cccd: str, scan_ho_ten: str) -> bool:
        """Lưu/update CCCD user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO cccd_users (scan_cccd, scan_ho_ten, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(scan_cccd) DO UPDATE SET
                scan_ho_ten = excluded.scan_ho_ten,
                updated_at = excluded.updated_at
            """, (scan_cccd, scan_ho_ten, datetime.now().isoformat(),
                  datetime.now().isoformat()))

            conn.commit()
            conn.close()
            logger.info(f"✅ Saved/Updated CCCD user: {scan_cccd}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving CCCD user: {e}")
            return False

    def add_form_record(
        self,
        file_id: str,
        scan_cccd: str,
        form_name: str,
        file_name: str,
        file_type: str = "docx",
        file_size: int = 0
    ) -> bool:
        """Thêm record form vào database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO stored_forms
            (file_id, scan_cccd, form_name, file_name, file_type, file_size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, scan_cccd, form_name, file_name, file_type,
                  file_size, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            logger.info(f"✅ Added form record: {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding form record: {e}")
            return False

    def get_forms_by_cccd(self, scan_cccd: str) -> List[Dict[str, Any]]:
        """Lấy tất cả form của một CCCD"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT file_id, form_name, file_name, file_type,
                   file_size, created_at
            FROM stored_forms
            WHERE scan_cccd = ?
            ORDER BY created_at DESC
            """, (scan_cccd,))

            forms = [dict(row) for row in cursor.fetchall()]
            conn.close()

            logger.info(f"✅ Retrieved {len(forms)} forms for CCCD: {scan_cccd}")
            return forms
        except Exception as e:
            logger.error(f"❌ Error getting forms: {e}")
            return []

    def get_cccd_user(self, scan_cccd: str) -> Dict[str, Any] | None:
        """Lấy info CCCD user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT scan_cccd, scan_ho_ten, created_at, updated_at
            FROM cccd_users
            WHERE scan_cccd = ?
            """, (scan_cccd,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ Error getting CCCD user: {e}")
            return None

    def delete_form_record(self, file_id: str) -> bool:
        """Xóa record form từ database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM stored_forms WHERE file_id = ?", (file_id,))

            conn.commit()
            conn.close()
            logger.info(f"✅ Deleted form record: {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting form record: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM cccd_users")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM stored_forms")
            form_count = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(file_size) FROM stored_forms")
            total_size = cursor.fetchone()[0] or 0

            conn.close()

            return {
                "total_users": user_count,
                "total_forms": form_count,
                "total_storage_bytes": total_size,
                "total_storage_mb": round(total_size / (1024**2), 2)
            }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

# Singleton instance
db = Database()
```

### 2️⃣ **Form Storage Service (Simplified)**

```python
# identifill_service/app/services/form_storage_service.py

import os
import uuid
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any
from app.core.database import db

logger = logging.getLogger(__name__)

class FormStorageService:
    """Lưu form .docx vào file system + track trong SQLite"""

    def __init__(self, storage_dir: str = "data"):
        self.base_dir = Path(storage_dir) / "scanned_documents"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Storage initialized: {self.base_dir}")

    def save_form(
        self,
        scan_cccd: str,
        scan_ho_ten: str,
        form_name: str,
        form_content: bytes,
        form_type: str = "docx"
    ) -> Dict[str, Any]:
        """Lưu form + track trong database"""
        try:
            # 1️⃣ Lưu user metadata vào DB
            db.save_cccd_user(scan_cccd, scan_ho_ten)

            # 2️⃣ Tạo thư mục CCCD
            cccd_dir = self.base_dir / scan_cccd
            cccd_dir.mkdir(exist_ok=True)

            forms_dir = cccd_dir / "forms"
            forms_dir.mkdir(exist_ok=True)

            # 3️⃣ Generate file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{form_name}_{timestamp}.{form_type}"
            file_path = forms_dir / file_name

            # 4️⃣ Lưu file
            with open(file_path, 'wb') as f:
                f.write(form_content)

            file_size = len(form_content)
            logger.info(f"✅ Saved form: {file_path} ({file_size} bytes)")

            # 5️⃣ Thêm record vào database
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
            return {"success": False, "message": str(e)}

    def get_forms(self, scan_cccd: str) -> Dict[str, Any]:
        """Lấy danh sách form từ database"""
        try:
            # Lấy user info
            user = db.get_cccd_user(scan_cccd)
            if not user:
                return {
                    "success": False,
                    "message": "No forms found for this CCCD"
                }

            # Lấy danh sách form
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
            return {"success": False, "message": str(e)}

    def download_form(
        self,
        scan_cccd: str,
        file_name: str
    ) -> Dict[str, Any]:
        """Download form từ file system"""
        try:
            file_path = self.base_dir / scan_cccd / "forms" / file_name

            if not file_path.exists():
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
            return {"success": False, "message": str(e)}

    def delete_form(
        self,
        scan_cccd: str,
        file_id: str,
        file_name: str
    ) -> Dict[str, Any]:
        """Xóa form từ file system + database"""
        try:
            # 1️⃣ Xóa file
            file_path = self.base_dir / scan_cccd / "forms" / file_name
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✅ Deleted file: {file_path}")

            # 2️⃣ Xóa record từ database
            db.delete_form_record(file_id)

            return {
                "success": True,
                "message": "Form deleted successfully"
            }

        except Exception as e:
            logger.error(f"❌ Error deleting form: {e}")
            return {"success": False, "message": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê lưu trữ"""
        return db.get_database_stats()
```

### 3️⃣ **API Endpoints**

```python
# identifill_service/app/api/v1/forms.py - CẬP NHẬT

from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
import logging
from app.services.form_storage_service import FormStorageService
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()
storage = FormStorageService()

class FormStats(BaseModel):
    total_users: int
    total_forms: int
    total_storage_mb: float

@router.post("/save")
async def save_form(
    form_file: UploadFile = File(...),
    scan_cccd: str = None,
    scan_ho_ten: str = None,
    form_name: str = None
):
    """
    💾 Lưu form .docx

    Form data:
    - form_file: File upload (.docx)
    - scan_cccd: 12-digit ID
    - scan_ho_ten: User full name
    - form_name: Form type (e.g., "contract", "request")
    """
    try:
        if not all([scan_cccd, scan_ho_ten, form_name]):
            raise HTTPException(
                status_code=400,
                detail="Missing required: scan_cccd, scan_ho_ten, form_name"
            )

        content = await form_file.read()

        logger.info(f"📁 Saving form: {form_name} for CCCD: {scan_cccd}")

        result = storage.save_form(
            scan_cccd=scan_cccd,
            scan_ho_ten=scan_ho_ten,
            form_name=form_name,
            form_content=content,
            form_type="docx"
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in save endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{scan_cccd}")
async def list_forms(scan_cccd: str):
    """
    📋 Lấy danh sách form của một CCCD

    Returns:
    {
      "success": true,
      "scan_cccd": "079123456789",
      "scan_ho_ten": "Nguyễn Văn A",
      "forms": [
        {
          "file_id": "uuid",
          "form_name": "contract",
          "file_name": "contract_20251025_103000.docx",
          "created_at": "2025-10-25T10:30:00"
        }
      ],
      "total_forms": 1
    }
    """
    try:
        result = storage.get_forms(scan_cccd)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in list endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{scan_cccd}/{file_name}")
async def download_form(scan_cccd: str, file_name: str):
    """
    📥 Download form cụ thể
    """
    try:
        result = storage.download_form(scan_cccd, file_name)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return FileResponse(
            path=f"data/scanned_documents/{scan_cccd}/forms/{file_name}",
            filename=file_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in download endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{scan_cccd}/{file_id}/{file_name}")
async def delete_form(scan_cccd: str, file_id: str, file_name: str):
    """
    🗑️ Xóa form
    """
    try:
        result = storage.delete_form(scan_cccd, file_id, file_name)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in delete endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=FormStats)
async def get_stats():
    """
    📊 Lấy thống kê lưu trữ
    """
    try:
        stats = storage.get_stats()
        return FormStats(**stats)
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4️⃣ **Cập nhật Config**

```python
# identifill_service/app/core/config.py - THÊM

class Settings(BaseSettings):
    # ... existing settings ...

    # 📁 Storage Configuration
    STORAGE_DIR: str = "data"
    DATABASE_PATH: str = "data/legalrag.db"
```

### 5️⃣ **Cập nhật Main.py**

```python
# identifill_service/main.py - THÊM initialization

from fastapi import FastAPI
from app.core.database import db

app = FastAPI(...)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Initializing database...")
    # Database auto-initializes when imported
    logger.info("✅ Database ready")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

---

## 📊 **Database Schema Visualization**

```
┌─────────────────────────────────────────┐
│          CCCD_USERS TABLE               │
├─────────────────────────────────────────┤
│ id (PK)   | scan_cccd (UK) | scan_ho_ten│
├─────────────────────────────────────────┤
│ 1         | 079123456789   | Nguyễn Văn A│
│ 2         | 082987654321   | Trần Thị B  │
└─────────────────────────────────────────┘
            1:N
            ↓
┌─────────────────────────────────────────┐
│        STORED_FORMS TABLE               │
├─────────────────────────────────────────┤
│ id | file_id | scan_cccd | form_name    │
├─────────────────────────────────────────┤
│ 1  | uuid-1  | 079123... | contract    │
│ 2  | uuid-2  | 079123... | request     │
│ 3  | uuid-3  | 082987... | invoice     │
└─────────────────────────────────────────┘
```

---

## 🎯 **Summary: SQLite + File System Hybrid**

### ✅ **LỢI ÍCH:**

1. **Đơn giản**: SQLite built-in Python, không cần cài DB server
2. **Dễ backup**: Copy 1 file `.db` + `data/scanned_documents/` folder
3. **Dễ query**: SQL để tìm form nhanh
4. **Transaction**: Đảm bảo data integrity
5. **Scaling**: Dễ migrate sang PostgreSQL sau
6. **Local friendly**: Hoạt động 100% offline

### 📁 **Cấu Trúc Cuối Cùng:**

```
project/
├── data/
│   ├── legalrag.db                    # ⭐ Metadata (SQLite)
│   └── scanned_documents/
│       ├── 079123456789/              # CCCD number
│       │   └── forms/
│       │       ├── contract_20251025_103000.docx
│       │       └── request_20251025_145500.docx
│       └── 082987654321/
│           └── forms/
│               └── invoice_20251025_160200.docx
├── identifill_service/
│   ├── app/
│   │   ├── api/v1/forms.py            # ✅ API endpoints
│   │   ├── services/form_storage_service.py  # ✅ Service logic
│   │   └── core/database.py           # ✅ SQLite manager
│   └── main.py
└── ...
```

---

## 🚀 **IMPLEMENTATION STEPS**

### Step 1: Create Backend Files

- ✅ `identifill_service/app/core/database.py` (SQLite setup)
- ✅ `identifill_service/app/services/form_storage_service.py` (Service)
- ✅ Update `identifill_service/app/api/v1/forms.py` (Endpoints)
- ✅ Update `identifill_service/main.py` (Initialize DB)

### Step 2: Create Frontend (Simple)

- ✅ `frontend/src/api/form-storage-api.ts` (API calls)
- ✅ `frontend/src/hooks/useFormStorage.ts` (State management)

### Step 3: Test

- ✅ Save form → Check `data/legalrag.db`
- ✅ List forms → Query database
- ✅ Download form → Get from file system

---

## ✨ **DATABASE QUERIES CHEAT SHEET**

```bash
# Check database
sqlite3 data/legalrag.db

# Query users
SELECT * FROM cccd_users;

# Query forms
SELECT * FROM stored_forms WHERE scan_cccd = '079123456789';

# Count forms per user
SELECT scan_cccd, COUNT(*) as form_count
FROM stored_forms
GROUP BY scan_cccd;

# Get total storage
SELECT SUM(file_size) FROM stored_forms;
```

---

## 🎓 **Vì Sao Chọn SQLite + File System?**

```
So sánh lựa chọn:

❌ File System Only:
- Khó query (phải read tất cả files)
- Khó backup (phức tạp)
- Khó migrate

✅ SQLite + File System:
- Dễ query (SQL)
- Dễ backup (1 DB file + 1 folder)
- Dễ migrate (SQL → PostgreSQL)
- Không cần DB server

❌ PostgreSQL Docker:
- Overkill cho local project
- Extra complexity
- Không cần bây giờ
```

**Bạn đủ rõ để bắt đầu implement chưa? 🚀**
