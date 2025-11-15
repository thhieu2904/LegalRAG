# QUICK REFERENCE - Metadata Extraction

## 🎯 Cách Hoạt Động (Simple Version)

```
1. User upload PDF
   ↓
2. Admin-Service receive
   ├─ Step 1: Upload to Storage (get file_path)
   ├─ Step 2: Extract text from Storage (get raw text)
   └─ Step 3: Extract metadata using patterns
   ↓
3. Return response with all metadata
```

---

## 🔎 Patterns - What Chúng Tìm

### Document Code (Mã Luật)

```
Patterns tìm kiếm:
- 68/2018/NĐ-CP          ← Nghị định
- 1205/2020/QĐ-TTg       ← Quyết định
- 45/2019/TT-BCA         ← Thông tư
- QT 01/BTNN             ← Quy trình

Regex: r'(\d+/\d{4}/NĐ-CP)' hoặc r'(QT\s*0?\d+/)'
```

### Dates (Ngày Tháng)

```
Patterns tìm kiếm:
- 01/7/2025              ← Format DD/MM/YYYY
- 15 tháng 3 năm 2024    ← Format chữ

Regex: r'(\d{1,2}/\d{1,2}/\d{4})'
```

### Organizations (Bộ, Sở, Cục)

```
Patterns tìm kiếm:
- Bộ Tư pháp
- Sở Lao động
- Cục Thuế
- Văn phòng UBND

Regex: r'(Bộ|Sở|Cục|Văn phòng)\s+\w+'
```

### Sections (Điều, Mục, Chương)

```
Patterns tìm kiếm:
- Điều 1, Điều 32
- Mục 1.1, Mục 2.3
- Chương I, Chương II

Regex: r'(Điều|Mục|Chương)\s+...'
```

---

## 📍 Code Location

**Main file:** `admin-service/src/main.py`

**Lines 63-155:** LegalMetadataExtractor class

- Lines 67-80: Pattern definitions
- Lines 82-98: extract_document_code()
- Lines 100-106: extract_dates()
- Lines 108-114: extract_organizations()
- Lines 116-122: extract_sections()
- Lines 124-155: extract_all()

**Lines 200-290:** Main endpoint

- POST /admin/process-document
- Calls extract_all() at line 258

---

## 🧪 How to Test

### Option 1: Use Docker (Running Now)

```bash
# Services are running
docker ps | grep legalrag

# Test endpoint
curl -X POST "http://localhost:8002/admin/process-document" \
  -F "file=@your_file.pdf"
```

### Option 2: Use Test Script

```bash
python test_admin_service.py
```

### Option 3: Use Interactive Demo

```bash
python demo_patterns.py
```

### Option 4: Test Regex Online

- Go to regex101.com
- Paste pattern: `r'(\d+/\d{4}/NĐ-CP)'`
- Paste text: `Nghị định 68/2018/NĐ-CP`
- See match highlight

---

## 🛠️ How to Add New Pattern

### For Legal Documents (Add to DOCUMENT_CODE_PATTERNS):

**Step 1:** Identify pattern in your document

```
Document: "Quyết định số 456/2022/QĐ-UBND"
Pattern: "Số + / + Year + / + QĐ-..."
```

**Step 2:** Write regex

```python
r'(\d+/\d{4}/QĐ-UBND)'
```

**Step 3:** Add to class

```python
DOCUMENT_CODE_PATTERNS = [
    r'(\d+/\d{4}/NĐ-CP)',
    r'(\d+/\d{4}/QĐ-)',
    r'(\d+/\d{4}/QĐ-UBND)',  # ← NEW
    r'(\d+/\d{4}/TT-)',
    r'(QT\s*0?\d+/)',
]
```

**Step 4:** Test

```python
text = "Quyết định số 456/2022/QĐ-UBND"
import re
matches = re.findall(r'(\d+/\d{4}/QĐ-UBND)', text)
print(matches)  # ['456/2022/QĐ-UBND']
```

---

## 🎓 Regex Quick Syntax

