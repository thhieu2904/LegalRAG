# Chạy nhanh bộ dev QR + Word

Ngày 05/10/2026: Docker Desktop đang lỗi khởi động. Theo yêu cầu người dùng,
không sửa Docker; lượt kiểm thử mới dùng adapter Python local gọi bộ quét/điền
thật. Xem [FORM_QA_20261005.md](FORM_QA_20261005.md) để biết cách thử hiện tại
và giới hạn của kết quả. Các task Docker dưới đây vẫn dành cho lúc engine chạy được.

## Khởi động bằng VS Code

1. Mở repo `D:\Personal\LegalRAG` bằng VS Code.
2. Bật Docker Desktop ở chế độ **Linux containers**. Cài dependency frontend
   một lần bằng `npm.cmd ci` trong thư mục `frontend` nếu chưa có `node_modules`.
3. Bấm **F1 → Tasks: Run Task → LegalRAG: Start QR + Word dev**.
4. Chờ terminal chuẩn bị in `FORM_DEV_READY`, rồi chờ Vite báo sẵn sàng.
   Task mở frontend và 3 terminal log Query / Form QR / Storage cùng một nhóm.
5. Mở Chrome tại:

   http://localhost:3006/forms/demo/Gi%E1%BA%A5y%20%C4%91%C4%83ng%20k%C3%BD%20khai%20sinh.docx

Đây là `.vscode/tasks.json`, không phải file JavaScript. Không tự chạy khi mở
workspace. Lần đầu build cần tải image nền và dependency; các lần sau dùng cache.
Thay frontend cập nhật qua Vite; thay Python cập nhật qua Uvicorn reload với
source mount chỉ đọc. Đổi dependency cần chạy lại task chuẩn bị để build image.

## Phạm vi bộ dev

Chỉ có frontend và 3 backend thuộc Compose project **legalrag-form-dev**:

| Thành phần | Địa chỉ trên máy | Nội dung chạy |
| --- | --- | --- |
| Frontend | `http://localhost:3006` | UI hiện tại, Vite dev |
| Query | `http://localhost:18002` | Router biểu mẫu hiện tại, không khởi động RAG/DB |
| Form | `http://localhost:18015` | Bộ giải mã QR và render/điền Word thật |
| Kho mẫu dev | `http://localhost:18010` | Một file Word local chỉ đọc, không phải MinIO |

Tất cả cổng chỉ bind `127.0.0.1`, không mở ra LAN/Tailscale. Không khởi động
Vistral, embedding, rerank, PostgreSQL, MinIO hay Admin. Trang chủ RAG và các
trang quản trị không thuộc bộ này; mở thẳng URL biểu mẫu ở trên.

Compose dev dùng Dockerfile hiện có và image tag local riêng. Các entry point
Query/kho mẫu dev nằm riêng; không sửa entry point production. Không sửa `.env`,
`docker-compose.yml`, `prod/docker-compose.yml`, volume hay dữ liệu server.
Thử tải image MinIO không thành công trong lượt kiểm tra này nên kho mẫu dev
dùng adapter local chỉ đọc; đây không phải đổi kiến trúc lưu trữ production.

Mẫu cố định là `thesis/refs/forms/Giấy đăng ký khai sinh.docx`, đối chiếu SHA-256
với cấu hình TypeScript. Có **37 ô**: 4 `scan_...` và 33 `form_...`;
QR cố định vào người yêu cầu, không có chọn vai trò ở mẫu này.
Camera/mic chỉ mở khi bấm nút. Không lưu
hồ sơ: gateway dev chặn `/forms/save`, bản nháp chỉ nằm trong phiên trang.

## Đọc QR, không OCR

- Chọn ảnh mã QR hoặc Camera QR. Mẫu khai sinh đã xác định sẵn 4 vị trí điền
  căn cước của **người yêu cầu**; các ô của cha/mẹ/trẻ nhập tay hoặc giọng nói.
- Camera hiện chụp bằng nút **Chụp & đọc QR**; khung vuông chỉ hướng dẫn căn mã,
  backend nhận toàn bộ khung hình PNG theo độ phân giải video gốc, không cắt theo
  khung hướng dẫn. Chặn bấm chụp lặp khi đang lấy/đọc ảnh; video hiển thị toàn
  khung thay vì cắt mép. Chưa có quét liên tục/tự chụp/tự lấy nét.
- API gửi `scan_mode: "qr"`; thiếu thuộc tính này vẫn mặc định QR để tương thích.
  Yêu cầu `"ocr"` bị từ chối. Chỉ giải mã QR có payload căn cước hợp lệ về cấu trúc,
  không đọc chữ, không nhận barcode khác hay QR URL. Đây không phải xác thực
  căn cước thật/giả hay đối chiếu dữ liệu dân cư.
- QR chỉ điền 4 ô `scan_...` chưa chỉnh. Ô đã nhập hoặc chủ động xóa được
  giữ nguyên; kiểm tra và xác nhận nội dung trước khi tải Word.
- Log quét mới chỉ ghi thành công/thời gian, không ghi ảnh hay nội dung căn cước.

## Kiểm thử và dừng

Khi backend Docker đang chạy, chọn task **LegalRAG: Test form backend + real QR**.
Script chạy 25 ca Python trong Form image và smoke test dùng QR tạo từ dữ liệu
giả, ảnh chỉ có chữ, API QR-only, preview Mammoth, hash và xuất Word trong RAM.
Task này không dùng dữ liệu căn cước thật. Smoke test phiên bản mới chưa chạy
lại qua Docker trong lượt 05/10; kiểm thử QR thật local là phép thử riêng.

Frontend trong thư mục `frontend`: `npm.cmd run test:forms`, `npm.cmd run build`.
Ngày 05/10/2026: **32 ca frontend**, **25 ca Python local**, build và ESLint
phạm vi FormFillPage PASS. Bộ giải mã native đã đọc ảnh người dùng cung cấp
và 4 biến thể trong RAM, không lưu dữ liệu căn cước vào báo cáo.
Xuất Word với dữ liệu giả điền đủ 37/37 ô. Kiểm tra Chrome: không còn chọn vai
trò; một ô nhập; **Xong** cập nhật, **Hủy** giữ nguyên và cảnh báo số ô thiếu.
LibreOffice đã render 2 trang; còn lưu ý tiêu đề Chú thích có thể nằm lẻ cuối
trang sau khi điền. Xem báo cáo QA để phân biệt kiểm thử native và Docker.
**NOT RUN:** camera/mic thật trên UX mới, Microsoft Word, tích hợp Docker mới,
MinIO/DB/RAG production, triển khai server và thao tác Run Task trong UI VS Code.

Để dừng: kết thúc task Frontend/log qua **Tasks: Terminate Task** hoặc Ctrl+C
trong terminal tương ứng, rồi chạy **LegalRAG: Stop form dev backend**.
Task dừng chỉ gọi `stop` trên project dev; không xóa container/volume/dữ liệu.

Có thể chạy riêng bằng PowerShell tại root repo:

```powershell
powershell.exe -NoProfile -File .\scripts\dev\form-dev.ps1 -Action up
powershell.exe -NoProfile -File .\scripts\dev\form-dev.ps1 -Action frontend
```

Lệnh frontend chạy lâu dài; dùng terminal khác cho `-Action test`, `-Action status`
hoặc `-Action logs -Service form-service`. Bộ dev này chỉ dùng để phát triển;
chưa phải compose nâng cấp server.
