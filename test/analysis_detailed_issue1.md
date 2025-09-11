"""
PHÂN TÍCH CHI TIẾT VẤN ĐỀ 1: LLM không sử dụng đúng nội dung JSON
"""

## HIỆN TRẠNG VÀ VẤN ĐỀ

### Câu hỏi user: "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"

### LLM trả lời hiện tại (SAI):

```
Theo quy định tại Điều 2 Thông tư 85/2019/TT-BTC, giấy tờ chứng minh việc nhập cảnh hợp pháp vào Việt Nam là một trong các giấy tờ sau:
- Hộ chiếu hoặc giấy tờ có giá trị thay hộ chiếu (sau đây gọi chung là hộ chiếu);
- Giấy thông hành hoặc giấy tờ khác có giá trị đi lại quốc tế.
Trường hợp cha mẹ lựa chọn quốc tịch nước ngoài cho con, thì văn bản thỏa thuận phải có xác nhận của cơ quan nhà nước có thẩm quyền của nước mà người đó là công dân.
```

### LLM nên trả lời (ĐÚNG) dựa trên JSON content_chunks[0]:

```
Để đăng ký khai sinh có yếu tố nước ngoài, bạn cần chuẩn bị các giấy tờ sau:

**Giấy tờ chính:**
1. Tờ khai đăng ký khai sinh theo mẫu
2. Giấy chứng sinh hoặc giấy tờ khác do cơ quan có thẩm quyền nước ngoài cấp (đối với trường hợp trẻ em sinh ra tại nước ngoài)
3. Văn bản thỏa thuận của cha, mẹ về việc lựa chọn quốc tịch cho con (trường hợp cha hoặc mẹ hoặc cả cha, mẹ là người nước ngoài)
4. Giấy tờ chứng minh việc trẻ em nhập cảnh hợp pháp vào Việt Nam (hộ chiếu, giấy tờ có giá trị đi lại quốc tế có dấu xác nhận nhập cảnh)
5. Văn bản xác nhận của cơ quan công an có thẩm quyền về việc trẻ em đang cư trú tại Việt Nam

**Giấy tờ khác:**
6. Hộ chiếu/Thẻ căn cước công dân của người yêu cầu
7. Giấy tờ có giá trị chứng minh thông tin về cư trú (nếu cần)
8. Văn bản ủy quyền (được chứng thực) nếu có ủy quyền

📋 Xem biểu mẫu đính kèm bên dưới.
```

## NGUYÊN NHÂN GỐC RỄ

### 1. LLM sử dụng "knowledge leakage" thay vì document content

- LLM dựa vào pre-trained knowledge về "Thông tư 85/2019/TT-BTC"
- Không focus vào nội dung cụ thể trong JSON document
- Đây là vấn đề **PROMPT ENGINEERING** chứ không phải context length

### 2. Prompt structure không force LLM sử dụng provided context

- Context có đầy đủ thông tin đúng nhưng LLM không ưu tiên nó
- Cần prompt template force LLM "ONLY use provided context"

## PHÂN TÍCH "RÚT NGẮN CONTEXT"

### Context hiện tại: 6954 chars

- **Prompt template**: ~1000 chars
- **Document content**: ~3619 chars (từ JSON)
- **Instruction**: ~1000 chars
- **Query**: ~65 chars
- **Reserve for generation**: ~1500 chars

### GPU Context limit: 5120 tokens

- 6954 chars ≈ 1390-1740 tokens (tùy tokenizer)
- **VẪN CÒN DÀNH CHỖ** cho generation (3380-3730 tokens)
- **KHÔNG CẦN rút ngắn context**

### "Rút ngắn context" có nghĩa là:

1. **Semantic filtering**: Chỉ giữ chunks relevant với query
2. **Priority ranking**: Đưa most relevant chunks lên đầu
3. **Smart truncation**: Cắt bớt boilerplate, giữ core content

### CÓ NÊN RÚT NGẮN KHÔNG?

#### ✅ KHÔNG NÊN rút ngắn vì:

1. **Legal context requires completeness**: Văn bản pháp lý cần ngữ cảnh đầy đủ
2. **Cross-reference importance**: Các điều khoản liên quan đến nhau
3. **Still within limit**: 6954 chars vẫn trong giới hạn GPU
4. **Risk of missing info**: Rút ngắn có thể mất thông tin quan trọng

#### ❌ Chỉ rút ngắn nếu:

- Context > 4500 chars (để dành 1500 cho generation)
- Query rất specific và chỉ cần 1-2 chunks
- Performance issue rõ ràng

## GIẢI PHÁP ĐỀ XUẤT

### 1. PROMPT ENGINEERING (Ưu tiên cao)

```python
prompt_template = f"""
BẠN LÀ CHUYÊN GIA TƯ VẤN PHÁP LUẬT.

**QUY TẮC NGHIÊM NGẶT:**
1. CHỈ sử dụng thông tin từ DOCUMENT được cung cấp bên dưới
2. KHÔNG sử dụng kiến thức bên ngoài về pháp luật
3. Trả lời CHÍNH XÁC dựa trên nội dung document
4. Nếu document không có thông tin, hãy nói "Không có thông tin trong tài liệu"

**DOCUMENT CONTEXT:**
{document_content}

**CÂU HỎI:** {query}

**TRẢ LỜI dựa trên DOCUMENT trên:**
"""
```

### 2. CONTEXT PRIORITIZATION (Không rút ngắn toàn bộ)

- Đưa most relevant chunks lên đầu
- Highlight key information
- Giữ nguyên full context

### 3. STRUCTURED RESPONSE TEMPLATE

- Force LLM format output theo structure cụ thể
- Ensure coverage of all required points

## KẾT LUẬN

**KHÔNG CẦN rút ngắn context** vì:

- Context 6954 chars vẫn OK với GPU limit 5120 tokens
- Legal content cần completeness
- Vấn đề chính là **prompt engineering** chứ không phải context length

**FOCUS VÀO:**

1. ✅ Cải thiện prompt template (force use document content)
2. ✅ Context prioritization (relevant chunks first)
3. ✅ Response structure (guided format)
4. ❌ KHÔNG rút ngắn context length
