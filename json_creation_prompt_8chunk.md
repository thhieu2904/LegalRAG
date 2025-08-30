# HƯỚNG DẪN TẠO JSON 8 CHUNK CHO QUY TRÌNH CHỨNG THỰC

## MỤC TIÊU

Tạo cấu trúc JSON chuẩn hóa với 8 chunk để tối ưu hóa việc truy xuất thông tin từ các tài liệu quy trình chứng thực.

## CẤU TRÚC 8 CHUNK

### Chunk 1: Thông tin cơ bản và tiêu đề

**Nội dung cần trích xuất:**

- Tên đầy đủ của thủ tục
- Mã hiệu (ví dụ: QT 01/CX-HCTP)
- Ngày ban hành
- Cơ quan ban hành
- Mục đích của thủ tục
- Phạm vi áp dụng

**Ví dụ:**

```
"Tiêu đề: Thủ tục chứng thực chữ ký
Mã hiệu: QT 01/CX-HCTP
Ngày ban hành: 07/7/2025
Cơ quan ban hành: Sở Tư pháp
Mục đích: Quy định thành phần hồ sơ, lệ phí, trình tự, cách thức và thời gian giải quyết hồ sơ hành chính"
```

### Chunk 2: Định nghĩa và viết tắt

**Nội dung cần trích xuất:**

- Danh sách tất cả từ viết tắt
- Định nghĩa đầy đủ của từng từ

**Ví dụ:**

```
UBND: Ủy ban nhân dân
TTHC: Thủ tục hành chính
GCN: Giấy chứng nhận
ISO: Hệ thống quản lý chất lượng - TCVN ISO 9001:2015
BPTN&HT: Bộ phận tiếp nhận và hỗ trợ kết quả
CN & TC: Cá nhân và tổ chức
CQHCNN: Cơ quan hành chính nhà nước
```

### Chunk 3: Thành phần và số lượng hồ sơ

**Nội dung cần trích xuất:**

- Danh sách giấy tờ cần nộp
- Số lượng bộ hồ sơ
- Yêu cầu về bản chính/bản sao
- Giấy tờ kèm theo (nếu có)

**Ví dụ:**

```
Người yêu cầu chứng thực phải xuất trình các giấy tờ sau:
+ Bản chính hoặc bản sao có chứng thực Giấy chứng minh nhân dân/Thẻ căn cước công dân
+ Giấy tờ, văn bản cần chứng thực chữ ký
+ Bản dịch tiếng Việt (nếu văn bản bằng tiếng nước ngoài)
```

### Chunk 4: Thời hạn giải quyết

**Nội dung cần trích xuất:**

- Thời gian xử lý hồ sơ
- Các trường hợp đặc biệt
- Thời gian trả kết quả
- Quy định về phiếu hẹn

**Ví dụ:**

```
Thời hạn thực hiện yêu cầu chứng thực là ngay trong ngày cơ quan, tổ chức tiếp nhận yêu cầu hoặc trong ngày làm việc tiếp theo nếu tiếp nhận yêu cầu sau 15 giờ.
Trường hợp phải kéo dài thời hạn giải quyết thì người tiếp nhận hồ sơ phải có phiếu hẹn ghi rõ thời gian (giờ, ngày) trả kết quả.
```

### Chunk 5: Đối tượng và cơ quan thực hiện

**Nội dung cần trích xuất:**

- Đối tượng được thực hiện thủ tục
- Cơ quan có thẩm quyền thực hiện
- Địa điểm thực hiện

**Ví dụ:**

```
Đối tượng thực hiện thủ tục hành chính: Cá nhân
Cơ quan thực hiện thủ tục hành chính: Phòng Công chứng
```

### Chunk 6: Kết quả thực hiện và lệ phí

**Nội dung cần trích xuất:**

- Kết quả của thủ tục
- Hình thức trả kết quả
- Mức lệ phí chi tiết
- Cách thức thu phí

**Ví dụ:**

