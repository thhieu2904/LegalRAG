# LegalRAG Microservices Architecture

Complete implementation of a modern legal document RAG system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                          │
│                         Port 3000                                   │
└────────────┬──────────────────────┬──────────────────────┬──────────┘
             │                      │                      │
      ┌──────▼─────┐         ┌──────▼──────┐        ┌──────▼──────┐
      │   Query    │         │  Admin      │        │ Identifill  │
      │  Service   │         │  Service    │        │  Service    │
      │  Port 8005 │         │  Port 8007  │        │  Port 8002  │
      └────┬──────┘         └──┬────┬─────┘        └──────┬──────┘
           │                   │    │                     │
      ┌────┴───────────────────┴─┬──┴─────────┐          │
      │                          │            │          │
  ┌───▼────┐  ┌──────────┐  ┌───▼───┐  ┌────▼────┐     │
  │Embedding│  │ Vector   │  │Storage │  │   LLM   │     │
  │ Service │  │ Service  │  │Service │  │ Service │     │
  │Port 8004│  │Port 8003 │  │Port8001│  │Port 8006│     │
  └────┬────┘  └────┬─────┘  └──┬─────┘  └────┬────┘     │
       │            │           │             │           │
       │ ┌──────────┴───────────┴─────────────┘           │
       │ │                                                 │
    ┌──▼─▼──────────────────────────────────┐    ┌────────▼────┐
    │        CCCD SCAN SERVICE               │    │   (unused)  │
    │  (Optional External Integration)       │    │   Scanner   │
    └───────────────────────────────────────┘    └─────────────┘
       │            │           │             │
    ┌──▼────────────┴────┬──────▼──────┬──────▼────────┐
    │                    │             │               │
┌───▼──────┐  ┌──────────▼───┐  ┌─────▼──────┐  ┌────▼────────┐
│  MinIO   │  │  PostgreSQL  │  │   pgvector │  │  Models     │
│  S3-like │  │  Database    │  │  Extension │  │  (Cached)   │
│  Storage │  │  Port 5432   │  │  (Indexes) │  │             │
└──────────┘  └──────────────┘  └────────────┘  └─────────────┘
```

## Service Components

### 1. **Storage Service** (Port 8001)

- **Purpose**: MinIO wrapper for file operations
- **Functions**: Upload, download, list, delete, extract text from PDFs
- **Tech Stack**: FastAPI, MinIO, PyPDF2
- **Key Endpoints**:
  - `POST /upload` - Upload file
  - `GET /download` - Download file
  - `GET /list` - List files in document
  - `GET /extract-text` - Extract text from PDF

### 2. **Vector Service** (Port 8003)

- **Purpose**: PostgreSQL pgvector operations for semantic search
- **Functions**: Insert vectors, search by similarity, delete, count
- **Tech Stack**: FastAPI, PostgreSQL (pgvector), psycopg2
- **Key Endpoints**:
  - `POST /insert` - Insert single vector
  - `POST /insert-batch` - Batch insert vectors
  - `POST /search` - Vector similarity search
  - `DELETE /delete` - Delete vectors
  - `GET /count` - Get statistics

### 3. **Embedding Service** (Port 8004)

- **Purpose**: Text embedding using local ML model
- **Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Dimension**: 384-dimensional vectors
- **Tech Stack**: FastAPI, sentence-transformers, torch
- **Key Endpoints**:
  - `POST /embed` - Embed single text
  - `POST /embed-batch` - Batch embed texts

### 4. **LLM Service** (Port 8006)

- **Purpose**: Text generation using local LLM
- **Models**: Gemma 2 9B (default) or Llama 3.1 8B
- **Requirements**: NVIDIA GPU (12GB+ VRAM)
- **Tech Stack**: FastAPI, transformers, torch, CUDA
- **Key Endpoints**:
  - `POST /generate` - Generate text from prompt

### 5. **Query Service** (Port 8005)

- **Purpose**: RAG orchestrator - coordinate all services for Q&A
- **Pipeline**: Embed question → Vector search → Build context → LLM generation
- **Tech Stack**: FastAPI, httpx (async HTTP)
- **Key Endpoints**:
  - `POST /query` - Ask question and get answer with sources

### 6. **Admin Service** (Port 8007)

- **Purpose**: Document management and ingestion orchestration
- **Pipeline**: Upload → Extract → Chunk → Embed → Index → Save metadata
- **Tech Stack**: FastAPI, psycopg2
- **Key Endpoints**:
  - `POST /upload` - Upload and process document
  - `GET /documents` - List documents
  - `DELETE /documents/{id}` - Delete document

### 7. **Identifill Service** (Port 8002)

- **Purpose**: CCCD (Vietnamese ID card) scanning and data extraction
- **Status**: Existing service, minimal changes needed
- **Tech Stack**: Python, OpenCV, TensorFlow/PyTorch

## Data Flow Examples

### Example 1: Document Upload & Ingestion

```
User uploads PDF
     ↓
Admin Service receives file
     ↓
→ Storage Service: Upload file to MinIO
   ├ Returns file_id and storage path
   ├ Extracts text from PDF
   └ Returns text content
     ↓
Admin Service chunks text (500 chars, 50 overlap)
     ↓
→ Embedding Service: Embed all chunks (384-dim vectors)
   ├ Batch processes (32 chunks at a time)
   └ Returns embeddings list
     ↓
→ Vector Service: Insert vectors + metadata into PostgreSQL
   ├ Creates HNSW index
   ├ Stores chunk content, document_id, similarity searchable
   └ Returns vector count
     ↓
