# Vector Service

PostgreSQL pgvector-based vector search service for semantic similarity.

## API Endpoints

- `POST /insert` - Insert single vector
- `POST /insert-batch` - Insert multiple vectors
- `POST /search` - Search similar vectors
- `POST /delete` - Delete vectors
- `GET /count` - Get statistics
- `GET /health` - Health check
- `GET /docs` - FastAPI documentation
