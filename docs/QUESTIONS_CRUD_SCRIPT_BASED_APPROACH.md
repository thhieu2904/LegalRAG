# 🚀 Script-Based VectorDB Rebuild Approach - Chi tiết phân tích

**Ngày tạo:** 11/10/2025  
**Đề xuất:** Sử dụng Python script (như `cache.py`) thay vì async background tasks

---

## 📋 TÓM TẮT ĐỀ XUẤT

### Ý tưởng chính

Thay vì sử dụng FastAPI BackgroundTasks cho VectorDB rebuild:

```python
# ❌ Old approach (trong example code)
background_tasks.add_task(rebuild_vectordb_for_document, collection, doc_id)
```

Sử dụng endpoint trigger Python script:

```python
# ✅ New approach (user's proposal)
POST /api/rebuild/trigger → spawn subprocess → run rebuild_script.py
```

### Workflow

```
User Update Questions
    ↓
Admin Service: Update questions.json file
    ↓
Admin Service: POST /api/internal/rebuild/trigger
    ↓
RAG Service: Spawn subprocess python rebuild_script.py
    ↓
RAG Service: Return immediately (script runs independently)
    ↓
rebuild_script.py: Execute full rebuild logic
    ↓
rebuild_script.py: Update status file
    ↓
User/Admin: Check status via GET /api/rebuild/status
```

---

## 🎯 PHÂN TÍCH CHI TIẾT

### ✅ ƯU ĐIỂM (PROS)

#### 1. **Process Isolation** (⭐⭐⭐⭐⭐)

**Vấn đề với BackgroundTasks:**

```python
# BackgroundTasks runs in same process as FastAPI
background_tasks.add_task(heavy_rebuild)
# If rebuild crashes → might affect other requests
# Memory spike → affects entire server
# CPU intensive → blocks event loop
```

**Solution với Script:**

```python
# Script runs in separate process
subprocess.Popen(['python', 'rebuild_script.py'])
# Script crash → server unaffected ✅
# Memory spike → isolated to script process ✅
# CPU intensive → doesn't block server ✅
```

**Kết luận:** Script approach an toàn hơn nhiều!

#### 2. **Resource Management** (⭐⭐⭐⭐⭐)

**BackgroundTasks limitations:**

- Shares memory với FastAPI process
- Shares CPU quota
- Cạnh tranh resources với request handling
- Không thể prioritize properly

**Script advantages:**

```bash
# Can use nice/ionice to control priority
nice -n 19 python rebuild_script.py  # Low CPU priority
ionice -c 3 python rebuild_script.py # Idle I/O priority

# Can limit resources with cgroups (Docker)
docker run --cpus="0.5" --memory="512m" rebuild_container

# Can run on different machine/container
docker exec rebuild_worker python rebuild_script.py
```

**Kết luận:** Kiểm soát resources tốt hơn 100%!

#### 3. **Proven & Tested Code** (⭐⭐⭐⭐⭐)

Bạn đã có `cache.py` hoạt động tốt:

```python
# rag_service/tools/cache.py - PROVEN CODE ✅
- ✅ Handle PyTorch compatibility
- ✅ Safe model loading strategies
- ✅ Proper error handling
- ✅ Logging & progress tracking
- ✅ Backup & validation
- ✅ Multi-phase rebuild (Router + Clarify)
```

**Reuse thay vì rewrite:**

```python
# ❌ Bad: Rewrite rebuild logic in FastAPI
async def _rebuild_document_vectordb(...):
    # Duplicate cache.py logic
    # Different bugs, different edge cases
    # Hard to maintain consistency

# ✅ Good: Reuse cache.py
subprocess.run(['python', 'tools/cache.py', '--collection', collection])
# Same proven logic
# Consistency guaranteed
# Less code to maintain
```

**Kết luận:** Tái sử dụng code đã proven = less risk!

#### 4. **Progress Tracking & Logging** (⭐⭐⭐⭐)

**Script có logging tốt hơn:**

