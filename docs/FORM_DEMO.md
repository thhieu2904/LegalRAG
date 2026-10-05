# Demo điền Word bằng QR và giọng nói

## Phạm vi

Giữ microservices hiện tại. Thay đổi frontend, Query gateway và Form Service;
không đổi LLM, RAG, schema cơ sở dữ liệu hay dữ liệu đang chạy trên server.
Chưa push hay triển khai server. Bộ Docker dev QR/Word từng chạy được;
lượt kiểm thử 05/10/2026 dùng adapter native do Docker Desktop lỗi khởi động.
Theo yêu cầu người dùng, không sửa Docker và không thay Docker production.

Đã cấu hình **một mẫu**: `Giấy đăng ký khai sinh.docx` do người dùng cung cấp,
đã dùng marker mới tại `thesis/refs/forms/Giấy đăng ký khai sinh.docx`.
File gốc ở root giữ nguyên; bản demo có thêm thuộc tính giữ tiêu đề Chú thích
với đoạn sau. Thuộc tính này chưa giải quyết được ngắt trang trong LibreOffice.
Đây là demo kỹ thuật, không phải xác nhận tính hợp lệ pháp lý của mẫu.
Các mẫu còn lại phải được cung cấp và đối chiếu riêng, không tự suy đoán vị trí.

## Cách dùng

1. Mở biểu mẫu như luồng hiện có của ứng dụng.
2. Quét căn cước của **người yêu cầu**: mẫu đã xác định sẵn 4 vị trí, không phải
   chọn người nhận dữ liệu nữa. Camera chỉ mở khi bấm **Mở camera**;
   có thể chọn ảnh hoặc bỏ qua quét.
3. QR chỉ điền 4 ô `scan_...` chưa từng chỉnh. Không điền thông tin trẻ,
   dân tộc, quốc tịch, cơ quan hay nơi cấp căn cước bằng suy đoán.
4. Bấm một ô để sửa. Nếu đã có nội dung, quét lại không tự ghi đè; nút gợi ý QR
   trong ô cho phép chủ động lấy dữ liệu mới rồi xác nhận.
5. Để nói: bấm **Bấm để nói**, nói rõ nội dung cho ô đang sửa. Chữ nhận diện
   hiện trực tiếp trong **cùng ô nhập**, không có ô bản nháp hay nút chuyển nội dung.
   Nút mic đổi thành **Dừng** trong lúc nghe, rồi **Nói lại** khi ô có nội dung.
   Giao diện chỉ có hướng dẫn thao tác; không còn thông báo công nghệ/online hay
   checkbox xác nhận lặp lại ở mỗi ô. Quyền micro của trình duyệt vẫn giữ nguyên.
6. Kiểm tra/sửa chữ ngay trong ô rồi bấm **Xong** một lần để cập nhật biểu mẫu.
   **Nói lại** thay nội dung trong ô khi có kết quả mới, không nối trùng hay xóa
   nội dung cũ nếu chưa nhận được lời nói. **Hủy**/đóng ô giữ giá trị trước khi sửa.
   Không tự lưu hay tự gửi form sau khi nói.
7. Tải Word. Nếu còn ô trống, có thông báo số ô thiếu và lựa chọn hủy/tải tiếp.
   Mở Word kiểm tra lại nội dung và bố cục trước khi sử dụng.

Không bật camera/mic tự động, không tự khởi động lại nhận diện. Đóng ô hoặc đổi
mẫu dừng phiên nhận diện. Phiên nói tối đa 60 giây; khi dừng vẫn chờ kết quả
cuối, có giới hạn chờ để tránh treo.
Trong lúc nghe/chờ kết quả cuối, ô tạm chỉ đọc và nút **Xong** tạm khóa để tránh
ghi nhận nội dung chưa hoàn tất. Kết thúc hoặc lỗi thì có thể gõ/sửa tiếp;
lỗi nhận diện không xóa chữ đã có. Mỗi ô giới hạn 2.000 ký tự cả gõ lẫn nói.

Ghi chú kỹ thuật: vẫn dùng nhận diện tiếng Việt của Chrome có internet, không
phải nhận diện offline. Âm thanh có thể được gửi tới dịch vụ nhận diện của trình
duyệt. Thay đổi câu chữ giao diện không thay đổi phương thức xử lý này.