```
\d        = Digit (0-9)
\w        = Word (a-z, A-Z, 0-9, _)
\s        = Space (space, tab)
.         = Any character
+         = 1 or more
*         = 0 or more
?         = optional (0 or 1)
{n}       = exactly n
{n,m}     = between n and m
[abc]     = a OR b OR c
[^abc]    = NOT (a OR b OR c)
(...)     = capture / group
```

---

## 📊 Test Data

**PDF File Used:**

- Name: "Thủ tục xác định cơ quan giải quyết bồi thường.pdf"
- Size: 355 KB
- Pages: 7
- Characters: 11,140

**Extracted Results:**

- Document Code: `QT 0 1/`
- Dates: `["01/7/2025", "12/6/2025"]`
- Organizations: `["Bộ Tư", "Sở Lao", ...]` (8 organizations)
- Sections: `["Điều 32", "Điều 41", ...]` (10 sections)
- Confidence: 75% (3 out of 4 fields extracted)

---

## 🔗 Related Documentation

- `METADATA_EXTRACTION_LOGIC.md` - Detailed explanation
- `METADATA_EXTRACTION_VISUAL.md` - Visual examples
- `CUSTOM_PATTERNS_GUIDE.md` - How to add patterns
- `EXTRACTION_EXPLAINED.md` - Complete overview

---

## 🚀 Current Architecture

```
┌─────────────────────────────────────────┐
│         User / API Client               │
└──────────────────┬──────────────────────┘
                   │
                   ↓ POST /admin/process-document
         ┌─────────────────────────┐
         │   Admin-Service (8002)  │
         │                         │
         │ 3-Step Orchestration:   │
         │ 1. Upload to Storage    │
         │ 2. Extract Text         │
         │ 3. Extract Metadata     │
         └──────────┬──────────────┘
                    │
                ┌───┴────┐
                ↓        ↓
        ┌──────────────┐ ┌──────────────────┐
        │   Storage    │ │ LegalMetadata    │
        │   Service    │ │ Extractor        │
        │   (8001)     │ │                  │
        └──────────────┘ │ - Doc Code       │
                         │ - Dates          │
                         │ - Organizations  │
                         │ - Sections       │
                         └──────────────────┘
                                 │
                                 ↓
        ┌─────────────────────────────────────────┐
        │  Response: Metadata + Text Stats        │
        └─────────────────────────────────────────┘
```

---

## ✅ Checklist - How to Verify It's Working

- [ ] All 4 services running: `docker ps` shows minio, postgres, storage, admin
- [ ] Health check passes: `curl http://localhost:8002/health`
- [ ] Storage health: `curl http://localhost:8001/health`
- [ ] Endpoint accessible: `curl http://localhost:8002/docs` (Swagger UI)
- [ ] Test with PDF: `python test_admin_service.py`
- [ ] Get response 200 with metadata
- [ ] All 4 extraction fields populated (or at least some)
- [ ] Confidence score > 0

---

## 🐛 Troubleshooting

### Pattern Not Matching

```python
# Test pattern
import re
pattern = r'(\d+/\d{4}/NĐ-CP)'
text = "Theo Nghị định 68/2018/NĐ-CP"
matches = re.findall(pattern, text)
if not matches:
    # Debug:
    print("Pattern:", pattern)
    print("Text:", text)
    # Check: Is pattern correct? Is text correct format?
```

### Confidence Score Low

- Low score means not all 4 fields extracted
- This is NORMAL! Not all documents have all 4 types
- Check logs: which fields were found?

### Endpoint Returns Error

- Check Storage is running: `docker logs legalrag-storage`
- Check PDF file is valid: try with test PDF
- Check file size < 50MB

---

## 💡 Tips

1. **Test patterns online:** regex101.com
2. **Use raw strings:** `r'pattern'` not `'pattern'`
3. **Test incrementally:** Add one pattern, test, then next
4. **Check logs:** `docker logs legalrag-admin`
5. **Start simple:** Basic pattern first, then complex

---

## 📞 Support

**Files to check:**

- `admin-service/src/main.py` - Main code
- `admin-service/requirements.txt` - Dependencies
- `docker-compose.yml` - Container config
- Docs in `docs/` folder

**Test script:**

- `test_admin_service.py`
- `demo_patterns.py`

**Logs:**

- `docker logs legalrag-admin`
- `docker logs legalrag-storage`
