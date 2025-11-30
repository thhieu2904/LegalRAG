# Form Service Integration - Implementation Summary

## Overview

This document summarizes the changes made to fix the `identifill_service` compatibility issues and integrate form handling into the new microservices architecture.

## Problem Statement

The old `identifill_service` had several issues:

1. Called non-existent `rag-service` endpoints
2. Used local SQLite database instead of PostgreSQL
3. Used local file storage instead of MinIO
4. Port was not standardized (8005 instead of 801X pattern)

## Solution Architecture

### Port Architecture (Standardized)

| Port Range | Purpose                | Services                                                                                |
| ---------- | ---------------------- | --------------------------------------------------------------------------------------- |
| 800X       | User-facing APIs       | admin (8001), query (8002)                                                              |
| 801X       | Internal microservices | storage (8010), embedding (8011), vector (8012), rerank (8013), llm (8014), form (8015) |
| 9XXX       | Infrastructure         | minio API (9000), minio console (9001)                                                  |
| 5432       | Database               | PostgreSQL                                                                              |
| 3000       | Frontend               | React app                                                                               |

### Service Communication Flow

```
Frontend (3000)
    ├── Query-Service (8002) ─ User Q&A
    │       ├── /forms/cccd/scan → Form-Service (8015)
    │       ├── /forms/render → Form-Service (8015)
    │       ├── /forms/fill → Form-Service (8015)
    │       └── /forms/save → Storage-Service (8010)
    │
    └── Admin-Service (8001) ─ Document management
            └── /admin/user-forms → Storage-Service (8010)

Form-Service (8015)
    └── Storage-Service (8010) ─ Get/Upload files from MinIO
```

### Storage Pattern (Simplified)

No new database tables for user forms. Using MinIO folder naming convention:

```
MinIO Bucket: legal-documents
├── documents/{doc_id}/          # Document PDFs
├── forms/{doc_id}/              # Form templates (DOCX)
└── user_forms/{session_id}/     # Filled forms
        └── {cccd}_{form-name}.docx  # or {form-name}.docx if no CCCD
```

## Files Created/Modified

### New: `form-service/` (Port 8015)

| File                            | Purpose                                              |
| ------------------------------- | ---------------------------------------------------- |
| `config.py`                     | Service configuration with STORAGE_SERVICE_URL       |
| `main.py`                       | FastAPI app with /health, /render, /fill, /cccd/scan |
| `src/models.py`                 | Pydantic schemas                                     |
| `src/services/cccd_scanner.py`  | QR code scanning (reused from old service)           |
| `src/services/form_renderer.py` | DOCX→HTML conversion via mammoth                     |
| `src/services/form_filler.py`   | Template filling with docxtpl                        |
| `requirements.txt`              | Dependencies                                         |
| `Dockerfile`                    | Container build with libzbar0                        |
| `README.md`                     | Documentation                                        |

### Modified: `llm-service/`

| File            | Change                            |
| --------------- | --------------------------------- |
| `.env`          | Port 8006 → 8014                  |
| `src/config.py` | SERVICE_PORT 8006 → 8014          |
| `Dockerfile`    | Multiple EXPOSE/CMD lines updated |

### Modified: `query-service/`

| File                   | Change                                      |
| ---------------------- | ------------------------------------------- |
| `src/config.py`        | Added FORM_SERVICE_URL                      |
| `src/main.py`          | Import and include forms router             |
| `src/routers/forms.py` | **NEW** - Forward endpoints to form-service |

### Modified: `admin-service/`

| File                        | Change                                      |
| --------------------------- | ------------------------------------------- |
| `src/main.py`               | Import and include user_forms router        |
| `src/routers/user_forms.py` | **NEW** - Manage user-filled forms in MinIO |

### Modified: `docker-compose.yml`

| Change   | Details                                |
| -------- | -------------------------------------- |
| LLM port | 8006 → 8014                            |
| Removed  | identifill-service (old)               |
| Added    | form-service (new, port 8015)          |
| Updated  | query-service depends_on form-service  |
| Updated  | query-service FORM_SERVICE_URL env var |

### Renamed: `identifill_service/` → `identifill_service_old/`

Old service preserved for reference, no longer used.

## API Endpoints

### Query-Service Forms API (User-facing)

| Endpoint                  | Method | Description                      |
| ------------------------- | ------ | -------------------------------- |
| `/forms/cccd/scan`        | POST   | Scan CCCD QR code (base64 image) |
| `/forms/cccd/scan/upload` | POST   | Scan CCCD from file upload       |
| `/forms/render`           | POST   | Render DOCX template to HTML     |
| `/forms/fill`             | POST   | Fill template with data          |
| `/forms/save`             | POST   | Save filled form to MinIO        |
| `/forms/health`           | GET    | Check form-service health        |

### Admin-Service User Forms API

| Endpoint                                             | Method | Description                |
| ---------------------------------------------------- | ------ | -------------------------- |
| `/admin/user-forms`                                  | GET    | List all user-filled forms |
| `/admin/user-forms/{session_id}`                     | GET    | List forms for session     |
| `/admin/user-forms/{session_id}/download/{filename}` | GET    | Download form              |
| `/admin/user-forms/{session_id}/{filename}`          | DELETE | Delete form                |
| `/admin/user-forms/{session_id}`                     | DELETE | Delete all session forms   |

### Form-Service API (Internal)

| Endpoint     | Method | Description             |
| ------------ | ------ | ----------------------- |
| `/health`    | GET    | Health check            |
| `/cccd/scan` | POST   | Scan CCCD QR code       |
| `/render`    | POST   | Render template to HTML |
| `/fill`      | POST   | Fill template with data |

## Next Steps

1. **Test form-service** - Build and run form-service container
2. **Frontend integration** - Update frontend to use new `/forms/*` endpoints
3. **E2E testing** - Test full flow: scan CCCD → fill form → save → download

## Notes

- All form templates are stored in MinIO under `forms/{document_id}/`
- User-filled forms go to `user_forms/{session_id}/`
- No PostgreSQL tables needed for user forms (simplicity over features)
- CCCD scanning uses pyzbar (requires libzbar0 in Docker)
