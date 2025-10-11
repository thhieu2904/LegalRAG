# 🚀 QUESTIONS CRUD - Docker Implementation Plan

**Ngày tạo:** 11/10/2025  
**Mục đích:** Implementation đầy đủ CRUD cho questions system trên Docker  
**Architecture:** HTTP-based communication (không mount volumes)

---

## 📋 OVERVIEW

### Current State

```
Frontend (3000) ─────→ Admin Service (8001) ─────→ RAG Service files (local)
                       ├─ GET /questions ✅        └─ questions.json (read-only)
                       └─ POST/PUT/DELETE ❌
```

### Target State

```
Frontend (3000) ────→ Admin Service (8001) ────→ RAG Service (8000)
  ├─ Questions UI         ├─ CRUD endpoints          ├─ File management API
  ├─ Edit form            ├─ Validation              ├─ Read questions.json
  └─ Rebuild button       └─ Business logic          ├─ Write questions.json
                                                      └─ Rebuild trigger API
                                                           └─→ spawn rebuild_script.py
```

---

## 🏗️ ARCHITECTURE DETAILS

### Service Communication Flow

#### 1. **Read Flow** (Already working)

```
User → Frontend → Admin API → PathConfig → File System
GET /questions
```

#### 2. **Write Flow** (NEW - Need to implement)

```
User → Frontend → Admin API → RAG API → File System
POST/PUT/DELETE /questions → POST /internal/files/questions → Write file
```

#### 3. **Rebuild Flow** (NEW - Script-based)

```
User → Frontend → Admin API → RAG API → Subprocess
POST /rebuild → POST /internal/rebuild/trigger → spawn rebuild_script.py
```

### Why RAG Service needs File Management API?

**Problem:**

- Admin Service runs in container A
- questions.json files in RAG Service container B (volume mount)
- Cannot directly access files across containers without shared volume
- Docker distributed deployment → HTTP API better than volume mounting

**Solution:**

```python
# Admin Service (Container A)
async def update_questions(collection, doc_id, data):
    # Call RAG Service API
    response = await httpx.post(
        f"http://rag_service:8000/internal/files/questions",
        json={
            "collection": collection,
            "doc_id": doc_id,
            "data": data
        }
    )

# RAG Service (Container B - has file access)
@router.post("/internal/files/questions")
async def write_questions_file(request):
    # Has access to mounted volume
    file_path = f"/app/data/storage/collections/{collection}/documents/{doc_id}/questions.json"
    with open(file_path, 'w') as f:
        json.dump(request.data, f)
```

---

## 📐 DETAILED IMPLEMENTATION PLAN

### PHASE 1: RAG Service - Internal File Management API (4-6h)

#### File: `rag_service/app/api/internal_files.py` (NEW)

**Endpoints cần tạo:**

```python
POST   /internal/files/questions/{collection}/{doc_id}      # Create questions.json
PUT    /internal/files/questions/{collection}/{doc_id}      # Update questions.json
DELETE /internal/files/questions/{collection}/{doc_id}      # Delete questions.json
GET    /internal/files/questions/{collection}/{doc_id}      # Read questions.json (backup)
```

**Security:**

- Internal endpoints - chỉ cho Admin Service gọi
- API key authentication hoặc internal network
- Validation: check collection/doc_id exists

**Implementation checklist:**

- [ ] Create `internal_files.py`
- [ ] Add file read/write logic
- [ ] Add validation
- [ ] Add backup mechanism
- [ ] Add error handling
- [ ] Register router in main.py
- [ ] Test with curl

**Code skeleton:**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from pathlib import Path

router = APIRouter(prefix="/internal/files", tags=["internal-files"])

class QuestionsData(BaseModel):
    main_question: str
    question_variants: list[str]

