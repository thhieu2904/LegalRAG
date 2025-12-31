# Admin Service

Document management and ingestion orchestrator.

## Pipeline

1. Upload file to storage
2. Extract and chunk text
3. Embed chunks
4. Index vectors
5. Save metadata to database

## API

- `POST /upload` - Upload document
- `GET /documents` - List documents
- `DELETE /documents/{id}` - Delete document
