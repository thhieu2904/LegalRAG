# Build và cập nhật QR/Word từ Git trên server Windows

Không cần build image trên máy phát triển rồi push Docker Hub. Server clone/pull
source, tự build image local và dùng image đó cho 3 service:
`frontend`, `query-service`, `form-service`. Các service RAG/Vistral và dữ liệu
vẫn dùng cấu hình hiện tại. Đây không phải chuyển toàn bộ 9 service sang build.

## Điều kiện và phạm vi

- Server có Git, Docker Desktop chạy Linux containers và Docker Compose.
- Có internet để tải image nền Node/Python/Nginx và dependency npm/PyPI khi
  chưa có cache; không cần repository Docker Hub cho image ứng dụng mới.
- Clone vào một thư mục source riêng; giữ nguyên Compose và `.env` đang chạy
  trên server, không ghi đè chúng bằng bản trong Git.
- Giữ đúng Compose project cũ để dùng lại network và volume. Sao lưu dữ liệu
  bằng quy trình hiện có, giữ image/Compose cũ để rollback trước khi cập nhật.
- Không chạy `docker compose down -v`, prune hoặc xóa volume/model cache.

File override: `prod/docker-compose.form-source.yml`.
Script: `scripts/deploy/form-source.ps1`, mặc định chỉ kiểm tra cấu hình.
Build context là đường dẫn tuyệt đối của clone, không phụ thuộc chỗ để Compose
cũ. Script đối chiếu cấu hình trước/sau trong RAM, không in mật khẩu `.env`.
Chỉ cho phép đổi image/build/pull policy và healthcheck ở 3 service đã chọn.
Query healthcheck dùng Python/httpx vì image Python slim không có curl.
Frontend healthcheck dùng IPv4 `127.0.0.1`, tránh Alpine wget kiểm tra vào `::1`
trong khi Nginx chỉ listen IPv4.

## 1. Chuẩn bị source và xác định cấu hình server đang dùng

Sau khi commit được push lên GitHub, trên server clone/pull đúng revision.
Các lệnh dưới đây là hướng dẫn vận hành; trạng thái một lần triển khai phải
được xác nhận bằng log và metadata thực tế, không suy ra từ tài liệu này.

```powershell
git clone https://github.com/thhieu2904/LegalRAG.git
Set-Location -LiteralPath .\LegalRAG
# Những lần sau, trong clone sạch:
git pull --ff-only
```

Nếu đã có clone, không clone chồng vào đó; chỉ pull khi đã xử lý thay đổi local.
Kiểm tra project và vị trí Compose cũ (chỉ đọc):

```powershell
$legalragLabels = (docker inspect legalrag-query --format '{{json .Config.Labels}}' | ConvertFrom-Json)
$legalragLabels.'com.docker.compose.project'
$legalragLabels.'com.docker.compose.project.config_files'
$legalragLabels.'com.docker.compose.project.working_dir'
```

Điền **đường dẫn thực tế** và project vừa kiểm tra, không dùng các ví dụ này
nguyên xi. Nếu server đang dùng nhiều file Compose/override, dừng để đối chiếu
toàn bộ chuỗi file trước; script hiện nhận một base Compose, không được bỏ qua
override đang chạy.

```powershell
$legalragDeploy = @{
    ComposePath = 'C:\DUONG-DAN-CU\docker-compose.yml'
    EnvPath = 'C:\DUONG-DAN-CU\.env'
    ProjectName = 'PROJECT-CU-DA-KIEM-TRA'
}
```

## 2. Kiểm tra và build trên server

Tại root clone, trong PowerShell:

```powershell
& .\scripts\deploy\form-source.ps1 -Action check @legalragDeploy
& .\scripts\deploy\form-source.ps1 -Action build @legalragDeploy
& .\scripts\deploy\form-source.ps1 -Action preflight @legalragDeploy
```

`check` gọi Compose config, không cần engine và không khởi động container.
`build` cần engine; tải image nền nếu cần, build đúng 3 service, chưa thay
container đang chạy. Tag mặc định là commit Git hiện tại. Script từ chối build
hoặc cập nhật khi các đầu vào source còn thay đổi chưa commit.
`preflight` chỉ kiểm tra engine, ownership project/service và sự tồn tại của
ba image local; không khởi động hoặc thay container. Ownership đọc JSON labels,
không dùng tên label có dấu nháy trong Go template trên Windows PowerShell 5.

Frontend dùng Node 22, `npm ci` với lockfile và `npm run build` (có kiểm tra TS).
Chỉ `.env.docker` công khai được chép vào build; không chép `.env` riêng.
Các URL trong `.env.docker` là `localhost`, phù hợp trình duyệt ngay trên server.
URL Vite được đóng vào bundle: thay environment container không đổi URL đó.
Các Python image không chép `.env` từ build context; environment vẫn lấy từ
Compose/`.env` cũ qua tham số `EnvPath`.

