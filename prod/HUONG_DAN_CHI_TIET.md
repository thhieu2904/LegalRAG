# 🎯 HƯỚNG DẪN CHI TIẾT CHO WINDOWS 10 PRO

## 📋 Yêu Cầu Trước Khi Bắt Đầu

### **Bước 0: Cài đặt Docker Desktop (NẾU CHƯA CÓ)**

1. **Download Docker Desktop:**

   - Vào: https://www.docker.com/products/docker-desktop/
   - **Download for Windows** → File `.exe`
   - **Size:** ~500MB

2. **Cài đặt Docker Desktop:**

   - **Double-click** file `.exe` vừa tải
   - **Follow hướng dẫn** (Next → Next → Install)
   - **Restart máy** khi được yêu cầu

3. **Khởi động Docker Desktop:**

   - **Tìm icon Docker** trên Desktop hoặc Start Menu
   - **Double-click** để mở
   - **Chờ Docker Engine khởi động** (icon Docker màu xanh ở System Tray)

4. **Kiểm tra Docker hoạt động:**
   - **Mở Command Prompt** (`Windows + R` → gõ `cmd`)
   - **Gõ:** `docker --version`
   - **Thấy version** → ✅ OK!

### **Sau khi có Docker Desktop:**

- ✅ **Docker Desktop** đã cài và chạy
- ✅ **NVIDIA GPU** (RTX 3060 hoặc tương đương)
- ✅ **NVIDIA Container Toolkit** (sẽ hướng dẫn cài bên dưới)

---

## 🚀 TỪNG BƯỚC CHI TIẾT

### **Bước 1: Tạo thư mục trên Windows**

1. **Mở File Explorer** (phím `Windows + E`)
2. **Vào ổ D:** (click vào `This PC` → `Local Disk (D:)`)
3. **Click chuột phải** trong ổ D → **New** → **Folder**
4. **Đặt tên:** `LegalRAG` (chính xác tên này)
5. **Enter** để tạo thư mục

### **Bước 2: Copy 2 files vào thư mục**

**Copy 2 files này vào `D:\LegalRAG\`:**

- `docker-compose.yml`
- `.env`

**Cách copy:**

1. **Chọn cả 2 files** (Ctrl + Click)
2. **Copy:** `Ctrl + C`
3. **Vào D:\LegalRAG**
4. **Paste:** `Ctrl + V`

### **Bước 3: Mở Terminal tại thư mục**

**Cách 1 (Dễ nhất):**

1. **Trong File Explorer**, vào `D:\LegalRAG`
2. **Click vào address bar** (nơi hiện `D:\LegalRAG`)
3. **Gõ:** `cmd` rồi **Enter**
4. **Terminal sẽ mở** đúng tại thư mục này

**Cách 2:**

1. **Click chuột phải** trong thư mục `D:\LegalRAG`
2. **Chọn:** `Open in Terminal` (nếu có)
3. **Hoặc:** `Open PowerShell window here`

**Cách 3:**

1. **Mở Command Prompt** (`Windows + R` → gõ `cmd` → Enter)
2. **Gõ:** `cd D:\LegalRAG`
3. **Enter**

### **Bước 4: Chạy lệnh**

**Trong Terminal, gõ từng lệnh:**

```bash
# Lệnh 1: Chạy hệ thống
docker-compose up -d
```

**⏳ Chờ 2-3 phút**, sau đó:

```bash
# Lệnh 2: Xem quá trình khởi động
docker-compose logs -f rag-service
```

### **Bước 5: Chờ đợi và theo dõi**

**📊 Timeline:**

- **Phút 0-2:** Pull Docker images từ Docker Hub
- **Phút 2-12:** Download AI models (PhoGPT 2.5GB + Vietnamese models)
- **Phút 12-15:** Load models lên GPU và khởi động
- **Phút 15+:** ✅ Sẵn sàng!

**🎯 Dấu hiệu THÀNH CÔNG:**

```
🎉 LegalRAG API started successfully!
💡 Architecture: Embedding(CPU) + LLM(GPU) + Reranker(GPU)
```

**📱 Khi thấy thông báo trên:**

- **Nhấn:** `Ctrl + C` để thoát logs
- **Mở browser:** http://localhost:5173
- **Test thử:** Hỏi "Làm CCCD cần giấy tờ gì?"

### **Bước 6: Quản lý bằng Docker Desktop (TIỆN LỢI)**

**Mở Docker Desktop:**

1. **Click icon Docker** ở System Tray (góc phải màn hình)
2. **Vào tab "Containers"**
3. **Thấy 3 containers:**
   - `legalrag-frontend` → Web interface
   - `legalrag-rag-service` → AI engine
   - `legalrag-identifill-service` → CCCD scanner

**Quản lý containers:**

- **▶️ Start:** Click nút Play để khởi động
- **⏸️ Stop:** Click nút Stop để tạm dừng
- **🔄 Restart:** Click nút Restart để khởi động lại
- **📋 Logs:** Click container → View logs
- **🗑️ Delete:** Click container → Delete (cẩn thận!)

**🎯 Ưu điểm Docker Desktop:**

- **Quản lý trực quan** thay vì gõ lệnh
- **Xem logs dễ dàng**
- **Monitor resource usage** (CPU, RAM)
- **One-click start/stop** toàn bộ hệ thống

---

## 🔧 KHẮC PHỤC SỰ CỐ

### **Nếu GPU không được nhận diện:**

```bash
# Kiểm tra GPU
nvidia-smi

# Kiểm tra Docker GPU
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

### **Nếu hết VRAM:**

1. **Sửa file `.env`:**
   ```
   ENABLE_VRAM_SWAPPING=true
   ```
2. **Restart:**
   ```bash
   docker-compose restart rag-service
   ```

### **Nếu Port bị chiếm:**

1. **Sửa `docker-compose.yml`**, thay:
   ```yaml
   ports:
     - "3000:5173" # Thay 5173 thành 3000
     - "8001:8000" # Thay 8000 thành 8001
   ```

---

## 🎊 KẾT QUẢ CUỐI CÙNG

**Anh sẽ có hệ thống hoàn chỉnh tại:**

- **🌐 Web Interface:** http://localhost:5173
- **🔧 RAG API:** http://localhost:8000
- **📱 CCCD Scanner:** http://localhost:8002

**🔥 Chính xác như máy dev của em!**

---

## 📞 Hỗ Trợ

**Nếu gặp lỗi, chụp màn hình và gửi:**

- Terminal error messages
- Docker Desktop status
- `nvidia-smi` output

**Em sẽ support ngay!** 🚀
