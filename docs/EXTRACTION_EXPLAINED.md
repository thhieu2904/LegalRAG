# METADATA EXTRACTION - QUÁ TRÌNH HOẠT ĐỘNG

## 🎯 Tóm Tắt

Admin-Service có một class `LegalMetadataExtractor` dùng **Regex Patterns** để tìm và trích xuất thông tin từ text của PDF.

```
PDF → Extract Text → LegalMetadataExtractor.extract_all()
                      ├─ extract_document_code()
                      ├─ extract_dates()
                      ├─ extract_organizations()
                      └─ extract_sections()
                           ↓
                      Return metadata
```

---

## 📋 4 Loại Patterns Chính

### 1️⃣ DOCUMENT CODE - Mã Nghị Định/Quyết Định

**Mục đích:** Tìm mã của tài liệu (ví dụ: 68/2018/NĐ-CP)

**Patterns:**

```python
r'(\d+/\d{4}/NĐ-CP)'   # 68/2018/NĐ-CP
r'(\d+/\d{4}/QĐ-)'     # 1205/2020/QĐ-TTg
r'(\d+/\d{4}/TT-)'     # 45/2019/TT-BCA
r'(QT\s*0?\d+/)'       # QT 01/BTNN
```

**Cách hoạt động:**

```
Text: "...Mã hiệu: QT 0 1/BTNN..."
       ↓
Loop through patterns:
  1. Try pattern 1 (Nghị định) → NO MATCH
  2. Try pattern 2 (Quyết định) → NO MATCH
  3. Try pattern 3 (Thông tư) → NO MATCH
  4. Try pattern 4 (Quy trình) → MATCH! "QT 0 1/"
       ↓
Return: "QT 0 1/"
```

---

### 2️⃣ DATES - Ngày Tháng Năm

**Mục đích:** Tìm tất cả các ngày tháng trong tài liệu

**Patterns:**

```python
r'(\d{1,2}/\d{1,2}/\d{4})'           # 01/7/2025, 15/03/2024
r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})'  # 15 tháng 3 năm 2024
```

**Cách hoạt động:**

```
Text: "Ngày ban hành: 01/7/2025"
       ↓
Pattern 1: r'(\d{1,2}/\d{1,2}/\d{4})'
  - Tìm: 1-2 digits / 1-2 digits / 4 digits
  - Tìm thấy: "01/7/2025" ✓
       ↓
Return: ["01/7/2025"]
```

---

### 3️⃣ ORGANIZATIONS - Bộ, Sở, Cục

**Mục đích:** Tìm tên các cơ quan chính phủ

**Patterns:**

```python
r'(Bộ\s+\w+)'          # Bộ Tư pháp, Bộ Lao động
r'(Sở\s+\w+)'          # Sở Tư pháp, Sở Lao động
r'(Cục\s+\w+)'         # Cục Thuế
r'(Văn phòng\s+\w+)'   # Văn phòng UBND
```

**Cách hoạt động:**

```
Text: "...Bộ Tư pháp công bố...Sở Lao động tỉnh A..."
       ↓
Pattern 1: r'(Bộ\s+\w+)' → Tìm "Bộ" + từ → "Bộ Tư"
Pattern 2: r'(Sở\s+\w+)' → Tìm "Sở" + từ → "Sở Lao"
Pattern 3: r'(Cục\s+\w+)' → Không tìm thấy
Pattern 4: r'(Văn phòng\s+\w+)' → Tìm "Văn phòng" + từ
       ↓
Return: ["Bộ Tư", "Sở Lao", "Văn phòng UBND"]
```

---

### 4️⃣ SECTIONS - Điều, Mục, Chương

**Mục đích:** Tìm các phần/điều/mục của tài liệu

**Patterns:**

```python
r'(Điều\s+\d+)'       # Điều 1, Điều 32
r'(Mục\s+\d+\.\d+)'   # Mục 1.1, Mục 2.3
r'(Chương\s+[IVX]+)'  # Chương I, Chương II
```

**Cách hoạt động:**

```
Text: "...Chương I...Điều 1...Mục 1.1...Điều 32..."
       ↓
Pattern 1: r'(Điều\s+\d+)' → "Điều 1", "Điều 32"
Pattern 2: r'(Mục\s+\d+\.\d+)' → "Mục 1.1"
Pattern 3: r'(Chương\s+[IVX]+)' → "Chương I"
       ↓
Return: ["Điều 1", "Mục 1.1", "Điều 32", "Chương I"]
```

---

## 🔧 Regex Syntax Cơ Bản

```
\d    = Digit (0-9)                    → \d+ = 1 hoặc nhiều digits
\w    = Word character (a-z, A-Z, _)  → \w+ = 1 hoặc nhiều ký tự
\s    = Whitespace (space, tab)        → \s+ = 1 hoặc nhiều spaces
+     = 1 hoặc nhiều lần
*     = 0 hoặc nhiều lần
?     = Optional (0 hoặc 1 lần)
{n}   = Chính xác n lần
[...]  = Character class                → [IVX]+ = Một hoặc nhiều chữ La Mã
[^...] = NOT character class            → [^(\n]+ = Bất kỳ ký tự nào trừ "(" hoặc newline
(...)  = Capture group                  → Ghi nhớ match
```

