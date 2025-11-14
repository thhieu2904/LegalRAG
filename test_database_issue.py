#!/usr/bin/env python
"""
🔍 Database Diagnostic Tool
Check both databases and identify the issue
"""

import sqlite3
import os

print("=" * 60)
print("🔍 DATABASE DIAGNOSTIC REPORT")
print("=" * 60)

# Database 1: Root database (admin_service)
db1_path = "data/legalrag.db"
print(f"\n📦 DATABASE 1: {db1_path}")
print("-" * 60)

if os.path.exists(db1_path):
    conn1 = sqlite3.connect(db1_path)
    c1 = conn1.cursor()
    
    # Check schema
    c1.execute("PRAGMA table_info(stored_forms)")
    schema = c1.fetchall()
    print(f"✅ File exists")
    print(f"   Schema columns: {[row[1] for row in schema]}")
    
    # Check data
    c1.execute("SELECT COUNT(*) FROM stored_forms")
    count = c1.fetchone()[0]
    print(f"   Records: {count}")
    
    conn1.close()
else:
    print(f"❌ File not found")

# Database 2: Identifill database
db2_path = "identifill_service/data/legalrag.db"
print(f"\n📦 DATABASE 2: {db2_path}")
print("-" * 60)

if os.path.exists(db2_path):
    conn2 = sqlite3.connect(db2_path)
    c2 = conn2.cursor()
    
    # Check schema
    c2.execute("PRAGMA table_info(stored_forms)")
    schema = c2.fetchall()
    print(f"✅ File exists")
    print(f"   Schema columns: {[row[1] for row in schema]}")
    
    # Check data
    c2.execute("SELECT COUNT(*) FROM stored_forms")
    count = c2.fetchone()[0]
    print(f"   Records: {count}")
    
    if count > 0:
        c2.execute("SELECT scan_cccd, form_name, file_name FROM stored_forms")
        for row in c2.fetchall():
            print(f"   - CCCD: {row[0]}, Form: {row[1]}, File: {row[2]}")
    
    conn2.close()
else:
    print(f"❌ File not found")

print("\n" + "=" * 60)
print("🚨 ISSUE ANALYSIS")
print("=" * 60)
print("""
The problem is clear:
1. identifill_service saves to: identifill_service/data/legalrag.db
2. admin_service reads from: data/legalrag.db
3. They are TWO DIFFERENT DATABASES!

Data is saving to identifill_service DB but admin panel reads from admin_service DB.

✅ SOLUTION:
Make identifill_service use the SAME database file as admin_service.
Or: Make admin_service query the identifill_service database.

Recommend: Use a shared database location or sync between services.
""")
