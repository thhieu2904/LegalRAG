# LegalRAG Frontend - Docker Deployment

## 📦 Build & Deploy

### 1. Build Docker Image

```bash
cd d:\Personal\LegalRAG\frontend
docker build -t legalrag-frontend:latest .
```

### 2. Run with Docker Compose

```bash
cd d:\Personal\LegalRAG
docker-compose up --build frontend
```

### 3. Access Application

- Frontend: http://localhost:3000
- Health Check: http://localhost:3000/health

## 🔧 Environment Variables

Environment variables are set in `docker-compose.yml`:

```yaml
environment:
  VITE_API_BASE_URL: http://localhost:8001
  VITE_APP_TITLE: LegalRAG System
  VITE_MAX_FILE_SIZE: 10485760
```

## 🐳 Dockerfile Architecture

**Multi-stage build:**

1. **Build Stage** (node:20-alpine)
   - Install dependencies
   - Build React app with Vite
   - Output to `dist/`

2. **Production Stage** (nginx:alpine)
   - Serve static files with Nginx
   - Configure for React Router (SPA)
   - Expose port 3000

## 📝 Files Created

- `Dockerfile` - Multi-stage build configuration
- `.dockerignore` - Exclude unnecessary files
- `.env.docker` - Docker-specific environment variables

## 🚀 Quick Start (Full Stack)

Run all services:

```bash
cd d:\Personal\LegalRAG
docker-compose up --build
```

Services will be available at:

- Frontend: http://localhost:3000
- Admin API: http://localhost:8001
- Query API: http://localhost:8002
- MinIO: http://localhost:9001
- PostgreSQL: localhost:5432

## 🛠️ Troubleshooting

### Frontend not loading?

1. Check if build succeeded:

```bash
docker logs legalrag-frontend
```

2. Check health endpoint:

```bash
curl http://localhost:3000/health
```

3. Rebuild without cache:

```bash
docker-compose build --no-cache frontend
docker-compose up frontend
```

### API calls failing?

Check if backend services are running:

```bash
docker ps | grep legalrag
```

Ensure admin-service is running on port 8001:

```bash
curl http://localhost:8001/health
```

### Logo not showing?

Logo is copied from `frontend/public/LOGO_HCC.jpg` during build.
Ensure file exists before building.

## 📊 Production Notes

- Nginx serves static files efficiently
- React Router handled with `try_files` directive
- Health check endpoint at `/health`
- Optimized Alpine Linux image (~50MB)
