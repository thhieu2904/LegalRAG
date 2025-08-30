# PROMPT KHỞI ĐỘNG TẠO JSON CHUẨN HÓA

## 🎯 MỤC TIÊU

Tạo file JSON với cấu trúc chuẩn hóa, tối ưu cho hệ thống RAG và tra cứu pháp luật

## 📋 CẤU TRÚC CHUẨN HÓA

### ✅ METADATA (Thông tin cơ bản)

```json
"metadata": {
  "document_id": "DOC_XXX",
  "document_code": "QT XX/XXX",
  "title": "Tiêu đề đầy đủ của thủ tục",
  "version": "01",
  "issue_date": "DD/MM/YYYY",
  "document_type": "Quy trình hành chính",
  "issuing_authority": "Cơ quan ban hành",
  "applicable_scope": "Phạm vi áp dụng",
  "purpose": "Mục đích của quy trình",
  "keywords": [
    "từ khóa 1",
    "từ khóa 2",
    "từ khóa 3"
  ],
  "references": [
    "Văn bản pháp luật 1",
    "Văn bản pháp luật 2"
  ],
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z",
  "status": "active"
}
```

### ✅ FEE_STRUCTURE (Cấu trúc phí chuẩn)

```json
"fee_structure": {
  "base_fee": 0,
  "additional_fees": [
    {
      "description": "Mô tả loại phí",
      "amount_vnd": 8000,
      "unit": "bản"
    }
  ],
  "exemptions": [
    "Trường hợp miễn phí 1",
    "Trường hợp miễn phí 2"
  ],
  "payment_methods": [
    "Tiền mặt",
    "Chuyển khoản"
  ],
  "fee_notes": "Ghi chú về phí"
}
```

### ✅ FORM_LOGIC (Thông tin biểu mẫu)

```json
"form_logic": {
  "required_forms": [
    "Tờ khai theo mẫu"
  ],
  "optional_forms": [
    "Giấy ủy quyền (nếu có)"
  ],
  "form_requirements": [
    "Form phải có đầy đủ thông tin"
  ],
  "submission_methods": [
    "Nộp trực tiếp tại cơ quan",
    "Gửi qua bưu điện",
    "Nộp trực tuyến"
  ],
  "form_notes": "Ghi chú về biểu mẫu"
}
```

### ✅ CONTENT_CHUNKS (Nội dung chia nhỏ)

```json
"content_chunks": [
  {
    "chunk_id": "chunk_001_basic_info",
    "title": "Thông tin cơ bản",
    "content": "Nội dung chi tiết từ văn bản gốc",
    "keywords": [
      "từ khóa 1",
      "từ khóa 2",
      "từ khóa 3"
    ],
    "source_reference": "DOC_XXX - Trang đầu",
    "chunk_type": "header",
    "importance_score": 0.9
  }
]
```

## 📊 NGUYÊN TẮC CHIA CHUNKS

### ✅ CHUNK TYPES (Loại chunks)

- **header** - Thông tin cơ bản, mục lục (importance_score: 0.8-0.9)
- **purpose_scope** - Mục đích và phạm vi áp dụng (importance_score: 0.9-1.0)
- **references_definitions** - Tài liệu viện dẫn và định nghĩa (importance_score: 0.7-0.8)
- **procedure_details** - Nội dung quy trình chi tiết (importance_score: 1.0)
- **forms_documents** - Biểu mẫu và hồ sơ lưu (importance_score: 0.7-0.8)

### ✅ CHUNKS CƠ BẢN (luôn có)

- **Thông tin cơ bản** - Header, mục lục, trách nhiệm
- **Mục đích và phạm vi** - Mục đích, đối tượng áp dụng
- **Thành phần hồ sơ** - Danh sách giấy tờ cần nộp
- **Cơ quan thực hiện** - Địa điểm và thẩm quyền
- **Thời hạn giải quyết** - Thời gian xử lý
- **Lệ phí** - Chi phí thực hiện
- **Kết quả thực hiện** - Sản phẩm đầu ra

