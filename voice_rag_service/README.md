# Voice RAG Service

Simple Vietnamese Text-to-Speech service using F5-TTS for LegalRAG system.

## 🚀 Quick Start

### 1. Create Environment

```bash
conda env create -f environment.yml
conda activate voice_rag_service
```

### 2. Start Service

```bash
python main.py
```

Service runs on: `http://localhost:8003`

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

### Voice Info

```bash
GET /api/voice/info
```

### Synthesize Speech

```bash
POST /api/voice/synthesize
{
  "text": "Theo quy định tại Điều 123 Bộ luật Dân sự...",
  "speed": 1.0
}
```

## 🎯 Features

- ✅ Vietnamese TTS using F5-TTS
- ✅ GPU acceleration (CUDA)
- ✅ Legal document optimized
- ✅ Simple API interface
- ✅ CORS enabled for frontend

## 🔧 Architecture

- **Engine**: F5-TTS v1 Base model
- **Sample Rate**: 24kHz
- **Format**: WAV
- **Language**: Vietnamese
- **Reference**: Chinese voice (closest to Vietnamese)

This is a simplified, working Vietnamese TTS service for LegalRAG.