@router.put("/questions/{collection}/{doc_id}")
async def update_questions_file(
    collection: str,
    doc_id: str,
    data: QuestionsData
):
    """Write questions.json file - called by Admin Service"""
    try:
        # Get file path
        file_path = Path(f"data/storage/collections/{collection}/documents/{doc_id}/questions.json")

        # Validate path exists
        if not file_path.parent.exists():
            raise HTTPException(404, "Document not found")

        # Backup current file
        if file_path.exists():
            backup_path = file_path.with_suffix('.json.backup')
            shutil.copy(file_path, backup_path)

        # Write new data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data.dict(), f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Questions updated"}

    except Exception as e:
        # Rollback from backup if exists
        raise HTTPException(500, str(e))
```

---

### PHASE 2: RAG Service - Rebuild API (3-5h)

#### File: `rag_service/app/api/internal_rebuild.py` (NEW)

**Endpoints cần tạo:**

```python
POST   /internal/rebuild/trigger    # Trigger rebuild script
GET    /internal/rebuild/status     # Check rebuild status
POST   /internal/rebuild/cancel     # Cancel running rebuild
```

**Script integration:**

```python
@router.post("/rebuild/trigger")
async def trigger_rebuild(
    scope: str,  # 'document', 'collection', 'all'
    collection: str = None,
    doc_id: str = None
):
    """Trigger rebuild_script.py via subprocess"""

    # Build command
    cmd = ['python', 'tools/rebuild_selective.py', '--scope', scope]
    if collection:
        cmd.extend(['--collection', collection])
    if doc_id:
        cmd.extend(['--doc-id', doc_id])

    # Spawn subprocess (detached)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    return {
        "success": True,
        "message": "Rebuild triggered",
        "pid": process.pid
    }
```

**Status tracking:**

```python
STATUS_FILE = Path("data/cache/rebuild_status.json")

@router.get("/rebuild/status")
async def get_rebuild_status():
    """Read status from file written by script"""
    if not STATUS_FILE.exists():
        return {"status": "idle"}

    with open(STATUS_FILE) as f:
        return json.load(f)
```

**Implementation checklist:**

- [ ] Create `internal_rebuild.py`
- [ ] Add subprocess management
- [ ] Add status tracking
- [ ] Add timeout handling
- [ ] Create `rebuild_selective.py` (reuse cache.py)
- [ ] Test rebuild trigger
- [ ] Test status tracking

---

### PHASE 3: Admin Service - CRUD Endpoints (4-6h)

#### File: `admin_service/app/api/questions.py` (UPDATE)

**Add new endpoints:**

```python
POST   /api/questions/collections/{collection}/documents/{doc_id}
PUT    /api/questions/collections/{collection}/documents/{doc_id}
DELETE /api/questions/collections/{collection}/documents/{doc_id}
PATCH  /api/questions/collections/{collection}/documents/{doc_id}/variants
```

**HTTP client configuration:**

```python
# admin_service/app/core/config.py
class AdminConfig:
    RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag_service:8000")
    RAG_SERVICE_TIMEOUT = 30  # seconds
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "your-secret-key")
```

**Implementation:**

```python
import httpx

RAG_SERVICE_URL = AdminConfig.RAG_SERVICE_URL

@router.put("/questions/collections/{collection}/documents/{doc_id}")
async def update_questions(
    collection: str,
    doc_id: str,
    data: QuestionsUpdateRequest
):
    """Update questions - calls RAG Service to write file"""
    try:
        # Validate input
        if not data.main_question:
            raise HTTPException(400, "main_question required")

        # Call RAG Service to update file
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{RAG_SERVICE_URL}/internal/files/questions/{collection}/{doc_id}",
                json={
                    "main_question": data.main_question,
                    "question_variants": data.question_variants
                },
                headers={"X-Internal-API-Key": AdminConfig.INTERNAL_API_KEY},
                timeout=30.0
            )

            if response.status_code != 200:
                raise HTTPException(500, f"Failed to update file: {response.text}")

        # Trigger rebuild if requested
        if data.rebuild_vectordb:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{RAG_SERVICE_URL}/internal/rebuild/trigger",
                    json={
                        "scope": "document",
                        "collection": collection,
                        "doc_id": doc_id
                    },
                    timeout=10.0
                )

        return {
            "success": True,
            "message": "Questions updated successfully"
        }

    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(500, str(e))
