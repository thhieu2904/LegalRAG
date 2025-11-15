# Metadata Extraction Logic - Chi Tiết

## 1. Overview - Cấu trúc Tổng quát

Admin-Service có một class `LegalMetadataExtractor` chịu trách nhiệm trích xuất thông tin từ text của tài liệu pháp luật Việt Nam.

```python
LegalMetadataExtractor
├── extract_document_code()  → 68/2018/NĐ-CP
├── extract_dates()          → [01/7/2025, 12/6/2025]
├── extract_organizations()  → [Bộ Tư Pháp, Sở Lao Động]
├── extract_sections()       → [Điều 1, Mục 1.1, Chương I]
└── extract_all()            → Gọi tất cả 4 hàm trên
```

---

## 2. Chi Tiết Từng Pattern

### 2.1 Document Code Pattern (Mã Nghị Định/Quyết Định)

**Code:**

```python
DOCUMENT_CODE_PATTERNS = [
    r'(\d+/\d{4}/NĐ-CP)',  # Nghị định: 68/2018/NĐ-CP
    r'(\d+/\d{4}/QĐ-)',     # Quyết định: 68/2018/QĐ-...
    r'(\d+/\d{4}/TT-)',     # Thông tư: 68/2018/TT-...
    r'(QT\s*0?\d+/)',       # Quy trình: QT 01/BTNN
]
```

**Giải thích:**