Camera hiện **chụp thủ công** bằng nút **Chụp & đọc QR**, sau đó gửi ảnh tới backend.
Ảnh dùng PNG toàn khung ở độ phân giải video gốc; không cắt theo ô hướng dẫn.
Trong lúc lấy/đọc ảnh, chặn thao tác chụp lặp. PNG không chứng minh ảnh thực tế
sẽ nét hơn; camera bị mờ/lóa vẫn cần thử trực tiếp.
Chưa có nhận diện QR liên tục, tự chụp khi thấy mã, kiểm tra độ nét hay code điều
khiển lấy nét. Autofocus sẵn có của camera (nếu có) không phải tính năng mới.

**Thay đổi hành vi so với bản cũ:** tải Word không tự gọi `/forms/save` để lưu
hồ sơ lên MinIO/cơ sở dữ liệu. Bản nháp chỉ nằm trong bộ nhớ của trang; đổi mẫu,
tải lại hoặc rời trang làm mất bản nháp. Không ghi dữ liệu QR/chữ nói vào log mới
hay localStorage. Ảnh QR vẫn được gửi tới backend để giải mã như luồng cũ;
giọng nói không đi qua backend LegalRAG.

## Cấu hình mẫu

- Registry: `frontend/src/pages/FormFillPage/templates/index.ts`.
- Mẫu đầu tiên: `templates/birthRegistration.ts`.
- Kiểu cấu hình: `templates/types.ts`.
- Trạng thái thống nhất và chính sách bảo vệ dữ liệu: `draft.ts`.
- Điều phối tải mẫu/quét/xuất, bỏ phản hồi cũ: `hooks/useFormFill.ts`.
- Nhận diện và phiên mic: `speech.ts`, `components/FieldDictation.tsx`.
- Điền DOCX: `form-service/src/services/docx_fields.py`.

Cấu hình gắn với **SHA-256 của đúng file Word và tập placeholder chính xác**,
không đoán theo tên file. Form Service trả hash khi render; Query gateway chuyển
hash; frontend gửi hash khi fill. Backend từ chối nếu file đã thay đổi giữa lúc
xem và xuất. Với gateway cũ hoặc mẫu khác hash, giao diện vẫn cho nhập từng ô
nhưng QR chỉ tham khảo, không tự áp cấu hình sai mẫu.

Mẫu hiện tại có **37 ô**: 4 `scan_...` và 33 `form_...`.

| Marker Word | Dữ liệu tự điền từ QR |
| --- | --- |
| `scan_ho_ten` | Họ tên người yêu cầu |
| `scan_ngay_sinh` | Ngày sinh người yêu cầu |
| `scan_dia_chi` | Nơi cư trú người yêu cầu |
| `scan_cccd` | Chỉ số căn cước, không tự ghép ngày/nơi cấp |

Ô thủ công là `form_1`, `form_6` đến `form_36`, rồi `form_38` trong bảng lồng.
Không có `form_37`; không đổi số. `form_...` là ID ổn định, ý nghĩa/nhãn nằm
trong cấu hình TypeScript. Ô Có/Không yêu cầu bản sao là hình ảnh trong Word
gốc, **chưa điền tự động**; số lượng bản sao (`form_38`) đã điền được.
Hash mẫu hiện tại: `527768935ee88fa1e3b167c2a9300fc5b0a2ba7605cd79e75808d7e6db77b3c0`.

### Thêm một mẫu

1. Tạo/bổ sung `{{scan_...}}` hoặc `{{form_...}}` tại đúng vị trí trong Word;
   dùng tên gồm chữ ASCII,
   số và dấu gạch dưới, bắt đầu bằng chữ. Có thể dùng một ID lặp ở nhiều vị trí.
   Không đặt placeholder bên trong ảnh.
2. Đọc file cuối cùng và lập danh sách ID/nhãn/nhóm. Mỗi ô QR khai báo cả
   `roleId` và `qrSource`; ô nhập tay/giọng nói không cần hai thuộc tính này.
   `scan_ho_ten` ánh xạ tới nguồn `field_ho_ten`, tương tự cho ngày sinh/địa chỉ.
   `scan_cccd` của mẫu này lấy nguồn `field_cccd` (số đơn thuần).
   `identity_document` vẫn là tùy chọn riêng cho mẫu cần ghép số và ngày cấp;
   không tự bịa nơi cấp. Đặt một vai trò nếu mẫu có đích QR cố định.
