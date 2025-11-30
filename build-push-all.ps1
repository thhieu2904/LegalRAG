# ============================================================================
# LegalRAG - Build & Push All Services to Docker Hub
# ============================================================================
# Usage: .\build-push-all.ps1 [-Tag "v1.0.0"] [-User "thhieu"]
# ============================================================================

param(
    [string]$Tag = "latest",
    [string]$User = "thhieu"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "LegalRAG - Build & Push All Services" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow
Write-Host "Docker Hub User: $User" -ForegroundColor Cyan
Write-Host "Image Tag: $Tag" -ForegroundColor Cyan
Write-Host ""

# Danh sách services
$services = @(
    @{ Name = "admin-service"; Context = "./admin-service"; Dockerfile = "admin-service/Dockerfile"; Target = $null },
    @{ Name = "query-service"; Context = "./query-service"; Dockerfile = "query-service/Dockerfile"; Target = $null },
    @{ Name = "storage-service"; Context = "./storage-service"; Dockerfile = "storage-service/Dockerfile"; Target = $null },
    @{ Name = "vector-service"; Context = "./vector-service"; Dockerfile = "vector-service/Dockerfile"; Target = $null },
    @{ Name = "embedding-service"; Context = "./embedding-service"; Dockerfile = "embedding-service/Dockerfile"; Target = $null },
    @{ Name = "rerank-service"; Context = "./rerank-service"; Dockerfile = "rerank-service/Dockerfile"; Target = "runtime" },
    @{ Name = "llm-service"; Context = "./llm-service"; Dockerfile = "llm-service/Dockerfile"; Target = "runtime-gpu" },
    @{ Name = "form-service"; Context = "./form-service"; Dockerfile = "form-service/Dockerfile"; Target = $null },
    @{ Name = "frontend"; Context = "./frontend"; Dockerfile = "frontend/Dockerfile"; Target = $null }
)

$total = $services.Count
$current = 0
$failed = @()

foreach ($svc in $services) {
    $current++
    $imageName = "$User/legalrag-$($svc.Name -replace '-service', ''):$Tag"
    
    # Điều chỉnh tên image
    if ($svc.Name -eq "admin-service") { $imageName = "$User/legalrag-admin:$Tag" }
    elseif ($svc.Name -eq "query-service") { $imageName = "$User/legalrag-query:$Tag" }
    elseif ($svc.Name -eq "storage-service") { $imageName = "$User/legalrag-storage:$Tag" }
    elseif ($svc.Name -eq "vector-service") { $imageName = "$User/legalrag-vector:$Tag" }
    elseif ($svc.Name -eq "embedding-service") { $imageName = "$User/legalrag-embedding:$Tag" }
    elseif ($svc.Name -eq "rerank-service") { $imageName = "$User/legalrag-rerank:$Tag" }
    elseif ($svc.Name -eq "llm-service") { $imageName = "$User/legalrag-llm:$Tag" }
    elseif ($svc.Name -eq "form-service") { $imageName = "$User/legalrag-form:$Tag" }
    elseif ($svc.Name -eq "frontend") { $imageName = "$User/legalrag-frontend:$Tag" }
    
    Write-Host ""
    Write-Host "[$current/$total] Building $($svc.Name)..." -ForegroundColor Cyan
    Write-Host "  Image: $imageName" -ForegroundColor Gray
    
    try {
        # Build
        if ($svc.Target) {
            docker build --target $svc.Target -t $imageName -f $svc.Dockerfile $svc.Context
        } else {
            docker build -t $imageName -f $svc.Dockerfile $svc.Context
        }
        
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
        
        # Push
        Write-Host "  Pushing..." -ForegroundColor Gray
        docker push $imageName
        
        if ($LASTEXITCODE -ne 0) { throw "Push failed" }
        
        Write-Host "  ✅ Success" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ Failed: $_" -ForegroundColor Red
        $failed += $svc.Name
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Yellow

if ($failed.Count -eq 0) {
    Write-Host "✅ All $total services built and pushed successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️ $($failed.Count) service(s) failed:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}

Write-Host ""
Write-Host "Images pushed with tag: $Tag" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Yellow
