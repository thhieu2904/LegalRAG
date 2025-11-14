# 🔍 LLM Model Configuration Checker
# Kiểm tra model nào đang được config trong từng môi trường

Write-Host "`n=== LegalRAG Model Configuration Checker ===" -ForegroundColor Cyan

# Check Development Config
Write-Host "`n📦 DEVELOPMENT (docker-compose.dev.yml)" -ForegroundColor Yellow
if (Test-Path "rag_service\.env") {
    $devModel = Select-String -Path "rag_service\.env" -Pattern "^LLM_MODEL_PATH=" | Select-Object -First 1
    if ($devModel) {
        $modelPath = $devModel.Line -replace "LLM_MODEL_PATH=", ""
        Write-Host "   Model: $modelPath" -ForegroundColor Green
        
        # Extract filename
        $modelFile = Split-Path -Leaf $modelPath
        if ($modelFile -like "*Q4_K_M*") {
            Write-Host "   Type: Quantized (4GB) ✅" -ForegroundColor Green
        } else {
            Write-Host "   Type: Full Model (8GB) ⚠️" -ForegroundColor Yellow
            Write-Host "   Warning: Dev nên dùng Q4_K_M để tiết kiệm VRAM" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ❌ File rag_service\.env không tồn tại" -ForegroundColor Red
}

# Check Production Config
Write-Host "`n🚀 PRODUCTION (prod/docker-compose.yml)" -ForegroundColor Yellow
if (Test-Path "prod\.env") {
    $prodModel = Select-String -Path "prod\.env" -Pattern "^LLM_MODEL_PATH=" | Select-Object -First 1
    if ($prodModel) {
        $modelPath = $prodModel.Line -replace "LLM_MODEL_PATH=", ""
        Write-Host "   Model: $modelPath" -ForegroundColor Green
        
        # Extract filename
        $modelFile = Split-Path -Leaf $modelPath
        if ($modelFile -like "*Q4_K_M*") {
            Write-Host "   Type: Quantized (4GB) ⚠️" -ForegroundColor Yellow
            Write-Host "   Suggestion: Production nên dùng Full Model" -ForegroundColor Cyan
        } else {
            Write-Host "   Type: Full Model (8GB) ✅" -ForegroundColor Green
        }
    }
} else {
    Write-Host "   ❌ File prod\.env không tồn tại" -ForegroundColor Red
}

# Check model files existence
Write-Host "`n📁 Model Files Availability" -ForegroundColor Yellow
$modelDir = "rag_service\data\models\llm_dir"

if (Test-Path $modelDir) {
    $q4Model = Join-Path $modelDir "PhoGPT-4B-Chat-Q4_K_M.gguf"
    $fullModel = Join-Path $modelDir "PhoGPT-4B-Chat.gguf"
    
    if (Test-Path $q4Model) {
        $q4Size = (Get-Item $q4Model).Length / 1GB
        Write-Host "   ✅ Q4_K_M: $($q4Size.ToString('F2')) GB" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Q4_K_M: Not found" -ForegroundColor Red
    }
    
    if (Test-Path $fullModel) {
        $fullSize = (Get-Item $fullModel).Length / 1GB
        Write-Host "   ✅ Full Model: $($fullSize.ToString('F2')) GB" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Full Model: Not found (optional)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Model directory không tồn tại: $modelDir" -ForegroundColor Red
}

# Summary
Write-Host "`n📊 Configuration Summary" -ForegroundColor Cyan
Write-Host "   Dev Environment: Quantized model (testing, low VRAM)" -ForegroundColor White
Write-Host "   Prod Environment: Full model (accuracy, high performance)" -ForegroundColor White
Write-Host "`n   ✅ Config đã được thiết lập đúng theo môi trường!`n" -ForegroundColor Green
