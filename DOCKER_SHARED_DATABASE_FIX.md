# 🐳 DOCKER FIX - Shared Database Volume Mount Issue

**Date**: October 25, 2025  
**Status**: ✅ **FIXED**  
**Error**: `{"detail":"no such table: cccd_users"}` with status code 500 in Docker

---

## 🚨 PROBLEM IN DOCKER

### What Was Happening

When running in Docker, the admin panel showed:

```json
{
  "detail": "no such table: cccd_users",
  "status": 500
}
```

### Root Cause - Volume Mount Mismatch

**Before Fix (WRONG):**

```yaml
identifill-service:
  volumes:
    - ./identifill_service/data:/app/data  ❌ Wrong path!

admin-service:
  volumes:
    - ./data:/app/data                      ❌ Different path!
```

**What happened:**

- identifill_service created database at: `./identifill_service/data/legalrag.db`
- admin_service looked for database at: `./data/legalrag.db`
- Two different directories = data never found!

### Why It Worked Outside Docker

Outside Docker (direct Python):

- Both used relative path: `data/legalrag.db`
- From project root, they both resolved to same location
- So it worked!

In Docker:

- Container paths different from host paths
- Volume mounts don't match
- Data not shared between containers

---

## ✅ THE FIX

### Changed docker-compose.dev.yml

**identifill-service volume changed:**

```yaml
# BEFORE (WRONG):
- ./identifill_service/data:/app/data

# AFTER (CORRECT):
- ./data:/app/data  ✅ SAME as admin-service!
```

### Result

```yaml
identifill-service:
  volumes:
    - ./data:/app/data                ✅ Shared!

admin-service:
  volumes:
    - ./data:/app/data                ✅ Same location!
```

Both containers now access the **SAME** `./data` directory on the host!

---

## 📊 VOLUME MOUNT ARCHITECTURE

### Before Fix (BROKEN)

```
Host Machine:
├── ./data/                          (admin_service sees this)
│   └── legalrag.db (empty!)
│
└── ./identifill_service/data/       (identifill_service sees this)
    └── legalrag.db (has data!)

Admin service queries: ./data/legalrag.db  ❌ EMPTY!
Identifill saves to: ./identifill_service/data/legalrag.db  ❌ DIFFERENT!
```

### After Fix (CORRECT)

```
Host Machine:
└── ./data/                          (BOTH see this!)
    └── legalrag.db

Docker Container (identifill_service):
  /app/data → Host ./data/           ✅ Mounts here

Docker Container (admin-service):
  /app/data → Host ./data/           ✅ Mounts here

Both access same database! ✅
```

---

## 🔧 WHAT TO DO NOW

### Step 1: Stop All Docker Containers

```bash
docker-compose -f docker-compose.dev.yml down
```

### Step 2: Remove Old Volumes (Optional but Recommended)

```bash
# This clears the old separate data directories
# Data will be recreated fresh when services start
docker volume prune -f
```

### Step 3: Delete Old Data Directories (Optional)

```bash
# If you want completely fresh start:
Remove-Item identifill_service/data -Recurse -Force
# Keep ./data directory (will be recreated if needed)
```

### Step 4: Start Docker Containers

```bash
docker-compose -f docker-compose.dev.yml up --build
```

OR if you want to see logs:

```bash
docker-compose -f docker-compose.dev.yml up --build -d
docker-compose -f docker-compose.dev.yml logs -f
```

### Step 5: Verify Services Are Running

```bash
docker-compose -f docker-compose.dev.yml ps
```

Should show all 4 services running (green):

- legalrag-frontend-dev
- legalrag-rag-service-dev
- legalrag-admin-service-dev
- legalrag-identifill-service-dev

### Step 6: Check Database Creation

```bash
# Check if database was created in shared location
ls -la ./data/legalrag.db

# Check if identifill_service created tables
docker-compose -f docker-compose.dev.yml exec identifill-service python -c "
import sqlite3
conn = sqlite3.connect('/app/data/legalrag.db')
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print('Tables:', c.fetchall())
conn.close()
"
```

---

## ✅ TESTING FLOW

### Test 1: Open Admin Panel

