# Copilot Instructions for LegalRAG_OCR

## Project Overview

- **LegalRAG_OCR** is a multi-service system for legal document Q&A, OCR, and Vietnamese CCCD (citizen ID) QR code scanning.
- The workspace includes:
  - `frontend/`: React + Vite + TypeScript SPA, integrates with backend APIs for RAG, OCR, and QR scanning.
  - `identifill_service/`: FastAPI service for CCCD QR code scanning and card detection (port 8002).
  - `rag_service/`: FastAPI-based RAG (Retrieval-Augmented Generation) backend (port 8000).

## Architecture & Data Flow

- **Frontend** calls backend services via REST APIs:
  - `/api` and `/router` → RAG service (port 8000)
  - `/api/v1/qr/scan`, `/api/v1/card/detect` → Identifill service (port 8002)
  - `/ocr` endpoints → OCR service (port 8001, not included in this repo)
- All API endpoints and base URLs are configured in `frontend/src/api/axios-config.ts`.
- Each backend service is independently deployable and has its own health check endpoint.

## Developer Workflows

- **Frontend**
  - Dev: `cd frontend && npm install && npm run dev`
  - Build: `npm run build`
  - Lint: `npm run lint`
  - Uses Vite, TailwindCSS, Radix UI, and Axios.
  - API integration patterns: see `frontend/src/api/` for service wrappers and error handling conventions.
- **Identifill Service**
  - Python 3.11, Conda env (`identifill_env`)
  - Start: `conda activate identifill_env && cd identifill_service && uvicorn main:app --reload --host 0.0.0.0 --port 8002`
  - API docs: see `identifill_service/README.md` for endpoint details and request/response formats.
- **RAG Service**
  - Python, FastAPI, optimized for VRAM usage (see `rag_service/main.py`)
  - Start: `python rag_service/main.py` (ensure dependencies and models are available)
  - Key features: context expansion, ambiguous query detection, session management.

## Project-Specific Conventions

- **Action Plan First:** Always start with a todo list/plan before coding (see `.github/instructions/instruction_copilot.instructions.md`).
- **API Layer:** All API calls are wrapped in service modules under `frontend/src/api/`.
- **Error Handling:** Centralized in Axios interceptors (`axios-config.ts`).
- **Clarification Flow:** Ambiguous queries trigger clarification UI (see `MainChatPage.tsx`, `useChat.ts`, and `ClarificationOptions`).
- **Vietnamese CCCD Data:** QR and OCR data structures are defined in `frontend/src/api/ocr-api.ts` and `qr-scanner-api.ts`.
- **CORS:** Each backend service manages its own CORS settings.

## Integration & Extension

- To add new backend endpoints, update the relevant API wrapper in `frontend/src/api/` and ensure interceptors handle errors.
- For new frontend features, follow the context-driven state management and component structure in `frontend/src/`.
- For backend service changes, update the corresponding `README.md` for API docs and usage.

## References

- See `identifill_service/README.md` for full API docs and troubleshooting.
- See `.github/instructions/instruction_copilot.instructions.md` for required agent workflow.
- See `FRONTEND_CLARIFICATION_FIX.md` for clarification UI/logic patterns.

---

**Always follow the action plan/todo-first workflow and reference the API/service wrappers for integration patterns.**
