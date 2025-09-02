# CCCD OCR Autofill - Kế Hoạch Triển Khai Hoàn Chỉnh

## Tổng Quan Dự Án

### Mục Tiêu

Xây dựng tính năng OCR tự động điền form từ camera scan CCCD, tích hợp vào hệ thống LegalRAG hiện có. Tạo component có thể tái sử dụng cho nhiều loại form khác nhau.

### Phạm Vi MVP

- **Document Target**: DOC_001 - Đăng ký khai sinh (`quy_trinh_cap_ho_tich_cap_xa`)
- **Form Target**: `form_dang_ky_khai_sinh.docx`
- **Workflow**: Scan CCCD → OCR → Auto-fill form fields → Preview/Download

### Tech Stack

- **Backend**: FastAPI (hiện có) + Redis (cache) + TrOCR/Donut (OCR) + python-docx-template
- **Frontend**: React/TypeScript (hiện có) + Camera API + PDF.js preview
- **Storage**: Redis (session cache) + Local ephemeral storage

---

## Phase 1: Foundation & Infrastructure (Tuần 1)

**Timeline**: 5-7 ngày | **Priority**: Critical

### 1.1 Dependencies & Environment Setup

**Duration**: 1-2 ngày

#### Backend Dependencies

- [ ] **Thêm vào requirements.txt**:

  ```
  redis==5.0.0
  aioredis==2.0.1
  docxtpl==0.16.8
  mammoth==1.6.0
  easyocr==1.7.0
  opencv-python-headless==4.8.1.78
  python-multipart==0.0.20  # đã có
  ```

- [ ] **Cài đặt LibreOffice** (cho docx→pdf conversion):

  ```bash
  # Windows (chocolatey)
  choco install libreoffice
  # hoặc download manual từ libreoffice.org
  ```

- [ ] **Redis Setup**:
  - [ ] Cài Redis local (Windows: chocolatey/docker)
  - [ ] Test connection: `redis-cli ping`

#### Frontend Dependencies

- [ ] **Thêm vào package.json**:
  ```json
  "react-webcam": "^7.1.1",
  "pdfjs-dist": "^3.11.174"
  ```

### 1.2 Project Structure Setup

**Duration**: 1 ngày

- [ ] **Backend structure**:

  ```
  backend/app/
  ├── services/
  │   ├── ocr_service.py          # NEW
  │   ├── form_filler_service.py  # NEW
  │   ├── redis_helper.py         # NEW
  │   └── form_metadata_service.py # NEW
  ├── api/
  │   ├── ocr.py                  # NEW
  │   └── forms.py                # EXTEND existing
  ├── models/
  │   └── ocr_schemas.py          # NEW
  └── core/
      └── redis_config.py         # NEW
  ```

- [ ] **Frontend structure**:
  ```
  frontend/src/components/
  ├── ocr/
  │   ├── CameraCapture.tsx       # NEW
  │   ├── OCRResults.tsx          # NEW
  │   ├── FormPreview.tsx         # NEW
  │   └── OCRWorkflow.tsx         # NEW - Main component
  └── common/
      └── PDFViewer.tsx           # NEW
  ```

### 1.3 Configuration & Settings

**Duration**: 0.5 ngày

- [ ] **Redis config** (`backend/app/core/redis_config.py`):

  ```python
  REDIS_URL = "redis://localhost:6379"
  REDIS_TTL_SESSION = 900  # 15 minutes
  REDIS_TTL_IMAGE = 120    # 2 minutes
  ```

- [ ] **OCR config**:
  ```python
  OCR_MODEL_NAME = "microsoft/trocr-base-printed"  # MVP
  OCR_CONFIDENCE_THRESHOLD = 0.7
  TEMP_UPLOAD_DIR = "./tmp/uploads"
  ```

---

## Phase 2: Form Metadata & Backend Core (Tuần 1-2)

**Timeline**: 3-4 ngày | **Priority**: Critical

### 2.1 Form Metadata System

**Duration**: 1 ngày

