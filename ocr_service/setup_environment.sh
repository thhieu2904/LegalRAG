#!/bin/bash
# OCR Microservice Environment Setup Script
# Creates and configures conda environment for OCR processing

set -e  # Exit on error

echo "🚀 Setting up OCR Microservice Conda Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment name
ENV_NAME="ocr-microservice"

echo -e "${BLUE}📋 Environment Configuration:${NC}"
echo "  - Name: $ENV_NAME"
echo "  - Python: 3.11"
echo "  - Purpose: Vietnamese CCCD OCR Processing"
echo "  - Backend: CPU-optimized (no GPU required)"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Conda is not installed or not in PATH${NC}"
    echo "Please install Miniconda or Anaconda first:"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo -e "${BLUE}🔍 Checking existing environment...${NC}"
if conda env list | grep -q "^$ENV_NAME "; then
    echo -e "${YELLOW}⚠️ Environment '$ENV_NAME' already exists${NC}"
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️ Removing existing environment...${NC}"
        conda env remove -n $ENV_NAME -y
    else
        echo -e "${BLUE}ℹ️ Using existing environment${NC}"
        conda activate $ENV_NAME
        exit 0
    fi
fi

echo -e "${BLUE}📦 Creating conda environment from environment.yml...${NC}"
if [ -f "environment.yml" ]; then
    conda env create -f environment.yml
else
    echo -e "${YELLOW}⚠️ environment.yml not found, creating manually...${NC}"
    
    # Create basic environment
    conda create -n $ENV_NAME python=3.11 -y
    
    # Activate environment
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
    
    # Install conda packages
    echo -e "${BLUE}📦 Installing conda packages...${NC}"
    conda install -c conda-forge -y \
        fastapi uvicorn python-multipart \
        pydantic redis-py \
        opencv pillow numpy \
        transformers scikit-learn \
        regex python-dotenv click rich \
        httpx psutil pytest black isort
    
    # Install PyTorch CPU
    echo -e "${BLUE}🔥 Installing PyTorch (CPU-only)...${NC}"
    conda install -c pytorch pytorch-cpu torchvision-cpu -y
    
    # Install pip packages
    echo -e "${BLUE}📦 Installing pip packages...${NC}"
    pip install pydantic-settings aioredis vietocr unidecode langdetect \
                python-jose[cryptography] passlib[bcrypt] orjson \
                python-dateutil aiofiles
fi

echo -e "${GREEN}✅ Environment created successfully!${NC}"

# Activate the environment for verification
echo -e "${BLUE}🧪 Activating environment and running verification...${NC}"
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

# Verification script
python << EOF
import sys
print(f"🐍 Python: {sys.version.split()[0]}")

try:
    import fastapi
    print(f"🌐 FastAPI: {fastapi.__version__}")
except ImportError:
    print("❌ FastAPI not found")

try:
    import cv2
    print(f"🎥 OpenCV: {cv2.__version__}")
except ImportError:
    print("❌ OpenCV not found")

try:
    import torch
    print(f"🔥 PyTorch: {torch.__version__} (CPU: {not torch.cuda.is_available()})")
except ImportError:
    print("❌ PyTorch not found")

try:
    import redis
    print(f"💾 Redis: {redis.__version__}")
except ImportError:
    print("❌ Redis not found")

try:
    from vietocr.tool.predictor import Predictor
    print("🇻🇳 VietOCR: Available")
except ImportError:
    print("❌ VietOCR: Not installed")

print(f"\n✅ Environment '{ENV_NAME}' is ready!")
EOF

echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "  1. Activate environment: ${YELLOW}conda activate $ENV_NAME${NC}"
echo "  2. Start OCR service: ${YELLOW}python main.py${NC}"
echo "  3. Run tests: ${YELLOW}python test_structure.py${NC}"
echo "  4. View API docs: ${YELLOW}http://localhost:8001/docs${NC}"
echo ""
echo -e "${BLUE}💡 Usage tips:${NC}"
echo "  - Always activate the environment before working on OCR service"
echo "  - Use 'conda deactivate' to exit the environment"
echo "  - Update dependencies with: conda env update -f environment.yml"
echo ""
