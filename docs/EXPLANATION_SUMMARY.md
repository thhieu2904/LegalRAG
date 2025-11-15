# METADATA EXTRACTION - TỔNG KẾT

## 📚 Bạn Hỏi Gì?

> "mình thấy bạn đã pass test nhưng mình chưa hiểu config lắm nha, kiểu như làm sao nó extract được code và biết nó thuộc trường nào trong dữ liệu, mỗi một bộ luật lại có cấu trúc khác biệt nhau xíu code ở đoạn nào là logic check phần đó"

## ✅ Câu Trả Lời

Mình vừa tạo 5 files giải thích chi tiết:

### 1. 📖 **EXTRACTION_EXPLAINED.md** (Đọc Trước Tiên)

- Simple, visual explanation
- Cách patterns hoạt động từng bước
- Regex syntax cơ bản
- 👉 **Start here if confused**

### 2. 📋 **QUICK_REFERENCE.md** (Cheat Sheet)

- Quick lookup table
- Code locations
- How to test
- Common issues

### 3. 🔬 **METADATA_EXTRACTION_LOGIC.md** (Chi Tiết)

- In-depth explanation của từng pattern
- Data flow diagram
- Extract all() function details

### 4. 🎯 **METADATA_EXTRACTION_VISUAL.md** (Visual Examples)

- Step-by-step pattern matching
- Real text examples
- Show exactly what regex finds

### 5. 🛠️ **CUSTOM_PATTERNS_GUIDE.md** (Extend)

- How to add patterns for new document types
- Example: Contract extraction
- Regex cheat sheet

### 6. 🧪 **demo_patterns.py** (Interactive Demo)

```bash
python demo_patterns.py
# Shows all patterns working
# Interactive tester included
```

---

## 🎬 TÓM TẮT NGẮN GỌN

### The Core Logic (5 phút để hiểu)

```
1. PDF uploaded to Admin-Service
   ↓
2. Admin calls Storage: "Extract text from PDF"
   ↓
3. Get raw text from PDF
   ↓
4. Run LegalMetadataExtractor.extract_all(text)
   ├─ For each pattern type:
   │  ├─ DOCUMENT_CODE_PATTERNS: Find like "68/2018/NĐ-CP"
   │  ├─ DATE_PATTERNS: Find like "01/7/2025"
   │  ├─ ORGANIZATION_PATTERNS: Find like "Bộ Tư Pháp"
   │  └─ SECTION_PATTERNS: Find like "Điều 32"
   ├─ Each pattern searches text using regex
   ├─ Returns what was found for each field
   └─ Calculates confidence (% fields found)
   ↓
5. Return metadata + text + file info
```

### Pattern Example (How It Works)

**Pattern:** `r'(Điều\s+\d+)'` (Find "Điều" + number)

**Text:**

```
Chương I. Nguyên tắc chung
Điều 1. Mục đích
Mục 1.1. Định nghĩa
Điều 2. Phạm vi
Điều 32. Quyền và nghĩa vụ
```

**What Regex Finds:**

```
Điều 1   ← MATCH (Điều + 1)
Điều 2   ← MATCH (Điều + 2)
Điều 32  ← MATCH (Điều + 32)
```

**Result:**

```python
["Điều 1", "Điều 2", "Điều 32"]
```

---

## 🔍 FOUR TYPES OF METADATA

| Field             | Pattern                          | Finds        | Example       |
| ----------------- | -------------------------------- | ------------ | ------------- |
| **Document Code** | Multiple patterns                | Law code     | 68/2018/NĐ-CP |
| **Dates**         | 2 formats                        | All dates    | 01/7/2025     |
| **Organizations** | 4 types (Bộ, Sở, Cục, Văn phòng) | Gov agencies | Bộ Tư Pháp    |
| **Sections**      | 3 types (Điều, Mục, Chương)      | Structure    | Điều 32       |

---

## 💻 CODE LOCATION

**File:** `admin-service/src/main.py`

**Key Parts:**

