# LegalRAG Tools

## 4 Essential Tools for LegalRAG System Setup

### Overview

This directory contains 4 essential tools for setting up and maintaining the LegalRAG system. These tools should be run in order for a fresh installation.

> **⚡ Architecture Note**: Tool 2 has been consolidated from 2 separate components into 1 unified tool for simpler architecture.

---

## 🔧 Tool 1: Setup Models & Environment

**File:** `1_setup_models.py`

**Purpose:** Initialize the complete AI model environment

- Create required directory structure
- Download and verify Vietnamese embedding model (AITeamVN/Vietnamese_Embedding_v2)
- Download and verify Vietnamese reranker model (AITeamVN/Vietnamese_Reranker)
- Check LLM model availability (PhoGPT-4B-Chat)
- Test model functionality

**Usage:**

```bash
# Full setup with model downloads
python tools/1_setup_models.py

# Verify existing models only (no downloads)
python tools/1_setup_models.py --verify-only
```

**Requirements:**

- ~4.5GB free disk space for models
- Internet connection for downloads
- CUDA-compatible GPU recommended

---

## 📊 Tool 2: Build Vector Database (UNIFIED)

**File:** `2_build_vectordb_unified.py`

**Purpose:** Unified tool for JSON processing and vector database building

- Process JSON documents with integrated document processing
- Generate embeddings for all document chunks
- Create ChromaDB vector database with proper metadata
- Support context expansion through document_id and chunk_index_num
- Single tool replaces both document processing and database building steps

**Usage:**

```bash
# Build vector database from documents/
python tools/2_build_vectordb_unified.py

# Force rebuild (clear existing)
python tools/2_build_vectordb_unified.py --force

# Clean entire vectordb directory
python tools/2_build_vectordb_unified.py --clean
```

**Requirements:**

- Documents in `data/documents/` directory
- Models from Tool 1 already setup
- Sufficient RAM for embedding generation

---

## 🎯 Tool 3: Generate Smart Router

**File:** `3_generate_smart_router.py`

**Purpose:** Create intelligent query routing examples

- Generate advanced question templates with metadata-aware specificity
- Create smart filters with multi-dimensional filtering
- Extract key attributes from document metadata
- Generate priority scores for routing decisions

**Usage:**

```bash
# Generate smart router examples
python tools/3_generate_smart_router.py

# Force rebuild existing examples
python tools/3_generate_smart_router.py --force
```

**Output:** Smart router examples in `data/router_examples_smart/`

---

## ⚡ Tool 4: Build Router Cache

**File:** `4_build_router_cache.py`

**Purpose:** Pre-compute embeddings cache for fast router startup

- Load all router examples from `router_examples_smart/`
- Generate embeddings for questions and variants
- Save embeddings cache for instant router initialization
- Dramatically reduce server startup time

**Usage:**

```bash
# Build embeddings cache
python tools/4_build_router_cache.py

# Force rebuild cache
python tools/4_build_router_cache.py --force

# Allow model downloads if needed
python tools/4_build_router_cache.py --allow-download --force

# Verify existing cache only
python tools/4_build_router_cache.py --verify-only

# Clean incomplete model downloads
python tools/4_build_router_cache.py --clean-model
```

**Output:** Router embeddings cache in `data/cache/router_embeddings.pkl`

---

## 🚀 Complete Setup Workflow

For a fresh installation, run tools in this order:

```bash
# Step 1: Setup AI models
conda activate LegalRAG_v1
cd backend
python tools/1_setup_models.py

# Step 2: Build vector database
python tools/2_build_vectordb_unified.py

# Step 3: Generate smart router examples
python tools/3_generate_smart_router.py

# Step 4: Build router cache for fast startup
python tools/4_build_router_cache.py --force

# Now you can start the main server
python main.py
```

---

## 📝 Notes

- **Tool 1** must be run first to setup the AI models
- **Tool 2** processes your legal documents into searchable format
- **Tool 3** creates intelligent routing for better query handling
- **Tool 4** pre-computes embeddings for instant router startup

**Total Setup Time:** ~10-15 minutes (including model downloads)
**Disk Space Required:** ~5-6GB (models + data + cache)

---

## 🐛 Troubleshooting

**Model Download Issues:**

```bash
# Clean incomplete downloads and retry
python tools/4_build_router_cache.py --clean-model
python tools/1_setup_models.py
```

**Vector Database Issues:**

```bash
# Clean and rebuild vector database
python tools/2_build_vectordb_unified.py --clean
python tools/2_build_vectordb_unified.py
```

**Cache Issues:**

```bash
# Force rebuild router cache
python tools/4_build_router_cache.py --force
```

For more issues, check the individual tool logs and error messages.