Admin Service saves document metadata to database
     ↓
✅ Document ready for queries
```

### Example 2: Legal Document Query (RAG)

```
User asks: "Quyền sở hữu được định nghĩa như thế nào?"
     ↓
Query Service receives question
     ↓
→ Embedding Service: Embed question (384-dim vector)
     ↓
Query Service gets embedding result
     ↓
→ Vector Service: Search top-K similar chunks (top_k=10)
   ├ Uses cosine distance similarity
   ├ Returns: chunk content + similarity score
   ├ Filters by threshold (0.7)
   └ Returns: [chunk1, chunk2, ..., chunk10]
     ↓
Query Service builds context:
   "Based on your documents:
    - Source 1 (0.92): [chunk content]
    - Source 2 (0.87): [chunk content]
    ..."
     ↓
→ LLM Service: Generate answer from context + question
   ├ Prompt: "Based on these sources, answer: [question]"
   ├ Returns: AI-generated answer
   └ Token count: 256 prompt + 128 response
     ↓
Query Service returns to user:
{
  "answer": "Quyền sở hữu là...",
  "sources": [
    {"content": "...", "similarity": 0.92},
    {"content": "...", "similarity": 0.87}
  ],
  "token_count": {"prompt": 256, "response": 128}
}
```

## Technology Stack

### Core Services

- **Framework**: FastAPI (async HTTP server)
- **Language**: Python 3.11
- **Container**: Docker + Docker Compose

### Data Layer

- **Object Storage**: MinIO (S3-compatible)
- **Vector Database**: PostgreSQL + pgvector extension
- **Indexing**: HNSW (Hierarchical Navigable Small World)

### ML Models (Local)

- **Embedding**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - 384-dimensional vectors
  - Multilingual support (Vietnamese + 50+ languages)
  - Lightweight (22MB model size)
  - CPU/GPU compatible
- **LLM**: Gemma 2 9B or Llama 3.1 8B
  - ~9B parameters
  - Instruction-tuned for Q&A
  - Requires NVIDIA GPU (12GB+ VRAM)
  - Temperature-controlled sampling

### Frontend

- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **Build**: Vite
- **Port**: 3000

## Port Allocation

```
Infrastructure:
  MinIO API        → 9000
  MinIO Console    → 9001
  PostgreSQL       → 5432

Services:
  Storage          → 8001
  Identifill       → 8002
  Vector           → 8003
  Embedding        → 8004
  Query            → 8005
  LLM              → 8006
  Admin            → 8007

Frontend:
  React App        → 3000
```

## Database Schema

### documents

```sql
id UUID PRIMARY KEY
filename VARCHAR
status VARCHAR (uploading, processing, completed, failed)
created_at TIMESTAMP
updated_at TIMESTAMP
is_deleted BOOLEAN
```

### chunks

```sql
id UUID PRIMARY KEY
document_id UUID (references documents)
chunk_index INT
content TEXT
embedding pgvector(384) -- Indexed with HNSW
created_at TIMESTAMP
```

### users

```sql
cccd_id VARCHAR PRIMARY KEY
full_name VARCHAR
dob DATE
gender VARCHAR
address TEXT
created_at TIMESTAMP
```

### forms

```sql
id UUID PRIMARY KEY
user_id VARCHAR (references users)
document_id UUID (references documents)
form_type VARCHAR
filled_data JSONB
created_at TIMESTAMP
```

## Performance Characteristics

### Embedding (sentence-transformers)

- Model size: 22MB
- Inference time: ~5ms per text (CPU)
- Batch size: 32 (configurable)
- Memory: ~500MB RAM (CPU)

### Vector Search (pgvector + HNSW)

- Index size: ~500MB for 50K vectors
- Search time: ~10-50ms for top-K=10
- Scalability: Tested up to 1M vectors

### LLM Generation (Gemma 2 9B)

- Model size: 18GB (VRAM)
- Inference time: ~2-5 seconds per query
- Memory: 12GB+ VRAM required
- Throughput: 1-2 queries/second

## Deployment Scenarios

### Development (Current)

- Docker Compose on local machine
- CPU embeddings, GPU LLM (optional)
- Direct port exposure (no proxy)
- Single replica of each service

### Staging

- Kubernetes cluster (optional)
- Health checks and auto-restart
- Persistent volumes for models
- Service mesh for observability

### Production

- Kubernetes or container orchestration
- Kong Gateway API proxy
- Load balancer for scale
- Separate infra for embeddings (CPU) and LLM (GPU)
- Monitoring and logging (Prometheus, ELK)
- Backup and disaster recovery

## Future Enhancements

1. **Async Job Processing**

   - Queue service for large document uploads
   - Background workers for batch processing
   - Progress tracking

2. **Advanced Search**

   - Hybrid search (semantic + keyword)
   - Filter by metadata (date, author, category)
   - Faceted search

3. **Multi-language Support**

   - Language detection
   - Per-document language model
   - Cross-language search

4. **Fine-tuning**

   - Domain-specific embedding model
   - Specialized legal document LLM
   - Custom chunking strategies

5. **API Gateway**

   - Kong Gateway (optional, currently skipped)
   - Rate limiting and authentication
   - API versioning

6. **Monitoring & Observability**
   - Service metrics (Prometheus)
   - Distributed tracing (Jaeger)
   - Logging aggregation (ELK)
   - Performance dashboards (Grafana)

---

**For setup instructions, see QUICKSTART.md**
**For API integration guide, see FRONTEND_API_INTEGRATION.md**