## 3. Cập nhật đúng 3 container

Chỉ thực hiện sau khi build thành công và đã chuẩn bị rollback/backup:

```powershell
& .\scripts\deploy\form-source.ps1 -Action up @legalragDeploy
& .\scripts\deploy\form-source.ps1 -Action status @legalragDeploy
```

Script kiểm tra container hiện có thuộc đúng project và service; yêu cầu image
local đã build. Lệnh up dùng `--no-deps --no-build --pull never`: không tự đổi
LLM/provider, không rebuild/start các service khác, không xóa dữ liệu.
Có thể gián đoạn ngắn ở UI/Query/Form; session chỉ giữ trong RAM có thể mất.
Healthcheck thành công chưa thay thế kiểm tra chức năng RAG hoặc MinIO/DB.

Giữ overlay này cho những lần cập nhật 3 service tiếp theo. Không quay lại lệnh
`docker compose pull/up` toàn stack từ base cũ nếu không chủ định rollback.

## 4. Mẫu Word là dữ liệu riêng, Git pull không cập nhật MinIO

Mẫu chuẩn nằm tại `thesis/refs/forms/Giấy đăng ký khai sinh.docx`:
4 marker `scan_...`, 33 marker `form_...`, không có `form_37`.
Hash: `527768935ee88fa1e3b167c2a9300fc5b0a2ba7605cd79e75808d7e6db77b3c0`.

Phải đưa **đúng file đã đánh marker** tới object template đang được dùng trong
kho mẫu và giữ backup object cũ. Không chạy lại bộ tự đánh dấu/chuyển đổi cũ
nếu nó sửa marker hoặc lưu lại DOCX, vì hash sẽ khác. Quy trình thay template
trên server chưa tự động hóa và chưa được chạy trong lượt này.
Trước khi chốt nâng cấp, render phải trả đúng hash và 37 marker đã cấu hình.
Nếu chưa đổi file trong kho, UI chỉ cho nhập thủ công, không tự áp mapping QR
của mẫu mới lên mẫu cũ. URL `/forms/demo/...` chỉ thuộc bộ dev, không phải object
demo được tự tạo trên server production.

Kiểm tra bằng dữ liệu giả: quét điền đúng 4 ô, sửa một ô rồi quét lại không bị
ghi đè; gõ/nói/Xong/Hủy; xuất Word; thử một câu hỏi RAG; kiểm tra MinIO/DB.
Bản Word đã render bằng LibreOffice còn lưu ý ngắt trang tiêu đề Chú thích;
cần kiểm tra bản in. Mic/camera thật và Docker production chưa được xác nhận.

## Rollback

Giữ file base/env và image cũ (ví dụ v1.0.2) ở server. Chạy Compose **không thêm
source override**, chỉ chọn 3 service và dùng image cũ đã có:

```powershell
docker compose --project-name $legalragDeploy.ProjectName --env-file $legalragDeploy.EnvPath -f $legalragDeploy.ComposePath up -d --no-deps --no-build --pull never frontend query-service form-service
```

Đối chiếu tag trong base/env trước khi chạy. Không rollback source bằng cách
xóa dữ liệu. Nếu đã thay object Word, khôi phục riêng bản mẫu tương ứng.

## Ranh giới xác minh

Đã kiểm tra code QR/Word, frontend build và cấu hình Compose không cần engine.
Lượt chốt commit: 32 test frontend, 25 test Python, kiểm tra TypeScript cưỡng
bức và frontend build PASS từ bản source xuất theo Git index. Frontend dùng
dependency local hiện có; đây chưa phải cài dependency/build Linux trong image.
Compose/script check PASS trên Windows PowerShell 5 với `.env` giả không có
secret; đã thử từ chối base sai và source bẩn trước khi truy cập engine.
Guard triển khai có test offline bằng mock CLI (không dùng engine hoặc dữ liệu):
`powershell.exe -NoProfile -File scripts/deploy/tests/form-source.tests.ps1`.
Test kiểm tra check/preflight/up, từ chối project/service sai, thiếu image,
source bẩn và environment bị đổi; không tự suy ra acceptance production từ test.
Build Docker, triển khai và smoke trên một server cụ thể phải được ghi nhận
bằng log riêng. Không coi việc đọc tài liệu hoặc chạy preflight là đã deploy.

Tham khảo: [Docker Compose build](https://docs.docker.com/reference/compose-file/build/),
[quy tắc merge và đường dẫn](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/).