- [ ] **Tạo metadata JSON** cho form khai sinh:

  ```json
  // forms/form_dang_ky_khai_sinh.json
  {
    "form_id": "form_dang_ky_khai_sinh",
    "docx_template": "form_dang_ky_khai_sinh.docx",
    "title": "Tờ khai đăng ký khai sinh",
    "fields": [
      {
        "key": "full_name",
        "label": "Họ và tên cha/mẹ",
        "docx_placeholder": "{{PARENT_NAME}}",
        "type": "text",
        "source": "cccd",
        "required": true
      },
      {
        "key": "cccd",
        "label": "Số CCCD",
        "docx_placeholder": "{{CCCD_NUMBER}}",
        "type": "text",
        "regex": "\\d{9,12}",
        "source": "cccd",
        "required": true
      },
      {
        "key": "dob",
        "label": "Ngày sinh",
        "docx_placeholder": "{{DOB}}",
        "type": "date",
        "format": "dd/MM/yyyy",
        "regex": "\\d{1,2}/\\d{1,2}/\\d{4}",
        "source": "cccd",
        "required": true
      },
      {
        "key": "address",
        "label": "Địa chỉ thường trú",
        "docx_placeholder": "{{ADDRESS}}",
        "type": "text",
        "source": "cccd",
        "required": true
      },
      {
        "key": "hometown",
        "label": "Quê quán",
        "docx_placeholder": "{{HOMETOWN}}",
        "type": "text",
        "source": "cccd",
        "required": false
      },
      {
        "key": "child_name",
        "label": "Họ và tên con",
        "docx_placeholder": "{{CHILD_NAME}}",
        "type": "text",
        "source": "manual",
        "required": true
      }
    ]
  }
  ```

- [ ] **Service metadata loader** (`form_metadata_service.py`):
  - [ ] Load/validate metadata JSON
  - [ ] Get field mapping by form_id
  - [ ] Validate field types & formats

### 2.2 Redis Session Management

**Duration**: 1 ngày

- [ ] **Redis helper service** (`redis_helper.py`):

  - [ ] Connection management
  - [ ] Session CRUD operations
  - [ ] TTL management
  - [ ] Clean expired sessions

- [ ] **Session schema**:
  ```python
  # Pydantic models
  class OCRSession(BaseModel):
      session_id: str
      form_id: str
      user_id: Optional[str] = None
      status: str = "initialized"  # initialized, processed, filled
      parsed_fields: Dict[str, Any] = {}
      confidence_scores: Dict[str, float] = {}
      created_at: datetime
      expires_at: datetime
  ```

### 2.3 OCR Service Core

**Duration**: 1-2 ngày

- [ ] **OCR service** (`ocr_service.py`):

  - [ ] Image preprocessing (resize, orientation)
  - [ ] TrOCR model loading & inference
  - [ ] Text extraction & confidence scoring
  - [ ] CCCD-specific field extraction (regex patterns)
  - [ ] Error handling & fallbacks

- [ ] **Field mapping logic**:
  - [ ] Extract số CCCD (regex: `\d{9,12}`)
  - [ ] Extract ngày sinh (regex: `\d{1,2}/\d{1,2}/\d{4}`)
  - [ ] Extract họ tên (NLP heuristics - đầu dòng, chữ in hoa)
  - [ ] Extract địa chỉ (multiline text after keywords)
  - [ ] Extract quê quán (similar to địa chỉ)

---

## Phase 3: Backend API Development (Tuần 2)

**Timeline**: 3-4 ngày | **Priority**: Critical

### 3.1 OCR API Endpoints

**Duration**: 2 ngày

- [ ] **POST /api/ocr/scan**:

  ```python
  # Input: multipart/form-data image + form_id
  # Output: session_id + parsed_fields + confidences
  ```

  - [ ] Validate image format & size
  - [ ] Process with OCR service
  - [ ] Store session in Redis
  - [ ] Return structured response

- [ ] **GET /api/ocr/session/{session_id}**:

  - [ ] Retrieve session data
  - [ ] Validate session exists & not expired
  - [ ] Return parsed fields + status

- [ ] **PUT /api/ocr/session/{session_id}/fields**:

  - [ ] Update parsed fields (user corrections)
  - [ ] Validate field formats
  - [ ] Update Redis session

- [ ] **DELETE /api/ocr/session/{session_id}**:
  - [ ] Clean up session
  - [ ] Remove temp files

### 3.2 Form Fill API

**Duration**: 2 ngày

- [ ] **Form filler service** (`form_filler_service.py`):

  - [ ] Load docx template using `python-docx-template`
  - [ ] Map session fields to template placeholders
  - [ ] Generate filled docx
  - [ ] Convert to PDF using LibreOffice
  - [ ] Store in temp location with TTL

