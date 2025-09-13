# Copilot Instructions for LegalRAG_OCR

## Project Overview

**LegalRAG_OCR** is a multi-service system for legal document Q&A, OCR, and Vietnamese CCCD (citizen ID) QR code scanning. The workspace includes:

- `frontend/`: React + Vite + TypeScript SPA, integrates with backend APIs for RAG, OCR, and QR scanning.
- `identifill_service/`: FastAPI service for CCCD QR code scanning and card detection (port 8002).
- `rag_service/`: FastAPI-based RAG (Retrieval-Augmented Generation) backend (port 8000).

## Architecture & Data Flow

- **Frontend** communicates with backend services via REST APIs:
  - `/api` and `/router` → RAG service (port 8000)
  - `/api/v1/qr/scan`, `/api/v1/card/detect` → Identifill service (port 8002)
  - `/ocr` endpoints → OCR service (port 8001, not included in this repo)
- All API endpoints and base URLs are configured in `frontend/src/api/axios-config.ts`.
- Each backend service is independently deployable and exposes a health check endpoint.

## Developer Workflows

### Frontend

- Dev: `cd frontend && npm install && npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`
- Uses Vite, TailwindCSS, Radix UI, and Axios.
- **API integration:** All API calls are wrapped in service modules under `frontend/src/api/` (e.g., `rag-api.ts`, `ocr-api.ts`, `qr-scanner-api.ts`).
- **Error handling:** Centralized in Axios interceptors (`axios-config.ts`).
- **Clarification UI:** Ambiguous queries trigger clarification UI (see `MainChatPage.tsx`, `useChat.ts`, and `ClarificationOptions`).

### Identifill Service

- Python 3.11, Conda env (`identifill_env`)
- Start: `conda activate identifill_env && cd identifill_service && uvicorn main:app --reload --host 0.0.0.0 --port 8002`
- API docs and endpoint details: see `identifill_service/README.md`.

### RAG Service

- Python, FastAPI, VRAM-optimized (see `rag_service/main.py`)
- Start: `python rag_service/main.py` (ensure dependencies and models are available)
- conda activate LegalRAG
- Key features: context expansion, ambiguous query detection, session management, VRAM optimization.

## Project-Specific Conventions

- **Action Plan First:** Always start with a todo list/plan before coding (see `.github/instructions/instruction_copilot.instructions.md`).
- **API Layer:** All API calls must go through service modules in `frontend/src/api/`.
- **Error Handling:** Use centralized Axios interceptors in `axios-config.ts` for all API error handling and logging.
- **Clarification Flow:** Ambiguous queries (detected by backend or frontend logic) trigger the clarification UI. See `useChat.ts` for state management and `MainChatPage.tsx` for UI logic. Example: `setCurrentClarification` is used to manage clarification prompts.
- **Data Structures:** Vietnamese CCCD QR and OCR data types are defined in `frontend/src/api/ocr-api.ts` and `qr-scanner-api.ts`.
- **CORS:** Each backend service manages its own CORS settings.

## Integration & Extension

- **Adding Backend Endpoints:** Update or add the relevant API wrapper in `frontend/src/api/` (e.g., add a new method to `rag-api.ts`), and ensure error handling is covered by interceptors.
- **Frontend Features:** Follow context-driven state management and modular component structure in `frontend/src/`.
- **Backend Changes:** Update the corresponding `README.md` for API documentation and usage examples.

## Examples

- **Adding a new API endpoint:**

  1. Implement the endpoint in the backend service (see `identifill_service/app/api/v1/` or `rag_service/app/api/`).
  2. Add a method to the relevant API wrapper in `frontend/src/api/`.
  3. Use the new method in frontend components/services.

- **Clarification UI pattern:**

  - When the backend returns an ambiguous query response, `useChat.ts` sets `currentClarification`, which triggers the UI in `MainChatPage.tsx`.

## References

- `identifill_service/README.md`: Full API docs and troubleshooting.
- `.github/instructions/instruction_copilot.instructions.md`: Required agent workflow.
- `FRONTEND_CLARIFICATION_FIX.md`: Clarification UI/logic patterns.

---

**Always follow the action plan/todo-first workflow and reference the API/service wrappers for integration patterns.**
