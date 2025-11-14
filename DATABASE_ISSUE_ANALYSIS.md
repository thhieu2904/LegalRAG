# 🚨 CRITICAL ISSUE FOUND - DATABASE MISMATCH

## 📊 PROBLEM SUMMARY

Your data is **NOT** showing up in the admin panel because:

**Two different database files are being used:**

1. **identifill_service/data/legalrag.db** ✅ Has 1 record

   - When you download form: Data is saved HERE
   - Columns: id, file_id, scan_cccd, form_name, file_name, file_type, file_size, created_at
   - Data: CCCD 079987654321, Form: Khai_sinh_20251025_124533.docx

2. **data/legalrag.db** ❌ Has 0 records
   - When you view admin panel: Data is read from HERE
   - Columns: form_id, scan_cccd, scan_ho_ten, filename, file_size, created_at, updated_at, form_path
   - Data: EMPTY (0 records)

---

## 🔍 ROOT CAUSE

### identifill_service/app/core/database.py (Line 14)

```python
DB_PATH = Path("data/legalrag.db")  # ❌ RELATIVE PATH!
```

When identifill_service runs, it creates: `identifill_service/data/legalrag.db`

### admin_service/app/core/database.py

```python
# Somewhere it points to: data/legalrag.db  # ❌ DIFFERENT LOCATION!
```

When admin_service runs, it creates: `data/legalrag.db`

---

## ✅ SOLUTION

We need to make both services use the **same database file**.

**Option 1: Update identifill_service to use shared database** (RECOMMENDED)

Edit `identifill_service/app/core/database.py`:

```python
# Change from:
DB_PATH = Path("data/legalrag.db")

# To (absolute path from project root):
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "legalrag.db"
# This resolves to: d:\Personal\LegalRAG_OCR\data\legalrag.db
```

**Option 2: Configure via environment variable**

```python
import os
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "../../../data/legalrag.db"))
```

---

## 📁 FILE STRUCTURE BEFORE FIX

```
d:\Personal\LegalRAG_OCR\
├── data/
│   └── legalrag.db  ❌ 0 records (admin_service uses this)
├── identifill_service/
│   └── data/
│       └── legalrag.db  ✅ 1 record (identifill_service uses this)
└── ...
```

---

## 🎯 VERIFICATION STEPS

After fix, run this to verify:

```bash
# 1. Check both databases are the same (one file)
Get-ChildItem -Recurse -Filter "legalrag.db" | Select FullName

# 2. Should see only: d:\Personal\LegalRAG_OCR\data\legalrag.db

# 3. Verify database has the data:
python -c "import sqlite3; conn = sqlite3.connect('data/legalrag.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM stored_forms'); print('Records:', c.fetchone()[0]); conn.close()"

# Should show: Records: 1
```

---

## 🔧 IMPLEMENTATION STEPS

1. **Fix identifill_service database path**

   - Update DB_PATH to use absolute path from project root
   - Delete old: `identifill_service/data/legalrag.db`

2. **Delete old identifill database**

   ```bash
   Remove-Item identifill_service/data/legalrag.db -Force
   ```

3. **Restart services**

   - Stop identifill_service
   - Delete `identifill_service/data/` directory (optional)
   - Restart identifill_service
   - It will now use: `data/legalrag.db` (shared with admin_service)

4. **Test the flow**
   - Fill form with CCCD
   - Download
   - Check admin panel → Should now show the form!

---

## 📋 EXPECTED RESULT AFTER FIX

```
✅ File exists: d:\Personal\LegalRAG_OCR\data\legalrag.db
   Records: 1 (from your recent download)
   - CCCD: 079987654321
   - Form: Khai_sinh_20251025_124533.docx
```

Admin panel → Quản lý Form → Should see the form in the list!

---

## 🎉 WHY THIS HAPPENED

- identifill_service has its own database module (created independently)
- admin_service has its own database module (created separately)
- They both use `Path("data/legalrag.db")` but different relative paths
- Result: **Two separate databases in different locations**

---

## 📌 NEXT STEP

Ready to implement the fix? I'll:

1. Update identifill_service database path
2. Clean up old database files
3. Test to verify everything works
4. Commit the changes

Should I proceed? 🚀
