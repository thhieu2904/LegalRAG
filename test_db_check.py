import sqlite3
import os

db_path = 'd:\\Personal\\LegalRAG_OCR\\data\\legalrag.db'

print(f"Checking database at: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")
print(f"File size: {os.path.getsize(db_path)} bytes")

try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print(f"Tables found: {tables}")
    
    if tables:
        for table in tables:
            c.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = c.fetchone()[0]
            print(f"  {table[0]}: {count} rows")
    
    conn.close()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Error: {e}")