```python
# cache.py already has detailed logging:
logger.info("🔄 STARTING COMPREHENSIVE CACHE REBUILD")
logger.info("📋 PHASE 1: BUILDING ROUTER CACHE")
logger.info(f"✅ Generated embeddings for {collection_name}/{doc_name}")
logger.info("🎉 COMPREHENSIVE CACHE REBUILD COMPLETE!")

# Easy to track progress:
tail -f rag_service/logs/rebuild.log

# Can write progress to file:
with open('rebuild_status.json', 'w') as f:
    json.dump({
        'status': 'running',
        'progress': '50%',
        'current_collection': 'quy_trinh_xxx',
        'documents_processed': 10,
        'documents_total': 20
    }, f)
```

**So với BackgroundTasks:**

```python
# BackgroundTasks - hard to track:
background_tasks.add_task(rebuild)
# No built-in progress tracking
# Hard to know if still running
# Hard to debug if hangs
```

**Kết luận:** Dễ monitor và debug hơn!

#### 5. **Error Recovery** (⭐⭐⭐⭐⭐)

**Script failure không crash server:**

```python
# Scenario 1: Script crashes
subprocess.run(['python', 'rebuild.py'])
# Server: Still running ✅
# Script: Exit code 1, logs error
# Action: Retry or alert admin

# Scenario 2: Script OOM
# Server: Unaffected ✅
# Script: Killed by OS
# Action: Increase script memory limit

# Scenario 3: Script hangs
# Server: Still serving requests ✅
# Script: Timeout & kill after 5 minutes
# Action: Investigate hang cause
```

**So với BackgroundTasks:**

```python
# BackgroundTasks failure:
async def rebuild_task():
    raise Exception("OOM")

# Server might be affected
# Hard to isolate failure
# No built-in timeout
```

**Kết luận:** Fault tolerance tốt hơn nhiều!

#### 6. **Flexibility & Reusability** (⭐⭐⭐⭐)

**Script có thể chạy nhiều cách:**

```bash
# 1. Manual rebuild
cd rag_service && python tools/cache.py

# 2. Scheduled rebuild (cron)
0 2 * * * cd /app/rag_service && python tools/cache.py

# 3. Triggered by API
curl -X POST http://localhost:8000/api/rebuild/trigger

# 4. Triggered by file watcher
inotifywait -m data/storage/collections | while read event; do
    python tools/cache.py
done

# 5. CI/CD pipeline
- name: Rebuild cache
  run: python rag_service/tools/cache.py
```

**Kết luận:** Tái sử dụng được ở nhiều contexts!

---

### ⚠️ NHƯỢC ĐIỂM (CONS)

#### 1. **Process Spawn Overhead** (⭐⭐)

**Latency cao hơn:**

```python
# BackgroundTasks: ~1-5ms overhead
background_tasks.add_task(rebuild)

# Subprocess: ~50-200ms overhead
subprocess.Popen(['python', 'rebuild.py'])
# - Fork process: ~20ms
# - Python startup: ~30-100ms
# - Import modules: ~50ms
```

**Mitigation:**

```python
# Option 1: Accept overhead (totally fine)
# 200ms là acceptable cho rebuild operation
# User không expect instant rebuild

# Option 2: Keep process warm (advanced)
# Start rebuild_worker.py at startup
# Worker listens on queue/socket
# No spawn overhead

# Option 3: Use faster script launcher
subprocess.Popen(['python', '-S', 'rebuild.py'])
# -S: Skip site initialization, faster startup
```

**Kết luận:** Overhead acceptable cho use case này!

#### 2. **Subprocess Management Complexity** (⭐⭐⭐)

**Phải quản lý subprocess lifecycle:**

```python
# Issues cần handle:
- Zombie processes if not waited
- Resource leaks if process hangs
- Multiple concurrent rebuilds
- Process timeout
- Signal handling (SIGTERM, SIGKILL)
- Exit code interpretation
```

**Mitigation:**

```python
# Use proper subprocess management:
import subprocess
import signal
import psutil  # For advanced process control

def run_rebuild_script(collection, doc_id, timeout=300):
    """Run rebuild with proper management"""
    try:
        # Start process
        process = subprocess.Popen(
            ['python', 'rebuild.py', '--collection', collection],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Prevent signal propagation
        )

        # Wait with timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode

            if exit_code == 0:
                logger.info(f"✅ Rebuild success: {stdout}")
            else:
                logger.error(f"❌ Rebuild failed: {stderr}")

        except subprocess.TimeoutExpired:
            # Kill hung process
            process.kill()
            process.wait()
            logger.error(f"❌ Rebuild timeout after {timeout}s")

    except Exception as e:
        logger.error(f"❌ Rebuild error: {e}")

    finally:
        # Ensure cleanup
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
            if process.poll() is None:
                process.kill()
```

