# 🔧 Environment Configuration Guide

## 📋 Overview

LegalRAG sử dụng environment variables để cấu hình URLs cho different deployment environments.

## 🚀 Quick Setup

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Local Development (Default)

```bash
# .env
ENVIRONMENT=local
RAG_SERVICE_URL=http://localhost:8000
IDENTIFILL_SERVICE_URL=http://localhost:8002
```

### 3. Docker Development

```bash
# .env
ENVIRONMENT=docker
# URLs are auto-configured in docker-compose.yml
```

### 4. Production Deployment

```bash
# .env
ENVIRONMENT=production
PROD_RAG_URL=https://api.legalrag.com
PROD_IDENTIFILL_URL=https://identifill.legalrag.com
```

## 🏗️ Architecture

### Service Communication Matrix

| Environment    | Frontend → RAG | Frontend → Identifill | Identifill → RAG    |
| -------------- | -------------- | --------------------- | ------------------- |
| **Local**      | localhost:8000 | localhost:8002        | localhost:8000      |
| **Docker**     | localhost:8000 | localhost:8002        | rag-service:8000    |
| **Production** | api.domain.com | identifill.domain.com | internal.domain.com |

### 🔍 URL Resolution Logic

#### Backend Services (Python)

```python
# Identifill Service
1. Check RAG_SERVICE_URL env var
2. Check ENVIRONMENT + auto-detect
3. Fallback to localhost:8000
```

#### Frontend (Browser)

```typescript
// Browser-based resolution
1. Check VITE_*_SERVICE_URL env vars (build time)
2. Runtime hostname detection (dev only)
3. Fallback to localhost URLs
```

## ⚙️ Environment Variables

### 🎯 Core Variables

- `ENVIRONMENT`: `local` | `docker` | `production`
- `RAG_SERVICE_URL`: Direct override for RAG service
- `IDENTIFILL_SERVICE_URL`: Direct override for Identifill

### 🌐 Frontend Variables (Vite)

- `VITE_RAG_SERVICE_URL`: Frontend → RAG
- `VITE_IDENTIFILL_SERVICE_URL`: Frontend → Identifill
- `VITE_OCR_SERVICE_URL`: Frontend → OCR

### 🚀 Production Variables

- `PROD_RAG_URL`: Production RAG service URL
- `PROD_IDENTIFILL_URL`: Production Identifill URL

## 🐳 Docker Usage

### Local Development

```bash
# Services auto-detect internal Docker networking
docker-compose up --build
```

### Production Deployment

```bash
# Set production URLs
export ENVIRONMENT=production
export PROD_RAG_URL=https://api.legalrag.com
docker-compose -f docker-compose.prod.yml up
```

## 🔧 Troubleshooting

### Connection Refused Errors

```bash
# Check environment detection
echo $ENVIRONMENT
echo $RAG_SERVICE_URL

# Verify Docker networking
docker-compose exec identifill-service curl http://rag-service:8000/health
```

### Frontend Can't Connect

```bash
# Check browser console for URL resolution logs
# Look for: "🌐 Using VITE_RAG_SERVICE_URL: ..."

# Verify environment variables in build
npm run build && cat dist/assets/index-*.js | grep "localhost"
```

## 🎯 Best Practices

1. **Always use .env files** - Don't hardcode URLs
2. **Test all environments** - Local, Docker, Production
3. **Check logs** - Services log their detected URLs
4. **Use explicit env vars** - Don't rely on auto-detection for production
