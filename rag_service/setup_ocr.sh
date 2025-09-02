#!/bin/bash

echo "🚀 Setting up OCR microservice..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the backend directory"
    exit 1
fi

print_status "Installing Python dependencies..."

# Install OCR-specific dependencies
print_status "Installing OCR dependencies..."
pip install vietocr==0.3.12
pip install opencv-python==4.10.0.84
pip install imutils==0.5.4
pip install redis==5.2.1
pip install aioredis==2.0.1
pip install python-decouple==3.8

# Install all requirements
pip install -r requirements.txt

print_success "Python dependencies installed"

# Check if Redis is installed
print_status "Checking Redis installation..."
if command -v redis-server &> /dev/null; then
    print_success "Redis is already installed"
else
    print_warning "Redis is not installed. Please install Redis:"
    echo "  - On Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  - On macOS: brew install redis"
    echo "  - On Windows: Use Docker or WSL"
    echo "  - Or use Docker Compose (recommended)"
fi

# Check if Docker is available
if command -v docker &> /dev/null; then
    print_success "Docker is available"
    print_status "You can use Docker Compose to run Redis:"
    echo "  docker-compose -f docker-compose-ocr.yml up -d redis-ocr"
else
    print_warning "Docker not found. Consider installing Docker for easier Redis setup"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p data/cache
mkdir -p logs
mkdir -p debug_images

# Set up environment file
if [ ! -f ".env.ocr" ]; then
    print_error ".env.ocr file not found!"
    exit 1
fi

print_status "Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.ocr .env
    print_success "Environment file created from .env.ocr"
else
    print_warning ".env file already exists. You may need to merge OCR settings manually"
fi

print_success "OCR microservice setup completed!"

echo ""
print_status "Next steps:"
echo "1. Start Redis server:"
echo "   - Local: redis-server"
echo "   - Docker: docker-compose -f docker-compose-ocr.yml up -d redis-ocr"
echo ""
echo "2. Start the backend server:"
echo "   python main.py"
echo ""
echo "3. Access OCR endpoints at:"
echo "   - Upload: POST http://localhost:8000/api/ocr/upload-image"
echo "   - Process: POST http://localhost:8000/api/ocr/process/{session_id}"
echo "   - Results: GET http://localhost:8000/api/ocr/results/{session_id}"
echo "   - Health: GET http://localhost:8000/api/ocr/health"
echo ""
echo "4. Access API documentation:"
echo "   http://localhost:8000/docs"
echo ""

print_status "Troubleshooting:"
echo "- If VietOCR fails to install, try: pip install --no-deps vietocr"
echo "- If Redis connection fails, check REDIS_HOST and REDIS_PORT in .env"
echo "- Check logs in the console for detailed error messages"
