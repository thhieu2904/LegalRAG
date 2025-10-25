#!/usr/bin/env python3
"""Query database to verify stored forms"""

import sqlite3

db = sqlite3.connect('d:\\Personal\\LegalRAG_OCR\\identifill_service\\data\\legalrag.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

print('🔍 Database Contents:')
print('=' * 70)
print()

# Show cccd_users
print('📋 CCCD Users Table:')
cursor.execute('SELECT * FROM cccd_users')
for row in cursor.fetchall():
    print(f"  - {row['scan_cccd']}: {row['scan_ho_ten']}")

print()

# Show stored_forms
print('📋 Stored Forms Table:')
cursor.execute('SELECT * FROM stored_forms ORDER BY created_at DESC')
for row in cursor.fetchall():
    print(f"  - {row['form_name']}: {row['file_name']} ({row['file_size']} bytes)")

db.close()
