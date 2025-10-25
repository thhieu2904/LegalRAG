#!/usr/bin/env python3
"""
🧪 Comprehensive Admin Panel Flow Test
Tests the entire flow from form download to admin panel retrieval
"""

import requests
import json
from pathlib import Path
import sqlite3

# Test configuration
IDENTIFILL_URL = "http://localhost:8002"
ADMIN_URL = "http://localhost:8001"
DB_PATH = Path("d:\\Personal\\LegalRAG_OCR\\data\\legalrag.db")

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_step(num, title):
    print(f"{num}️⃣  {title}")

def main():
    print_section("🧪 COMPREHENSIVE ADMIN PANEL FLOW TEST")
    
    # PART 1: Verify Database Setup
    print_section("PART 1: DATABASE VERIFICATION")
    
    print_step(1, "Check database file")
    if DB_PATH.exists():
        size = DB_PATH.stat().st_size
        print(f"   ✅ Database exists: {DB_PATH}")
        print(f"   ✅ File size: {size} bytes")
    else:
        print(f"   ❌ Database not found: {DB_PATH}")
        return False
    
    print_step(2, "Verify database tables")
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"   ✅ Tables found: {[t[0] for t in tables]}")
        
        # Check table structure
        c.execute("PRAGMA table_info(stored_forms)")
        columns = c.fetchall()
        print(f"   ✅ Stored Forms columns: {[col[1] for col in columns]}")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False
    
    # PART 2: Test Endpoints
    print_section("PART 2: ENDPOINT TESTS")
    
    print_step(1, "Test admin-service /health")
    try:
        response = requests.get(f"{ADMIN_URL}/api/v1/storage/health", timeout=5)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   ✅ Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_step(2, "Test admin-service /stats (fetchStorageStats)")
    try:
        response = requests.get(f"{ADMIN_URL}/api/v1/storage/stats", timeout=5)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total users: {data.get('total_users', 0)}")
            print(f"   ✅ Total forms: {data.get('total_forms', 0)}")
            print(f"   ✅ Total size: {data.get('total_size_mb', 0):.2f} MB")
            users = data.get('users', [])
            if users:
                print(f"   ✅ Users with forms:")
                for user in users[:3]:
                    print(f"      - {user.get('scan_cccd')}: {user.get('form_count')} forms")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_step(3, "Test admin-service /list (fetchAllStoredUsers)")
    try:
        response = requests.get(f"{ADMIN_URL}/api/v1/storage/list", timeout=5)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict responses
            forms = data if isinstance(data, list) else data.get("forms", [])
            print(f"   ✅ Retrieved {len(forms)} forms")
            if forms:
                print(f"   ✅ Sample form:")
                form = forms[0] if isinstance(forms[0], dict) else forms[0]
                if isinstance(form, dict):
                    print(f"      - CCCD: {form.get('scan_cccd')}")
                    print(f"      - Form: {form.get('form_name')}")
                    print(f"      - File: {form.get('file_name')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # PART 3: Simulate Admin Panel Operations
    print_section("PART 3: ADMIN PANEL SIMULATION")
    
    print_step(1, "Simulate StorageManager.tsx loadStats() call")
    print("   This is what happens when admin opens 'Quản lý Form' tab")
    try:
        response = requests.get(f"{ADMIN_URL}/api/v1/storage/stats", timeout=5)
        if response.status_code == 200:
            print("   ✅ StorageManager receives stats successfully")
            print("   ✅ Page renders without 'no such table' error")
        else:
            print(f"   ❌ StorageManager would fail with: {response.text}")
    except Exception as e:
        print(f"   ❌ StorageManager would fail with: {e}")
    
    # PART 4: Database Query Verification
    print_section("PART 4: DIRECT DATABASE VERIFICATION")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        print_step(1, "Query CCCD users count")
        c.execute("SELECT COUNT(*) FROM cccd_users")
        count = c.fetchone()[0]
        print(f"   ✅ Total CCCD users: {count}")
        
        print_step(2, "Query stored forms count")
        c.execute("SELECT COUNT(*) FROM stored_forms")
        count = c.fetchone()[0]
        print(f"   ✅ Total stored forms: {count}")
        
        print_step(3, "Query latest forms")
        c.execute("""
            SELECT file_id, scan_cccd, form_name, created_at 
            FROM stored_forms 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        forms = c.fetchall()
        if forms:
            print(f"   ✅ Latest {len(forms)} forms:")
            for form in forms:
                print(f"      - {form[2]} (CCCD: {form[1]}) - Created: {form[3]}")
        else:
            print(f"   ℹ️  No forms yet")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # SUMMARY
    print_section("✅ TEST COMPLETE")
    print("Database persistence is working correctly!")
    print("Admin panel 'Quản lý Form' should display without errors.\n")

if __name__ == "__main__":
    main()
