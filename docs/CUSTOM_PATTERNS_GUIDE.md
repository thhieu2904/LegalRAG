# Custom Patterns - Cách Thêm Patterns Mới Cho Tài Liệu Khác

## Problem Statement

Mỗi loại tài liệu pháp luật Việt Nam có cấu trúc khác nhau:

- **Nghị định (NĐ)** → Format: `XX/YYYY/NĐ-CP`
- **Quyết định (QĐ)** → Format: `XX/YYYY/QĐ-TTg`
- **Quy trình (QT)** → Format: `QT XX/YYY`
- **Hợp đồng** → Có `Bên A:`, `Bên B:`, `Ngày ký:`
- **Biên bản** → Có `Thời gian:`, `Địa điểm:`, `Người tham dự:`

Hiện tại Admin-Service chỉ xử lý 4 trường metadata. Bạn muốn add thêm cho type document khác.

---

## Solution: Add Custom Patterns

### Step 1: Identify Pattern in Document

**Example: Add extraction cho "Hợp đồng" (Contract)**

Open PDF, xem structure:

```
HỢPĐỒNG DỊCH VỤ

Bên A: Công ty Cổ phần ABC (gọi tắt là "Bên A")
Bên B: Ông Nguyễn Văn X, sinh năm 1990, ở địa chỉ ... (gọi tắt là "Bên B")

Thỏa thuận như sau:

Điểm 1: Nội dung công việc
Điểm 2: Thời gian thực hiện
Điểm 3: Thanh toán
...

Ngày ký: 15/01/2025
Nơi ký: Tại văn phòng Công ty ABC
```

### Step 2: Write Regex Patterns

```python
# Thêm vào LegalMetadataExtractor class
CONTRACT_PATTERNS = {
    "party_a": r'Bên\s+A\s*:\s*([^(\n]+)',          # Bên A: ...
    "party_b": r'Bên\s+B\s*:\s*([^(\n]+)',          # Bên B: ...
    "contract_points": r'Điểm\s+(\d+)',             # Điểm 1, 2, 3
    "signing_date": r'Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})',  # Ngày ký: 15/01/2025
    "signing_location": r'Nơi\s+ký\s*:\s*([^\n]+)', # Nơi ký: ...
}
```

**Giải thích từng pattern:**

| Pattern          | Regex                             | Ý Nghĩa                                            |
| ---------------- | --------------------------------- | -------------------------------------------------- |
| Party A          | `Bên\s+A\s*:\s*([^(\n]+)`         | "Bên A:" + khoảng cách + text đến "(" hoặc newline |
| Party B          | `Bên\s+B\s*:\s*([^(\n]+)`         | Tương tự Party A                                   |
| Contract Points  | `Điểm\s+(\d+)`                    | "Điểm" + số                                        |
| Signing Date     | `Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})` | "Ngày ký:" + date DD/MM/YYYY                       |
| Signing Location | `Nơi\s+ký\s*:\s*([^\n]+)`         | "Nơi ký:" + text đến newline                       |

### Step 3: Implement Extract Function

```python
class LegalMetadataExtractor:
    """Existing code..."""

    # Add contract patterns
    CONTRACT_PATTERNS = {
        "party_a": r'Bên\s+A\s*:\s*([^(\n]+)',
        "party_b": r'Bên\s+B\s*:\s*([^(\n]+)',
        "contract_points": r'Điểm\s+(\d+)',
        "signing_date": r'Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})',
        "signing_location": r'Nơi\s+ký\s*:\s*([^\n]+)',
    }

    @staticmethod
    def extract_contract_parties(text: str) -> Optional[Dict[str, str]]:
        """Extract contract parties (Bên A, Bên B)"""
        result = {}

        # Extract Party A
        match_a = re.search(CONTRACT_PATTERNS["party_a"], text)
        if match_a:
            result["party_a"] = match_a.group(1).strip()

        # Extract Party B
        match_b = re.search(CONTRACT_PATTERNS["party_b"], text)
        if match_b:
            result["party_b"] = match_b.group(1).strip()

        return result if result else None

    @staticmethod
    def extract_contract_points(text: str) -> Optional[List[int]]:
        """Extract contract points (Điểm 1, 2, 3, ...)"""
        matches = re.findall(CONTRACT_PATTERNS["contract_points"], text)
        if matches:
            return [int(m) for m in matches]
        return None

    @staticmethod
    def extract_signing_info(text: str) -> Optional[Dict[str, str]]:
        """Extract signing date and location"""
        result = {}

        # Extract signing date
        match_date = re.search(CONTRACT_PATTERNS["signing_date"], text)
        if match_date:
            result["signing_date"] = match_date.group(1)

        # Extract signing location
        match_loc = re.search(CONTRACT_PATTERNS["signing_location"], text)
        if match_loc:
            result["signing_location"] = match_loc.group(1).strip()

        return result if result else None
```