- [ ] **POST /api/forms/{form_id}/autofill**:

  ```python
  # Input: session_id + field_overrides (optional)
  # Output: filled_docx_url + pdf_preview_url
  ```

  - [ ] Validate session exists
  - [ ] Load form metadata
  - [ ] Fill template with session data
  - [ ] Convert & store outputs
  - [ ] Return download URLs

- [ ] **GET /api/forms/{form_id}/metadata**:
  - [ ] Return form metadata JSON
  - [ ] Field definitions for frontend validation

---

## Phase 4: Frontend Development (Tuần 2-3)

**Timeline**: 4-5 ngày | **Priority**: Critical

### 4.1 Camera Capture Component

**Duration**: 2 ngày

- [ ] **CameraCapture.tsx**:

  - [ ] `getUserMedia` integration
  - [ ] Real-time video preview
  - [ ] Capture frame to canvas
  - [ ] Image compression before upload
  - [ ] Error handling (no camera, permissions)

- [ ] **Features**:
  - [ ] Auto-detect CCCD frame (optional - nice to have)
  - [ ] Manual capture button
  - [ ] Preview captured image
  - [ ] Retake functionality
  - [ ] Loading states during upload

### 4.2 OCR Results Interface

**Duration**: 1 ngày

- [ ] **OCRResults.tsx**:
  - [ ] Display parsed fields with confidence badges
  - [ ] Editable form inputs for corrections
  - [ ] Field validation (regex, required)
  - [ ] Confidence color coding (green/yellow/red)
  - [ ] Save changes to session

### 4.3 Form Preview & Fill

**Duration**: 2 ngày

- [ ] **FormPreview.tsx**:

  - [ ] Render docx as HTML (mammoth) - left pane
  - [ ] Highlight fillable fields
  - [ ] PDF preview after autofill - right pane
  - [ ] Download buttons (docx/pdf)

- [ ] **PDF Viewer integration**:
  - [ ] PDF.js setup
  - [ ] Zoom controls
  - [ ] Print functionality

### 4.4 Main Workflow Component

**Duration**: 1 ngày

- [ ] **OCRWorkflow.tsx** - Orchestrator component:
  - [ ] Step-by-step wizard UI
  - [ ] State management (camera → ocr → review → fill → preview)
  - [ ] Progress indicators
  - [ ] Error boundary & user feedback
  - [ ] Integration with existing chat workflow

---

## Phase 5: Integration & Testing (Tuần 3)

**Timeline**: 3-4 ngày | **Priority**: High

### 5.1 Backend Integration Testing

**Duration**: 1-2 ngày

- [ ] **Unit tests**:

  - [ ] OCR service field extraction
  - [ ] Form metadata loading
  - [ ] Redis session management
  - [ ] Form filling accuracy

- [ ] **Integration tests**:
  - [ ] Full API workflow: scan → process → fill
  - [ ] Error scenarios (invalid image, expired session)
  - [ ] Performance testing (OCR latency)

### 5.2 Frontend Integration

**Duration**: 1 ngày

- [ ] **Component integration**:
  - [ ] Wire camera → OCR API calls
  - [ ] State management between components
  - [ ] Error handling & user feedback
  - [ ] Loading states & progress bars

### 5.3 End-to-End Testing

**Duration**: 1 ngày

- [ ] **Manual testing**:

  - [ ] Multiple CCCD samples (different lighting, angles)
  - [ ] Field accuracy validation
  - [ ] Form filling correctness
  - [ ] Download functionality
  - [ ] Browser compatibility (Chrome, Firefox, Edge)

- [ ] **Performance validation**:
  - [ ] OCR processing time (<10s target)
  - [ ] Form generation time (<5s target)
  - [ ] Session cleanup verification

---

## Phase 6: Production Readiness (Tuần 4)

**Timeline**: 2-3 ngày | **Priority**: Medium

### 6.1 Security & Privacy

**Duration**: 1 ngày

- [ ] **Security measures**:

  - [ ] Validate file uploads (type, size limits)
  - [ ] Rate limiting on OCR endpoints
  - [ ] Redis security (auth, network isolation)
  - [ ] Input sanitization & validation

- [ ] **Privacy compliance**:
  - [ ] Auto-cleanup expired sessions
  - [ ] No long-term image storage
  - [ ] User consent UI
  - [ ] Data masking in logs

### 6.2 Monitoring & Logging

**Duration**: 1 ngày

- [ ] **Logging**:

  - [ ] OCR success/failure rates
  - [ ] Processing times & performance metrics
  - [ ] Error categories & debugging info
  - [ ] User session tracking (anonymized)

