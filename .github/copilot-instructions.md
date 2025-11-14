# LegalRAG Copilot Instructions

## 🏗️ System Architecture

**LegalRAG** is a Vietnamese legal document Q&A system with microservices architecture:

### Services Overview

- **Frontend** (Port 3000/5173): React/TypeScript SPA with Vite
- **RAG Service** (Port 8000): Legal document retrieval-augmented generation
- **Identifill Service** (Port 8002): CCCD QR code scanning and card detection

### Key Architecture Patterns

#### Multi-Service Communication

```typescript
// frontend/src/api/axios-config.ts - Centralized API configuration
export const ragAPI = axios.create({ baseURL: "http://localhost:8000" });
export const identifillAPI = axios.create({ baseURL: "http://localhost:8002" });

```

#### Vietnamese Legal Domain Focus

- CCCD (Vietnamese ID card) processing with QR code parsing
- Legal document Q&A with context expansion
- Voice integration for accessibility
- Form processing for administrative procedures

## 🚀 Critical Developer Workflows

### Environment Setup

```bash
# 1. Frontend (always first)
cd frontend && npm install

# 2. Python services require conda environments
# Identifill Service
conda env create -f identifill_service/environment.yml
conda activate identifill_env
cd identifill_service && pip install -r requirements.txt

# RAG Service (no conda env file, use pip directly)
cd rag_service && pip install -r requirements.txt
```

### Development Startup Sequence

```bash
# Terminal 1: Frontend (Vite dev server)
cd frontend && npm run dev

# Terminal 2: RAG Service
conda activate LegalRAG && cd rag_service && python main.py

# Terminal 3: Identifill Service
conda activate identifill_env && cd identifill_service && python main.py

# Terminal 4: OCR Service (if needed)
# OCR service startup commands
```

### Production Deployment

- Services run independently on different ports
- CORS configured for localhost origins
- Token-based authentication via localStorage
- Health checks available at `/health` endpoints

## 📋 Project Conventions

### API Response Patterns

```typescript
// Consistent error handling across services
interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  processing_time?: number;
  confidence?: number;
}
```

### CCCD Data Structure

```typescript
// frontend/src/api/qr-scanner-api.ts
interface CCCDData {
  scan_cccd: string;        // 12-digit citizen ID
  scan_cmnd?: string;       // Old 9-digit ID
  scan_ho_ten: string;      // Full name
  scan_ngay_sinh: string;   // DOB (DDMMYYYY)
  scan_gioi_tinh: string;   // Gender
  scan_dia_chi: string;     // Address
  scan_ngay_cap: string;    // Issue date (DDMMYYYY)
}
```

### State Management

- React hooks for component-level state (`useChat`, `useVoice`)
- Context providers for global state (`VoiceContext`)
- Centralized API calls in dedicated service files

### File Organization

```
frontend/src/
├── api/           # Service-specific API calls
├── components/    # Reusable UI components
├── pages/         # Route-level components
├── hooks/         # Custom React hooks
├── contexts/      # React context providers
└── types/         # TypeScript type definitions
```

## 🔧 Development Patterns

### Error Handling

```typescript
// Centralized error interception in axios-config.ts
ragAPI.interceptors.response.use(
  (response) => console.log(`✅ RAG API Success: ${response.status}`),
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

### Logging Conventions

```python
# Python services use structured logging
logger.info("🚀 Starting LegalRAG API...")
logger.error(f"❌ Failed to initialize services: {e}")
```

### Testing Approach

- Create test scripts in `root/test/` directory
- Avoid full server startup for unit tests
- Use script-based testing over server-dependent tests
- Prefer isolated component testing

## 🎯 Key Integration Points

### Frontend-Backend Communication

- Axios interceptors for request/response logging
- Centralized error handling and token management
- CORS configuration for development origins
- Base64 image data transmission for OCR/CCCD processing

### Service Dependencies

- RAG Service: ChromaDB for vector storage, HuggingFace models
- Identifill Service: OpenCV for image processing, PyZBar for QR codes
- OCR Service: Vietnamese OCR models (VietOCR)

### Data Flow Patterns

1. **Chat Flow**: User message → RAG API → Vector search → LLM generation → Response
2. **CCCD Flow**: Image upload → Identifill API → QR detection → Data parsing → Form population
3. **Voice Flow**: Speech recognition → Text conversion → Chat processing → TTS response

## ⚡ Performance Considerations

### VRAM Optimization (RAG Service)

- Embedding model runs on CPU to save VRAM
- LLM and reranker models use GPU for parallel processing
- Context expansion caching for repeated queries
- Session management with automatic cleanup

### Image Processing

- Base64 encoding for image transmission
- Auto-crop functionality for card detection
- Confidence scoring for OCR results
- Processing time optimization (< 1 second target)

## 🔍 Debugging Guidelines

### Common Issues

- **Port conflicts**: Check if services are already running
- **Conda environment**: Always activate correct environment
- **CORS errors**: Verify frontend origin in service config
- **Model loading**: Check HF_CACHE_DIR and offline mode settings

### Log Analysis

- Frontend: Browser console for API call logs
- Backend: Structured logging with emojis for quick identification
- Performance: Check `processing_time` in API responses

### Testing Strategy

```bash
# Test individual services without full startup
# Create isolated test scripts in test/ directory
# Use mock data for API testing
# Validate CCCD parsing with known test cases
```

## 📚 Essential Files to Reference

### Architecture Understanding

- `frontend/src/api/axios-config.ts` - Service communication setup
- `rag_service/main.py` - Service initialization and lifecycle
- `identifill_service/main.py` - QR scanning service setup
- `frontend/src/App.tsx` - Main application routing

### Key Components

- `frontend/src/hooks/useChat.ts` - Chat functionality
- `frontend/src/api/rag-api.ts` - RAG service integration
- `frontend/src/api/qr-scanner-api.ts` - CCCD processing
- `rag_service/app/services/rag_engine.py` - Core RAG logic

### Configuration

- `identifill_service/environment.yml` - Conda environment setup
- `rag_service/app/core/config.py` - Service configuration
- `frontend/package.json` - Frontend dependencies and scripts `</content>`
  `<parameter name="filePath">`d:\Personal\LegalRAG_OCR\.github\copilot-instructions.md
