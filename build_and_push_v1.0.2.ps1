# Build and Push LegalRAG v1.0.2 to DockerHub
# This script builds all services and pushes them to thhieu/legalrag-*

$VERSION = "v1.0.2"
$DOCKER_USERNAME = "thhieu"

Write-Host "🚀 Building LegalRAG $VERSION..." -ForegroundColor Cyan
Write-Host "=" * 80

# 1. Frontend
Write-Host "`n📦 Building Frontend..." -ForegroundColor Yellow
Set-Location frontend
docker build -t ${DOCKER_USERNAME}/legalrag-frontend:${VERSION} .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Frontend built successfully" -ForegroundColor Green

# 2. RAG Service
Write-Host "`n📦 Building RAG Service..." -ForegroundColor Yellow
Set-Location ../rag_service
docker build -t ${DOCKER_USERNAME}/legalrag-rag-service:${VERSION} .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ RAG Service build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ RAG Service built successfully" -ForegroundColor Green

# 3. Identifill Service
Write-Host "`n📦 Building Identifill Service..." -ForegroundColor Yellow
Set-Location ../identifill_service
docker build -t ${DOCKER_USERNAME}/legalrag-identifill-service:${VERSION} .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Identifill Service build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Identifill Service built successfully" -ForegroundColor Green

# 4. Admin Service
Write-Host "`n📦 Building Admin Service..." -ForegroundColor Yellow
Set-Location ../admin_service
docker build -t ${DOCKER_USERNAME}/legalrag-admin-service:${VERSION} .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Admin Service build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Admin Service built successfully" -ForegroundColor Green

Set-Location ..

Write-Host "`n" + ("=" * 80)
Write-Host "✅ All services built successfully!" -ForegroundColor Green
Write-Host "`n🚢 Pushing to DockerHub..." -ForegroundColor Cyan

# Push all images
docker push ${DOCKER_USERNAME}/legalrag-frontend:${VERSION}
docker push ${DOCKER_USERNAME}/legalrag-rag-service:${VERSION}
docker push ${DOCKER_USERNAME}/legalrag-identifill-service:${VERSION}
docker push ${DOCKER_USERNAME}/legalrag-admin-service:${VERSION}

Write-Host "`n" + ("=" * 80)
Write-Host "🎉 LegalRAG $VERSION deployed to DockerHub!" -ForegroundColor Green
Write-Host "`nImages:" -ForegroundColor Cyan
Write-Host "  - ${DOCKER_USERNAME}/legalrag-frontend:${VERSION}"
Write-Host "  - ${DOCKER_USERNAME}/legalrag-rag-service:${VERSION}"
Write-Host "  - ${DOCKER_USERNAME}/legalrag-identifill-service:${VERSION}"
Write-Host "  - ${DOCKER_USERNAME}/legalrag-admin-service:${VERSION}"
