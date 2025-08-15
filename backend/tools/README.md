# LegalRAG Tools - Enhanced Multi-Aspect Generation System

## 5 Essential Tools for LegalRAG System Setup

### Overview

This directory contains 5 essential tools for setting up and maintaining the LegalRAG system, with breakthrough multi-aspect question generation capability. Run tools in order for fresh installation.

> **🚀 NEW**: Tool 5 implements revolutionary multi-aspect multi-persona generation to achieve 30+ questions per document with comprehensive coverage.

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

# Verify only (no downloads)
python tools/1_setup_models.py --verify-only

# Force clean setup
python tools/1_setup_models.py --clean
```

**Output:** Models stored in `data/models/`

---

## 🗂️ Tool 2: Build Unified Vector Database

**File:** `2_build_vectordb_unified.py`

**Purpose:** Process documents and create searchable vector database

- Parse all legal document files from multiple collections
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

## 🎯 Tool 3: Generate Smart Router (Legacy)

**File:** `3_generate_smart_router.py`

**Purpose:** Create intelligent query routing examples (Template-based)

- Generate question templates with metadata-aware specificity
- Create smart filters with multi-dimensional filtering
- Extract key attributes from document metadata
- Generate priority scores for routing decisions

> **⚠️ Note:** This is the legacy template-based generator. For production use, prefer Tool 5 for comprehensive question generation.

**Usage:**

```bash
# Generate basic smart router examples
python tools/3_generate_smart_router.py

# Force rebuild existing examples
python tools/3_generate_smart_router.py --force
```

**Output:** Smart router examples in `data/router_examples_smart/`

---

## ⚡ Tool 4: Build Router Cache

**File:** `4_build_router_cache.py`

**Purpose:** Pre-compute embeddings cache for fast router startup

- Load all router examples from `router_examples_smart/` or `router_examples_smart_v4/`
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

## 🚀 **NEW** Tool 5: Multi-Aspect Multi-Persona Router Generator

**File:** `generate_router_with_llm_v4_multi_aspect.py`

**Purpose:** Revolutionary comprehensive question generation system

**🎯 Target:** Generate 30+ diverse, high-quality questions per document

**🔧 Method:** Chunk × Persona Matrix Generation

- **Chunks:** Process each content section separately for full context coverage
- **Personas:** 5 distinct user types with unique question styles and concerns
- **Matrix:** Generate questions for every relevant (chunk, persona) combination

**👥 User Personas:**

- **Người Lần Đầu:** Basic step-by-step questions for beginners
- **Người Bận Rộn:** Time-focused, efficiency-oriented questions
- **Người Cẩn Thận:** Detailed conditions, special cases, important notes
- **Người Làm Hộ:** Authorization, representation, proxy-related questions
- **Người Gặp Vấn Đề:** Problem-solving, special circumstances, difficulties

**🎨 Comprehensive Coverage:**

- **Aspects:** Documents, fees, timing, conditions, procedures, authorization, locations, results, special cases
- **Context:** Full content_chunks analysis (not just metadata)
- **Quality:** Advanced deduplication and quality filtering

**Usage:**

```bash
# Generate comprehensive multi-aspect router examples
python tools/generate_router_with_llm_v4_multi_aspect.py

# Force rebuild existing examples
python tools/generate_router_with_llm_v4_multi_aspect.py --force

# Custom directories
python tools/generate_router_with_llm_v4_multi_aspect.py --docs data/documents --output data/router_examples_smart_v4
```

**Output:**

**Output:**

- Comprehensive router examples in `data/router_examples_smart_v4/`
- Detailed generation report: `multi_aspect_generation_summary_v4.json`

**⚡ Latest Improvements (V4.1):**

- **Enhanced Smart Filters:** Restored detailed metadata analysis logic from V3
- **Increased Diversity:** Temperature tuned to 0.6 for more natural questions
- **Optimized Deduplication:** Dual-strategy algorithm (similarity vs normalized)
- **Advanced Monitoring:** Real-time effectiveness tracking and comprehensive analytics

**Performance:**

- **Quality:** Context-aware questions from actual document content
- **Quantity:** 30+ questions per document (vs. <10 from legacy tools)
- **Coverage:** Full document aspects × diverse user perspectives
- **Efficiency:** Intelligent persona-aspect mapping for focused generation

---

## 🚀 Complete Setup Workflow (Updated)

For a fresh installation with comprehensive question generation:

```bash
# Step 1: Setup AI models
conda activate LegalRAG_v1
cd backend
python tools/1_setup_models.py

# Step 2: Build vector database
python tools/2_build_vectordb_unified.py

# Step 3A: OPTIONAL - Generate legacy template-based router
python tools/3_generate_smart_router.py

# Step 3B: RECOMMENDED - Generate comprehensive multi-aspect router
python tools/generate_router_with_llm_v4_multi_aspect.py

# Step 4: Build router cache for fast startup
python tools/4_build_router_cache.py --force

# Now you can start the main server
python main.py
```

---

## 📊 Generation Method Comparison

| Feature            | Tool 3 (Legacy)         | Tool 5 (Multi-Aspect) |
| ------------------ | ----------------------- | --------------------- |
| Questions per doc  | 6-8                     | 30+                   |
| Context awareness  | Metadata only           | Full content chunks   |
| User perspectives  | Generic                 | 5 distinct personas   |
| Question variety   | Template-based          | LLM-generated diverse |
| Coverage           | Basic aspects           | Comprehensive matrix  |
| Quality            | Structured but limited  | Rich, context-aware   |
| **Recommendation** | **Development/Testing** | **Production**        |

---

## 📝 Notes

- **Tool 1** must be run first to setup the AI models
- **Tool 2** processes your legal documents into searchable format
- **Tool 3** creates basic routing (legacy approach)
- **Tool 5** creates comprehensive routing with 30+ questions per document **(RECOMMENDED)**
- **Tool 4** pre-computes embeddings for instant router startup

**Total Setup Time:** ~15-20 minutes (including model downloads + comprehensive generation)
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

**Multi-Aspect Generation Issues:**

```bash
# Force rebuild with comprehensive generation
python tools/generate_router_with_llm_v4_multi_aspect.py --force

# Check generation summary for statistics
cat data/router_examples_smart_v4/multi_aspect_generation_summary_v4.json
```

**Cache Issues:**

```bash
# Force rebuild router cache (works with both legacy and v4 examples)
python tools/4_build_router_cache.py --force
```

For more issues, check the individual tool logs and detailed error messages.

---

## 🔬 Advanced Usage

### Testing the Multi-Aspect Generator

```bash
# Test on a single collection
python tools/generate_router_with_llm_v4_multi_aspect.py --docs data/documents/quy_trinh_cap_ho_tich_cap_xa

# Generate with custom output location
python tools/generate_router_with_llm_v4_multi_aspect.py --output data/test_router_v4

# Force regenerate everything
python tools/generate_router_with_llm_v4_multi_aspect.py --force --docs data/documents --output data/router_examples_smart_v4
```

### Performance Monitoring

The multi-aspect generator provides detailed statistics:

- Per-chunk processing metrics
- Persona activation rates
- Deduplication effectiveness
- Generation speed and success rates

Check the summary JSON file for comprehensive analytics on the generation process.

### Integration with Existing System

The v4 generator is fully backward compatible:

- Same JSON output format as legacy generators
- Compatible with existing cache system (Tool 4)
- Seamless integration with main server routing logic
- Enhanced metadata and smart filters for better matching