```python
# Lines 63-155: LegalMetadataExtractor class
class LegalMetadataExtractor:

    # Pattern definitions (lines 67-80)
    DOCUMENT_CODE_PATTERNS = [...]
    DATE_PATTERNS = [...]
    ORGANIZATION_PATTERNS = [...]
    SECTION_PATTERNS = [...]

    # Extract functions (lines 82-122)
    @staticmethod
    def extract_document_code(text: str) -> Optional[str]
    @staticmethod
    def extract_dates(text: str) -> Optional[List[str]]
    @staticmethod
    def extract_organizations(text: str) -> Optional[List[str]]
    @staticmethod
    def extract_sections(text: str) -> Optional[List[str]]

    # Main function (lines 124-155)
    @staticmethod
    def extract_all(text: str, pages: int = 0) -> Dict[str, Any]:
        # Calls all 4 extract functions above
        # Calculates confidence score
        # Returns complete metadata dict

# Lines 200-290: Endpoint that uses extract_all()
@app.post("/admin/process-document")
async def process_document(file: UploadFile, document_id: str = "doc-001"):
    # STEP 3 (line 258):
    metadata_dict = LegalMetadataExtractor.extract_all(text, pages=pages)
```

---

## 🧪 CURRENT TEST RESULT

**PDF:** "Thủ tục xác định cơ quan giải quyết bồi thường.pdf"

**Extracted:**

```json
{
  "document_code": "QT 0 1/",
  "dates": ["01/7/2025", "12/6/2025"],
  "organizations": ["Bộ Tư", "Bộ trưởng", "Văn phòng UBND", "Sở Tư"],
  "sections": ["Điều 32", "Điều 41", "Điều 33"],
  "extraction_confidence": 0.75
}
```

**Explanation:**

- 3 out of 4 fields found (dates, orgs, sections)
- 1 field NOT found (document_code is null)
- So confidence = 3/4 = 75%

---

## ❓ FAQ

### Q: Why some fields are null?

**A:** Not all documents have all 4 types. A contract might not have "Điều X", so sections will be null. That's OK!

### Q: How do patterns know what field they belong to?

**A:** By their class variable name:

- `extract_document_code()` → Returns document_code
- `extract_dates()` → Returns dates
- `extract_organizations()` → Returns organizations
- `extract_sections()` → Returns sections

### Q: Can I add patterns for new documents?

**A:** YES! See CUSTOM_PATTERNS_GUIDE.md. Example:

```python
CONTRACT_PATTERNS = {
    "party_a": r'Bên\s+A\s*:\s*([^(\n]+)',
    "party_b": r'Bên\s+B\s*:\s*([^(\n]+)',
}
```

### Q: What if pattern doesn't match?

**A:** Test it:

```python
import re
pattern = r'(\d+/\d{4}/NĐ-CP)'
text = "Nghị định 68/2018/NĐ-CP"
matches = re.findall(pattern, text)
print(matches)  # ['68/2018/NĐ-CP'] if works
```

### Q: Different document types have different structures?

**A:** Exactly! That's why:

1. Current patterns work for legal documents
2. Need different patterns for contracts, forms, etc.
3. Solution: Add `doc_type` parameter to endpoint (see guide)

---

## 🚀 WHAT YOU LEARNED

✅ How patterns work (regex rules)
✅ How LegalMetadataExtractor processes text
✅ Where the code is located
✅ How to test patterns
✅ How to extend for new document types
✅ What confidence score means
✅ How each field gets its value

---

## 📖 NEXT STEPS (If Interested)

1. **Try the demo:**

   ```bash
   python demo_patterns.py
   ```

2. **Add a custom pattern:**

   - Edit `ORGANIZATION_PATTERNS`
   - Test with new organization

3. **Support new document type:**

   - Add `CONTRACT_PATTERNS` (see guide)
   - Implement `extract_contract_parties()`
   - Update endpoint with `doc_type` parameter

4. **Improve extraction:**
   - Tune existing patterns
   - Test with real documents
   - Adjust confidence calculation

---

## 🎯 KEY INSIGHT

> **Patterns are just text-finding rules. Regex is the language to express those rules.**

Each pattern says: "Find text that looks like this: [PATTERN]"

That's it! Simple, powerful, and extensible.

---

## 📞 HELP

**Confused about:**

- Regex syntax? → See QUICK_REFERENCE.md "Regex Syntax"
- How endpoint works? → See EXTRACTION_EXPLAINED.md
- How to extend? → See CUSTOM_PATTERNS_GUIDE.md
- Visual examples? → See METADATA_EXTRACTION_VISUAL.md

**All files in:** `docs/` folder
