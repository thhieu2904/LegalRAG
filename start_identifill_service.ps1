# IdentiFill Service PowerShell Deployment Script
# Enhanced version with better error handling and logging

param(
    [string]$Mode = "production",
    [switch]$Debug = $false,
    [switch]$Install = $false,
    [switch]$CheckDeps = $false,
    [int]$Port = 8000
)

# Configuration
$ProjectRoot = "d:\Personal\LegalRAG_OCR"
$ServiceDir = Join-Path $ProjectRoot "identifill_service"
$CondaEnv = "identifill_env"
$LogFile = Join-Path $ProjectRoot "identifill_service.log"

# Colors for output
$Colors = @{
    Info = "Green"
    Warning = "Yellow" 
    Error = "Red"
    Success = "Cyan"
}

function Write-Log {
    param($Message, $Type = "Info")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Type] $Message"
    Write-Host $logMessage -ForegroundColor $Colors[$Type]
    Add-Content -Path $LogFile -Value $logMessage
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." "Info"
    
    # Check conda
    try {
        $condaVersion = conda --version 2>$null
        Write-Log "Conda found: $condaVersion" "Success"
    }
    catch {
        Write-Log "Conda not found in PATH. Please install Anaconda/Miniconda." "Error"
        return $false
    }
    
    # Check environment
    $envList = conda info --envs 2>$null | Out-String
    if ($envList -match $CondaEnv) {
        Write-Log "Conda environment '$CondaEnv' found" "Success"
    }
    else {
        Write-Log "Conda environment '$CondaEnv' not found" "Error"
        Write-Log "Available environments:" "Info"
        conda info --envs
        return $false
    }
    
    # Check service directory
    if (Test-Path $ServiceDir) {
        Write-Log "Service directory found: $ServiceDir" "Success"
    }
    else {
        Write-Log "Service directory not found: $ServiceDir" "Error"
        return $false
    }
    
    # Check main.py
    $mainPy = Join-Path $ServiceDir "main.py"
    if (Test-Path $mainPy) {
        Write-Log "main.py found" "Success"
    }
    else {
        Write-Log "main.py not found in service directory" "Error"
        return $false
    }
    
    return $true
}

function Install-Dependencies {
    Write-Log "Installing/updating dependencies..." "Info"
    
    Set-Location $ServiceDir
    
    # Activate environment and install requirements
    $installCmd = @"
conda activate $CondaEnv
if (Test-Path requirements.txt) {
    pip install -r requirements.txt
    Write-Host "Dependencies installed from requirements.txt"
} else {
    Write-Host "requirements.txt not found, skipping dependency installation"
}
"@
    
    try {
        Invoke-Expression $installCmd
        Write-Log "Dependencies installation completed" "Success"
    }
    catch {
        Write-Log "Failed to install dependencies: $_" "Error"
        return $false
    }
    
    return $true
}

function Test-Dependencies {
    Write-Log "Checking installed packages..." "Info"
    
    $checkCmd = @"
conda activate $CondaEnv
python -c "
try:
    import fastapi, uvicorn, pyzbar, cv2, numpy
    print('✓ All critical packages are installed')
    
    # Version info
    import pkg_resources
    packages = ['fastapi', 'uvicorn', 'opencv-python', 'pyzbar', 'numpy']
    for pkg in packages:
        try:
            version = pkg_resources.get_distribution(pkg).version
            print(f'✓ {pkg}: {version}')
        except:
            print(f'✗ {pkg}: Not found')
    
except ImportError as e:
    print(f'✗ Missing package: {e}')
    exit(1)
"
"@
    
    try {
        $result = Invoke-Expression $checkCmd
        Write-Log $result "Success"
        return $true
    }
    catch {
        Write-Log "Dependency check failed: $_" "Error"
        return $false
    }
}

function Start-Service {
    Write-Log "Starting IdentiFill Service..." "Info"
    Write-Log "Mode: $Mode, Port: $Port, Debug: $Debug" "Info"
    
    Set-Location $ServiceDir
    
    # Prepare environment variables
    $env:MODE = $Mode
    $env:PORT = $Port.ToString()
    if ($Debug) {
        $env:DEBUG = "1"
        $env:LOG_LEVEL = "DEBUG"
    }
    
    # Construct run command
    $runCmd = @"
conda activate $CondaEnv
python main.py
"@
    
    Write-Log "Service will be available at: http://localhost:$Port" "Info"
    Write-Log "API documentation at: http://localhost:$Port/docs" "Info"
    Write-Log "Press Ctrl+C to stop the service" "Warning"
    Write-Log "" "Info"
    
    try {
        Invoke-Expression $runCmd
    }
    catch {
        Write-Log "Service stopped with error: $_" "Error"
        return $false
    }
    
    Write-Log "Service stopped gracefully" "Success"
    return $true
}

# Main execution
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   IdentiFill Service PowerShell Script   " -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Log "Starting deployment process..." "Info"
Write-Log "Project Root: $ProjectRoot" "Info"
Write-Log "Service Directory: $ServiceDir" "Info"
Write-Log "Conda Environment: $CondaEnv" "Info"
Write-Log "Log File: $LogFile" "Info"
Write-Host ""

# Store original location
$OriginalLocation = Get-Location

try {
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Log "Prerequisites check failed. Exiting." "Error"
        exit 1
    }
    
    # Install dependencies if requested
    if ($Install) {
        if (-not (Install-Dependencies)) {
            Write-Log "Dependency installation failed. Exiting." "Error"
            exit 1
        }
    }
    
    # Check dependencies if requested
    if ($CheckDeps) {
        if (-not (Test-Dependencies)) {
            Write-Log "Dependency check failed. Exiting." "Error"
            exit 1
        }
    }
    
    # Start the service
    if (-not (Start-Service)) {
        Write-Log "Service failed to start properly. Exiting." "Error"
        exit 1
    }
}
finally {
    # Return to original location
    Set-Location $OriginalLocation
    Write-Log "Returned to original directory: $(Get-Location)" "Info"
}

Write-Log "Script execution completed." "Success"