**Kết luận:** Phức tạp hơn nhưng có patterns đã proven!

#### 3. **Status Tracking Mechanism** (⭐⭐⭐)

**Cần mechanism để track script status:**

**Problem:**

```python
# API trigger script
POST /api/rebuild/trigger → subprocess.Popen()
# API returns immediately: 202 Accepted

# User asks: "Is rebuild done?"
GET /api/rebuild/status → ??? How to know?
```

**Solutions:**

**Option A: File-based status** (Simplest)

```python
# rebuild.py writes status file
status_file = 'data/cache/rebuild_status.json'

def update_status(status, progress=0):
    with open(status_file, 'w') as f:
        json.dump({
            'status': status,  # 'idle', 'running', 'success', 'failed'
            'progress': progress,
            'started_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'collection': collection,
            'doc_id': doc_id,
            'pid': os.getpid()
        }, f)

# API reads status file
GET /api/rebuild/status:
    with open(status_file, 'r') as f:
        return json.load(f)
```

**Option B: Database status** (More robust)

```python
# SQLite for status tracking
import sqlite3

conn = sqlite3.connect('rebuild_jobs.db')
conn.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        status TEXT,
        progress INTEGER,
        started_at TEXT,
        completed_at TEXT,
        error TEXT
    )
''')

# rebuild.py updates DB
def update_status(job_id, status):
    conn.execute(
        'UPDATE jobs SET status=?, updated_at=? WHERE id=?',
        (status, datetime.now().isoformat(), job_id)
    )
    conn.commit()
```

**Option C: Redis/Queue** (Enterprise)

```python
import redis
r = redis.Redis()

# Script updates Redis
r.hset('rebuild:status', mapping={
    'status': 'running',
    'progress': 50,
    'updated_at': time.time()
})

# API reads from Redis
GET /api/rebuild/status:
    return r.hgetall('rebuild:status')
```

**Kết luận:** File-based simplest, SQLite best balance!

---

## 🏗️ THIẾT KẾ IMPLEMENTATION

### Architecture Tổng Quan

```
┌─────────────────┐
│  Admin Service  │
│   (Port 8001)   │
└────────┬────────┘
         │ 1. Update questions.json
         │ 2. POST /internal/rebuild/trigger
         ↓
┌─────────────────┐
│   RAG Service   │
│   (Port 8000)   │
├─────────────────┤
│ /internal/      │
│  rebuild/       │
│   trigger ──────┼──→ subprocess.Popen(['python', 'rebuild_script.py'])
│   status        │              │
│   cancel        │              ↓
└─────────────────┘    ┌──────────────────────┐
         ↑             │  rebuild_script.py   │
         │             │  (Separate Process)  │
         │             ├──────────────────────┤
         │             │ 1. Load questions    │
         │             │ 2. Rebuild VectorDB  │
         │             │ 3. Update cache      │
         │             │ 4. Write status      │
         │             └──────────────────────┘
         │                        │
         │ 3. GET /rebuild/status │
         └────────────────────────┘
                     (Read status file)
```

### Phase 1: Tận dụng cache.py hiện tại

**File structure:**

```
rag_service/
├── tools/
│   ├── cache.py                    ← Existing (keep as-is)
│   ├── rebuild_selective.py        ← NEW (wrapper cho selective rebuild)
│   └── rebuild_status.py           ← NEW (status management)
├── app/
│   └── api/
│       └── rebuild.py              ← NEW (API endpoints)
└── data/
    ├── cache/
    │   ├── rebuild_status.json     ← NEW (status tracking)
    │   └── rebuild_queue.json      ← NEW (queue pending rebuilds)
    └── logs/
        └── rebuild.log             ← NEW (rebuild logs)
```

### Phase 2: Script Design

