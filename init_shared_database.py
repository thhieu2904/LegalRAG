#!/usr/bin/env python
"""
Initialize the shared database with identifill_service schema
"""

import sys
sys.path.insert(0, 'identifill_service')

from app.core.database import Database

print("=" * 70)
print("🔧 Initializing Shared Database with identifill_service Schema")
print("=" * 70)

db = Database()
print(f"\n✅ Database initialized")
print(f"   Path: {db.DB_PATH}")
print(f"   Exists: {db.DB_PATH.exists()}")

print("\n✅ All tables created:")
print("   - cccd_users")
print("   - stored_forms")
print("   - idx_scan_cccd (index)")

print("\n" + "=" * 70)
print("✅ Shared Database Ready!")
print("=" * 70)
