import requests
import json
from pathlib import Path

# Test configuration
IDENTIFILL_URL = "http://localhost:8002"
ADMIN_URL = "http://localhost:8001"

print("=" * 60)
print("🧪 Testing Download & Storage Flow")
print("=" * 60)

# Step 1: Check database state before
print("\n1️⃣ Checking database state BEFORE download...")
db_path = Path("d:\\Personal\\LegalRAG_OCR\\data\\legalrag.db")
if db_path.exists():
    print(f"   ✅ Database exists: {db_path.stat().st_size} bytes")
else:
    print(f"   ❌ Database not found: {db_path}")

# Step 2: Simulate CCCD scan data
print("\n2️⃣ Creating test form with CCCD data...")
test_cccd_data = {
    "scan_cccd": "084201000001",
    "scan_ho_ten": "Nguyễn Văn A",
    "scan_ngay_sinh": "01011990",
    "scan_gioi_tinh": "Nam",
    "scan_dia_chi": "123 Đường ABC, Hà Nội",
    "scan_ngay_cap": "01012020"
}

# Step 3: Create a test form file
print("\n3️⃣ Creating test form file...")
test_form_content = "Đơn đề nghị cấp CCCD\n" + json.dumps(test_cccd_data, indent=2, ensure_ascii=False)
test_file = Path("d:\\Personal\\LegalRAG_OCR\\data\\test_form.txt")
test_file.parent.mkdir(parents=True, exist_ok=True)
test_file.write_text(test_form_content, encoding="utf-8")
print(f"   ✅ Created test file: {test_file}")

# Step 4: Call identifill /save endpoint
print("\n4️⃣ Calling identifill-service /save endpoint...")
try:
    with open(test_file, "rb") as f:
        files = {
            "form_file": ("test_form.txt", f, "text/plain"),
        }
        data = {
            "scan_cccd": test_cccd_data["scan_cccd"],
            "scan_ho_ten": test_cccd_data["scan_ho_ten"],
            "form_name": "Khai_sinh_test",
        }
        
        response = requests.post(
            f"{IDENTIFILL_URL}/api/v1/storage/save",
            files=files,
            data=data,
            timeout=10
        )
        
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        file_id = result.get("file_id")
        print(f"   ✅ Form saved with ID: {file_id}")
    else:
        print(f"   ❌ Failed to save form")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 5: Check database state after
print("\n5️⃣ Checking database state AFTER download...")
import sqlite3
try:
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Check CCCD users
    c.execute("SELECT COUNT(*) FROM cccd_users")
    count_users = c.fetchone()[0]
    print(f"   ✅ CCCD Users: {count_users} rows")
    
    # Check stored forms
    c.execute("SELECT COUNT(*) FROM stored_forms")
    count_forms = c.fetchone()[0]
    print(f"   ✅ Stored Forms: {count_forms} rows")
    
    # Show form details
    if count_forms > 0:
        c.execute("SELECT file_id, scan_cccd, form_name FROM stored_forms ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        print(f"\n   Latest form:")
        print(f"      - File ID: {row[0]}")
        print(f"      - CCCD: {row[1]}")
        print(f"      - Form Name: {row[2]}")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Step 6: Test admin-service list endpoint
print("\n6️⃣ Testing admin-service /list endpoint...")
try:
    response = requests.get(f"{ADMIN_URL}/api/v1/storage/list", timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        # Handle both list and dict responses
        forms = data if isinstance(data, list) else data.get("forms", [])
        print(f"   ✅ Found {len(forms)} forms in admin service")
        if forms:
            first_form = forms[0] if isinstance(forms[0], dict) else None
            if first_form:
                print(f"      - CCCD: {first_form.get('scan_cccd')}")
                print(f"      - Form Name: {first_form.get('form_name')}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Flow test complete!")
print("=" * 60)