---

## 🎬 Cách Patterns Được Dùng Trong Code

**Code hiện tại (admin-service/src/main.py):**

```python
class LegalMetadataExtractor:
    # Define patterns
    DOCUMENT_CODE_PATTERNS = [...]
    DATE_PATTERNS = [...]
    ORGANIZATION_PATTERNS = [...]
    SECTION_PATTERNS = [...]

    @staticmethod
    def extract_all(text: str, pages: int = 0) -> Dict:
        # 1. Extract từng trường
        document_code = extract_document_code(text)
        dates = extract_dates(text)
        organizations = extract_organizations(text)
        sections = extract_sections(text)

        # 2. Tính confidence (bao nhiêu % data được extract)
        extracted_fields = sum([
            1 if document_code else 0,
            1 if dates else 0,
            1 if organizations else 0,
            1 if sections else 0,
        ])
        confidence = extracted_fields / 4.0  # 0.0 to 1.0

        # 3. Return kết quả
        return {
            "document_code": document_code,
            "dates": dates,
            "organizations": organizations,
            "sections": sections,
            "extraction_confidence": confidence,
        }
```

---

## 🧪 Test Result - Ví Dụ Thực Tế

**Input:** PDF file "Thủ tục xác định cơ quan giải quyết bồi thường.pdf"

**Output từ endpoint:**

```json
{
  "file_id": "test-doc-001",
  "file_path": "documents/test-doc-001/...",
  "file_size": 355568,
  "text": "SỞ TƯ PHÁP QUY TRÌNH...",
  "text_stats": {
    "pages": 7,
    "characters": 11140,
    "words": 2596
  },
  "metadata": {
    "document_code": null,           ← Không tìm thấy (0/4)
    "dates": ["01/7/2025", "12/6/2025"],
    "organizations": ["Bộ Tư", "Bộ trưởng", ...],
    "sections": ["Điều 32", "Điều 41", ...],
    "extraction_confidence": 0.75    ← 3 trường / 4 = 75%
  }
}
```

---

## 🚀 Cách Mở Rộng Cho Document Type Khác

### Example: Add Support Cho Hợp Đồng (Contract)

```python
# Bước 1: Define patterns
CONTRACT_PATTERNS = {
    "party_a": r'Bên\s+A\s*:\s*([^(\n]+)',
    "party_b": r'Bên\s+B\s*:\s*([^(\n]+)',
    "signing_date": r'Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})',
}

# Bước 2: Create extract function
def extract_contract_parties(text: str) -> Optional[Dict]:
    result = {}
    match_a = re.search(CONTRACT_PATTERNS["party_a"], text)
    if match_a:
        result["party_a"] = match_a.group(1).strip()
    # ... tương tự cho party_b
    return result if result else None

# Bước 3: Add to extract_all()
if doc_type == "contract":
    parties = extract_contract_parties(text)
    return {
        "parties": parties,
        "signing_date": extract_signing_date(text),
        "extraction_confidence": ...,
    }

# Bước 4: Update endpoint
@app.post("/admin/process-document")
async def process_document(
    file: UploadFile,
    doc_type: str = "legal"  # ADD THIS
):
    metadata = extract_all(text, doc_type=doc_type)
    # ...
```

---

## 📊 Comparison: Patterns Khác Nhau

| Document Type | Patterns                   | Example Match        |
| ------------- | -------------------------- | -------------------- |
| **Legal**     | Code, Dates, Org, Sections | 68/2018/NĐ-CP        |
| **Contract**  | Parties, Points, Sign Date | Bên A: Công ty ABC   |
| **Minutes**   | Time, Location, Attendees  | Hôm 15/3/2025, Sở XX |
| **Form**      | Fields, Dates, Amounts     | Tên: ..., Ngày: ...  |

---

## 🔍 Debugging: Làm Sao Biết Pattern Sai?

### Khi Pattern Không Match:

```python
text = "Mã hiệu: QT 0 1/BTNN"
pattern = r'(QT\s*0?\d+/)'

# Test pattern
import re
matches = re.findall(pattern, text)
print(matches)  # Should print: ['QT 0 1/']

# Nếu empty [] = KHÔNG MATCH
# Nguyên nhân có thể:
# 1. Pattern sai → Debug regex
# 2. Text khác → Update pattern
# 3. Case sensitive → Add (?i) flag
```

---

## 📚 Resources Để Học Regex

- **Regex101.com** - Interactive regex tester
- **Regex cheat sheet** - Xem file CUSTOM_PATTERNS_GUIDE.md
- **Python re module** - Official docs

---

## ✅ Summary

| Concept           | Giải Thích                       |
| ----------------- | -------------------------------- |
| **Pattern**       | Regex rule để tìm text cụ thể    |
| **Match**         | Kết quả khi pattern tìm thấy     |
| **Capture Group** | `(...)` - Phần text được ghi nhớ |
| **Extraction**    | Process tìm và trích xuất data   |
| **Confidence**    | % data được extract thành công   |

**Key Takeaway:**

- Mỗi pattern = 1 regex rule
- Patterns độc lập → có thể test riêng
- Dễ mở rộng → add pattern mới cho document type khác
- Tính confidence dựa trên số trường được extract
