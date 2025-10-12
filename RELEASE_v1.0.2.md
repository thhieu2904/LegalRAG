# LegalRAG v1.0.2 Release Summary

## 📋 Version Information

- **Version**: v1.0.2
- **Release Date**: October 12, 2025
- **Docker Images**:
  - `thhieu/legalrag-frontend:v1.0.2`
  - `thhieu/legalrag-rag-service:v1.0.2`
  - `thhieu/legalrag-identifill-service:v1.0.2`
  - `thhieu/legalrag-admin-service:v1.0.2`

## ✨ Changes from v0.1.1

### Removed

- ❌ **TTS Service**: Removed experimental F5-TTS Vietnamese service
  - Reason: Vietnamese diacritics tokenization issues with F5-TTS
  - Impact: System now uses browser's built-in Web Speech API (giọng An)

### Architecture Updates

- ✅ Simplified docker-compose.yml (4 services instead of 5)
- ✅ Removed GPU sharing complexity between RAG and TTS services
- ✅ Reduced memory requirements (10G instead of 14G)
- ✅ Faster startup time without TTS model loading

## 🎯 Voice System

### Current Implementation (v1.0.2)

- **Engine**: Browser Web Speech API
- **Voice**: Vietnamese "An" (Microsoft An - Vietnamese (Vietnam))
- **Pros**:
  - ✅ Works offline in browser
  - ✅ No GPU required
  - ✅ Perfect Vietnamese pronunciation
  - ✅ Instant response (no model loading)
- **Cons**:
  - ⚠️ Limited voice options
  - ⚠️ Browser-dependent quality

## 🚀 Deployment

### Quick Start

```bash
cd prod
docker-compose up -d
```

### Services

1. **Frontend** (Port 5173): React SPA with Vite
2. **RAG Service** (Port 8000): Legal Q&A with GPU support
3. **Admin Service** (Port 8001): Document management
4. **Identifill Service** (Port 8002): CCCD scanning

### Hardware Requirements

- **GPU**: NVIDIA RTX 3060 (12GB VRAM) or better
- **RAM**: 16GB minimum
- **Storage**: 50GB for models and data

## 📝 Build Instructions

### Manual Build

```powershell
# Build all services
.\build_and_push_v1.0.2.ps1
```

### Individual Service Build

```bash
# Frontend
cd frontend && docker build -t thhieu/legalrag-frontend:v1.0.2 .

# RAG Service
cd rag_service && docker build -t thhieu/legalrag-rag-service:v1.0.2 .

# Identifill Service
cd identifill_service && docker build -t thhieu/legalrag-identifill-service:v1.0.2 .

# Admin Service
cd admin_service && docker build -t thhieu/legalrag-admin-service:v1.0.2 .
```

## 🔄 Migration from v0.1.1

### For Existing Users

1. Pull new docker-compose.yml from prod/
2. Stop old containers: `docker-compose down`
3. Pull new images: `docker-compose pull`
4. Start new version: `docker-compose up -d`

### Data Preservation

- ✅ All data in `rag_data` volume is preserved
- ✅ No database migration needed
- ✅ Existing documents and embeddings remain intact

## 🐛 Known Issues

- None reported for v1.0.2

## 🔮 Future Plans

- [ ] Server-side Vietnamese TTS with VITS/Piper
- [ ] Multi-GPU support for scaling
- [ ] Docker image optimization (reduce size)
- [ ] Kubernetes deployment manifests

## 📞 Support

- GitHub: https://github.com/thhieu2904/LegalRAG
- Docker Hub: https://hub.docker.com/u/thhieu

---

**Note**: This version focuses on stability and production readiness by removing experimental TTS features.
