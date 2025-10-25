# 🐳 DOCKER RESTART GUIDE - After Volume Fix

**Issue**: Admin panel couldn't access identifill_service database due to volume mount mismatch  
**Solution**: Updated `docker-compose.dev.yml` to share database volume  
**Status**: ✅ Ready to apply

---

## 🔄 RESTART STEPS

### Step 1: Stop All Docker Containers

```bash
cd d:\Personal\LegalRAG_OCR

# Stop all running containers
docker-compose -f docker-compose.dev.yml down

# Output should show:
# Stopping legalrag-admin-service-dev...
# Stopping legalrag-identifill-service-dev...
# Stopping legalrag-rag-service-dev...
# Stopping legalrag-frontend-dev...
# Removing containers...
```

### Step 2: Remove Old Volumes & Clean Up

```bash
# Remove volumes to start fresh
docker-compose -f docker-compose.dev.yml down -v

# Output should show:
# Removing volumes...
# (identifill_models removed)
```

### Step 3: Rebuild Images

```bash
# Rebuild all images with new configuration
docker-compose -f docker-compose.dev.yml build --no-cache

# Output should show:
# Building frontend...
# Building rag-service...
# Building admin-service...
# Building identifill-service...
# Successfully built ...
```

### Step 4: Start All Services

```bash
# Start all containers
docker-compose -f docker-compose.dev.yml up

# Wait for all services to start, look for:
# ✅ Admin Service running on 0.0.0.0:8001
# ✅ Identifill Service running on 0.0.0.0:8002
# ✅ RAG Service running on 0.0.0.0:8000
# ✅ Frontend running on 0.0.0.0:5173
```

---

## ✅ VERIFICATION CHECKLIST

### Check 1: Verify Container Status

```bash
# In a new terminal:
docker ps

# Should show 4 running containers:
# - legalrag-frontend-dev (port 5173)
# - legalrag-rag-service-dev (port 8000)
# - legalrag-admin-service-dev (port 8001)
# - legalrag-identifill-service-dev (port 8002)
```

### Check 2: Verify Volume Mounts

```bash
# Check identifill_service volume
docker inspect legalrag-identifill-service-dev | grep -A 5 "Mounts"

# Check admin_service volume
docker inspect legalrag-admin-service-dev | grep -A 5 "Mounts"

# Both should show:
# - Source: .../data
# - Destination: /app/data
# - Mode: rw (read-write!)
```

### Check 3: Check Service Logs

```bash
# Check admin_service logs
docker logs legalrag-admin-service-dev

# Should see:
# ✅ "🚀 Admin Service running..."
# ❌ Should NOT see: "no such table", "Database error"

# Check identifill_service logs
docker logs legalrag-identifill-service-dev

# Should see:
# ✅ "Database initialized at..."
# ✅ "🚀 Identifill Service running..."
```

### Check 4: Verify Database Access

```bash
# Check if database exists in shared volume
docker exec legalrag-identifill-service-dev ls -la /app/data/

# Should show:
# -rw-r--r-- ... legalrag.db

# Verify admin_service can also see it
docker exec legalrag-admin-service-dev ls -la /app/data/

# Should show SAME database file!
```

### Check 5: Test Frontend Access

```
Open browser: http://localhost:5173

✅ Frontend loads without errors
✅ Go to Admin → "Quản lý Form"
❌ Should NOT see: "no such table: cccd_users"
```

---

## 🧪 FULL E2E TEST

After Docker restart:

1. **Download Form**:

   - Go to form page
   - Scan CCCD OR fill form with CCCD field
   - Click Download
   - ✅ File downloads to browser

2. **Check Admin Panel**:

   - Go to Admin → "Quản lý Form"
   - ✅ Should see form in list!
   - ✅ Should see user CCCD and name
   - ✅ No errors!

3. **Download from Admin**:

   - Click download button on form
   - ✅ File downloads again

4. **Delete from Admin**:
   - Click delete button
   - ✅ Form disappears from list

---

## 🚨 TROUBLESHOOTING

### If containers fail to start:

```bash
# Check logs for errors
docker logs legalrag-admin-service-dev
docker logs legalrag-identifill-service-dev

# Common errors and solutions:
# ❌ "Port 8001 already in use"
#    → Other service using port, or old container still running
#    → Solution: docker-compose down -v && restart

# ❌ "Cannot find image"
#    → Build failed
#    → Solution: docker-compose build --no-cache

# ❌ "Volume permission denied"
#    → Permission issue with ./data directory
#    → Solution: Check ./data folder permissions
```

### If admin panel still shows "no such table" error:

```bash
# 1. Check database was created
docker exec legalrag-identifill-service-dev sqlite3 /app/data/legalrag.db ".tables"
# Should show: cccd_users  stored_forms

# 2. Check admin_service can access it
docker exec legalrag-admin-service-dev sqlite3 /app/data/legalrag.db ".tables"
# Should show SAME tables

# 3. If still not working:
#    - Delete ./data/legalrag.db
#    - Restart docker-compose
#    - Let identifill_service recreate database
```

### If database file doesn't persist:

```bash
# Check volume is mounted correctly
docker inspect legalrag-identifill-service-dev

# Verify under "Mounts" section:
# "Source": "...data",
# "Destination": "/app/data"

# If not correct:
# - Stop containers: docker-compose down
# - Check docker-compose.dev.yml has correct volumes
# - Restart: docker-compose up
```

---

## 📊 WHAT CHANGED

### docker-compose.dev.yml Update

**BEFORE** (Wrong):

```yaml
admin-service:
  volumes:
    - ./rag_service/data/storage:/app/data/storage:ro  ❌ Wrong path!
    - ./admin_service/app:/app/app
```

**AFTER** (Fixed):

```yaml
admin-service:
  volumes:
    - ./data:/app/data  ✅ Same as identifill!
    - ./admin_service/app:/app/app
```

**Result**: Both services now use `/app/data` pointing to same `./data` directory

---

## 🎯 QUICK SUMMARY

| Issue                        | Solution             | Status   |
| ---------------------------- | -------------------- | -------- |
| Admin can't access database  | Share data volume    | ✅ Fixed |
| Volume is read-only          | Remove `:ro` flag    | ✅ Fixed |
| Services use different paths | Both use `/app/data` | ✅ Fixed |

---

## 🚀 ONE-LINER RESTART

```bash
cd d:\Personal\LegalRAG_OCR && docker-compose -f docker-compose.dev.yml down -v && docker-compose -f docker-compose.dev.yml build --no-cache && docker-compose -f docker-compose.dev.yml up
```

---

**Status**: ✅ **READY FOR DOCKER RESTART**  
**Expected Result**: Admin panel will work with identifill_service database! 🎉

Run the steps above and let me know if you see any errors! 👀