- [ ] **Health checks**:
  - [ ] Redis connectivity
  - [ ] Model loading status
  - [ ] Disk space monitoring (temp files)

### 6.3 Documentation & Deployment

**Duration**: 1 ngày

- [ ] **API documentation**:

  - [ ] OpenAPI/Swagger specs
  - [ ] Request/response examples
  - [ ] Error codes & messages

- [ ] **Deployment prep**:
  - [ ] Environment variables setup
  - [ ] Docker configuration updates
  - [ ] Production Redis configuration
  - [ ] LibreOffice installation scripts

---

## Phase 7: Chat Integration (Future - Post MVP)

**Timeline**: 1-2 tuần | **Priority**: Low

### 7.1 Workflow Integration

- [ ] **Chat trigger detection**:

  - [ ] Detect form-related queries
  - [ ] Show "Autofill with CCCD" button
  - [ ] Launch OCR workflow modal

- [ ] **Result integration**:
  - [ ] Return filled form to chat context
  - [ ] Show completion summary
  - [ ] Allow further questions about filled form

---

## Technical Requirements

### Hardware/Infrastructure

- **Development**:

  - CPU: Intel/AMD 4+ cores (OCR processing)
  - RAM: 8GB+ (model loading)
  - Storage: 2GB+ free (temp files, models)
  - Camera: Any webcam/laptop camera

- **Production**:
  - CPU: 8+ cores or GPU (NVIDIA) for better OCR performance
  - RAM: 16GB+ for concurrent users
  - Redis: 1GB+ memory
  - Storage: SSD recommended for temp file I/O

### Performance Targets

- **OCR Processing**: <10 giây per image
- **Form Generation**: <5 giây
- **Session TTL**: 15 phút (configurable)
- **Concurrent Users**: 10+ users simultaneous OCR

### Browser Support

- Chrome 80+ (primary)
- Firefox 75+
- Safari 13+ (iOS/macOS)
- Edge 80+

---

## Risk Assessment & Mitigation

### High Risk

1. **OCR Accuracy** → Mitigation: Confidence scoring, manual review, model fine-tuning
2. **Camera Permissions** → Mitigation: Clear user guidance, fallback file upload
3. **Form Template Changes** → Mitigation: Metadata versioning, template validation

### Medium Risk

1. **Performance Issues** → Mitigation: Async processing, caching, GPU acceleration
2. **Redis Availability** → Mitigation: Health checks, fallback to database sessions
3. **Browser Compatibility** → Mitigation: Progressive enhancement, polyfills

### Low Risk

1. **PDF Generation** → Mitigation: Multiple conversion tools, format fallbacks
2. **Storage Limits** → Mitigation: Cleanup automation, monitoring alerts

---

## Success Metrics

### Functional Metrics

- [ ] OCR accuracy >85% for key fields (CCCD, DOB, Name)
- [ ] End-to-end workflow completion <60 giây
- [ ] Form filling accuracy >95%
- [ ] Zero data persistence beyond session TTL

### User Experience Metrics

- [ ] Camera capture success rate >90%
- [ ] User workflow completion rate >80%
- [ ] Error recovery success >95%
- [ ] Browser compatibility 100% (supported browsers)

### Technical Metrics

- [ ] API response time <2s (95th percentile)
- [ ] System uptime >99%
- [ ] Memory usage <512MB per session
- [ ] Zero data leaks or security issues

---

## Future Enhancements (Post-MVP)

### Phase 2+ Features

1. **Advanced OCR**: Donut model fine-tuning for Vietnamese documents
2. **Multi-document**: Support passport, driver license, other IDs
3. **Form Templates**: Visual form builder for new document types
4. **Batch Processing**: Multiple forms from single CCCD scan
5. **Mobile App**: React Native implementation
6. **AI Validation**: Cross-reference filled data with knowledge base

### Scalability Improvements

1. **Microservice Architecture**: Separate OCR service
2. **Queue System**: Redis Queue/Celery for heavy processing
3. **CDN Integration**: Fast global access for form templates
4. **Database Migration**: PostgreSQL for form metadata

---

**Tổng thời gian ước tính**: 3-4 tuần cho MVP hoàn chỉnh  
**Resources cần**: 1 Full-stack developer  
**Budget ước tính**: $0 (sử dụng open-source tools)

---

_Last updated: September 1, 2025_  
_Project: LegalRAG OCR Integration_  
_Version: MVP 1.0 Plan_
