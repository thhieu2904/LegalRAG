# Environment Deployment Guide

## Thông tin môi trường hiện tại

- **Environment Name**: LegalRAG_v1
- **Python Version**: 3.11.13
- **Environment Type**: Conda
- **Environment Path**: D:\env\conda\LegalRAG_v1

## Các file sao lưu được tạo

### 1. environment.yml

File này chứa toàn bộ cấu hình conda environment, bao gồm:

- Tất cả conda packages và versions
- Pip packages
- Python version
- Channel sources

**Cách sử dụng:**

```bash
# Tạo environment mới từ file
conda env create -f environment.yml

# Hoặc tạo với tên khác
conda env create -f environment.yml -n your_env_name
```

### 2. conda-packages.txt

File này chứa danh sách packages theo format conda export.

**Cách sử dụng:**

```bash
# Tạo environment mới
conda create -n new_env_name python=3.11

# Install packages từ file
conda install --file conda-packages.txt
```

### 3. pip-requirements.txt

File này chứa pip packages để backup thêm.

**Cách sử dụng:**

```bash
pip install -r pip-requirements.txt
```

## ⚠️ Lưu ý quan trọng về GPU Packages

**Hai thư viện sau cần được cài đặt trước tiên qua x64 Native Tools Command Prompt:**

### PyTorch với CUDA Support

```bash
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

### Llama-cpp-python

```bash
pip install llama-cpp-python
```

**Lý do:**

- Các thư viện này cần GPU/CUDA support
- Thường khó detect được ở terminal bình thường
- Cần x64 native environment để compile chính xác

## Quy trình deployment được khuyến nghị

### Bước 1: Cài đặt GPU packages trước

1. Mở **x64 Native Tools Command Prompt for VS**
2. Activate conda environment:
   ```bash
   conda activate your_env_name
   ```
3. Cài đặt PyTorch:
   ```bash
   conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
   ```
4. Cài đặt llama-cpp-python:
   ```bash
   pip install llama-cpp-python
   ```

### Bước 2: Restore từ environment file

```bash
# Option 1: Sử dụng environment.yml (khuyến nghị)
conda env create -f environment.yml

# Option 2: Sử dụng conda-packages.txt
conda create -n new_env_name python=3.11
conda install --file conda-packages.txt

# Option 3: Backup với pip
pip install -r pip-requirements.txt
```

### Bước 3: Verify installation

```bash
# Test PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Test llama-cpp-python
python -c "import llama_cpp; print('llama-cpp-python installed successfully')"
```

## Thông tin CUDA

- **CUDA Version**: 12.1
- **PyTorch CUDA**: 12.1
- **Packages liên quan**:
  - cuda-cccl=12.9.27
  - cuda-cudart=12.1.105
  - cuda-libraries=12.1.0
  - libcublas=12.1.0.26
  - pytorch-cuda=12.1

## Ghi chú thêm

- Environment này đã được tối ưu cho LegalRAG project
- Bao gồm các thư viện AI/ML: transformers, sentence-transformers, chromadb, langchain
- Có FastAPI, Streamlit cho web development
- Đã cài đặt các công cụ xử lý document: python-docx, lxml
