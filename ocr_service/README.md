# OCR Service

Vietnamese CCCD (Căn cước công dân) OCR Processing Service - Independent microservice for optical character recognition and data extraction from Vietnamese identity cards.

## 🎯 Features

- **Vietnamese CCCD Recognition**: Specialized OCR for Vietnamese citizen ID cards
- **CPU-Optimized Processing**: Efficient processing using CPU-only VietOCR models
- **Dual-Side Processing**: Support for both front and back sides of CCCD
- **Session Management**: Redis-based session tracking with automatic cleanup
- **Real-time Processing**: Asynchronous OCR processing with status tracking
- **Structured Data Extraction**: Extracts specific fields with confidence scores
- **Microservice Architecture**: Independent service with HTTP API communication
- **Image Preprocessing**: Advanced image enhancement for better OCR accuracy
- **Health Monitoring**: Comprehensive health checks and service statistics

## 🏗️ Architecture

```
OCR Microservice (Port 8001)
├── FastAPI Application
├── VietOCR Engine (CPU-optimized)
├── Redis Cache (DB 1)
├── Image Processing Pipeline
└── RESTful API Endpoints
```

## 📦 Installation

### Prerequisites

- Python 3.11+
- Conda (Miniconda or Anaconda)
- Redis Server
- Docker & Docker Compose (optional)

### Conda Environment Setup (Recommended)

**The OCR microservice uses a dedicated conda environment for complete isolation:**

1. **Quick setup with script:**

```bash
# Windows
setup_environment.bat

# Linux/MacOS
bash setup_environment.sh
```

2. **Manual conda setup:**

```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate ocr-microservice

# Verify installation
python -c "import fastapi, cv2, torch; print('✅ Dependencies ready')"
```

3. **Daily usage:**

```bash
# Always activate before working
conda activate ocr-microservice

# Start OCR service
python main.py

# Deactivate when done
conda deactivate
```

### Why Separate Conda Environment?

- ✅ **Complete isolation** from other projects (including RAG engine)
- ✅ **No dependency conflicts** between OCR and RAG services
- ✅ **CPU-optimized packages** (PyTorch CPU, no CUDA overhead)
- ✅ **Easier deployment** and containerization
- ✅ **Independent version management**

### Using Docker (Recommended)

1. **Clone and navigate to OCR service directory:**

```bash
cd ocr-service
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env file with your configuration
```

3. **Start services:**

```bash
docker-compose up -d
```

4. **Verify installation:**

```bash
curl http://localhost:8001/health
```

### Manual Installation

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Start Redis server:**

```bash
redis-server
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env file
```

4. **Run the service:**

```bash
python main.py
```

## 🔧 Configuration

### Environment Variables

| Variable               | Default                     | Description             |
| ---------------------- | --------------------------- | ----------------------- |
| `HOST`                 | `0.0.0.0`                   | Service host            |
| `PORT`                 | `8001`                      | Service port            |
| `REDIS_HOST`           | `localhost`                 | Redis server host       |
| `REDIS_PORT`           | `6379`                      | Redis server port       |
| `REDIS_DB`             | `1`                         | Redis database number   |
| `TORCH_CPU_THREADS`    | `4`                         | CPU threads for PyTorch |
| `MAX_IMAGE_SIZE_MB`    | `10`                        | Maximum image size      |
| `SESSION_EXPIRY_HOURS` | `2`                         | Session expiration time |
| `CORS_ORIGINS`         | `http://localhost:3000,...` | Allowed CORS origins    |

### Service Configuration

The service uses CPU-optimized VietOCR models with the following optimizations:

- Single batch processing
- Disabled beam search for speed
- Memory-efficient image preprocessing
- Async processing with background tasks

## 📡 API Endpoints

### Core Endpoints

| Method   | Endpoint                        | Description            |
| -------- | ------------------------------- | ---------------------- |
| `GET`    | `/`                             | Service information    |
| `GET`    | `/health`                       | Health check           |
| `POST`   | `/api/v1/sessions`              | Create new session     |
| `POST`   | `/api/v1/sessions/{id}/upload`  | Upload image           |
| `POST`   | `/api/v1/sessions/{id}/process` | Start OCR processing   |
| `GET`    | `/api/v1/sessions/{id}/results` | Get processing results |
| `GET`    | `/api/v1/sessions/{id}/status`  | Get session status     |
| `DELETE` | `/api/v1/sessions/{id}`         | Delete session         |

### Utility Endpoints

| Method | Endpoint                      | Description                    |
| ------ | ----------------------------- | ------------------------------ |
| `POST` | `/api/v1/upload-and-process`  | Upload and process in one call |
| `GET`  | `/api/v1/stats`               | Service statistics             |
| `POST` | `/api/v1/maintenance/cleanup` | Manual cleanup                 |

## 💻 Usage Examples

### 1. Basic OCR Processing

```python
import requests
import base64

# Create session
response = requests.post('http://localhost:8001/api/v1/sessions')
session_id = response.json()['session']['session_id']

# Upload front side image
with open('cccd_front.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

upload_data = {
    "side": "front",
    "image_data": image_data,
    "image_format": "jpeg"
}
requests.post(f'http://localhost:8001/api/v1/sessions/{session_id}/upload', json=upload_data)

# Start processing
process_data = {"process_both_sides": False}
requests.post(f'http://localhost:8001/api/v1/sessions/{session_id}/process', json=process_data)

# Get results
results = requests.get(f'http://localhost:8001/api/v1/sessions/{session_id}/results')
print(results.json())
```