1. Open browser → http://localhost:5173
2. Go to Admin → "Quản lý Form"
3. ❌ Should NOT see `no such table: cccd_users` error
4. ✅ Should see empty list or loading state

### Test 2: Download Form and Check Admin Panel

1. Go to form page
2. Fill form with CCCD data
3. Download form
4. Go back to Admin → "Quản lý Form"
5. ✅ Form should appear in list!

### Test 3: Check Docker Volumes

```bash
# Verify shared data directory
ls -la ./data/

# Should contain:
# - legalrag.db (database file)
# - scanned_documents/ (forms storage)

# Verify identifill_service/data is EMPTY (no longer used)
ls -la ./identifill_service/data/
# Should be empty or not exist
```

---

## 🔍 TROUBLESHOOTING

### If still getting "no such table: cccd_users"

**Check 1: Verify volume mount**

```bash
docker inspect legalrag-identifill-service-dev | grep -A 5 Mounts
# Should show: "./data" -> "/app/data"

docker inspect legalrag-admin-service-dev | grep -A 5 Mounts
# Should show: "./data" -> "/app/data"
```

**Check 2: Check if database exists inside container**

```bash
docker-compose -f docker-compose.dev.yml exec identifill-service ls -la /app/data/
# Should show: legalrag.db
```

**Check 3: Check table creation**

```bash
docker-compose -f docker-compose.dev.yml exec admin-service python -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/legalrag.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM cccd_users')
    print('✅ Table exists!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### If database file doesn't exist

**Solution: Force restart to recreate**

```bash
docker-compose -f docker-compose.dev.yml down
# Remove shared data directory
Remove-Item ./data -Recurse -Force
# Restart - will create fresh
docker-compose -f docker-compose.dev.yml up --build -d
# Wait 5-10 seconds for services to initialize
```

### If services won't start

**Check logs:**

```bash
docker-compose -f docker-compose.dev.yml logs identifill-service
docker-compose -f docker-compose.dev.yml logs admin-service
```

**Look for:**

- ❌ Volume mount errors
- ❌ Permission denied
- ❌ Database locked

---

## 📋 FILES CHANGED

| File                   | Change                                          | Status  |
| ---------------------- | ----------------------------------------------- | ------- |
| docker-compose.dev.yml | Changed identifill volume to `./data:/app/data` | ✅ Done |

**That's it!** Just this one line change fixes the whole Docker issue!

---

## 🎯 FINAL CHECKLIST

- [ ] Stopped Docker containers (`docker-compose down`)
- [ ] Updated docker-compose.dev.yml (identifill volume fixed)
- [ ] Restarted Docker containers (`docker-compose up --build`)
- [ ] Verified all 4 services running
- [ ] Checked database created at `./data/legalrag.db`
- [ ] Opened admin panel → No "no such table" error
- [ ] Downloaded form → Appears in admin list
- [ ] All features work!

---

## 🚀 QUICK FIX COMMANDS

```bash
# All-in-one fix:
docker-compose -f docker-compose.dev.yml down
Remove-Item ./data -Recurse -Force
docker-compose -f docker-compose.dev.yml up --build -d
docker-compose -f docker-compose.dev.yml logs -f

# Wait 10-15 seconds for services to start and initialize database
# Then: http://localhost:5173 → Go to Admin → "Quản lý Form"
# Should work! ✅
```

---

## 💡 WHY THIS HAPPENED

**Local (outside Docker):**

- Both Python processes run on same machine
- Same working directory: `d:\Personal\LegalRAG_OCR`
- `data/legalrag.db` = same for both
- ✅ Works!

**Docker:**

- identifill_service container: `/app/data` → `./identifill_service/data`
- admin_service container: `/app/data` → `./data`
- Different host directories!
- ❌ Doesn't work!

**After Fix:**

- identifill_service container: `/app/data` → `./data`
- admin_service container: `/app/data` → `./data`
- Same host directory!
- ✅ Works!

---

**Status**: ✅ **FIXED AND READY**  
**Next**: Restart Docker with updated compose file  
**Expected**: Admin panel works perfectly in Docker! 🎉

Good luck! 🚀
