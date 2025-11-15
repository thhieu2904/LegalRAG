# Visual Example - Cách Patterns Làm Việc

## Example 1: Document Code Pattern

### Text Input:

```
SỞ TƯ PHÁP  QUY TRÌNH
Thủ tục xác định cơ quan giải quyết bồi thường Mã hiệu: QT 0 1/BTNN
```

### Pattern Matching Process:

```
Pattern 1: r'(\d+/\d{4}/NĐ-CP)'
├─ Looking for: số/4chữsố/NĐ-CP
├─ Text scan: "QT 0 1/BTNN" → NO MATCH ✗
│
Pattern 2: r'(\d+/\d{4}/QĐ-)'
├─ Looking for: số/4chữsố/QĐ-
├─ Text scan: "QT 0 1/BTNN" → NO MATCH ✗
│
Pattern 3: r'(\d+/\d{4}/TT-)'
├─ Looking for: số/4chữsố/TT-
├─ Text scan: "QT 0 1/BTNN" → NO MATCH ✗
│
Pattern 4: r'(QT\s*0?\d+/)'  ← THIS ONE!
├─ Looking for: "QT" + optional whitespace + optional 0 + số + "/"
├─ Text scan: "QT 0 1/"
│   - QT ✓
│   - \s* (space) ✓
│   - 0? (optional 0) ✓
│   - \d+ (1) ✓
│   - / ✓
├─ MATCH! ✓
│
└─ Result: "QT 0 1/"
```

### Code Execution:

```python
text = "...Mã hiệu: QT 0 1/BTNN..."
for pattern in DOCUMENT_CODE_PATTERNS:
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]  # ← Trả về "QT 0 1/"

# Output: "QT 0 1/"
```

---

## Example 2: Date Pattern

### Text Input:

```
Ngày ban hành: 01/7/2025
...
Hôm nay là 15 tháng 3 năm 2024
```

### Pattern Matching Process:

```
Date 1: "01/7/2025"
├─ Pattern 1: r'(\d{1,2}/\d{1,2}/\d{4})'
│  ├─ \d{1,2}: "01" (2 digits) ✓
│  ├─ /: "/" ✓
│  ├─ \d{1,2}: "7" (1 digit) ✓
│  ├─ /: "/" ✓
│  ├─ \d{4}: "2025" (4 digits) ✓
│  └─ MATCH: "01/7/2025" ✓
│
Date 2: "15 tháng 3 năm 2024"
├─ Pattern 1: r'(\d{1,2}/\d{1,2}/\d{4})'
│  └─ NO MATCH (không có dấu /) ✗
│
├─ Pattern 2: r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})'
│  ├─ \d{1,2}: "15" ✓
│  ├─ \s+: " " (space) ✓
│  ├─ tháng: "tháng" ✓
│  ├─ \s+: " " ✓
│  ├─ \d{1,2}: "3" ✓
│  ├─ \s+: " " ✓
│  ├─ năm: "năm" ✓
│  ├─ \s+: " " ✓
│  ├─ \d{4}: "2024" ✓
│  └─ MATCH: "15 tháng 3 năm 2024" ✓
│
Result: ["01/7/2025", "15 tháng 3 năm 2024"]
```

### Code Execution:

```python
text = "Ngày ban hành: 01/7/2025\nHôm nay là 15 tháng 3 năm 2024"
dates = []
for pattern in DATE_PATTERNS:
    matches = re.findall(pattern, text)
    dates.extend(matches)
# dates = ["01/7/2025", "15 tháng 3 năm 2024"]

return list(set(dates))  # Remove duplicates
# Output: ["01/7/2025", "15 tháng 3 năm 2024"]
```

---

## Example 3: Organization Pattern

### Text Input:

```
SỞ TƯ PHÁP QUỐC
Bộ Tư pháp công bố...
Sở Lao động tỉnh A...
Cục Thuế trung ương...
Văn phòng UBND thành phố...
Bộ phận quản lý...
```