3. Lấy SHA-256 (`Get-FileHash -Algorithm SHA256 -LiteralPath '...docx'`), tạo
   một file `.ts` theo `birthRegistration.ts`, thêm vào registry.
4. Đưa **đúng file đã băm** vào kho mẫu theo luồng quản trị hiện có. Lưu lại bằng
   Word dù không đổi nội dung cũng có thể đổi hash: khi đó phải đối chiếu/cập nhật
   cấu hình và build lại frontend.
5. Kiểm thử từng vai trò bằng dữ liệu giả, sửa một ô rồi quét lại để xác nhận
   không bị ghi đè; thử một ô lặp; xuất Word và kiểm tra các vị trí/định dạng.

## Kiểm thử local

Khi Docker chạy được, dùng VS Code: F1 → **Tasks: Run Task** →
**LegalRAG: Start QR + Word dev**. Xem [FORM_DEV.md](FORM_DEV.md) để biết
phạm vi bộ dev, các terminal log và cách dừng. Bộ này giải mã QR thật;
fixture ở mục dưới vẫn chỉ trả QR giả và không nên dùng để thử quét.
Lượt kiểm thử mới không dùng Docker: [FORM_QA_20261005.md](FORM_QA_20261005.md).

Frontend (thư mục `frontend`):

```powershell
npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd run test:forms
npm.cmd run build
```

Python (thư mục `form-service`, dùng môi trường có python-docx và pydantic):

```powershell
python -B -X utf8 -m unittest discover -s tests -v
```

Kết quả ngày 05/10/2026: **32 ca frontend**, **25 ca Python local**, build frontend
và ESLint FormFillPage PASS. Bao gồm mapping `scan_/form_`, QR đích cố định,
không ghi đè, khung ảnh PNG gốc, nhập giọng nói trực tiếp, nói lại, chờ kết quả
cuối, hủy, lỗi và giới hạn ký tự.
Frontend tests chạy các module TS/TSX thật với nhận diện/hook/API giả lập, không
phải kiểm thử mic thật. Python tests kiểm tra thay thế qua nhiều run, bảng lồng,
ô lặp, header/footer, ảnh/định dạng không liên quan, hash đổi và parser QR/ngày.
Các thư viện network/image không có trong môi trường kiểm thử được stub;
không thực sự giải mã ảnh QR trong các ca unit test.
Phép thử native riêng đã giải mã ảnh thật và 4 biến thể bằng OpenCV/pyzbar,
render bằng Mammoth và xuất Word với đủ 37 giá trị giả.
Parser cũ từ chối payload có 4 cột dự phòng rỗng ở cuối; đã sửa chỉ bỏ cột rỗng
phía cuối rồi vẫn kiểm tra đủ 7 trường lõi. Cột mở rộng có nội dung vẫn từ chối.
Đo thời gian bằng đồng hồ monotonic để không bị thời gian xử lý âm.

Lịch sử: 20 ca Python và smoke Docker từng PASS ở lượt dựng bộ dev trước,
không phải bằng chứng cho bản mới sau thay marker/parser. **Docker smoke mới
NOT RUN**; adapter native không thay thế Query/MinIO/DB/RAG production.

### Giao diện kiểm thử riêng, không phải server

`frontend/scripts/form-demo-fixture.py` phục vụ mẫu Word đã đánh dấu, preview
chỉ có nội dung, dữ liệu QR giả và xuất bằng bộ điền DOCX thật. Chỉ nghe ở
`127.0.0.1:8766`; không lưu hồ sơ/file và không nối tới MinIO hay database.
Endpoint quét **không giải mã ảnh**: luôn trả dữ liệu giả. Không đưa căn cước
thật vào môi trường này.

Terminal 1 (trong `frontend`, Python có python-docx):

```powershell
python -B -X utf8 scripts/form-demo-fixture.py
```

Terminal 2 (trong `frontend`; biến chỉ áp dụng phiên terminal):

