@echo off
REM Script to recreate conda environment for LegalRAG on Windows

echo === LegalRAG Environment Setup Script ===
echo This script will create a new conda environment with all required packages
echo.

REM Check if environment name is provided
if "%1"=="" (
    set ENV_NAME=LegalRAG_v1
    echo Using default environment name: %ENV_NAME%
) else (
    set ENV_NAME=%1
    echo Using provided environment name: %ENV_NAME%
)

echo.
echo Step 1: Creating conda environment with Python 3.11...
conda create -n %ENV_NAME% python=3.11 -y

echo.
echo Step 2: Activating environment...
call conda activate %ENV_NAME%

echo.
echo Step 3: Installing GPU packages (PyTorch with CUDA)...
echo *** IMPORTANT: Make sure you're running this in x64 Native Tools Command Prompt
echo Installing PyTorch with CUDA 12.1 support...
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y

echo.
echo Step 4: Installing llama-cpp-python...
pip install llama-cpp-python

echo.
echo Step 5: Installing packages from environment.yml...
if exist environment.yml (
    echo Creating new environment from environment.yml...
    conda env create -f environment.yml -n %ENV_NAME%
    echo Environment created successfully from environment.yml
) else (
    echo environment.yml not found. Installing from conda-packages.txt...
    if exist conda-packages.txt (
        conda install --file conda-packages.txt -y
    ) else (
        echo ERROR: No environment files found!
        exit /b 1
    )
)

echo.
echo Step 6: Installing remaining pip packages...
if exist pip-requirements.txt (
    pip install -r pip-requirements.txt
)

echo.
echo Step 7: Verifying installation...
echo Testing PyTorch CUDA availability...
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo.
echo Testing llama-cpp-python...
python -c "import llama_cpp; print('llama-cpp-python installed successfully')"

echo.
echo === Environment setup completed! ===
echo Environment name: %ENV_NAME%
echo To activate: conda activate %ENV_NAME%
pause