### Step 4: Integrate Into extract_all()

```python
@staticmethod
def extract_all(text: str, pages: int = 0, doc_type: str = "legal") -> Dict[str, Any]:
    """
    Extract all metadata from text

    Args:
        text: Document text
        pages: Number of pages
        doc_type: "legal" (default), "contract", "minutes", etc.
    """

    if doc_type == "legal":
        # Existing legal document extraction
        document_code = LegalMetadataExtractor.extract_document_code(text)
        dates = LegalMetadataExtractor.extract_dates(text)
        organizations = LegalMetadataExtractor.extract_organizations(text)
        sections = LegalMetadataExtractor.extract_sections(text)

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

    elif doc_type == "contract":
        # New contract extraction
        parties = LegalMetadataExtractor.extract_contract_parties(text)
        contract_points = LegalMetadataExtractor.extract_contract_points(text)
        signing_info = LegalMetadataExtractor.extract_signing_info(text)

        extracted_fields = sum([
            1 if parties else 0,
            1 if contract_points else 0,
            1 if signing_info else 0,
        ])
        confidence = extracted_fields / 3.0

        return {
            "parties": parties,
            "contract_points": contract_points,
            "signing_date": signing_info.get("signing_date") if signing_info else None,
            "signing_location": signing_info.get("signing_location") if signing_info else None,
            "pages": pages,
            "word_count": len(text.split()),
            "extraction_confidence": confidence,
        }
```

### Step 5: Update Endpoint to Accept doc_type

```python
@app.post("/admin/process-document", response_model=ProcessDocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    document_id: str = "doc-001",
    doc_type: str = "legal",  # ADD THIS
):
    """
    Args:
        file: PDF file
        document_id: Document ID
        doc_type: "legal" (Nghị định/QĐ/etc), "contract" (Hợp đồng), "minutes" (Biên bản)
    """

    # ... existing code ...

    # STEP 3: Extract metadata
    metadata_dict = LegalMetadataExtractor.extract_all(
        text,
        pages=pages,
        doc_type=doc_type  # PASS doc_type
    )
    metadata = ExtractedMetadata(**metadata_dict)

    # ... rest of code ...
```

---

## Example: Contract Document

### Input Text:

```
HỢPĐỒNG DỊCH VỤ

Bên A: Công ty Cổ phần ABC (gọi tắt là "Bên A")
Bên B: Ông Nguyễn Văn X, sinh năm 1990 (gọi tắt là "Bên B")

Điểm 1: Nội dung công việc
Điểm 2: Thời gian thực hiện
Điểm 3: Thanh toán
Điểm 4: Bảo mật

Ngày ký: 15/01/2025
Nơi ký: Tại văn phòng Công ty ABC
```

### Pattern Matching:

```
Pattern: r'Bên\s+A\s*:\s*([^(\n]+)'
Text: "Bên A: Công ty Cổ phần ABC (gọi tắt là "Bên A")"
Match: "Công ty Cổ phần ABC "  ← Stops at "("

Pattern: r'Bên\s+B\s*:\s*([^(\n]+)'
Text: "Bên B: Ông Nguyễn Văn X, sinh năm 1990 (gọi tắt là "Bên B")"
Match: "Ông Nguyễn Văn X, sinh năm 1990 "  ← Stops at "("

Pattern: r'Điểm\s+(\d+)'
Text: "Điểm 1: ... Điểm 2: ... Điểm 3: ... Điểm 4: ..."
Matches: ["1", "2", "3", "4"]

Pattern: r'Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})'
Text: "Ngày ký: 15/01/2025"
Match: "15/01/2025"

Pattern: r'Nơi\s+ký\s*:\s*([^\n]+)'
Text: "Nơi ký: Tại văn phòng Công ty ABC"
Match: "Tại văn phòng Công ty ABC"
```

### Output:

```json
{
  "parties": {
    "party_a": "Công ty Cổ phần ABC",
    "party_b": "Ông Nguyễn Văn X, sinh năm 1990"
  },
  "contract_points": [1, 2, 3, 4],
  "signing_date": "15/01/2025",
  "signing_location": "Tại văn phòng Công ty ABC",
  "pages": 5,
  "word_count": 1200,
  "extraction_confidence": 1.0
}
```

