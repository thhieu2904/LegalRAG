# LegalRAG - Refactored Microservices Architecture

## 🎯 Overview

LegalRAG is a Retrieval-Augmented Generation (RAG) system for Vietnamese legal documents, refactored from monolithic to microservices architecture.

### Key Features

- 📄 **Document Management**: Upload, process, and manage legal documents
- 🔍 **Semantic Search**: Vector-based similarity search using pgvector
- 🤖 **AI Q&A**: Local LLM-powered question answering (Gemma/Llama)
- 🆔 **CCCD Scanning**: Vietnamese ID card scanning and parsing
- 📝 **Form Management**: Legal document form generation and management

## 🏗️ Architecture

### Services Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Port 3000)                   │
│                     React + TypeScript                       │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ HTTP REST APIs
                │
    ┌───────────┼───────────────────┬─────────────────────┐
    │           │                   │                     │
┌───▼────┐  ┌──▼───┐  ┌─────▼─────┐  ┌──────▼─────────┐
│ Query  │  │Admin │  │Identifill │  │    Storage     │
│ :8005  │  │:8007 │  │   :8002   │  │     :8001      │
└────┬───┘  └──┬───┘  └───────────┘  └────────┬───────┘
     │         │                               │
     │         │                               │
┌────▼─────────▼──────────┐           ┌───────▼────────┐
│    Orchestration Layer  │           │  MinIO Storage │
│  Embedding + Vector +   │           │    (Port 9000) │
│    LLM Services         │           └────────────────┘
└─────────┬───────────────┘
          │
    ┌─────┼──────────────┐
    │     │              │
┌───▼──┐ ┌▼────┐  ┌─────▼─┐
│Vector│ │Embed│  │  LLM  │
│:8003 │ │:8004│  │ :8006 │
└──┬───┘ └─────┘  └───────┘
   │
┌──▼────────────────┐
│  PostgreSQL       │
│  + pgvector       │
│  (Port 5432)      │
└───────────────────┘
```

### Port Allocation

| Service              | Port | Description            |
| -------------------- | ---- | ---------------------- |
| **Infrastructure**   |
| PostgreSQL           | 5432 | Database with pgvector |
| MinIO API            | 9000 | S3-compatible storage  |
| MinIO Console        | 9001 | Web UI for MinIO       |
| **Backend Services** |
| Storage Service      | 8001 | File upload/download   |
| Identifill Service   | 8002 | CCCD scanning          |
| Vector Service       | 8003 | Vector search          |
| Embedding Service    | 8004 | Text embeddings        |
| Query Service        | 8005 | Q&A orchestration      |
| LLM Service          | 8006 | Text generation        |
| Admin Service        | 8007 | Document management    |
| **Frontend**         |
| React App            | 3000 | Web interface          |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU (for LLM service)
- 16GB+ RAM recommended
- 50GB+ disk space (for models)

### 1. Clone Repository

```bash
git clone https://github.com/thhieu2904/LegalRAG.git
cd LegalRAG
```

### 2. Download Models

**Embedding Model:**

```bash
# Download sentence-transformers model
mkdir -p embedding-service/models
cd embedding-service/models
# Model will auto-download on first run
```

**LLM Model:**

```bash
# Download Gemma 2 9B or Llama 3.1 8B
mkdir -p llm-service/models
cd llm-service/models
# Use huggingface-cli or manual download
huggingface-cli download google/gemma-2-9b-it
```

### 3. Start Services

```bash
# Start all services
docker compose up --build

# Or start specific services
docker compose up postgres-vector minio storage-service vector-service
```

### 4. Initialize Database

Database schema will be automatically created on first run via `schema.sql`.

### 5. Access Services

- **Frontend**: http://localhost:3000
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)
- **Query API**: http://localhost:8005/docs
- **Admin API**: http://localhost:8007/docs

## 📁 Project Structure

```
LegalRAG/
├── docker-compose.yml           # Main orchestration
├── schema.sql                   # Database schema
│
├── frontend/                    # React application
│   ├── src/
│   └── Dockerfile
│
├── storage-service/             # MinIO wrapper
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
│
├── vector-service/              # pgvector operations
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
│
├── embedding-service/           # Local embeddings
│   ├── src/
│   ├── models/                  # Downloaded models
│   ├── Dockerfile
│   └── requirements.txt
│
├── llm-service/                 # Local LLM
│   ├── src/
│   ├── models/                  # Downloaded models
│   ├── Dockerfile
│   └── requirements.txt
│
├── query-service/               # RAG orchestrator
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
│
├── admin-service/               # Document management
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
│
└── identifill-service/          # CCCD scanning
    ├── app/
    ├── Dockerfile
    └── requirements.txt