### ➕ CHUNKS BỔ SUNG (tùy loại văn bản)

- **Tài liệu viện dẫn** - Văn bản pháp luật liên quan
- **Định nghĩa và viết tắt** - Giải thích thuật ngữ
- **Đối tượng thực hiện** - Ai được thực hiện thủ tục
- **Yêu cầu điều kiện** - Điều kiện tiên quyết
- **Quy trình thực hiện** - Các bước chi tiết
- **Biểu mẫu** - Mẫu đơn, tờ khai
- **Căn cứ pháp lý** - Văn bản viện dẫn

### ❌ TRÁNH

- Chunk quá lớn (>800 từ)
- Chunk quá nhỏ (<100 từ)
- Thông tin trùng lặp
- Cấu trúc không logic
- Chunk không có keywords rõ ràng

## 🚀 HƯỚNG DẪN THỰC HIỆN

### Bước 1: Phân tích văn bản gốc

```markdown
- Đọc kỹ toàn bộ file DOC
- Liệt kê các mục chính
- Xác định thông tin quan trọng
- Phân loại theo cấu trúc chuẩn
```

### Bước 2: Trích xuất thông tin metadata

```markdown
- Document ID và code (DOC_XXX, QT XX/XXX)
- Title và version đầy đủ
- Issuing authority và issue date
- Applicable scope và purpose
- Keywords và references quan trọng
- Created/updated timestamps
```

### Bước 3: Phân tích fee_structure

```markdown
- Phí cơ bản (base_fee)
- Các loại phí bổ sung (additional_fees)
- Trường hợp miễn phí (exemptions)
- Phương thức thanh toán (payment_methods)
- Ghi chú về phí (fee_notes)
```

### Bước 4: Xác định form_logic

```markdown
- Required forms (biểu mẫu bắt buộc)
- Optional forms (biểu mẫu tùy chọn)
- Form requirements (yêu cầu về biểu mẫu)
- Submission methods (cách thức nộp)
- Form notes (ghi chú về biểu mẫu)
```

### Bước 5: Chia content_chunks

```markdown
- Mỗi chunk 1 chủ đề rõ ràng
- Chunk ID dạng string (chunk_001_xxx)
- Chunk type phù hợp (header, purpose_scope, etc.)
- Importance score từ 0.0-1.0
- Keywords phong phú và chính xác
- Source reference rõ ràng
```

## 📝 QUY TẮC CHUẨN HÓA

### ✅ METADATA PHẢI CÓ:

- document_id: ID chuẩn của document (DOC_XXX)
- document_code: mã hiệu quy trình (QT XX/XXX)
- title: tiêu đề đầy đủ
- version: phiên bản (01, 02, etc.)
- issue_date: ngày ban hành (DD/MM/YYYY)
- document_type: loại văn bản
- issuing_authority: cơ quan ban hành
- applicable_scope: phạm vi áp dụng
- purpose: mục đích của quy trình
- keywords: mảng từ khóa quan trọng
- references: mảng văn bản pháp luật viện dẫn
- created_at: timestamp tạo (ISO 8601)
- updated_at: timestamp cập nhật (ISO 8601)
- status: trạng thái (active, inactive)

### ✅ FEE_STRUCTURE PHẢI CÓ:

- base_fee: số tiền phí cơ bản (VNĐ)
- additional_fees: mảng các phí bổ sung
- exemptions: mảng trường hợp miễn phí
- payment_methods: mảng phương thức thanh toán
- fee_notes: ghi chú về lệ phí

### ✅ FORM_LOGIC PHẢI CÓ:

- required_forms: mảng biểu mẫu bắt buộc
- optional_forms: mảng biểu mẫu tùy chọn
- form_requirements: mảng yêu cầu về biểu mẫu
- submission_methods: mảng cách thức nộp hồ sơ
- form_notes: ghi chú về biểu mẫu

