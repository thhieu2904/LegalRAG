@echo off
:: WeChat QRCode Scanner setup and run script
:: This script sets up the WeChat QRCode Scanner and runs it

echo ===================================================
echo WeChat QRCode Scanner Setup and Run
echo ===================================================
echo.

:: Store current directory
set "ORIGINAL_DIR=%CD%"
set "PROJECT_DIR=%~dp0"

:: Check for conda
call conda --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Conda not found. Please install Anaconda or Miniconda.
    pause
    exit /b 1
)

:: Check for environment
echo [INFO] Checking for conda environment...
call conda info --envs | findstr identifill_env >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Environment not found. Creating new environment...
    call conda create -y -n identifill_env python=3.10
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create conda environment.
        pause
        exit /b 1
    )
)

:: Activate environment
echo [INFO] Activating conda environment...
call conda activate identifill_env
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate conda environment.
    pause
    exit /b 1
)

:: Install requirements
echo [INFO] Installing requirements...
cd /d "%PROJECT_DIR%"
call pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

:: Download model files
echo [INFO] Downloading model files...
python download_wechat_qrcode_models.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Failed to download model files.
)

:: Create test directory if it doesn't exist
if not exist "%PROJECT_DIR%\test_images" (
    echo [INFO] Creating test images directory...
    mkdir "%PROJECT_DIR%\test_images"
    echo [INFO] Please add test images to the test_images directory.
)

:: Run the test script
echo [INFO] Running test script...
python test_wechat_qrcode.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Test script encountered errors.
)

:: Ask user if they want to run the server
echo.
echo [INFO] Do you want to start the API server? (Y/N)
set /p START_SERVER=
if /i "%START_SERVER%"=="Y" (
    echo [INFO] Starting server...
    python main.py
) else (
    echo [INFO] Server not started.
)

:: Return to original directory
cd /d "%ORIGINAL_DIR%"
echo.
echo [INFO] All operations completed.
pause
