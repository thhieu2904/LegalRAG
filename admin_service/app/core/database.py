"""
💾 DATABASE INITIALIZATION
Initialize SQLite database and create tables for storage management
"""

import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DB_PATH = "data/legalrag.db"


def init_database():
    """
    Initialize database and create tables if they don't exist
    """
    try:
        # Create data directory if it doesn't exist
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Database directory ready: {db_dir}")

        # Connect to database (creates it if it doesn't exist)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create stored_forms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stored_forms (
                form_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_cccd TEXT NOT NULL,
                scan_ho_ten TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                form_path TEXT
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scan_cccd 
            ON stored_forms(scan_cccd)
        """)

        conn.commit()
        conn.close()

        logger.info(f"✅ Database initialized: {DB_PATH}")
        logger.info("✅ Table 'stored_forms' created")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def verify_database():
    """
    Verify database and table exist
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='stored_forms'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            logger.info("✅ Database verification: stored_forms table exists")
            return True
        else:
            logger.error("❌ Database verification: stored_forms table NOT found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False


def get_table_info():
    """
    Get table schema information
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(stored_forms)")
        columns = cursor.fetchall()
        conn.close()
        
        info = {
            "table": "stored_forms",
            "columns": [
                {
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default": col[4],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        }
        
        return info
        
    except Exception as e:
        logger.error(f"❌ Error getting table info: {e}")
        return None


if __name__ == "__main__":
    # For standalone testing
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 Initializing database...")
    init_database()
    
    print("\n✅ Verifying database...")
    if verify_database():
        print("✅ Database verification passed")
        info = get_table_info()
        if info:
            print("\n📋 Table Schema:")
            print(f"Table: {info['table']}")
            for col in info['columns']:
                print(f"  - {col['name']:20s} {col['type']:15s} PK={col['primary_key']} NN={col['not_null']}")
    else:
        print("❌ Database verification failed")
        sys.exit(1)