### Pattern Matching Process:

```
Organization 1: "SỞ TƯ PHÁP"
├─ Pattern 1: r'(Bộ\s+\w+)'
│  └─ NO MATCH ✗ (doesn't start with "Bộ")
├─ Pattern 2: r'(Sở\s+\w+)'
│  ├─ Sở: "Sở" (but uppercase "SỞ")
│  └─ Case sensitive → NO MATCH ✗
├─ Pattern 3: r'(Cục\s+\w+)'
│  └─ NO MATCH ✗
└─ Pattern 4: r'(Văn phòng\s+\w+)'
   └─ NO MATCH ✗

Note: Regex default case-sensitive!
"SỞ" ≠ "Sở" (uppercase vs lowercase)

Organization 2: "Bộ Tư pháp"
├─ Pattern 1: r'(Bộ\s+\w+)'
│  ├─ Bộ: "Bộ" ✓
│  ├─ \s+: " " ✓
│  ├─ \w+: "Tư" (word characters) ✓
│  └─ MATCH: "Bộ Tư" ✓

Organization 3: "Sở Lao động"
├─ Pattern 2: r'(Sở\s+\w+)'
│  ├─ Sở: "Sở" ✓
│  ├─ \s+: " " ✓
│  ├─ \w+: "Lao" ✓
│  └─ MATCH: "Sở Lao" ✓

Organization 4: "Cục Thuế"
├─ Pattern 3: r'(Cục\s+\w+)'
│  ├─ Cục: "Cục" ✓
│  ├─ \s+: " " ✓
│  ├─ \w+: "Thuế" ✓
│  └─ MATCH: "Cục Thuế" ✓

Organization 5: "Văn phòng UBND"
├─ Pattern 4: r'(Văn phòng\s+\w+)'
│  ├─ Văn phòng: "Văn phòng" ✓
│  ├─ \s+: " " ✓
│  ├─ \w+: "UBND" ✓
│  └─ MATCH: "Văn phòng UBND" ✓

Organization 6: "Bộ phận"
├─ Pattern 1: r'(Bộ\s+\w+)'
│  ├─ Bộ: "Bộ" ✓
│  ├─ \s+: " " ✓
│  ├─ \w+: "phận" ✓
│  └─ MATCH: "Bộ phận" ✓

Result: ["Bộ Tư", "Sở Lao", "Cục Thuế", "Văn phòng UBND", "Bộ phận"]
```

### Code Execution:

```python
text = "SỞ TƯ PHÁP...\nBộ Tư pháp...\nSở Lao động...\nCục Thuế...\nVăn phòng UBND...\nBộ phận..."
orgs = []
for pattern in ORGANIZATION_PATTERNS:
    matches = re.findall(pattern, text)
    orgs.extend(matches)
# orgs = ["Bộ Tư", "Sở Lao", "Cục Thuế", "Văn phòng UBND", "Bộ phận"]

return list(set(orgs))  # Remove duplicates
# Output: ["Bộ Tư", "Sở Lao", "Cục Thuế", "Văn phòng UBND", "Bộ phận"]
```

---

## Example 4: Section Pattern

### Text Input:

```
Chương I - Nguyên tắc chung
Điều 1 - Mục đích
Mục 1.1 - Định nghĩa
Điều 2 - Phạm vi
Chương II - Bộ máy tổ chức
Điều 32 - Quyền và nghĩa vụ
Mục 2.1 - Trách nhiệm
Điều 41 - Xử phạt
```

### Pattern Matching Process:

