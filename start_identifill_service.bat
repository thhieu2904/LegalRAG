@echo off
:: Automated deployment script for identifill_service
:: This script activates conda environment, navigates to service directory, and runs the application

echo ============================================
echo   IdentiFill Service Deployment Script
echo ============================================
echo.

:: Store current directory
set "ORIGINAL_DIR=%CD%"

:: Set project paths
set "PROJECT_ROOT=d:\Personal\LegalRAG_OCR"
set "SERVICE_DIR=%PROJECT_ROOT%\identifill_service"
set "CONDA_ENV=identifill_env"

echo [INFO] Project Root: %PROJECT_ROOT%
echo [INFO] Service Directory: %SERVICE_DIR%
echo [INFO] Conda Environment: %CONDA_ENV%
echo.

:: Check if conda is available
conda --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Conda is not available in PATH
    echo [ERROR] Please ensure Anaconda/Miniconda is installed and added to PATH
    pause
    exit /b 1
)

:: Check if environment exists
echo [INFO] Checking conda environment...
conda info --envs | findstr /C:"%CONDA_ENV%" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Conda environment '%CONDA_ENV%' not found
    echo [INFO] Available environments:
    conda info --envs
    pause
    exit /b 1
)

:: Navigate to service directory
echo [INFO] Navigating to service directory...
if not exist "%SERVICE_DIR%" (
    echo [ERROR] Service directory not found: %SERVICE_DIR%
    pause
    exit /b 1
)

cd /d "%SERVICE_DIR%"
echo [INFO] Current directory: %CD%

:: Check if main.py exists
if not exist "main.py" (
    echo [ERROR] main.py not found in service directory
    echo [ERROR] Please ensure you are in the correct directory
    pause
    exit /b 1
)

:: Activate conda environment and run the service
echo.
echo [INFO] Activating conda environment and starting service...
echo [INFO] Press Ctrl+C to stop the service
echo.

:: Use call to ensure the batch file doesn't exit after conda activate
call conda activate %CONDA_ENV%

:: Check if activation was successful
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate conda environment '%CONDA_ENV%'
    cd /d "%ORIGINAL_DIR%"
    pause
    exit /b 1
)

:: Show environment info
echo [INFO] Active conda environment:
echo [INFO] Python version:
python --version

echo [INFO] Installed packages:
pip list | findstr -i "fastapi uvicorn pyzbar opencv-python"

echo.
echo [INFO] Starting IdentiFill Service...
echo [INFO] Service will be available at: http://localhost:8000
echo [INFO] API documentation at: http://localhost:8000/docs
echo.

:: Run the application with error handling
python main.py

:: Capture exit code
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% EQU 0 (
    echo [INFO] Service stopped gracefully
) else (
    echo [ERROR] Service stopped with error code: %EXIT_CODE%
)

:: Return to original directory
cd /d "%ORIGINAL_DIR%"

echo.
echo [INFO] Returned to original directory: %CD%
pause

exit /b %EXIT_CODE%