```

**Implementation checklist:**

- [ ] Add RAG_SERVICE_URL config
- [ ] Create POST endpoint
- [ ] Create PUT endpoint
- [ ] Create DELETE endpoint
- [ ] Create PATCH endpoint
- [ ] Add HTTP client logic
- [ ] Add error handling
- [ ] Test all endpoints

---

### PHASE 4: Frontend - Questions UI (6-8h)

#### File: `frontend/src/pages/QuestionsManagementPage.tsx` (NEW)

**Components cần tạo:**

```typescript
1. QuestionsListView
   ├─ Collection selector
   ├─ Document selector
   └─ Questions table

2. QuestionEditModal
   ├─ Main question input
   ├─ Variants list (add/edit/delete)
   └─ Save/Cancel buttons

3. RebuildStatusBadge
   ├─ Status indicator (idle/running/success/failed)
   ├─ Progress bar
   └─ Rebuild button
```

**API integration:**

```typescript
// frontend/src/api/questions-api.ts
import { ragAPI } from "./axios-config";

export interface QuestionsData {
  main_question: string;
  question_variants: string[];
}

export const questionsAPI = {
  // GET (already exists via admin service)
  getQuestions: async (collection: string, docId: string) => {
    const response = await ragAPI.get(
      `/api/questions/collections/${collection}/documents/${docId}`
    );
    return response.data;
  },

  // UPDATE (new)
  updateQuestions: async (
    collection: string,
    docId: string,
    data: QuestionsData,
    rebuildVectorDB = false
  ) => {
    const response = await ragAPI.put(
      `/api/questions/collections/${collection}/documents/${docId}`,
      { ...data, rebuild_vectordb: rebuildVectorDB }
    );
    return response.data;
  },

  // CREATE (new)
  createQuestions: async (
    collection: string,
    docId: string,
    data: QuestionsData
  ) => {
    const response = await ragAPI.post(
      `/api/questions/collections/${collection}/documents/${docId}`,
      data
    );
    return response.data;
  },

  // DELETE (new)
  deleteQuestions: async (collection: string, docId: string) => {
    const response = await ragAPI.delete(
      `/api/questions/collections/${collection}/documents/${docId}`
    );
    return response.data;
  },

  // REBUILD STATUS
  getRebuildStatus: async () => {
    const response = await ragAPI.get("/internal/rebuild/status");
    return response.data;
  },

  // TRIGGER REBUILD
  triggerRebuild: async (
    scope: "document" | "collection" | "all",
    collection?: string,
    docId?: string
  ) => {
    const response = await ragAPI.post("/internal/rebuild/trigger", {
      scope,
      collection,
      doc_id: docId,
    });
    return response.data;
  },
};
```

**UI Components:**

**1. Questions Edit Form:**

```tsx
// frontend/src/components/admin/QuestionEditForm.tsx
import React, { useState } from "react";
import { QuestionsData } from "@/api/questions-api";

interface Props {
  initialData: QuestionsData;
  onSave: (data: QuestionsData) => Promise<void>;
  onCancel: () => void;
}