```powershell
$env:VITE_QUERY_SERVICE_URL = 'http://127.0.0.1:8766'
$env:VITE_ADMIN_SERVICE_URL = 'http://127.0.0.1:8766'
npm.cmd run dev -- --host 127.0.0.1 --port 3006 --strictPort
```

Mở Chrome `http://localhost:3006/forms/demo/Gi%E1%BA%A5y%20%C4%91%C4%83ng%20k%C3%BD%20khai%20sinh.docx`.
Kiểm tra UI đã thực hiện trước khi rút gọn hướng dẫn giọng nói: nhập giả, hai vị
 trí cùng ID dùng cùng bản nháp, mic mặc định tắt, xuất đúng ô tên, cảnh báo 36 ô thiếu,
hủy tải và **0 lần gọi lưu hồ sơ**. Preview fixture không chứng minh bố cục Word
hay luồng render bằng Mammoth trên Docker.
Sau khi rút gọn, bổ sung kiểm thử React render để xác nhận chỉ có hướng dẫn,
không còn tên công nghệ/yêu cầu online/checkbox và không khởi động mic khi render.
Sau khi bỏ bước chuyển bản nháp, đã kiểm tra trên Chrome với backend Docker dev
thật: chỉ một ô nhập, nút **Nói lại**, **Xong** cập nhật biểu mẫu, **Hủy** giữ nội dung
cũ. Chỉ gõ dữ liệu giả trong kiểm tra UI; không bật mic thật. Ảnh xác minh local:
`docs/operations.local/form-voice-simple-20261004.jpg`.

## Kế hoạch build từ source trên server (chưa thực hiện)

Đã bổ sung override và script build có kiểm tra phạm vi thay đổi:
[FORM_SOURCE_DEPLOY.md](FORM_SOURCE_DEPLOY.md). Chưa chạy build/up trên server.

Git pull đơn thuần không cập nhật container: `prod/docker-compose.yml` hiện
chỉ khai báo `image:` Docker Hub, không có `build:`.

1. Chốt revision source muốn chạy, giữ bản compose/env cũ để rollback và sao lưu
   dữ liệu bằng quy trình hiện có. Không ghi đè source máy đang phát triển.
2. Build/recreate **frontend, query-service, form-service** cùng bản. Context
   tương ứng là `frontend/`, `query-service/`, `form-service/`; Dockerfile đã có.
   Dùng tag local riêng và `prod/docker-compose.form-source.yml` chỉ cho ba
   service này; override đã có, chưa chạy build/up. Giữ nguyên compose/volumes và
   những service RAG khác, không dùng `down -v` hay xóa volume.
3. Frontend Dockerfile chép `.env.docker` khi build. Các URL Vite nằm trong
   bundle, thay environment lúc chạy container **không sửa** URL đã build.
   `.env.docker` hiện phù hợp trình duyệt chạy ngay máy server (`localhost`).
4. Đưa đúng mẫu/hash lên kho mẫu; kiểm tra render trả hash, QR vào 4 vị trí đúng,
   không ghi đè, nói-xem lại-xác nhận, Word đủ/thiếu ô và không tự lưu hồ sơ.
5. Nếu không đạt, quay lại tag/revision trước; không thay/xóa dữ liệu dùng chung.

**NOT RUN:** tích hợp Docker mới/MinIO/database/RAG production, triển khai
server, chụp camera thật, nhận diện mic thật trên UI mới, Microsoft Word;
thao tác Run Task trong giao diện VS Code. Tải ảnh tự động qua tiện ích Chrome
bị chặn quyền truy cập file; không đổi quyền đó. Kiểm thử API ảnh thật vẫn PASS.

LibreOffice đã render và kiểm tra cả 2 trang của mẫu và bản điền dữ liệu giả:
đủ 37 ô, không đổi ZIP part ngoài nội dung. Còn lưu ý tiêu đề **Chú thích** có
thể nằm lẻ cuối trang sau khi điền; `keepNext` chưa khắc phục được trong bảng
ngoài của mẫu này. Không coi đây là bản in đã hoàn tất. Preview web chỉ xem
nội dung, không chứng minh độ khớp bố cục in của Word.
