# Kế Hoạch Xây Dựng Microservice OCR Nhận Dạng Căn Cước Công Dân

## 📋 Tổng Quan Dự Án

### Mục Tiêu

Xây dựng một microservice hoàn chỉnh để:

- Chụp ảnh CCCD qua camera (mặt trước & mặt sau)
- Lưu trữ tạm thời trong Redis cache
- Sử dụng VietOCR để nhận dạng văn bản
- Trích xuất thông tin theo schema chuẩn
- Hiển thị kết quả trên giao diện

### Kiến Trúc Microservice

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   OCR Service   │
│   (React/TS)    │◄──►│   (FastAPI)      │◄──►│   (VietOCR)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Redis Cache    │
                       │  (Temp Storage) │
                       └─────────────────┘
```

## 🎯 Phase 1: Thiết Lập Cơ Sở Hạ Tầng (3-4 ngày)

### 1.1 Cài Đặt Dependencies và Environment

- [ ] Cài đặt Redis server
- [ ] Cài đặt VietOCR và dependencies
- [ ] Thiết lập Docker containers
- [ ] Cấu hình environment variables

### 1.2 Thiết Lập Backend Structure

- [ ] Tạo module `ocr_service` trong backend
- [ ] Thiết lập Redis client
- [ ] Tạo schemas cho CCCD data
- [ ] Thiết lập logging và error handling

### 1.3 Testing Setup

- [ ] Unit tests cho core functions
- [ ] Integration tests cho Redis
- [ ] Mock data cho development

## 🎯 Phase 2: Backend OCR Service (5-6 ngày)

### 2.1 Core OCR Engine

- [ ] Tích hợp VietOCR library
- [ ] Xây dựng image preprocessing
- [ ] Implement text detection và recognition
- [ ] Optimize performance cho CCCD format

### 2.2 Data Processing Pipeline

- [ ] Text extraction algorithms
- [ ] Pattern matching cho số CCCD
- [ ] Name extraction và validation
- [ ] Error handling và retry mechanisms

### 2.3 Cache Management

- [ ] Redis integration
- [ ] Image storage strategies
- [ ] Session management
- [ ] Automatic cleanup policies

### 2.4 API Endpoints

- [ ] `POST /api/ocr/upload-image` - Upload ảnh CCCD
- [ ] `GET /api/ocr/process/{session_id}` - Xử lý OCR
- [ ] `GET /api/ocr/results/{session_id}` - Lấy kết quả
- [ ] `DELETE /api/ocr/session/{session_id}` - Xóa session

## 🎯 Phase 3: Frontend Camera Interface (4-5 ngày)

### 3.1 Camera Component

- [ ] WebRTC camera access
- [ ] Image capture functionality
- [ ] Preview và confirm interface
- [ ] Mobile responsive design

### 3.2 Image Management

- [ ] Front/back side detection
- [ ] Image quality validation
- [ ] Compression và optimization
- [ ] Upload progress indicators

### 3.3 Results Display

- [ ] Schema-based form rendering
- [ ] Real-time OCR status updates
- [ ] Error handling và retry options
- [ ] Export functionality

## 🎯 Phase 4: Integration & Testing (3-4 ngày)

### 4.1 End-to-End Integration

- [ ] Frontend-Backend connection
- [ ] Error handling flows
- [ ] Performance optimization
- [ ] Security measures

### 4.2 Comprehensive Testing

- [ ] Unit tests coverage
- [ ] Integration tests
- [ ] E2E testing với real CCCD images
- [ ] Performance benchmarking

### 4.3 Documentation

- [ ] API documentation
- [ ] Setup instructions
- [ ] Usage guidelines
- [ ] Troubleshooting guide

## 📊 Technical Specifications

### CCCD Data Schema

```json
{
  "session_id": "uuid",
  "front_image": "base64_string",
  "back_image": "base64_string",
  "extracted_data": {
    "id_number": "string",
    "full_name": "string",
    "date_of_birth": "date",
    "gender": "string",
    "nationality": "string",
    "hometown": "string",
    "residence": "string",
    "issue_date": "date",
    "expiry_date": "date"
  },
  "confidence_scores": {
    "id_number": "float",
    "full_name": "float"
  },
  "processing_status": "enum",
  "created_at": "timestamp",
  "expires_at": "timestamp"
}
```

### API Response Format

```json
{
  "success": true,
  "data": "...",
  "message": "string",
  "session_id": "uuid",
  "processing_time": "float"
}
```

## 🔧 Technology Stack

### Backend

- **FastAPI**: Main web framework
- **VietOCR**: OCR engine
- **Redis**: Temporary storage
- **Pydantic**: Data validation
- **Pillow**: Image processing
- **OpenCV**: Image preprocessing

### Frontend

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **TailwindCSS**: Styling
- **Axios**: HTTP client
- **React Query**: State management

### DevOps

- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **pytest**: Testing framework
- **Jest**: Frontend testing

## 📈 Success Metrics

### Performance Targets

- OCR processing time: < 3 seconds per image
- Image upload: < 2 seconds
- Accuracy rate: > 95% for clear CCCD images
- Cache retention: 1 hour default

### Quality Metrics

- Test coverage: > 90%
- API response time: < 500ms
- Mobile compatibility: iOS/Android browsers
- Error rate: < 1%

## 🚀 Next Steps After Completion

1. **Advanced OCR Features**

   - Multiple CCCD formats support
   - Handwritten text recognition
   - Damaged/worn card handling

2. **Security Enhancements**

   - Image encryption
   - PII data protection
   - Audit logging

3. **Performance Optimization**

   - GPU acceleration
   - Batch processing
   - CDN integration

4. **Integration Features**
   - Database persistence option
   - External API connections
   - Webhook notifications

## 📝 Notes

- Ưu tiên mobile-first design do camera usage
- Implement progressive web app features
- Consider offline capabilities
- Plan for horizontal scaling
- Prepare for multi-language support (Vietnamese, English)