| Pattern           | Ý Nghĩa                      | Ví Dụ Trích Xuất          |
| ----------------- | ---------------------------- | ------------------------- |
| `\d+/\d{4}/NĐ-CP` | Số/Năm/NĐ-CP (Nghị định)     | **68/2018/NĐ-CP**         |
| `\d+/\d{4}/QĐ-`   | Số/Năm/QĐ- (Quyết định)      | **123/2020/QĐ-TTg**       |
| `\d+/\d{4}/TT-`   | Số/Năm/TT- (Thông tư)        | **45/2019/TT-BCA**        |
| `QT\s*0?\d+/`     | QT + số tùy chọn (Quy trình) | **QT 01/** hoặc **QT01/** |

**Example từ test PDF:**

```
Mã hiệu: QT 0 1/BTNN
↓
Pattern: r'(QT\s*0?\d+/)'
↓
Match: "QT 0 1/"
```

**Workflow:**

```
Text input: "...Mã hiệu: QT 0 1/BTNN..."
  ↓
Loop through patterns
  ↓
Try pattern 1 (Nghị định): No match ✗
Try pattern 2 (Quyết định): No match ✗
Try pattern 3 (Thông tư): No match ✗
Try pattern 4 (Quy trình): Match! ✓
  ↓
Return: "QT 0 1/"
```

---

### 2.2 Date Pattern (Ngày Tháng)

**Code:**

```python
DATE_PATTERNS = [
    r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
    r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})',  # DD tháng MM năm YYYY
]
```

**Giải thích:**

| Pattern                                   | Ý Nghĩa                            | Ví Dụ Trích Xuất              |
| ----------------------------------------- | ---------------------------------- | ----------------------------- |
| `\d{1,2}/\d{1,2}/\d{4}`                   | 1-2 chữ số / 1-2 chữ số / 4 chữ số | **01/7/2025**, **12/06/2025** |
| `\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}` | Dạng chữ "DD tháng MM năm YYYY"    | **1 tháng 7 năm 2025**        |

**Example:**

```
Text: "Ngày ban hành: 01/7/2025"
  ↓
Pattern 1: r'(\d{1,2}/\d{1,2}/\d{4})'
  ↓
Match: "01/7/2025" ✓

Text: "Ngày 15 tháng 3 năm 2024"
  ↓
Pattern 2: r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})'
  ↓
Match: "15 tháng 3 năm 2024" ✓
```

**Kết quả từ test:**

```
Extracted dates: ['01/7/2025', '12/6/2025']
```

---

### 2.3 Organization Pattern (Bộ, Sở, Cục)

**Code:**

```python
ORGANIZATION_PATTERNS = [
    r'(Bộ\s+\w+)',          # Bộ Tư pháp, Bộ Lao động
    r'(Sở\s+\w+)',          # Sở Tư pháp, Sở Lao động
    r'(Cục\s+\w+)',         # Cục Thuế
    r'(Văn phòng\s+\w+)',   # Văn phòng Chính phủ
]
```

**Giải thích:**

| Pattern           | Ý Nghĩa                   | Ví Dụ Trích Xuất                     |
| ----------------- | ------------------------- | ------------------------------------ |
| `Bộ\s+\w+`        | "Bộ" + khoảng trắng + từ  | **Bộ Tư**, **Bộ Trưởng**, **Bộ Lao** |
| `Sở\s+\w+`        | "Sở" + khoảng trắng + từ  | **Sở Tư**, **Sở Lao**                |
| `Cục\s+\w+`       | "Cục" + khoảng trắng + từ | **Cục Thuế**, **Cục Hải**            |
| `Văn phòng\s+\w+` | "Văn phòng" + từ          | **Văn phòng UBND**                   |

**Example:**

```
Text: "...SỞ TƯ PHÁP...Bộ Tư pháp...Sở Lao động..."
  ↓
Pattern 1 - Bộ: Matches "Bộ Tư" ✓
Pattern 2 - Sở: Matches "Sở Tư", "Sở Lao" ✓
Pattern 3 - Cục: No match
Pattern 4 - Văn phòng: Matches "Văn phòng UBND" ✓
  ↓
Result: ['Bộ Tư', 'Sở Tư', 'Sở Lao', 'Văn phòng UBND', ...]
```

**Kết quả từ test:**

```
Organizations: ['Bộ Tư', 'Bộ trưởng', 'Văn phòng UBND', 'Bộ phận', 'Sở Tư', 'Bộ Khoa']
```

---

### 2.4 Section Pattern (Điều, Mục, Chương)

**Code:**

```python
SECTION_PATTERNS = [
    r'(Điều\s+\d+)',       # Điều 1, Điều 32
    r'(Mục\s+\d+\.\d+)',   # Mục 1.1, Mục 2.3
    r'(Chương\s+[IVX]+)',  # Chương I, Chương II, Chương V
]
```

**Giải thích:**

| Pattern           | Ý Nghĩa             | Ví Dụ Trích Xuất                          |
| ----------------- | ------------------- | ----------------------------------------- |
| `Điều\s+\d+`      | "Điều" + số (Ả Rập) | **Điều 1**, **Điều 32**, **Điều 41**      |
| `Mục\s+\d+\.\d+`  | "Mục" + số.số       | **Mục 1.1**, **Mục 2.3**                  |
| `Chương\s+[IVX]+` | "Chương" + số La Mã | **Chương I**, **Chương II**, **Chương V** |

**Example:**

```
Text: "...Điều 32...Điều 33...Mục 1.1...Chương I..."
  ↓
Pattern 1: Matches "Điều 32", "Điều 33" ✓
Pattern 2: Matches "Mục 1.1" ✓
Pattern 3: Matches "Chương I" ✓
  ↓
Result: ['Điều 32', 'Điều 33', 'Mục 1.1', 'Chương I']
```

**Kết quả từ test:**

```
Sections: ['Điều 32', 'Điều \n41', 'Điều 33']
```

(Lưu ý: Có `\n` vì PDF text extraction có line breaks)

---

## 3. Extract All - Combine Tất Cả

**Code:**

```python
@staticmethod
def extract_all(text: str, pages: int = 0) -> Dict[str, Any]:
    # Gọi tất cả 4 hàm
    document_code = LegalMetadataExtractor.extract_document_code(text)
    dates = LegalMetadataExtractor.extract_dates(text)
    organizations = LegalMetadataExtractor.extract_organizations(text)
    sections = LegalMetadataExtractor.extract_sections(text)

    # Tính confidence (0.0 - 1.0)
    extracted_fields = sum([
        1 if document_code else 0,
        1 if dates else 0,
        1 if organizations else 0,
        1 if sections else 0,
    ])
    confidence = extracted_fields / 4.0

    return {
        "document_code": document_code,
        "dates": dates,
        "organizations": organizations,
        "sections": sections,
        "pages": pages,
        "word_count": len(text.split()),
        "extraction_confidence": confidence,
    }
```

**Workflow:**

```
Input: Raw text từ PDF
  ↓
extract_document_code() → "QT 0 1/"
extract_dates() → ["01/7/2025", "12/6/2025"]
extract_organizations() → ["Bộ Tư", "Sở Lao", ...]
extract_sections() → ["Điều 32", "Điều 33", ...]
  ↓
Calculate Confidence:
  - Có document_code: +1 ✓
  - Có dates: +1 ✓
  - Có organizations: +1 ✓
  - Có sections: +1 ✓
  - Total: 4/4 = 1.0 (100%) hoặc 3/4 = 0.75 (75%)
  ↓
Return: {document_code, dates, organizations, sections, confidence}
```

---

## 4. Cách Patterns Được Áp Dụng Trong Endpoint

**Trong `process_document()` endpoint:**

```python
# STEP 3: Extract metadata (Admin does this locally)
metadata_dict = LegalMetadataExtractor.extract_all(text, pages=pages)
metadata = ExtractedMetadata(**metadata_dict)

# Result:
return ProcessDocumentResponse(
    success=True,
    file_id=document_id,
    file_path=file_path,
    file_size=file_size,
    text=text,                    # Raw text từ Storage
    text_stats={...},
    metadata=metadata,             # ← Extracted metadata ở đây
    message=f"Successfully processed {file.filename}"
)
```

---

## 5. Data Flow Chi Tiết

```
User sends PDF
  ↓
POST /admin/process-document
  ↓
┌─────────────────────────────────────────────┐
│ STEP 1: Upload to Storage-Service           │
│ - Call: POST /upload                        │
│ - Input: PDF file                           │
│ - Output: file_path                         │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│ STEP 2: Extract Text from Storage-Service   │
│ - Call: POST /extract-text                  │
│ - Input: PDF file                           │
│ - Output: {text, pages, character_count}    │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│ STEP 3: Extract Metadata (Local in Admin)   │
│                                             │
│ text → LegalMetadataExtractor.extract_all() │
│          ↓                                   │
│          extract_document_code(text)        │
│          extract_dates(text)                │
│          extract_organizations(text)        │
│          extract_sections(text)             │
│          ↓                                   │
│       {metadata}                            │
└─────────────────────────────────────────────┘
  ↓
Return ProcessDocumentResponse with all fields
```

---

## 6. Test Result - Ví Dụ Thực Tế

**Input:** Tệp PDF "Thủ tục xác định cơ quan giải quyết bồi thường.pdf"

**Raw Text Sample:**

```
SỞ TƯ PHÁP  QUY TRÌNH
Thủ tục xác định cơ quan giải quyết bồi thường Mã hiệu: QT 0 1/BTNN
Lần ban hành: 01
Ngày ban hành: 01/7/2025
...
Điều 32, Điều 33, Điều 41
...
Bộ Tư pháp, Sở Lao động, Văn phòng UBND
```

**Extracted Metadata:**

```json
{
  "document_code": "QT 0 1/",
  "dates": ["01/7/2025", "12/6/2025"],
  "organizations": ["Bộ Tư", "Bộ trưởng", "Văn phòng UBND", "Sở Tư"],
  "sections": ["Điều 32", "Điều 33", "Điều 41"],
  "pages": 7,
  "word_count": 2596,
  "extraction_confidence": 0.75
}
```

---

## 7. Làm Sao Để Mở Rộng Patterns

Nếu muốn add pattern mới (ví dụ: extract người ký):

```python
# Thêm class variable mới
SIGNATORY_PATTERNS = [
    r'(Trưởng\s+\w+)',      # Trưởng phòng, Trưởng cơ quan
    r'(Chủ\s+tịch\s+\w+)',  # Chủ tịch UBND
]

# Thêm hàm extract mới
@staticmethod
def extract_signatories(text: str) -> Optional[List[str]]:
    signatories = []
    for pattern in LegalMetadataExtractor.SIGNATORY_PATTERNS:
        matches = re.findall(pattern, text)
        signatories.extend(matches)
    return list(set(signatories)) if signatories else None

# Gọi trong extract_all()
signatories = LegalMetadataExtractor.extract_signatories(text)
```

---

## 8. Summary

| Component                 | Chức Năng                    | Input        | Output                 |
| ------------------------- | ---------------------------- | ------------ | ---------------------- |
| `extract_document_code()` | Tìm mã pháp luật             | Text         | String (68/2018/NĐ-CP) |
| `extract_dates()`         | Tìm ngày tháng               | Text         | List[String]           |
| `extract_organizations()` | Tìm bộ/sở/cục                | Text         | List[String]           |
| `extract_sections()`      | Tìm điều/mục/chương          | Text         | List[String]           |
| `extract_all()`           | Gọi tất cả + tính confidence | Text + pages | Dict with all metadata |

**Key Insight:**

- Mỗi pattern là một **regex rule** để tìm pattern cụ thể
- Chúng hoạt động **độc lập** với nhau
- Có thể add/modify patterns mà không ảnh hưởng phần khác
- `confidence` tính dựa trên **số trường đã trích xuất được**
