"""
Phân tích 2 vấn đề chính từ log và output của user
"""

## VẤN ĐỀ 1: Text generation hiển thị sai trên frontend

### Nguyên nhân phân tích:

Từ output của user, ta thấy response text được hiển thị như sau:

```
Theo quy định tại Điều 2 Thông tư 85/2019/TT-BTC, giấy tờ chứng minh việc nhập cảnh hợp pháp vào Việt Nam là một trong các giấy tờ sau:
- Hộ chiếu hoặc giấy tờ có giá trị thay hộ chiếu (sau đây gọi chung là hộ chiếu);
- Giấy thông hành hoặc giấy tờ khác có giá trị đi lại quốc tế.
Trường hợp cha mẹ lựa chọn quốc tịch nước ngoài cho con, thì văn bản thỏa thuận phải có xác nhận của cơ quan nhà nước có thẩm quyền của nước mà người đó là công dân.
```

**VẤN ĐỀ:** Text này trả lời câu hỏi chung về giấy tờ nhập cảnh nhưng KHÔNG trả lời đúng câu hỏi cụ thể: "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"

### Nguyên nhân gốc rễ:

1. **LLM Model (PhoGPT) có thể bị giới hạn:**

   - Context window: `n_ctx_per_seq (5120) < n_ctx_train (8192)` - model không sử dụng hết capacity
   - Model size: PhoGPT-4B-Chat-Q4_K_M.gguf (quantized) có thể bị mất thông tin do quantization

2. **Prompt engineering issue:**

   - Context có thể quá dài (6954 chars) làm model bị confused
   - Câu hỏi gốc có thể bị "buried" trong context dài
   - Model có thể chọn thông tin general thay vì specific

3. **Context expansion quá aggressive:**
   - Log cho thấy: "Loading TOÀN BỘ DOCUMENT để đảm bảo ngữ cảnh pháp luật đầy đủ"
   - Full document (3619 chars) có thể chứa nhiều thông tin không liên quan

## VẤN ĐỀ 2: Backend báo "LOW RANK" nhiều

### Phân tích từ log:

```
2025-09-11 22:10:57,579 - app.services.reranker - WARNING - ⚠️  LOW RERANK SCORE (0.1666) - Conservative strategy may be triggered
2025-09-11 22:10:59,115 - app.services.reranker - WARNING - ⚠️  LOW RERANK SCORE (0.1666) - Conservative strategy may be triggered
```

### Nguyên nhân chi tiết:

1. **Reranker model issue:**

   - Model: AITeamVN/Vietnamese_Reranker
   - Score chỉ 0.1666 (rất thấp) cho document đúng nhất
   - Có thể model này không phù hợp với domain legal

2. **Query-Document mismatch:**

   - Query: "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"
   - Document được chọn đúng nhưng reranker score thấp
   - Có thể do embedding model và reranker model không sync

3. **Context length issue:**

   - Mỗi doc có 2000 chars khi rerank
   - Có thể quá dài hoặc chứa noise

4. **Router vs Reranker conflict:**
   - Router confidence: 0.8481 (HIGH)
   - Reranker score: 0.1666 (LOW)
   - Combined confidence: 0.4392
   - Cho thấy 2 model không đồng thuận

### Tác động:

- System phải chạy rerank 2 lần (fallback strategy)
- Performance giảm (1.64s + 1.53s cho rerank)
- Model selection không tối ưu

## KHUYẾN NGHỊ GIẢI PHÁP:

### Fix Frontend Text Generation:

1. Tune prompt template để focus hơn vào câu hỏi chính
2. Limit context length hoặc prioritize relevant chunks
3. Test với LLM model lớn hơn hoặc unquantized

### Fix Backend Low Rank:

1. Retrain hoặc fine-tune reranker model cho legal domain
2. Adjust reranker threshold (có thể 0.1666 là acceptable cho legal text)
3. Improve query preprocessing
4. Consider using ensemble reranking
