# 📚 LegalRAG Documentation

> **Centralized documentation for LegalRAG system**

## 📋 **Documentation Index**

### 🚀 **Getting Started**

- **[COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md)** - Complete system guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup instructions

### 🔧 **Technical Docs**

- **[CONFIG_SYSTEM.md](CONFIG_SYSTEM.md)** - Configuration details
- **[ENHANCED_RAG_SYSTEM.md](ENHANCED_RAG_SYSTEM.md)** - RAG architecture
- **[ROUTER_CACHE_SYSTEM.md](ROUTER_CACHE_SYSTEM.md)** - Smart routing system

### 🐳 **Deployment**

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- **[FRESH_INSTALL_GUIDE.md](FRESH_INSTALL_GUIDE.md)** - Clean installation

---

## 📖 **Quick Reference**

### **Start Development**

```bash
# Backend
cd backend && python main.py

# Frontend
cd frontend && npm run dev
```

### **Key URLs**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### **Main Features**

- 🤖 PhoGPT-4B Vietnamese LLM
- 🔍 ChromaDB Vector Search
- 🎯 Smart Query Router
- 💬 Multi-turn Clarification
- 🌐 Modern React Interface

---

For detailed information, see **[COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md)**

1. **Setup**: Xem `../README.md` cho hướng dẫn cài đặt chi tiết
2. **Quick Start**: Sử dụng `QUICKSTART_NEW.md` cho bản mới nhất
3. **API**: Truy cập http://localhost:8000/docs khi server đang chạy
4. **Scripts**: Xem `../backend/scripts/README.md` cho các utilities
5. **Tools**: Xem `../backend/tools/README.md` cho development tools

## Production Deployment

Trong môi trường production:

```bash
cd backend
python main.py
```

hoặc

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Ghi chú

- Luôn đọc `../README.md` trước
- Kiểm tra requirements và dependencies
- Đảm bảo cấu hình môi trường đúng
