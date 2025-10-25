# 🧪 QUICK TESTING GUIDE - After Database Fix

## ✅ Problem Fixed

Your admin panel error: `{"detail":"no such table: cccd_users"}`

**Root cause**: admin_service was trying to create its own database schema (conflicting with identifill_service)

**Solution**: Removed conflicting database initialization from admin_service. Now both services use the same shared database created by identifill_service.

---

## 🚀 IMMEDIATE STEPS

### 1. Stop All Services

```bash
# Ctrl+C in each terminal running the services
```

### 2. Kill Any Hanging Processes

```bash
# Make sure no Python processes are running on ports 8000, 8001, 8002, 5173
# Check Task Manager or use:
netstat -ano | findstr "8000\|8001\|8002\|5173"
```

### 3. Restart Services (In New Terminals)

**Terminal 1 - Frontend:**

```bash
cd frontend
npm run dev
```

**Terminal 2 - RAG Service:**

```bash
conda activate LegalRAG
cd rag_service
python main.py
```

**Terminal 3 - Identifill Service:**

```bash
conda activate identifill_env
cd identifill_service
python main.py
```

**Terminal 4 - Admin Service:**

```bash
cd admin_service
python main.py
```

---

## ✅ VERIFY DATABASE IS READY

```bash
# Run verification script
python verify_fix.py
```

Should show:

```
✅ Database Location: data/legalrag.db
✅ Tables: cccd_users, stored_forms
✅ Status: Ready!
```

---

## 🎯 TEST THE FLOW

### Test 1: Basic Admin Panel Load

1. Open browser → `http://localhost:5173` (or 3000)
2. Go to Admin → "Quản lý Form" menu
3. ❌ Should NOT see `{"detail":"no such table: cccd_users"}` error
4. ✅ Should see empty list (0 forms) or loading state

### Test 2: Download Form & See in Admin Panel

1. Go to form page
2. Fill form with CCCD data (or scan CCCD)
3. Click Download
4. ✅ Browser downloads file
5. Go back to Admin → "Quản lý Form"
6. ✅ Form should appear in list!
7. Can click user row to see forms

### Test 3: Download from Admin Panel

1. In admin panel, with form showing
2. Click the download icon/button
3. ✅ File downloads again

### Test 4: Delete from Admin Panel

1. In admin panel, with form showing
2. Click delete button
3. Confirm deletion
4. ✅ Form disappears from list
5. ✅ File is deleted from disk

---

## 🔍 VERIFICATION STEPS

### Check Database Has Tables

```bash
python -c "import sqlite3; c = sqlite3.connect('data/legalrag.db').cursor(); c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print('Tables:', [t[0] for t in c.fetchall()])"
```

Should show: `['cccd_users', 'stored_forms', 'sqlite_sequence']`

### Check Database Has Data (After Download)

```bash
python -c "import sqlite3; c = sqlite3.connect('data/legalrag.db').cursor(); c.execute('SELECT COUNT(*) FROM stored_forms'); print('Forms:', c.fetchone()[0])"
```

Should show: `Forms: 1` (or more after multiple downloads)

### Check Admin Service Starts Without Errors

Look at admin_service console output:

```
❌ Should NOT see: "Database initialization..."
✅ Should see: "🚀 Uvicorn running on..."
```

---

## 🐛 TROUBLESHOOTING

### If you still see "no such table: cccd_users"

**Solution 1: Restart identifill_service first**

- identifill_service must start BEFORE admin_service
- It creates the database tables

**Solution 2: Delete database and let it recreate**

```bash
Remove-Item data/legalrag.db -Force
# Then restart identifill_service - it will create new DB with correct schema
```

**Solution 3: Check admin service logs**
Look for error messages:

```
✅ Should see: "🚀 Admin Service running"
❌ Should NOT see: "Database", "init_database", "verify_database"
```

### If admin panel is blank (no error but shows nothing)

**Possible causes:**

1. identifill_service not started yet
2. No forms downloaded yet (empty is OK!)
3. CORS issues - check browser console

**Solution:**

1. Make sure ALL services are running
2. Download a form first
3. Check browser DevTools → Network tab for API errors

### If download button doesn't work in admin panel

**Possible causes:**

1. File doesn't exist on disk
2. Path is wrong
3. Admin service not running

**Solution:**

1. Check folder: `data/scanned_documents/` exists
2. Check file exists with right name
3. Check admin service console for errors

---

## 📊 EXPECTED BEHAVIOR

### Admin Panel (Before any downloads)

```
Statistics:
- Total Users: 0
- Total Forms: 0
- Total Size: 0 MB

Users List:
(empty)

Message: "No users with saved forms yet"
```

### Admin Panel (After 1 download with CCCD)

```
Statistics:
- Total Users: 1
- Total Forms: 1
- Total Size: ~200 KB

Users List:
- Row 1: CCCD | Name | 1 form | Download | Delete
```

### Admin Panel (Detail view for user)

```
Forms for User:
- File 1 | Size | Date | Download | Delete
```

---

## 🎯 SUCCESS CHECKLIST

- [ ] Services start without database errors
- [ ] Admin panel loads (no "no such table" error)
- [ ] Can download form with CCCD
- [ ] Form appears in admin panel list
- [ ] Can download form again from admin panel
- [ ] Can delete form from admin panel
- [ ] Form disappears after delete
- [ ] Can test multiple downloads

If all ✅, the fix works perfectly! 🎉

---

## 📞 DEBUGGING

If something still doesn't work:

1. **Check service status:**

   ```bash
   # Each service should print startup message in console
   ```

2. **Check database directly:**

   ```bash
   python verify_fix.py
   ```

3. **Check browser console:**

   - F12 → Console tab
   - Look for API error messages

4. **Check service logs:**

   - Look at console output of each service
   - Look for error messages

5. **Check files exist:**
   ```bash
   # Should exist after download:
   ls -la data/scanned_documents/CCCD_NUMBER/forms/
   ```

---

**Status**: Fix Complete ✅  
**Next Step**: Run the tests above  
**Expected Result**: Admin panel works perfectly! 🚀

Good luck! 🎉
