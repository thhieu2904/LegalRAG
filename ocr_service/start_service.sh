#!/bin/bash
# OCR Service Startup Script with Conda Environment Check
# Ensures correct conda environment is activated before starting service

set -e

ENV_NAME="ocr-microservice"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting OCR Microservice...${NC}"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Conda is not available in PATH${NC}"
    echo "Please install conda or activate conda environment manually:"
    echo "conda activate $ENV_NAME"
    exit 1
fi

# Check if correct environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "$ENV_NAME" ]]; then
    echo -e "${YELLOW}⚠️ Wrong conda environment active: $CONDA_DEFAULT_ENV${NC}"
    echo -e "${BLUE}🔄 Activating correct environment: $ENV_NAME${NC}"
    
    # Check if environment exists
    if ! conda env list | grep -q "^$ENV_NAME "; then
        echo -e "${RED}❌ Environment '$ENV_NAME' does not exist${NC}"
        echo "Please create it first:"
        echo "  conda env create -f environment.yml"
        echo "  or run: bash setup_environment.sh"
        exit 1
    fi
    
    # Activate environment
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
fi

echo -e "${GREEN}✅ Using conda environment: $CONDA_DEFAULT_ENV${NC}"

# Verify key dependencies
echo -e "${BLUE}🔍 Verifying dependencies...${NC}"
python -c "
try:
    import fastapi, uvicorn, cv2, torch, redis
    print('✅ Core dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    exit(1)
" || exit 1

# Check if Redis is running
echo -e "${BLUE}🔍 Checking Redis connection...${NC}"
python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=1)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'⚠️ Redis not available: {e}')
    print('Note: Service will start but caching will use fallback')
"

# Start the service
echo -e "${BLUE}🎯 Starting OCR service on port 8001...${NC}"
echo -e "${BLUE}📚 API Documentation: http://localhost:8001/docs${NC}"
echo -e "${BLUE}🏥 Health Check: http://localhost:8001/health${NC}"
echo ""

cd "$SCRIPT_DIR"
python main.py
