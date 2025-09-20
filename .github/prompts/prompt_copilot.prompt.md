---
description: "Thực hiện kiểm thử và gỡ lỗi theo quy trình ưu tiên script và phân tích log."
mode: "agent"
tools: ["codebase"]
---

## QUY TRÌNH KIỂM THỬ VÀ GỠ LỖI

Bạn đang thực hiện nhiệm vụ kiểm thử. Hãy tuân thủ nghiêm ngặt các bước trong quy trình này.

### Yêu cầu về phương pháp:

1. **Tạo Script Kiểm Thử:**

   - **Ưu tiên hàng đầu:** Viết một script riêng lẻ (Python hoặc Bash) để tái tạo và xác minh lỗi hoặc tính năng.
   - Script phải có thể chạy trực tiếp từ terminal.
   - Kích hoạt môi trường conda đúng
   - **TUYỆT ĐỐI KHÔNG** đề xuất khởi chạy server (ví dụ: `python main.py. `).

2. **Xử lý khi cần Log:**

   - Nếu không thể kiểm thử bằng script và cần xem log, hãy **DỪNG LẠI**.
   - Yêu cầu tôi cung cấp nội dung log liên quan. Không được tự ý truy cập file.

3. **Vị trí File Test:**

   - Nếu cần tạo file test mới, **luôn luôn** tạo chúng trong thư mục `root/test/`.

Hãy bắt đầu thực hiện yêu cầu kiểm thử theo các quy tắc trên.