```

## 🔧 Configuration

### Environment Variables

Each service has its own configuration. Key variables:

**Storage Service** (`storage-service/.env`):

```env
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=legal-documents
```

**Vector Service** (`vector-service/.env`):

```env
POSTGRES_HOST=postgres-vector
POSTGRES_USER=legalrag
POSTGRES_PASSWORD=legalrag123
POSTGRES_DB=legalrag
```

**Embedding Service** (`embedding-service/.env`):

```env
MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
DEVICE=cpu  # or cuda
```

**LLM Service** (`llm-service/.env`):

```env
MODEL_NAME=google/gemma-2-9b-it
DEVICE=cuda  # requires GPU
MAX_LENGTH=2048
```

## 🧪 Testing

### Test Individual Services

```bash
# Test storage service
curl http://localhost:8001/health

# Test vector service
curl http://localhost:8003/health

# Test embedding service
curl -X POST http://localhost:8004/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Luật hôn nhân và gia đình"}'

# Test query service
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Độ tuổi kết hôn là bao nhiêu?"}'
```

### Run Full Pipeline Test

```bash
# 1. Upload document (Admin Service)
curl -X POST http://localhost:8007/documents/upload \
  -F "file=@sample.pdf"

# 2. Query document (Query Service)
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Nội dung chính của văn bản?"}'
```

## 📊 Monitoring

### Check Service Status

```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f query-service
docker compose logs -f llm-service

# Check resource usage
docker stats
```

### Database Stats

```sql
-- Connect to PostgreSQL
psql -h localhost -U legalrag -d legalrag

-- Check document stats
SELECT * FROM get_document_stats();

-- Check vector index
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'chunks';
```

## 🔄 Development

### Run Services Locally (without Docker)

```bash
# Start infrastructure only
docker compose up postgres-vector minio

# Run services locally
cd storage-service
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001

cd ../vector-service
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8003
```

### Hot Reload

Services are configured with volume mounts for development:

```yaml
volumes:
  - ./storage-service:/app # Code changes auto-reload
```

## 🚀 Deployment

### Production Considerations

1. **Remove development volumes** from docker-compose.yml
2. **Use secrets management** (e.g., Docker secrets, Vault)
3. **Add Kong Gateway** for API management (optional)
4. **Configure CORS** properly in each service
5. **Add authentication** middleware
6. **Set up logging** (ELK stack, CloudWatch)
7. **Configure auto-scaling** (Kubernetes, ECS)

### Docker Compose Production

```bash
# Build production images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📝 API Documentation

Each service exposes FastAPI automatic documentation:

- Storage: http://localhost:8001/docs
- Vector: http://localhost:8003/docs
- Embedding: http://localhost:8004/docs
- Query: http://localhost:8005/docs
- LLM: http://localhost:8006/docs
- Admin: http://localhost:8007/docs
- Identifill: http://localhost:8002/docs

## 🔐 Security

- **No authentication** in current version (development)
- **TODO**: Add JWT authentication via Kong Gateway or custom middleware
- **MinIO**: Change default credentials in production
- **PostgreSQL**: Use strong passwords and connection encryption
- **CORS**: Configure allowed origins per service

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit Pull Request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Based on architecture patterns from AICenter-RAG
- Uses open-source models: sentence-transformers, Gemma, Llama
- PostgreSQL pgvector extension
- MinIO object storage
- FastAPI framework

## 📞 Support

- **Issues**: https://github.com/thhieu2904/LegalRAG/issues
- **Discussions**: https://github.com/thhieu2904/LegalRAG/discussions
