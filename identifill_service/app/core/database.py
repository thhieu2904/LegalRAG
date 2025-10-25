"""
SQLite Database Manager for Form Storage
Handles all database operations for storing and retrieving form metadata
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Database:
    """SQLite Database Manager for form storage metadata"""
    
    # Use shared database at /app/data/ (volume-mounted to host ./data/)
    # Path calculation: /app/app/core/database.py -> up 3 levels -> /app/ -> /app/data/legalrag.db
    DB_PATH = Path(__file__).parent.parent.parent / "data" / "legalrag.db"
    
    def __init__(self):
        """Initialize database and create tables if not exist"""
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
        logger.info(f"✅ Database initialized at: {self.DB_PATH}")
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(str(self.DB_PATH))
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
        logger.info("✅ Table 'cccd_users' initialized")
        
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
        logger.info("✅ Table 'stored_forms' initialized")
        
        # Index for faster queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scan_cccd 
        ON stored_forms(scan_cccd)
        """)
        logger.info("✅ Index 'idx_scan_cccd' created")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialization complete")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection with dict-like rows"""
        conn = sqlite3.connect(str(self.DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    
    def save_cccd_user(self, scan_cccd: str, scan_ho_ten: str) -> bool:
        """
        Save or update CCCD user
        
        Args:
            scan_cccd: 12-digit CCCD number
            scan_ho_ten: User full name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
            INSERT INTO cccd_users (scan_cccd, scan_ho_ten, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(scan_cccd) DO UPDATE SET
                scan_ho_ten = excluded.scan_ho_ten,
                updated_at = excluded.updated_at
            """, (scan_cccd, scan_ho_ten, now, now))
            
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
        """
        Add form record to database
        
        Args:
            file_id: Unique file identifier (UUID)
            scan_cccd: CCCD number
            form_name: Form type (e.g., "contract", "request")
            file_name: Actual file name with extension
            file_type: File type (default: "docx")
            file_size: File size in bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
            INSERT INTO stored_forms 
            (file_id, scan_cccd, form_name, file_name, file_type, file_size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, scan_cccd, form_name, file_name, file_type, file_size, now))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Added form record: {file_id} for CCCD: {scan_cccd}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding form record: {e}")
            return False
    
    def get_forms_by_cccd(self, scan_cccd: str) -> List[Dict[str, Any]]:
        """
        Get all forms for a specific CCCD
        
        Args:
            scan_cccd: CCCD number
            
        Returns:
            List of form records (dict)
        """
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
    
    def get_cccd_user(self, scan_cccd: str) -> Optional[Dict[str, Any]]:
        """
        Get CCCD user info
        
        Args:
            scan_cccd: CCCD number
            
        Returns:
            User dict or None if not found
        """
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
                logger.info(f"✅ Retrieved CCCD user: {scan_cccd}")
                return dict(row)
            
            logger.warning(f"⚠️ CCCD user not found: {scan_cccd}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting CCCD user: {e}")
            return None
    
    def delete_form_record(self, file_id: str) -> bool:
        """
        Delete form record from database
        
        Args:
            file_id: File ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM stored_forms WHERE file_id = ?", (file_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"✅ Deleted form record: {file_id}")
                return True
            else:
                logger.warning(f"⚠️ No record found to delete: {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting form record: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dict with total_users, total_forms, total_storage info
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Count users
            cursor.execute("SELECT COUNT(*) FROM cccd_users")
            user_count = cursor.fetchone()[0]
            
            # Count forms
            cursor.execute("SELECT COUNT(*) FROM stored_forms")
            form_count = cursor.fetchone()[0]
            
            # Get total storage
            cursor.execute("SELECT SUM(file_size) FROM stored_forms")
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            stats = {
                "total_users": user_count,
                "total_forms": form_count,
                "total_storage_bytes": total_size,
                "total_storage_mb": round(total_size / (1024**2), 2)
            }
            
            logger.info(f"✅ Database stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {
                "total_users": 0,
                "total_forms": 0,
                "total_storage_bytes": 0,
                "total_storage_mb": 0
            }


# Singleton instance
db = Database()
