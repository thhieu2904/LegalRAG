# OCR Microservice Environment Setup

## Quick Setup

### Create and activate conda environment:

```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate ocr-microservice

# Verify installation
python -c "import fastapi, cv2, torch; print('✅ All dependencies installed successfully')"
```

### Alternative manual setup:

```bash
# Create environment
conda create -n ocr-microservice python=3.11 -y

# Activate
conda activate ocr-microservice

# Install dependencies
conda install -c conda-forge fastapi uvicorn opencv pillow numpy redis-py -y
conda install -c pytorch pytorch-cpu torchvision-cpu -y
pip install -r requirements.txt
```

## Environment Management

### Daily usage:

```bash
# Always activate before working
conda activate ocr-microservice

# Run service
python main.py

# Run tests
python test_structure.py
```

### Update environment:

```bash
# Export current environment
conda env export > environment.yml

# Update from file
conda env update -f environment.yml --prune
```

### Clean installation:

```bash
# Remove environment
conda env remove -n ocr-microservice

# Recreate from scratch
conda env create -f environment.yml
```

## Environment Verification

Run this to verify your setup:

```python
import sys
print(f"Python: {sys.version}")

import fastapi
print(f"FastAPI: {fastapi.__version__}")

import cv2
print(f"OpenCV: {cv2.__version__}")

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

import redis
print(f"Redis: {redis.__version__}")

try:
    from vietocr.tool.predictor import Predictor
    print("✅ VietOCR: Available")
except ImportError:
    print("❌ VietOCR: Not installed - run 'pip install vietocr'")
```

## Production Notes

- This environment is optimized for **CPU-only** processing
- VietOCR will automatically use CPU backend
- PyTorch CPU version saves ~2GB compared to GPU version
- No CUDA dependencies needed for deployment