```
Section 1: "Chương I"
├─ Pattern 1: r'(Điều\s+\d+)'
│  └─ NO MATCH ✗ (doesn't start with "Điều")
├─ Pattern 2: r'(Mục\s+\d+\.\d+)'
│  └─ NO MATCH ✗ (doesn't start with "Mục")
├─ Pattern 3: r'(Chương\s+[IVX]+)'
│  ├─ Chương: "Chương" ✓
│  ├─ \s+: " " ✓
│  ├─ [IVX]+: "I" (Roman numeral) ✓
│  └─ MATCH: "Chương I" ✓

Section 2: "Điều 1"
├─ Pattern 1: r'(Điều\s+\d+)'
│  ├─ Điều: "Điều" ✓
│  ├─ \s+: " " ✓
│  ├─ \d+: "1" ✓
│  └─ MATCH: "Điều 1" ✓

Section 3: "Mục 1.1"
├─ Pattern 2: r'(Mục\s+\d+\.\d+)'
│  ├─ Mục: "Mục" ✓
│  ├─ \s+: " " ✓
│  ├─ \d+: "1" ✓
│  ├─ \.: "." ✓
│  ├─ \d+: "1" ✓
│  └─ MATCH: "Mục 1.1" ✓

Section 4: "Chương II"
├─ Pattern 3: r'(Chương\s+[IVX]+)'
│  ├─ Chương: "Chương" ✓
│  ├─ \s+: " " ✓
│  ├─ [IVX]+: "II" (Roman numerals) ✓
│  └─ MATCH: "Chương II" ✓

Section 5: "Điều 32"
├─ Pattern 1: r'(Điều\s+\d+)'
│  ├─ Điều: "Điều" ✓
│  ├─ \s+: " " ✓
│  ├─ \d+: "32" ✓
│  └─ MATCH: "Điều 32" ✓

Section 6: "Mục 2.1"
├─ Pattern 2: r'(Mục\s+\d+\.\d+)'
│  ├─ Mục: "Mục" ✓
│  ├─ \s+: " " ✓
│  ├─ \d+: "2" ✓
│  ├─ \.: "." ✓
│  ├─ \d+: "1" ✓
│  └─ MATCH: "Mục 2.1" ✓

Section 7: "Điều 41"
├─ Pattern 1: r'(Điều\s+\d+)'
│  ├─ Điều: "Điều" ✓
│  ├─ \s+: " " ✓
│  ├─ \d+: "41" ✓
│  └─ MATCH: "Điều 41" ✓

Result: ["Chương I", "Điều 1", "Mục 1.1", "Chương II", "Điều 32", "Mục 2.1", "Điều 41"]
```

### Code Execution:

```python
text = "Chương I...\nĐiều 1...\nMục 1.1...\nĐiều 2...\nChương II...\nĐiều 32...\nMục 2.1...\nĐiều 41..."
sections = []
for pattern in SECTION_PATTERNS:
    matches = re.findall(pattern, text)
    sections.extend(matches)
# sections = ["Chương I", "Điều 1", "Mục 1.1", "Chương II", "Điều 32", "Mục 2.1", "Điều 41"]

return list(set(sections))  # Remove duplicates
# Output: ["Chương I", "Điều 1", "Mục 1.1", "Chương II", "Điều 32", "Mục 2.1", "Điều 41"]
```

---

## Summary

| Pattern Type      | Works By                                        | Example    |
| ----------------- | ----------------------------------------------- | ---------- |
| **Document Code** | Tìm format cụ thể (XX/YYYY/ZZZ)                 | QT 0 1/    |
| **Dates**         | Tìm kiểu DD/MM/YYYY hoặc "DD tháng MM năm YYYY" | 01/7/2025  |
| **Organizations** | Tìm từ khóa (Bộ, Sở, Cục, Văn phòng) + từ sau   | Bộ Tư Pháp |
| **Sections**      | Tìm từ khóa (Điều, Mục, Chương) + số            | Điều 32    |

**Key Concept:**

- Mỗi pattern là một **find and replace rule** cơ bản
- Regex `\d` = digit (0-9)
- Regex `\w` = word character (a-z, A-Z, 0-9, \_)
- Regex `\s` = whitespace (space, tab)
- Regex `+` = 1 hoặc nhiều lần
- Regex `*` = 0 hoặc nhiều lần
- Regex `?` = optional (0 hoặc 1 lần)
