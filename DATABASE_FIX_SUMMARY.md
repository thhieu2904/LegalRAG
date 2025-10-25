# Database Persistence Fix - Root Cause Analysis

## 🔴 The Problem

**Symptom**: Admin panel showed error `{"detail":"no such table: stored_forms"}` even though Docker logs showed successful table creation.

**Root Cause**: Database path calculation was WRONG.

```python
# ❌ WRONG - Goes up 4 levels instead of 3
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "legalrag.db"

# File path analysis:
# __file__ = /app/app/core/database.py
# .parent = /app/app/core/
# .parent = /app/app/
# .parent = /app/
# .parent = /              ← WRONG! Should stop at /app/
# Result: /data/legalrag.db ← OUTSIDE VOLUME MOUNT!
```

## 🎯 The Solution

**Changed database path calculation to 3 levels up** (correct):

```python
# ✅ CORRECT - Goes up exactly 3 levels
DB_PATH = Path(__file__).parent.parent.parent / "data" / "legalrag.db"

# File path analysis:
# __file__ = /app/app/core/database.py
# .parent = /app/app/core/
# .parent = /app/app/
# .parent = /app/          ← STOP HERE
# Result: /app/data/legalrag.db ← INSIDE VOLUME MOUNT!
```

## 📍 Volume Mount Configuration

Docker-compose mounts:

```yaml
volumes:
  - ./data:/app/data # Host ./data/ → Container /app/data/
```

**Critical**: Files at `/data/` (root level) are NOT volume-mounted!

## 📊 Results

**BEFORE FIX**:

```
❌ Container database: /data/legalrag.db (0 bytes - NOT persisted)
❌ Host database: ./data/legalrag.db (0 bytes - empty file)
❌ No tables accessible to admin-service
❌ No data persistence across container restarts
```

**AFTER FIX**:

```
✅ Container database: /app/data/legalrag.db (28KB - IN VOLUME MOUNT)
✅ Host database: ./data/legalrag.db (28KB - PERSISTED!)
✅ Tables created: cccd_users, stored_forms
✅ Data persists across container restarts
✅ Admin-service can query tables successfully
```

## ✅ Verification

### 1. Database Files Created

```
✅ /app/data/legalrag.db (28KB in container)
✅ ./data/legalrag.db (28KB on host)
```

### 2. Tables Created

```sql
✅ cccd_users table
✅ stored_forms table
✅ idx_scan_cccd index
```

### 3. End-to-End Flow Test

```
✅ Step 1: Form save to identifill-service /save → Returns file_id
✅ Step 2: Check database → 1 CCCD user + 1 form record created
✅ Step 3: Query admin-service /list → Successfully retrieves forms
```

## 🔧 Files Modified

**identifill_service/app/core/database.py**

- Line 20: Fixed path calculation (3 levels up instead of 4)
- Added clarifying comment about volume mount location

## 🚀 Impact

- Database now persists correctly across service restarts
- Admin panel can query form storage successfully
- Complete download → save → query flow is operational
- No more "no such table" errors

## 📝 Testing Results

```
Test: test_download_flow.py

1️⃣ Database initialized: ✅ 28KB file created
2️⃣ Form saved: ✅ file_id = fc582561-e1ad-4864-bf35-0e4d9291de7c
3️⃣ Database record: ✅ CCCD user + stored form record created
4️⃣ Admin list query: ✅ Retrieved 2 forms successfully
5️⃣ Data persistence: ✅ Forms visible in both container and host
```

## 🎓 Lessons Learned

1. **Path Calculation**: When using `Path(__file__).parent`, count carefully:

   - Each `.parent` goes UP one directory level
   - In `/app/app/core/database.py`, need 3 `.parent` calls to reach `/app/`

2. **Volume Mounts**: Verify files are at the correct location:

   - Mount: `./data:/app/data`
   - Wrong location: `/data/` (not mounted)
   - Correct location: `/app/data/` (mounted)

3. **Debugging Docker Volumes**:
   - Check container path: `docker exec container ls -la /app/data/`
   - Check host path: `ls -la ./data/`
   - Both should have same file with same size