#### File 1: `rebuild_selective.py` (NEW)

```python
#!/usr/bin/env python3
"""
Selective VectorDB Rebuild Script
==================================
Reuses cache.py logic for selective document rebuild.
Can be called from API or run manually.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Reuse cache.py functions
from cache import (
    load_new_structure,
    generate_embeddings_safe,
    save_cache,
    validate_cache,
    _create_fused_text_like_vectordb
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../data/logs/rebuild.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Status file
STATUS_FILE = Path('../data/cache/rebuild_status.json')

def update_status(status, progress=0, message="", error=None):
    """Update rebuild status file"""
    status_data = {
        'status': status,  # 'idle', 'running', 'success', 'failed'
        'progress': progress,
        'message': message,
        'error': str(error) if error else None,
        'updated_at': datetime.now().isoformat(),
        'pid': os.getpid()
    }

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)

    logger.info(f"📊 Status: {status} - {message}")

def rebuild_document(collection, doc_id):
    """
    Rebuild VectorDB for specific document
    Reuses cache.py logic
    """
    try:
        update_status('running', 10, f'Loading {collection}/{doc_id}')

        # Load only this document (optimize cache.py to support filtering)
        logger.info(f"🔄 Rebuilding {collection}/{doc_id}")

        # Load questions + document data
        doc_dir = Path(f'../data/storage/collections/{collection}/documents/{doc_id}')

        if not doc_dir.exists():
            raise FileNotFoundError(f"Document not found: {collection}/{doc_id}")

        # Load questions.json
        questions_file = doc_dir / 'questions.json'
        if not questions_file.exists():
            raise FileNotFoundError(f"Questions not found: {questions_file}")

        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        update_status('running', 30, 'Loaded questions')

        # Load document.json
        doc_files = [f for f in doc_dir.glob('*.json') if f.name != 'questions.json']
        if not doc_files:
            raise FileNotFoundError(f"Document JSON not found in {doc_dir}")

        with open(doc_files[0], 'r', encoding='utf-8') as f:
            content_data = json.load(f)

        metadata = content_data.get('metadata', {})

        update_status('running', 50, 'Creating fused text')

        # Create fused text (reuse cache.py logic)
        fused_text = _create_fused_text_like_vectordb(questions_data, metadata, content_data)

        update_status('running', 70, 'Generating embeddings')

        # Generate embeddings (reuse cache.py logic)
        from cache import generate_embeddings_safe

        # Prepare data structure for embedding generation
        temp_data = {
            collection: {
                doc_id: {
                    'questions': questions_data,
                    'metadata': metadata,
                    'content_data': content_data,
                    'fused_text': fused_text,
                    'file_path': str(questions_file)
                }
            }
        }

        embeddings_data = generate_embeddings_safe(temp_data)

        if not embeddings_data:
            raise Exception("Failed to generate embeddings")

        update_status('running', 90, 'Updating cache')

        # Load existing cache
        cache_file = Path('../data/cache/router_embeddings.pkl')

        if cache_file.exists():
            import pickle
            with open(cache_file, 'rb') as f:
                cache_container = pickle.load(f)

            if isinstance(cache_container, dict) and 'data' in cache_container:
                existing_cache = cache_container['data']
                cache_metadata = cache_container['metadata']
            else:
                existing_cache = cache_container
                cache_metadata = {}
        else:
            existing_cache = {}
            cache_metadata = {}

        # Update with new document data
        if collection not in existing_cache:
            existing_cache[collection] = {}

        existing_cache[collection][doc_id] = embeddings_data[collection][doc_id]

        # Save updated cache
        cache_metadata['last_updated'] = datetime.now().isoformat()
        cache_metadata['last_rebuild_document'] = f"{collection}/{doc_id}"

        cache_with_metadata = {
            'data': existing_cache,
            'metadata': cache_metadata
        }

        import pickle
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_with_metadata, f)

        logger.info(f"✅ Cache updated for {collection}/{doc_id}")

        update_status('success', 100, f'Successfully rebuilt {collection}/{doc_id}')

        return True

    except Exception as e:
        logger.error(f"❌ Rebuild failed: {e}")
        update_status('failed', 0, f'Rebuild failed', error=e)
        return False

def rebuild_collection(collection):
    """Rebuild entire collection"""
    try:
        update_status('running', 0, f'Rebuilding collection: {collection}')

        # Get all documents in collection
        collection_dir = Path(f'../data/storage/collections/{collection}/documents')

        if not collection_dir.exists():
            raise FileNotFoundError(f"Collection not found: {collection}")

        doc_dirs = [d for d in collection_dir.iterdir() if d.is_dir()]
        total_docs = len(doc_dirs)

        logger.info(f"🔄 Rebuilding {total_docs} documents in {collection}")

        for i, doc_dir in enumerate(doc_dirs):
            doc_id = doc_dir.name
            progress = int((i / total_docs) * 100)

            update_status('running', progress, f'Rebuilding {doc_id} ({i+1}/{total_docs})')

            if not rebuild_document(collection, doc_id):
                logger.warning(f"⚠️ Failed to rebuild {collection}/{doc_id}")

        update_status('success', 100, f'Successfully rebuilt collection {collection}')
        return True

    except Exception as e:
        logger.error(f"❌ Collection rebuild failed: {e}")
        update_status('failed', 0, f'Collection rebuild failed', error=e)
        return False

def rebuild_all():
    """Rebuild entire VectorDB - reuse cache.py"""
    try:
        update_status('running', 0, 'Rebuilding entire VectorDB')

        logger.info("🔄 Running full cache rebuild (reusing cache.py)")

        # Just call cache.py main logic
        from cache import clean_old_cache, load_new_structure, generate_embeddings_safe, save_cache

        clean_old_cache()
        update_status('running', 20, 'Cleaned old cache')

        questions_data = load_new_structure()
        update_status('running', 40, 'Loaded all questions')

        cache_data = generate_embeddings_safe(questions_data)
        update_status('running', 70, 'Generated embeddings')

        save_cache(cache_data)
        update_status('running', 90, 'Saved cache')

        update_status('success', 100, 'Full rebuild complete')
        return True

    except Exception as e:
        logger.error(f"❌ Full rebuild failed: {e}")
        update_status('failed', 0, 'Full rebuild failed', error=e)
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rebuild VectorDB cache')
    parser.add_argument('--scope', choices=['document', 'collection', 'all'], required=True)
    parser.add_argument('--collection', help='Collection name (for document/collection scope)')
    parser.add_argument('--doc-id', help='Document ID (for document scope)')

    args = parser.parse_args()

    # Initialize status
    update_status('running', 0, f'Starting {args.scope} rebuild')

    try:
        if args.scope == 'document':
            if not args.collection or not args.doc_id:
                raise ValueError("--collection and --doc-id required for document scope")
            success = rebuild_document(args.collection, args.doc_id)

        elif args.scope == 'collection':
            if not args.collection:
                raise ValueError("--collection required for collection scope")
            success = rebuild_collection(args.collection)

        elif args.scope == 'all':
            success = rebuild_all()

        exit_code = 0 if success else 1
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"❌ Script error: {e}")
        update_status('failed', 0, 'Script error', error=e)
        sys.exit(1)
```