```
Kết quả thực hiện thủ tục hành chính: Giấy tờ, văn bản được chứng thực chữ ký
Phí: 10.000 đồng/trường hợp (trường hợp được tính là một hoặc nhiều chữ ký trong một giấy tờ, văn bản)
```

### Chunk 7: Yêu cầu và điều kiện thực hiện

**Nội dung cần trích xuất:**

- Các điều kiện tiên quyết
- Trường hợp không được thực hiện thủ tục
- Yêu cầu về năng lực hành vi
- Yêu cầu về giấy tờ tùy thân

**Ví dụ:**

```
Trường hợp không được chứng thực chữ ký:
- Tại thời điểm chứng thực, người yêu cầu chứng thực chữ ký không nhận thức và làm chủ được hành vi của mình
- Người yêu cầu chứng thực chữ ký xuất trình Giấy chứng minh nhân dân hoặc Hộ chiếu không còn giá trị sử dụng
```

### Chunk 8: Căn cứ pháp lý và quy trình chi tiết

**Nội dung cần trích xuất:**

- Danh sách văn bản pháp lý
- Quy trình xử lý công việc chi tiết
- Biểu mẫu sử dụng
- Hồ sơ lưu trữ

**Ví dụ:**

```
Căn cứ pháp lý:
- Nghị định số 23/2015/NĐ-CP ngày 16/02/2015 của Chính phủ
- Thông tư số 01/2020/TT-BTP ngày 03/3/2020 của Bộ trưởng Bộ Tư pháp

Quy trình xử lý:
1. Tiếp nhận hồ sơ, kiểm tra tính pháp lý và nội dung hồ sơ
2. Xem xét hồ sơ: Đồng ý ký chứng thực hoặc yêu cầu chỉnh sửa, bổ sung
3. Đóng dấu, thu lệ phí, trả hồ sơ cho người dân
```

## HƯỚNG DẪN TRIỂN KHAI

### Bước 1: Chuẩn bị

- Đọc kỹ nội dung tài liệu DOC
- Xác định cấu trúc và nội dung của từng phần
- Chuẩn bị template JSON 8 chunk

### Bước 2: Trích xuất thông tin

- Đọc từng phần của tài liệu
- Ánh xạ nội dung vào chunk tương ứng
- Đảm bảo không bỏ sót thông tin quan trọng

### Bước 3: Điền vào template

- Sao chép template json_template_8chunk.json
- Thay thế các placeholder [text] bằng nội dung thực tế
- Kiểm tra tính chính xác và đầy đủ

### Bước 4: Validation

- Kiểm tra tất cả 8 chunk đã được điền đầy đủ
- Xác minh thông tin pháp lý chính xác
- Đảm bảo cấu trúc JSON hợp lệ

## LƯU Ý QUAN TRỌNG

1. **Đảm bảo tính chính xác**: Thông tin pháp lý phải chính xác 100%
2. **Không trùng lặp**: Mỗi chunk chứa thông tin độc nhất
3. **Tính toàn diện**: 8 chunk phải bao quát toàn bộ nội dung tài liệu
4. **Dễ truy xuất**: Chia nhỏ giúp tìm kiếm và tham khảo chính xác hơn
5. **Tuân thủ pháp luật**: Cập nhật các văn bản pháp lý mới nhất

## VÍ DỤ HOÀN CHỈNH

Sau khi hoàn thành, file JSON sẽ có cấu trúc như sau:

- **Chunk 1**: Chứa thông tin cơ bản về thủ tục
- **Chunk 2**: Chứa tất cả định nghĩa và viết tắt
- **Chunk 3**: Chứa yêu cầu về hồ sơ
- **Chunk 4**: Chứa thông tin về thời hạn
- **Chunk 5**: Chứa thông tin về đối tượng và cơ quan
- **Chunk 6**: Chứa thông tin về kết quả và phí
- **Chunk 7**: Chứa các điều kiện và yêu cầu
- **Chunk 8**: Chứa căn cứ pháp lý và quy trình chi tiết

Template này sẽ được sử dụng để xử lý tất cả các tài liệu trong collection quy_trinh_chung_thuc.
