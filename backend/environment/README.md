# 🐍 LegalRAG Backend Environment Deployment Guide

## 📋 Tổng Quan

Thư mục này chứa tất cả các file cấu hình cần thiết để tái tạo môi trường Python cho backend LegalRAG. Environment này đã được tối ưu hóa đặc biệt cho:

- **AI/ML Processing**: PyTorch, Transformers, Sentence-Transformers
- **Vector Database**: ChromaDB, FAISS
- **RAG Framework**: LangChain, LangSmith
- **Web API**: FastAPI, Uvicorn
- **Document Processing**: python-docx, lxml, PyPDF2
- **GPU Acceleration**: CUDA 12.1, llama-cpp-python

## 📁 Cấu Trúc Files

```
backend/environment/
├── environment.yml           # File chính - Conda environment (KHUYẾN NGHỊ)
├── conda-packages.txt       # Backup danh sách conda packages
├── pip-requirements.txt     # Backup danh sách pip packages
├── setup_environment.bat    # Script tự động Windows
├── setup_environment.sh     # Script tự động Linux/Mac
└── ENVIRONMENT_DEPLOYMENT.md # File hướng dẫn này
```

## 🎯 Thông Tin Môi Trường Gốc

- **Tên Environment**: LegalRAG_v1
- **Python Version**: 3.11.13
- **Loại**: Conda Environment
- **Đường dẫn gốc**: `D:\env\conda\LegalRAG_v1`
- **Tổng số packages**: 180+ packages
- **Hỗ trợ GPU**: CUDA 12.1 với PyTorch

## ⚡ Quick Start - Triển Khai Nhanh (KHUYẾN NGHỊ)

### 🔥 Cách 1: Sử dụng Script Tự Động (Dễ nhất)

**Trên Windows:**

```cmd
# Mở x64 Native Tools Command Prompt for Visual Studio
# Navigate to backend/environment folder
cd path\to\backend\environment

# Chạy script với tên environment mong muốn
setup_environment.bat LegalRAG_Backend
```

**Trên Linux/Mac:**

```bash
# Navigate to backend/environment folder
cd path/to/backend/environment

# Make script executable
chmod +x setup_environment.sh

# Run script
./setup_environment.sh LegalRAG_Backend
```

### 🎯 Cách 2: Sử dụng environment.yml (Khuyến nghị)

```bash
# 1. Navigate to backend/environment folder
cd backend/environment

# 2. Create environment from yml file
conda env create -f environment.yml

# 3. Activate environment
conda activate LegalRAG_v1

# 4. Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

## 🔧 Hướng Dẫn Chi Tiết Từng Bước

### 📋 Yêu Cầu Hệ Thống

**Trước khi bắt đầu, đảm bảo hệ thống có:**

✅ **Conda hoặc Miniconda** đã cài đặt  
✅ **NVIDIA GPU** với CUDA 12.1+ (cho GPU acceleration)  
✅ **Visual Studio Build Tools** (Windows - cho compile C++ extensions)  
✅ **Git** (để clone repository nếu cần)  
✅ **Ít nhất 5GB dung lượng** trống

### 🚀 Bước 1: Chuẩn Bị Môi Trường

**Trên Windows:**

```cmd
# Mở x64 Native Tools Command Prompt for Visual Studio
# (Tìm trong Start Menu -> Visual Studio -> x64 Native Tools Command Prompt)

# Kiểm tra conda
conda --version

# Kiểm tra CUDA (nếu có GPU)
nvcc --version
```

**Trên Linux/Mac:**

```bash
# Kiểm tra conda
conda --version

# Kiểm tra CUDA (nếu có GPU)
nvcc --version
```

### 🏗️ Bước 2: Tạo Environment Mới

```bash
# Navigate to project directory
cd path/to/LegalRAG_Fixed/backend/environment

# Tạo environment từ file yml
conda env create -f environment.yml

# Hoặc tạo với tên khác
conda env create -f environment.yml -n your_custom_name
```

### ⚡ Bước 3: Kích Hoạt và Kiểm Tra

```bash
# Activate environment
conda activate LegalRAG_v1  # hoặc your_custom_name

# Kiểm tra Python version
python --version

# Kiểm tra pip
pip --version

# List installed packages
conda list | head -20
```

### 🧪 Bước 4: Verify Critical Packages

```bash
# Test PyTorch installation
python -c "
import torch
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA Version: {torch.version.cuda}')
    print(f'GPU Device: {torch.cuda.get_device_name(0)}')
"

# Test Transformers
python -c "from transformers import AutoTokenizer; print('✅ Transformers OK')"

# Test ChromaDB
python -c "import chromadb; print('✅ ChromaDB OK')"