**Usage examples:**

```bash
# Rebuild single document
python rebuild_selective.py --scope document --collection quy_trinh_test --doc-id DOC_001

# Rebuild collection
python rebuild_selective.py --scope collection --collection quy_trinh_test

# Rebuild all (same as cache.py)
python rebuild_selective.py --scope all
```

#### File 2: `app/api/rebuild.py` (NEW)

```python
"""
VectorDB Rebuild API Endpoints
===============================
Triggers rebuild_selective.py script via subprocess
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import subprocess
import json
import logging
import psutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rebuild", tags=["rebuild"])

STATUS_FILE = Path("data/cache/rebuild_status.json")
SCRIPT_PATH = "tools/rebuild_selective.py"
SCRIPT_TIMEOUT = 600  # 10 minutes max

class RebuildRequest(BaseModel):
    """Rebuild request model"""
    scope: str  # 'document', 'collection', 'all'
    collection: Optional[str] = None
    doc_id: Optional[str] = None

class RebuildResponse(BaseModel):
    """Rebuild response model"""
    success: bool
    message: str
    job_id: Optional[str] = None
    status: Optional[str] = None

@router.post("/trigger", response_model=RebuildResponse)
async def trigger_rebuild(request: RebuildRequest):
    """
    Trigger VectorDB rebuild script

    Returns immediately after starting script.
    Use /status endpoint to check progress.
    """
    try:
        # Validate request
        if request.scope == 'document':
            if not request.collection or not request.doc_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="collection and doc_id required for document scope"
                )
        elif request.scope == 'collection':
            if not request.collection:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="collection required for collection scope"
                )

        # Check if rebuild already running
        current_status = _get_current_status()
        if current_status and current_status.get('status') == 'running':
            pid = current_status.get('pid')
            if pid and psutil.pid_exists(pid):
                return RebuildResponse(
                    success=False,
                    message="Rebuild already running",
                    status="running"
                )
            else:
                logger.warning("⚠️ Stale rebuild process detected, cleaning up")

        # Build command
        cmd = ['python', SCRIPT_PATH, '--scope', request.scope]

        if request.collection:
            cmd.extend(['--collection', request.collection])
        if request.doc_id:
            cmd.extend(['--doc-id', request.doc_id])

        logger.info(f"🚀 Triggering rebuild: {' '.join(cmd)}")

        # Start subprocess (detached)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # Detach from parent
            cwd='rag_service'  # Important: set working directory
        )

        job_id = f"rebuild_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"✅ Rebuild started: PID={process.pid}, Job={job_id}")

        return RebuildResponse(
            success=True,
            message=f"Rebuild triggered successfully",
            job_id=job_id,
            status="queued"
        )

    except Exception as e:
        logger.error(f"❌ Failed to trigger rebuild: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger rebuild: {str(e)}"
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_rebuild_status():
    """
    Get current rebuild status

    Returns status from status file written by script
    """
    try:
        status_data = _get_current_status()

        if not status_data:
            return {
                'status': 'idle',
                'message': 'No rebuild running or completed recently'
            }

        # Check if process still alive
        pid = status_data.get('pid')
        if pid and status_data.get('status') == 'running':
            if not psutil.pid_exists(pid):
                status_data['status'] = 'failed'
                status_data['message'] = 'Rebuild process died unexpectedly'

        return status_data

    except Exception as e:
        logger.error(f"❌ Failed to get rebuild status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rebuild status: {str(e)}"
        )

@router.post("/cancel", response_model=RebuildResponse)
async def cancel_rebuild():
    """
    Cancel running rebuild

    Kills the rebuild process if running
    """
    try:
        status_data = _get_current_status()

        if not status_data or status_data.get('status') != 'running':
            return RebuildResponse(
                success=False,
                message="No rebuild running"
            )

        pid = status_data.get('pid')
        if not pid:
            return RebuildResponse(
                success=False,
                message="Rebuild PID not found"
            )

        if not psutil.pid_exists(pid):
            return RebuildResponse(
                success=False,
                message="Rebuild process not found"
            )

        # Kill process
        try:
            process = psutil.Process(pid)
            process.terminate()  # SIGTERM
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()  # SIGKILL
            process.wait()

        logger.info(f"🛑 Rebuild cancelled: PID={pid}")

        # Update status
        status_data['status'] = 'cancelled'
        status_data['message'] = 'Rebuild cancelled by user'

        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)

        return RebuildResponse(
            success=True,
            message="Rebuild cancelled successfully",
            status="cancelled"
        )

    except Exception as e:
        logger.error(f"❌ Failed to cancel rebuild: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel rebuild: {str(e)}"
        )

def _get_current_status() -> Optional[Dict[str, Any]]:
    """Read current status from file"""
    try:
        if not STATUS_FILE.exists():
            return None

        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Failed to read status file: {e}")
        return None
```