### 2. Both Sides Processing

```python
# Upload both sides and process
session_data = {"expires_in_hours": 4}
session = requests.post('http://localhost:8001/api/v1/sessions', json=session_data)
session_id = session.json()['session']['session_id']

# Upload front side
front_data = {"side": "front", "image_data": front_image_b64}
requests.post(f'http://localhost:8001/api/v1/sessions/{session_id}/upload', json=front_data)

# Upload back side
back_data = {"side": "back", "image_data": back_image_b64}
requests.post(f'http://localhost:8001/api/v1/sessions/{session_id}/upload', json=back_data)

# Process both sides
process_data = {"process_both_sides": True}
requests.post(f'http://localhost:8001/api/v1/sessions/{session_id}/process', json=process_data)
```

### 3. Convenience API

```python
# Upload and process in one call
upload_process_data = {
    "side": "front",
    "image_data": image_b64,
    "process_both_sides": False
}
result = requests.post('http://localhost:8001/api/v1/upload-and-process', json=upload_process_data)
```

## 📊 Response Format

### Extracted Data Structure

```json
{
  "success": true,
  "session_id": "uuid",
  "processing_status": "completed",
  "extracted_data": {
    "id_number": "012345678901",
    "full_name": "NGUYEN VAN A",
    "date_of_birth": "01/01/1990",
    "gender": "Nam",
    "nationality": "Việt Nam",
    "hometown": "Hà Nội, Việt Nam",
    "residence": "123 Phố ABC, Quận XYZ, Hà Nội",
    "issue_date": "01/01/2020",
    "expiry_date": "01/01/2030",
    "issued_by": "Cục Cảnh sát QLHC về TTXH"
  },
  "confidence_scores": {
    "id_number": 0.95,
    "full_name": 0.92,
    "date_of_birth": 0.88,
    "overall_confidence": 0.89
  },
  "processing_time": 12.5
}
```

## 🔍 Monitoring

### Health Check

```bash
curl http://localhost:8001/health
```

### Service Statistics

```bash
curl http://localhost:8001/api/v1/stats
```

### Redis Monitoring

Access Redis Commander at `http://localhost:8082` (in development mode)

## 🐳 Docker Configuration

### Production Deployment

```yaml
version: "3.8"
services:
  ocr-service:
    image: your-registry/ocr-service:latest
    ports:
      - "8001:8001"
    environment:
      - REDIS_HOST=redis-prod
      - DEBUG=false
    depends_on:
      - redis-prod
```

### Scaling

```bash
docker-compose up --scale ocr-service=3
```

## 🔧 Development

### Project Structure

```
ocr-service/
├── app/
│   ├── api/                 # API routes
│   ├── core/                # Core configuration
│   ├── models/              # Data models
│   └── services/            # Business logic
├── data/                    # Data storage
├── cache/                   # Cache directory
├── main.py                  # Application entry point
├── requirements.txt         # Dependencies
├── Dockerfile              # Container definition
└── docker-compose.yml      # Local development
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
black app/
isort app/
flake8 app/
mypy app/
```

## 📈 Performance

### Benchmarks

- **Average processing time**: 8-15 seconds per CCCD
- **CPU usage**: 60-80% during processing
- **Memory usage**: ~2GB with model loaded
- **Concurrent sessions**: Up to 10 simultaneous
- **Accuracy**: 85-95% depending on image quality

### Optimization Tips

1. **Image Quality**: Higher quality images yield better results
2. **Preprocessing**: Images are automatically enhanced
3. **CPU Cores**: Increase `TORCH_CPU_THREADS` for better performance
4. **Memory**: Ensure sufficient RAM for model loading
5. **Redis**: Use Redis persistence for production

## 🚨 Troubleshooting

### Common Issues

1. **Model Loading Fails**

   ```bash
   # Check PyTorch CPU installation
   python -c "import torch; print(torch.version)"
   ```

2. **Redis Connection Error**

   ```bash
   # Test Redis connectivity
   redis-cli -h localhost -p 6379 ping
   ```

3. **Memory Issues**

   ```bash
   # Monitor memory usage
   docker stats ocr-service
   ```

4. **OCR Accuracy Low**
   - Check image quality and resolution
   - Ensure proper lighting in source images
   - Verify CCCD is not damaged or obscured

### Logs

```bash
# View service logs
docker-compose logs -f ocr-service

# View Redis logs
docker-compose logs -f redis-ocr
```

## 🔐 Security

### Production Considerations

1. **API Authentication**: Add API key authentication
2. **Rate Limiting**: Implement request rate limiting
3. **Input Validation**: Validate image sizes and formats
4. **Data Encryption**: Encrypt sensitive data in Redis
5. **Network Security**: Use HTTPS and secure networks

### Environment Security

```bash
# Set secure Redis password
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> .env

# Use secrets management in production
# Docker secrets, Kubernetes secrets, etc.
```

## 📝 License

This project is part of the LegalRAG OCR system. See main project LICENSE file.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: See `/docs` endpoint when service is running
- **Health Check**: `/health` endpoint for service status

## 🔄 Changelog

### v1.0.0

- Initial release
- Vietnamese CCCD OCR support
- CPU-optimized processing
- Redis session management
- Docker containerization
- RESTful API
- Health monitoring