export const QuestionEditForm: React.FC<Props> = ({
  initialData,
  onSave,
  onCancel,
}) => {
  const [mainQuestion, setMainQuestion] = useState(initialData.main_question);
  const [variants, setVariants] = useState(initialData.question_variants);
  const [loading, setLoading] = useState(false);

  const handleAddVariant = () => {
    setVariants([...variants, ""]);
  };

  const handleUpdateVariant = (index: number, value: string) => {
    const newVariants = [...variants];
    newVariants[index] = value;
    setVariants(newVariants);
  };

  const handleDeleteVariant = (index: number) => {
    setVariants(variants.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await onSave({
        main_question: mainQuestion,
        question_variants: variants.filter((v) => v.trim()),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="question-edit-form">
      <div className="form-group">
        <label>Main Question *</label>
        <input
          type="text"
          value={mainQuestion}
          onChange={(e) => setMainQuestion(e.target.value)}
          placeholder="Enter main question"
          required
        />
      </div>

      <div className="form-group">
        <label>Question Variants</label>
        {variants.map((variant, index) => (
          <div key={index} className="variant-item">
            <input
              type="text"
              value={variant}
              onChange={(e) => handleUpdateVariant(index, e.target.value)}
              placeholder={`Variant ${index + 1}`}
            />
            <button
              type="button"
              onClick={() => handleDeleteVariant(index)}
              className="btn-delete"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={handleAddVariant}
          className="btn-add-variant"
        >
          + Add Variant
        </button>
      </div>

      <div className="form-actions">
        <button onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || !mainQuestion.trim()}
          className="btn-primary"
        >
          {loading ? "Saving..." : "Save Changes"}
        </button>
      </div>
    </div>
  );
};
```

**2. Rebuild Button Component:**

```tsx
// frontend/src/components/admin/RebuildButton.tsx
import React, { useState, useEffect } from "react";
import { questionsAPI } from "@/api/questions-api";

interface Props {
  collection?: string;
  docId?: string;
  onRebuildComplete?: () => void;
}

export const RebuildButton: React.FC<Props> = ({
  collection,
  docId,
  onRebuildComplete,
}) => {
  const [rebuildStatus, setRebuildStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Poll rebuild status
  useEffect(() => {
    const interval = setInterval(async () => {
      const status = await questionsAPI.getRebuildStatus();
      setRebuildStatus(status);

      if (status.status === "success" || status.status === "failed") {
        clearInterval(interval);
        if (status.status === "success" && onRebuildComplete) {
          onRebuildComplete();
        }
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRebuild = async () => {
    setLoading(true);
    try {
      const scope = docId ? "document" : collection ? "collection" : "all";
      await questionsAPI.triggerRebuild(scope, collection, docId);
      alert("Rebuild triggered successfully");
    } catch (error) {
      alert("Failed to trigger rebuild");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    if (!rebuildStatus || rebuildStatus.status === "idle") {
      return <span className="badge badge-gray">Idle</span>;
    }
    if (rebuildStatus.status === "running") {
      return (
        <span className="badge badge-blue">
          Running ({rebuildStatus.progress || 0}%)
        </span>
      );
    }
    if (rebuildStatus.status === "success") {
      return <span className="badge badge-green">Success</span>;
    }
    return <span className="badge badge-red">Failed</span>;
  };

  return (
    <div className="rebuild-section">
      <div className="rebuild-status">
        <span>Rebuild Status: </span>
        {getStatusBadge()}
      </div>
      <button
        onClick={handleRebuild}
        disabled={loading || rebuildStatus?.status === "running"}
        className="btn-rebuild"
      >
        {loading ? "Triggering..." : "🔄 Rebuild Cache"}
      </button>
    </div>
  );
};
```

**3. Main Questions Page:**

```tsx
// frontend/src/pages/QuestionsManagementPage.tsx
import React, { useState, useEffect } from "react";
import { questionsAPI, QuestionsData } from "@/api/questions-api";
import { QuestionEditForm } from "@/components/admin/QuestionEditForm";
import { RebuildButton } from "@/components/admin/RebuildButton";

export const QuestionsManagementPage = () => {
  const [collections, setCollections] = useState<string[]>([]);
  const [selectedCollection, setSelectedCollection] = useState("");
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(
    null
  );
  const [editMode, setEditMode] = useState(false);
  const [needsRebuild, setNeedsRebuild] = useState(false);

  // Load collections
  useEffect(() => {
    // Fetch collections from API
  }, []);

  // Load documents when collection selected
  useEffect(() => {
    if (selectedCollection) {
      // Fetch documents
    }
  }, [selectedCollection]);

  // Load questions when document selected
  useEffect(() => {
    if (selectedCollection && selectedDoc) {
      loadQuestions();
    }
  }, [selectedCollection, selectedDoc]);

  const loadQuestions = async () => {
    const data = await questionsAPI.getQuestions(
      selectedCollection,
      selectedDoc
    );
    setQuestionsData(data.data.questions);
  };

  const handleSave = async (data: QuestionsData) => {
    await questionsAPI.updateQuestions(
      selectedCollection,
      selectedDoc,
      data,
      false // Don't auto-rebuild
    );
    setQuestionsData(data);
    setEditMode(false);
    setNeedsRebuild(true); // Mark that rebuild needed
  };

  return (
    <div className="questions-management-page">
      <h1>Questions Management</h1>

      {/* Collection & Document Selector */}
      <div className="selectors">
        <select
          value={selectedCollection}
          onChange={(e) => setSelectedCollection(e.target.value)}
        >
          <option value="">Select Collection</option>
          {collections.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select
          value={selectedDoc}
          onChange={(e) => setSelectedDoc(e.target.value)}
          disabled={!selectedCollection}
        >
          <option value="">Select Document</option>
          {documents.map((d) => (
            <option key={d.id} value={d.id}>
              {d.title}
            </option>
          ))}
        </select>
      </div>

      {/* Questions Display/Edit */}
      {questionsData && !editMode && (
        <div className="questions-display">
          <div className="header">
            <h2>Questions</h2>
            <button onClick={() => setEditMode(true)} className="btn-edit">
              ✏️ Edit
            </button>
          </div>

          <div className="main-question">
            <strong>Main Question:</strong>
            <p>{questionsData.main_question}</p>
          </div>

          <div className="variants">
            <strong>
              Variants ({questionsData.question_variants.length}):
            </strong>
            <ul>
              {questionsData.question_variants.map((v, i) => (
                <li key={i}>{v}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {editMode && questionsData && (
        <QuestionEditForm
          initialData={questionsData}
          onSave={handleSave}
          onCancel={() => setEditMode(false)}
        />
      )}

      {/* Rebuild Section */}
      {questionsData && (
        <div className="rebuild-section">
          {needsRebuild && (
            <div className="rebuild-warning">
              ⚠️ Questions have been modified. Rebuild cache to apply changes.
            </div>
          )}
          <RebuildButton
            collection={selectedCollection}
            docId={selectedDoc}
            onRebuildComplete={() => setNeedsRebuild(false)}
          />
        </div>
      )}
    </div>
  );
};
```

**Implementation checklist:**

- [ ] Create QuestionsManagementPage.tsx
- [ ] Create QuestionEditForm component
- [ ] Create RebuildButton component
- [ ] Add questions-api.ts
- [ ] Add routing
- [ ] Add CSS styling
- [ ] Test UI flow

---

### PHASE 5: Docker Configuration (2-3h)

#### Update `docker-compose.yml`

```yaml
version: "3.8"

services:
  rag_service:
    build: ./rag_service
    container_name: rag_service
    ports:
      - "8000:8000"
    volumes:
      - ./rag_service/data:/app/data # Mount data directory
    environment:
      - INTERNAL_API_KEY=${INTERNAL_API_KEY:-your-secret-key}
    networks:
      - legalrag_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  admin_service:
    build: ./admin_service
    container_name: admin_service
    ports:
      - "8001:8001"
    environment:
      - RAG_SERVICE_URL=http://rag_service:8000 # Internal Docker network
      - INTERNAL_API_KEY=${INTERNAL_API_KEY:-your-secret-key}
    depends_on:
      - rag_service
    networks:
      - legalrag_network

  frontend:
    build: ./frontend
    container_name: frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_ADMIN_API_URL=http://localhost:8001
      - VITE_RAG_API_URL=http://localhost:8000
    depends_on:
      - admin_service
    networks:
      - legalrag_network

networks:
  legalrag_network:
    driver: bridge
```

#### Environment Variables (`.env`)

```bash
# Security
INTERNAL_API_KEY=your-super-secret-internal-api-key-change-in-production

# Service URLs
RAG_SERVICE_URL=http://rag_service:8000
ADMIN_SERVICE_URL=http://admin_service:8001
```

**Implementation checklist:**

- [ ] Update docker-compose.yml
- [ ] Create .env file
- [ ] Configure internal network
- [ ] Test inter-service communication
- [ ] Test volume mounts

---

## 📊 TESTING PLAN

### Unit Tests

```bash
# RAG Service
pytest rag_service/tests/test_internal_files.py
pytest rag_service/tests/test_rebuild_api.py

# Admin Service
pytest admin_service/tests/test_questions_crud.py

# Frontend
npm test -- QuestionEditForm.test.tsx
npm test -- RebuildButton.test.tsx
```

### Integration Tests

```python
# test_questions_crud_integration.py
async def test_full_crud_flow():
    # 1. Create questions
    response = await admin_client.post(
        "/api/questions/collections/test/documents/DOC_001",
        json={"main_question": "Test?", "question_variants": ["Test variant?"]}
    )
    assert response.status_code == 201

    # 2. Verify file created in RAG service
    file_response = await rag_client.get(
        "/internal/files/questions/test/DOC_001"
    )
    assert file_response.status_code == 200

    # 3. Update questions
    response = await admin_client.put(
        "/api/questions/collections/test/documents/DOC_001",
        json={"main_question": "Updated?", "question_variants": []}
    )
    assert response.status_code == 200

    # 4. Trigger rebuild
    response = await admin_client.post(
        "/api/rebuild/trigger",
        json={"scope": "document", "collection": "test", "doc_id": "DOC_001"}
    )
    assert response.status_code == 202

    # 5. Check rebuild status
    status = await admin_client.get("/api/rebuild/status")
    assert status.json()["status"] in ["running", "queued"]

    # 6. Delete questions
    response = await admin_client.delete(
        "/api/questions/collections/test/documents/DOC_001"
    )
    assert response.status_code == 200
```

### Manual Testing Checklist

```
[ ] Start all services via docker-compose
[ ] Access frontend at http://localhost:3000
[ ] Navigate to Questions Management page
[ ] Select collection and document
[ ] View existing questions
[ ] Click Edit button
[ ] Modify main question
[ ] Add/edit/delete variants
[ ] Save changes
[ ] Verify changes reflected in UI
[ ] Click Rebuild Cache button
[ ] Monitor rebuild status
[ ] Verify rebuild completes successfully
[ ] Test with multiple documents
[ ] Test concurrent edits
[ ] Test error scenarios
```

---

## 🎯 IMPLEMENTATION TIMELINE

### Week 1 (Phase 1-2): Backend Foundation

```
Day 1-2: RAG Service Internal APIs
├─ Create internal_files.py
├─ Create internal_rebuild.py
├─ Create rebuild_selective.py
└─ Test APIs with curl

Day 3-4: Admin Service CRUD
├─ Add CRUD endpoints
├─ HTTP client integration
└─ Test admin → rag communication

Day 5: Integration Testing
└─ End-to-end backend tests
```

### Week 2 (Phase 3-4): Frontend & Integration

```
Day 1-2: Frontend Components
├─ QuestionEditForm
├─ RebuildButton
└─ QuestionsManagementPage

Day 3-4: API Integration
├─ questions-api.ts
├─ Connect components to API
└─ Handle loading/error states

Day 5: UI Polish & Testing
├─ CSS styling
├─ Error handling
└─ User testing
```

### Week 3 (Phase 5): Docker & Production

```
Day 1-2: Docker Configuration
├─ Update docker-compose.yml
├─ Environment variables
└─ Inter-service networking

Day 3: Testing & Debugging
├─ Docker deployment test
├─ Performance testing
└─ Bug fixes

Day 4-5: Documentation & Handoff
├─ User documentation
├─ API documentation
└─ Deployment guide
```

---

## 📝 NEXT STEPS

### Immediate Actions (This Week)

1. ✅ Review & approve this plan
2. ✅ Create git feature branch: `feature/questions-crud`
3. ✅ Start Phase 1: RAG Service Internal APIs
4. ✅ Create `internal_files.py` skeleton
5. ✅ Test basic file operations

### Priority Order

1. **CRITICAL**: Phase 1 (RAG file API)
2. **HIGH**: Phase 2 (Rebuild API)
3. **HIGH**: Phase 3 (Admin CRUD)
4. **MEDIUM**: Phase 4 (Frontend UI)
5. **MEDIUM**: Phase 5 (Docker config)

---

**Ready to start? Let's implement Phase 1!** 🚀