### Phase 3: Integration vào Admin Service

```python
# admin_service/app/api/questions.py

@router.put("/questions/collections/{collection}/documents/{doc_id}")
async def update_questions(...):
    # 1. Update questions.json
    ...

    # 2. Invalidate cache
    await invalidate_rag_cache(collection, doc_id)

    # 3. Trigger rebuild via script (NEW!)
    if request.rebuild_vectordb:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{RAG_SERVICE_URL}/api/rebuild/trigger",
                    json={
                        "scope": "document",
                        "collection": collection,
                        "doc_id": doc_id
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Rebuild triggered: {result}")
                    vectordb_rebuild_queued = True
                else:
                    logger.warning(f"⚠️ Rebuild trigger failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Failed to trigger rebuild: {e}")

    return QuestionsResponse(
        success=True,
        ...
        vectordb_rebuild_queued=vectordb_rebuild_queued
    )
```

---

## 📊 SO SÁNH CỤ THỂ

### Performance Comparison

| Metric                | BackgroundTasks      | Script-based      |
| --------------------- | -------------------- | ----------------- |
| **Spawn overhead**    | ~1-5ms               | ~50-200ms         |
| **Memory isolation**  | ❌ Shared            | ✅ Isolated       |
| **CPU isolation**     | ❌ Shared            | ✅ Isolated       |
| **Crash impact**      | ⚠️ May affect server | ✅ No impact      |
| **Resource control**  | ❌ Limited           | ✅ Full control   |
| **Progress tracking** | ⚠️ Difficult         | ✅ Easy           |
| **Error recovery**    | ⚠️ Complex           | ✅ Simple         |
| **Code reuse**        | ❌ Rewrite           | ✅ Reuse cache.py |