---

## How to Test Custom Pattern

### 1. Update Code:

```python
# admin-service/src/main.py

class LegalMetadataExtractor:
    # ... existing patterns ...

    # Add new patterns
    CONTRACT_PATTERNS = {
        "party_a": r'Bên\s+A\s*:\s*([^(\n]+)',
        "party_b": r'Bên\s+B\s*:\s*([^(\n]+)',
        "signing_date": r'Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})',
    }

    @staticmethod
    def extract_contract_parties(text: str) -> Optional[Dict[str, str]]:
        result = {}
        match_a = re.search(CONTRACT_PATTERNS["party_a"], text)
        if match_a:
            result["party_a"] = match_a.group(1).strip()
        match_b = re.search(CONTRACT_PATTERNS["party_b"], text)
        if match_b:
            result["party_b"] = match_b.group(1).strip()
        return result if result else None

    # ... more functions ...
```

### 2. Update extract_all():

```python
@staticmethod
def extract_all(text: str, pages: int = 0, doc_type: str = "legal") -> Dict[str, Any]:
    if doc_type == "contract":
        parties = LegalMetadataExtractor.extract_contract_parties(text)
        return {
            "parties": parties,
            "pages": pages,
            "word_count": len(text.split()),
            "extraction_confidence": 1.0 if parties else 0.0,
        }
    else:
        # existing legal document code
        pass
```

### 3. Update Endpoint:

```python
@app.post("/admin/process-document")
async def process_document(
    file: UploadFile = File(...),
    document_id: str = "doc-001",
    doc_type: str = "legal",
):
    # ... existing code ...
    metadata_dict = LegalMetadataExtractor.extract_all(text, pages=pages, doc_type=doc_type)
    # ... rest ...
```

### 4. Test with Query Parameter:

```bash
# Test with legal document (default)
curl -X POST "http://localhost:8002/admin/process-document" \
  -F "file=@decree.pdf" \
  -F "document_id=dec-001"

# Test with contract
curl -X POST "http://localhost:8002/admin/process-document" \
  -F "file=@contract.pdf" \
  -F "document_id=cont-001" \
  -F "doc_type=contract"
```

---

## Regex Cheat Sheet for Common Cases

### Vietnamese Legal Documents

```regex
# Bộ, Sở, Cục + name
(Bộ|Sở|Cục)\s+\w+                # "Bộ Tư" hoặc "Sở Lao"

# Ngày tháng năm
\d{1,2}/\d{1,2}/\d{4}             # 15/01/2025
\d{1,2}\s+tháng\s+\d{1,2}         # 15 tháng 01

# Điều, Mục, Chương
Điều\s+\d+                        # Điều 1, Điều 32
Mục\s+\d+\.\d+                    # Mục 1.1, Mục 2.3
Chương\s+[IVX]+                   # Chương I, Chương II

# Văn bản (Nghị định, QĐ, etc)
\d+/\d{4}/(NĐ-CP|QĐ|TT)          # 68/2018/NĐ-CP

# Extract specific text until character
(Bên\s+A\s*:\s*[^(\n]+)           # "Bên A: ..." until "(" or newline
(Tên\s*:\s*[^,\n]+)               # "Tên: ..." until "," or newline
```

### Regex Syntax Reference

```regex
\d          = Digit (0-9)
\w          = Word character (a-z, A-Z, 0-9, _)
\s          = Whitespace (space, tab, newline)
.           = Any character
+           = 1 or more
*           = 0 or more
?           = 0 or 1 (optional)
{n}         = Exactly n times
{n,m}       = Between n and m times
[abc]       = a, b, or c
[^abc]      = NOT a, b, or c
^           = Start of line
$           = End of line
(...)       = Capture group
|           = OR
```

---

## Summary

| Step | Action                       | Code                           |
| ---- | ---------------------------- | ------------------------------ |
| 1    | Identify pattern in document | Visual inspection              |
| 2    | Write regex pattern          | `r'pattern...'`                |
| 3    | Create extract function      | `extract_something()`          |
| 4    | Add to extract_all()         | Call new function              |
| 5    | Update endpoint (optional)   | Add `doc_type` parameter       |
| 6    | Test                         | Send request with new doc_type |

**Key Insight:**

- Mỗi document type → mỗi set patterns
- Patterns độc lập → có thể test riêng
- `doc_type` parameter → switch logic
- Dễ mở rộng để support nhiều loại documents
