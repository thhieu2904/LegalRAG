# Embedding Service

Vietnamese Document Embedding service với legal document chunking.

## Model

**dangvantuan/vietnamese-document-embedding**

- 📐 Dimension: **768**
- 📏 Max tokens: **8,192**
- 🇻🇳 Optimized for Vietnamese legal documents
- 🔗 [Hugging Face](https://huggingface.co/dangvantuan/vietnamese-document-embedding)

## Features

- 🔤 **Text embedding** - Convert text to 768-dim vectors
- 📦 **Batch embedding** - Process multiple texts efficiently
- 📄 **Legal document chunking** - Structure-aware chunking (Điều, Mục, Chương)
- 🔐 **Admin authentication** - Protected endpoints for document processing
- 🎯 **Token counting** - Accurate token counting using model tokenizer

## Endpoints

### Public (No Authentication)

1. **`POST /embed`** - Embed single text
2. **`POST /embed-batch`** - Embed multiple texts

### Admin (Requires X-API-Key)

3. **`POST /chunk-and-embed`** - Chunk document and create embeddings

## Quick Start

```bash
# Start service
docker compose up -d embedding-service

# Test
python test_embedding_service.py
```

See [full documentation](README.md) for details.