### Complexity Comparison

| Aspect              | BackgroundTasks | Script-based    |
| ------------------- | --------------- | --------------- |
| **Implementation**  | ⭐⭐ Simple     | ⭐⭐⭐ Moderate |
| **Status tracking** | ⭐⭐⭐⭐ Hard   | ⭐⭐ Easy       |
| **Testing**         | ⭐⭐⭐ Moderate | ⭐ Very easy    |
| **Debugging**       | ⭐⭐⭐⭐ Hard   | ⭐ Very easy    |
| **Maintenance**     | ⭐⭐⭐ Moderate | ⭐⭐ Easy       |

---

## 🎯 KẾT LUẬN & KHUYẾN NGHỊ

### ✅ Đánh giá ý tưởng của bạn: **EXCELLENT!** (9/10)

**Lý do:**

1. ✅ **Tận dụng code proven** (`cache.py`) - Very smart!
2. ✅ **Better isolation** - Safety first
3. ✅ **Easier debugging** - Developer friendly
4. ✅ **Less corruption risk** - Production ready
5. ✅ **Flexible deployment** - Can run multiple ways

**Chỉ trừ điểm 1 vì:**

- Subprocess overhead (~200ms) - nhưng totally acceptable!

### 🚀 Khuyến nghị IMPLEMENTATION

**Recommended approach:**

```
Phase 1 (Week 1): Basic CRUD + File-based script trigger
├─ Implement CRUD endpoints
├─ Create rebuild_selective.py (reuse cache.py)
├─ Add /api/rebuild/trigger endpoint
└─ File-based status tracking

Phase 2 (Week 2): Enhanced status tracking
├─ Add /api/rebuild/status endpoint
├─ Add /api/rebuild/cancel endpoint
├─ Improve logging
└─ Add timeout & error handling

Phase 3 (Week 3): Production hardening
├─ Add concurrent rebuild prevention
├─ Add script process monitoring
├─ Add health checks
└─ Integration testing
```

### 📋 Action Items

**Immediate (This week):**

1. ✅ Review `cache.py` - đã có sẵn, hoạt động tốt
2. ✅ Create `rebuild_selective.py` - design đã có trong doc này
3. ✅ Create `/api/rebuild` endpoints - code example đã có
4. ✅ Test locally với 1 document

**Short-term (Next 2 weeks):**

1. Integration testing với full workflow
2. Add comprehensive error handling
3. Add monitoring & alerts
4. Production deployment

### 🎓 Bài học quan trọng

**"Simple is better than complex"**

- Script-based approach simpler để debug
- File-based status simpler để implement
- Reusing proven code simpler để maintain

**"Explicit is better than implicit"**

- Script process explicit & visible
- Status file explicit & inspectable
- Logs explicit & traceable

---

**Kết luận cuối cùng:** Ý tưởng của bạn RẤT TỐT! Khuyến nghị implement theo hướng này! 🚀
