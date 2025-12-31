# Query Service

RAG (Retrieval-Augmented Generation) orchestrator for legal document Q&A.

## Pipeline

1. **Embed Question** - Convert question to vector
2. **Search** - Find similar documents using pgvector
3. **Generate** - Use LLM to answer based on context

## API

`POST /query` - Answer a question