### ✅ CONTENT_CHUNKS PHẢI CÓ:

- chunk_id: ID dạng string (chunk_001_xxx)
- title: tiêu đề của chunk
- content: nội dung chi tiết
- keywords: mảng từ khóa
- source_reference: tham chiếu nguồn
- chunk_type: loại chunk (header, purpose_scope, etc.)
- importance_score: điểm quan trọng (0.0-1.0)

## 🎯 TIÊU CHÍ HOÀN THÀNH

- [ ] Metadata đầy đủ với document_id, keywords, references
- [ ] Fee_structure hoàn chỉnh (base_fee, additional_fees, exemptions, payment_methods, fee_notes)
- [ ] Form_logic chi tiết (required/optional forms, submission methods)
- [ ] Content_chunks 5-8 chunks với importance_score và chunk_type
- [ ] Keywords phong phú và chính xác cho mỗi chunk
- [ ] Source reference rõ ràng và nhất quán
- [ ] JSON syntax hợp lệ và format đẹp
- [ ] Unicode hiển thị đúng tiếng Việt
- [ ] Chunk size hợp lý (200-600 từ)
- [ ] RAG-optimized structure (importance scoring, semantic keywords)

## 💡 MẸO THỰC HÀNH

1. **Bắt đầu với template chuẩn**
2. **Điền metadata trước - tập trung vào keywords và references**
3. **Phân tích lệ phí chi tiết - bao gồm payment methods**
4. **Xác định form logic - required vs optional forms**
5. **Chia chunks theo logic - sử dụng chunk_type phù hợp**
6. **Gán importance_score - ưu tiên nội dung quan trọng**
7. **Test với RAG system - kiểm tra retrieval accuracy**
8. **Validate JSON structure - đảm bảo syntax đúng**

## 🔧 TEMPLATE JSON MẪU

```json
{
  "metadata": {
    "document_id": "DOC_001",
    "document_code": "QT 01/CT-HCTP",
    "title": "Cấp bản sao từ sổ gốc",
    "version": "01",
    "issue_date": "07/7/2025",
    "document_type": "Quy trình hành chính",
    "issuing_authority": "Sở Tư pháp",
    "applicable_scope": "Áp dụng đối với các tổ chức, cá nhân có nhu cầu thực hiện dịch vụ hành chính công",
    "purpose": "Quy định thành phần hồ sơ, lệ phí, trình tự, cách thức và thời gian giải quyết hồ sơ hành chính",
    "keywords": ["cấp bản sao", "sổ gốc", "chứng thực", "hành chính công"],
    "references": ["Nghị định số 23/2015/ND-CP", "Nghị định số 07/2025/ND-CP"],
    "created_at": "2025-01-27T10:00:00Z",
    "updated_at": "2025-01-27T10:00:00Z",
    "status": "active"
  },
  "fee_structure": {
    "base_fee": 0,
    "additional_fees": [],
    "exemptions": [],
    "payment_methods": [],
    "fee_notes": "Không có phí"
  },
  "form_logic": {
    "required_forms": [],
    "optional_forms": [],
    "form_requirements": [],
    "submission_methods": ["Nộp trực tiếp tại cơ quan", "Gửi qua bưu điện"],
    "form_notes": "Không có mẫu đơn, mẫu tờ khai"
  },
  "content_chunks": [
    {
      "chunk_id": "chunk_001_basic_info",
      "title": "Thông tin cơ bản",
      "content": "Nội dung...",
      "keywords": ["từ khóa"],
      "source_reference": "DOC_001 - Trang đầu",
      "chunk_type": "header",
      "importance_score": 0.9
    }
  ]
}
```

**Lưu ý:** Tuân thủ cấu trúc chuẩn để đảm bảo tính nhất quán và khả năng tích hợp với hệ thống RAG!