# Test LangChain
python -c "from langchain.llms import OpenAI; print('✅ LangChain OK')"

# Test FastAPI
python -c "from fastapi import FastAPI; print('✅ FastAPI OK')"

# Test llama-cpp-python (nếu cần)
python -c "import llama_cpp; print('✅ Llama-cpp-python OK')"
```

## 🚨 Xử Lý Sự Cố GPU Packages

### ⚠️ Vấn Đề Thường Gặp

**1. PyTorch không nhận diện GPU:**

```bash
# Gỡ cài PyTorch hiện tại
pip uninstall torch torchvision torchaudio

# Cài lại với CUDA support
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

**2. llama-cpp-python lỗi compilation:**

```bash
# Trên Windows - PHẢI dùng x64 Native Tools Command Prompt
pip uninstall llama-cpp-python
pip install llama-cpp-python --force-reinstall --no-cache-dir

# Nếu vẫn lỗi, cài pre-built wheel
pip install llama-cpp-python --find-links https://github.com/abetlen/llama-cpp-python/releases
```

### 🔧 Advanced Troubleshooting

**Environment không tạo được:**

```bash
# Clear conda cache
conda clean --all

# Update conda
conda update -n base conda

# Retry creation
conda env create -f environment.yml --force
```

**Packages conflict:**

```bash
# Tạo environment minimal trước
conda create -n LegalRAG_minimal python=3.11

# Activate và install từng nhóm
conda activate LegalRAG_minimal

# Install core packages first
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
pip install transformers sentence-transformers
pip install langchain chromadb
pip install fastapi uvicorn
# ... tiếp tục với packages khác
```

## 📦 Các File Backup Chi Tiết

### 1. `environment.yml` (File chính)

- **Mô tả**: File conda environment hoàn chỉnh
- **Bao gồm**: Tất cả conda packages, pip packages, channels, dependencies
- **Ưu điểm**: Tái tạo environment y hệt, bao gồm cả version constraints
- **Cách dùng**: `conda env create -f environment.yml`

### 2. `conda-packages.txt`

- **Mô tả**: Danh sách packages theo format conda export
- **Cách dùng**:

```bash
conda create -n new_env python=3.11
conda install --file conda-packages.txt
```

### 3. `pip-requirements.txt`

- **Mô tả**: Danh sách pip packages với versions
- **Cách dùng**: `pip install -r pip-requirements.txt`
- **Lưu ý**: Chỉ dùng sau khi đã cài conda packages

## 🎯 Production Deployment Tips

### 🐳 Docker Deployment

```dockerfile
# Dockerfile example
FROM continuumio/miniconda3:latest

WORKDIR /app
COPY backend/environment/environment.yml .

# Create environment
RUN conda env create -f environment.yml

# Activate environment
SHELL ["conda", "run", "-n", "LegalRAG_v1", "/bin/bash", "-c"]

# Copy application
COPY backend/ .

# Install additional packages if needed
RUN conda run -n LegalRAG_v1 pip install -r requirements.txt

# Run application
CMD ["conda", "run", "-n", "LegalRAG_v1", "python", "main.py"]
```

### 🚀 CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Setup Conda Environment
  run: |
    conda env create -f backend/environment/environment.yml
    conda activate LegalRAG_v1
    python -c "import torch; print(torch.cuda.is_available())"
```

### 💻 Development vs Production

**Development Environment:**

- Sử dụng `environment.yml` trực tiếp
- Có thể cài thêm debug tools: `jupyter`, `pytest`, `black`

**Production Environment:**

- Cân nhắc tạo environment minimal với chỉ packages cần thiết
- Remove các dev dependencies
- Pin exact versions cho stability

## 📝 Ghi Chú Quan Trọng

### 🔑 Key Points

- **LUÔN** sử dụng x64 Native Tools Command Prompt trên Windows
- **GPU packages** (PyTorch, llama-cpp) cần cài trước các packages khác
- **Environment.yml** là method được khuyến nghị nhất
- **Test thoroughly** sau khi setup xong

### 🌟 Best Practices

1. **Backup regular**: Export environment.yml định kỳ khi có thay đổi lớn
2. **Version pinning**: Pin exact versions cho production
3. **Documentation**: Update guide này khi có thay đổi major
4. **Testing**: Always test critical imports sau khi setup

### 📞 Support

Nếu gặp vấn đề trong quá trình setup:

1. Kiểm tra log messages chi tiết
2. Verify system requirements
3. Check CUDA compatibility
4. Try manual installation cho problematic packages

---

**Created**: September 2025  
**Environment**: LegalRAG_v1 (Python 3.11.13)  
**CUDA**: 12.1  
**Packages**: 180+ AI/ML focused packages
