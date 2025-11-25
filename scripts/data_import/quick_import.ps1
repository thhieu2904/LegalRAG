#!/usr/bin/env pwsh
# ============================================
# LegalRAG Quick Import Script (Windows)
# ============================================
# Run this script to quickly import all legal documents
# 
# Usage: .\quick_import.ps1 [-DryRun] [-CleanOnly]
# ============================================

param(
    [switch]$DryRun,
    [switch]$CleanOnly,
    [switch]$SkipConvert
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Get-Item $ScriptDir).Parent.Parent.FullName

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "    LegalRAG Data Import Tool" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed!" -ForegroundColor Red
    exit 1
}

# Check if services are running
Write-Host "📋 Checking services..." -ForegroundColor Yellow

$postgresRunning = docker ps --filter "name=legalrag-postgres" --format "{{.Names}}" 2>$null
$minioRunning = docker ps --filter "name=legalrag-minio" --format "{{.Names}}" 2>$null

if (-not $postgresRunning -or -not $minioRunning) {
    Write-Host "⚠️ Required services not running. Starting..." -ForegroundColor Yellow
    Push-Location $RootDir
    docker compose up -d postgres-vector minio
    Write-Host "⏳ Waiting for services to be healthy..."
    Start-Sleep -Seconds 10
    Pop-Location
}

Write-Host "✅ Services are running" -ForegroundColor Green
Write-Host ""

# Clean only mode
if ($CleanOnly) {
    Write-Host "🧹 Cleaning up old data..." -ForegroundColor Yellow
    $sqlFile = Join-Path $ScriptDir "cleanup_old_data.sql"
    Get-Content $sqlFile | docker exec -i legalrag-postgres psql -U legalrag -d legalrag
    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
    exit 0
}

# Create network if not exists
$networkExists = docker network ls --filter "name=legalrag-network" --format "{{.Name}}" 2>$null
if (-not $networkExists) {
    Write-Host "📡 Creating Docker network..." -ForegroundColor Yellow
    docker network create legalrag-network
}

# Build and run import
Write-Host "🚀 Starting import process..." -ForegroundColor Yellow
Write-Host ""

Push-Location $RootDir

$importArgs = @()
if ($DryRun) {
    $importArgs += "--dry-run"
    Write-Host "⚠️ DRY RUN MODE - No changes will be made" -ForegroundColor Magenta
}
if ($SkipConvert) {
    $importArgs += "--skip-convert"
}

# Build and run
$composeFile = Join-Path $RootDir "docker-compose.import.yml"
docker compose -f $composeFile build
docker compose -f $composeFile run --rm data-import python import_data.py $importArgs

Pop-Location

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "    Import Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Check results:" -ForegroundColor Yellow
Write-Host "   docker exec -it legalrag-postgres psql -U legalrag -d legalrag -c 'SELECT name, display_name, document_count FROM collections;'"
Write-Host ""
Write-Host "📝 View logs:" -ForegroundColor Yellow
Write-Host "   Get-Content $ScriptDir\logs\import_*.log"
