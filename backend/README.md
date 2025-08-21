# LegalRAG Backend

## Overview

The LegalRAG backend provides AI-powered legal document search and question-answering capabilities for Vietnamese administrative procedures.

## Features

- **Smart Query Routing**: Automatic classification to appropriate document collections
- **Vector Search**: Semantic search across legal documents using Vietnamese embeddings
- **Form Integration**: Automatic detection and attachment of relevant forms
- **CRUD Operations**: Full router question management
- **Multi-collection Support**: Organized by procedure types

## Quick Start

### 1. Environment Setup

```bash
# Create conda environment
conda create -n LegalRAG_v1 python=3.11
conda activate LegalRAG_v1

# Install dependencies
pip install -r requirements.txt
```

### 2. Model Setup

```bash
python tools/1_setup_models.py
```

### 3. Build Vector Database

```bash
python tools/2_build_vectordb_modernized.py --force
```

### 4. Start API Server

```bash
python main.py
```

The API will be available at http://localhost:8000

## Document Structure

```
data/storage/collections/
├── quy_trinh_cap_ho_tich_cap_xa/    # Civil registration procedures
├── quy_trinh_chung_thuc/            # Notarization procedures
└── quy_trinh_nuoi_con_nuoi/         # Adoption procedures
```

Each document directory contains:

- `.json` - RAG content (indexed)
- `.doc` - Original document
- `router_questions.json` - Routing questions
- `forms/` - Related forms

## API Endpoints

### Query

- `POST /api/v1/query` - Submit questions and get answers
- `GET /api/v1/session/{id}` - Get session information

### Router CRUD

- `GET /api/v1/router/collections` - List collections
- `GET /api/v1/router/collections/{name}` - Get collection details
- `POST /api/v1/router/questions` - Add new questions
- `PUT /api/v1/router/questions/{id}` - Update questions
- `DELETE /api/v1/router/questions/{id}` - Delete questions

## Performance

- **Documents**: 53 across 3 collections
- **Router Questions**: 1,133 with cached embeddings
- **Startup Time**: ~3 seconds (with cache)
- **Query Time**: ~1-3 seconds average

## Architecture

- **Embedding**: CPU (VRAM optimized)
- **LLM**: GPU (PhoGPT-4B-Chat)
- **Reranker**: GPU (Vietnamese Reranker)
- **Vector DB**: ChromaDB
- **Cache**: Pickle-based with metadata versioning
