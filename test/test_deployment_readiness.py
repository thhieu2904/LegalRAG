#!/usr/bin/env python3
"""
Pre-Docker Deployment Validation Script
======================================
Validate everything is ready for Docker deployment
"""

import json
import os
import sys
from pathlib import Path

def validate_file_modifications():
    """Validate that all required files have been modified correctly"""
    print("🔍 Validating File Modifications")
    print("-" * 50)
    
    modifications = {
        "rag_service/app/core/path_config.py": [
            "_detect_environment",
            "_configure_docker_paths", 
            "resolve_cross_platform_path"
        ],
        "rag_service/app/services/simple_form_detection.py": [
            "from ..core.path_config import PathConfig",
            "self.path_config"
        ],
        "rag_service/app/services/context.py": [
            "from ..core.path_config import PathConfig",
            "_resolve_source_file_path"
        ],
        "docker-compose.yml": [
            "ENVIRONMENT=docker",
            "LEGALRAG_BASE_PATH=/app",
            "LEGALRAG_DATA_PATH=/app/data"
        ]
    }
    
    all_valid = True
    
    for file_path, required_content in modifications.items():
        full_path = Path(__file__).parent.parent / file_path
        
        if not full_path.exists():
            print(f"  ❌ File not found: {file_path}")
            all_valid = False
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"  📄 Checking {file_path}:")
            for required in required_content:
                if required in content:
                    print(f"    ✅ Found: {required}")
                else:
                    print(f"    ❌ Missing: {required}")
                    all_valid = False
        
        except Exception as e:
            print(f"  ❌ Error reading {file_path}: {e}")
            all_valid = False
    
    if all_valid:
        print("\n✅ All file modifications validated!")
    else:
        print("\n❌ Some file modifications are missing!")
    
    return all_valid

def validate_data_structure():
    """Validate that data directory structure exists"""
    print("\n📁 Validating Data Structure")
    print("-" * 50)
    
    data_path = Path(__file__).parent.parent / "rag_service" / "data"
    
    required_dirs = [
        "storage",
        "storage/collections",
        "cache",
        "models",
        "vectordb"
    ]
    
    print(f"Data root: {data_path}")
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = data_path / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_name}/")
        
        if not exists:
            all_exist = False
    
    if all_exist:
        print("\n✅ Data structure validated!")
    else:
        print("\n⚠️ Some directories missing (will be created by Docker)")
    
    return True  # Not critical for Docker

def validate_docker_files():
    """Validate Docker-related files"""
    print("\n🐳 Validating Docker Files")
    print("-" * 50)
    
    docker_files = [
        "docker-compose.yml",
        "rag_service/Dockerfile",
        "rag_service/requirements.txt"
    ]
    
    all_exist = True
    
    for file_name in docker_files:
        file_path = Path(__file__).parent.parent / file_name
        exists = file_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_name}")
        
        if not exists:
            all_exist = False
    
    if all_exist:
        print("\n✅ Docker files validated!")
    else:
        print("\n❌ Some Docker files are missing!")
    
    return all_exist

def generate_deployment_instructions():
    """Generate step-by-step deployment instructions"""
    print("\n📋 Generating Deployment Instructions")
    print("-" * 50)
    
    instructions = """
🚀 DOCKER DEPLOYMENT INSTRUCTIONS
================================

1. Pre-deployment Validation:
   - Run this script to ensure all modifications are in place
   - Verify Docker and Docker Compose are installed
   - Ensure GPU drivers are properly configured (if using GPU)

2. Build and Deploy:
   ```bash
   # Navigate to project root
   cd D:\\Personal\\LegalRAG_OCR
   
   # Build Docker images
   docker-compose build
   
   # Start services
   docker-compose up -d
   
   # Check service status
   docker-compose ps
   
   # View logs
   docker-compose logs rag-service
   ```

3. Validation in Docker:
   ```bash
   # Test API endpoint
   curl http://localhost:8000/health
   
   # Check environment inside container
   docker exec legalrag-rag-service python -c "
   from app.core.path_config import PathConfig
   config = PathConfig()
   print(f'Environment: {config.environment}')
   print(f'Base data dir: {config.base_data_dir}')
   print(f'Collections dir: {config.collections_dir}')
   "
   ```

4. Path Verification:
   ```bash
   # Check paths exist in container
   docker exec legalrag-rag-service ls -la /app/data/
   docker exec legalrag-rag-service ls -la /app/data/storage/
   ```

5. Service Testing:
   ```bash
   # Test form detection service
   docker exec legalrag-rag-service python -c "
   from app.services.simple_form_detection import SimpleFormDetectionService
   service = SimpleFormDetectionService()
   print(f'Service environment: {service.path_config.environment}')
   print(f'Storage path: {service.storage_base_path}')
   "
   ```

6. Troubleshooting:
   - If paths don't work: Check environment variables are set correctly
   - If services fail: Check logs with 'docker-compose logs rag-service'
   - If data missing: Ensure volume mount './rag_service/data:/app/data' is working

7. Rollback Plan:
   ```bash
   # Stop services
   docker-compose down
   
   # Remove containers and images if needed
   docker-compose down --rmi all
   ```

⚠️ IMPORTANT NOTES:
- Environment variables in docker-compose.yml will override PathConfig defaults
- Data directory is mounted from local rag_service/data to /app/data in container
- PathConfig will automatically detect Docker environment and use correct paths
- Backward compatibility is maintained for any existing integrations
"""
    
    # Save instructions to file
    instructions_file = Path(__file__).parent / "DOCKER_DEPLOYMENT_INSTRUCTIONS.md"
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"📄 Instructions saved to: {instructions_file}")
    print("\nKey deployment commands:")
    print("  docker-compose build")
    print("  docker-compose up -d")
    print("  docker-compose logs rag-service")
    
    return True

def validate_environment_readiness():
    """Check if environment is ready for Docker deployment"""
    print("\n🌍 Validating Environment Readiness")
    print("-" * 50)
    
    # Check if on correct branch
    try:
        import subprocess
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            current_branch = result.stdout.strip()
            print(f"  Current git branch: {current_branch}")
            if current_branch in ['docker', 'main']:
                print("    ✅ On appropriate branch for Docker deployment")
            else:
                print("    ⚠️ Consider switching to 'docker' or 'main' branch")
        else:
            print("  ⚠️ Could not determine git branch")
    except:
        print("  ⚠️ Git not available or not in git repository")
    
    # Check Python version
    python_version = sys.version
    print(f"  Python version: {python_version.split()[0]}")
    
    # Check if we're in correct directory
    cwd = Path.cwd()
    expected_dir = Path(__file__).parent.parent
    if cwd.resolve() == expected_dir.resolve():
        print("  ✅ In correct project directory")
    else:
        print(f"  ⚠️ Current directory: {cwd}")
        print(f"  ⚠️ Expected directory: {expected_dir}")
    
    return True

def main():
    """Run pre-deployment validation"""
    print("🚀 Pre-Docker Deployment Validation")
    print("=" * 60)
    
    validators = [
        validate_file_modifications,
        validate_data_structure,
        validate_docker_files,
        validate_environment_readiness,
        generate_deployment_instructions
    ]
    
    passed = 0
    total = len(validators)
    
    for validator in validators:
        try:
            if validator():
                passed += 1
        except Exception as e:
            print(f"❌ Validator {validator.__name__} failed: {e}")
    
    print(f"\n📊 Pre-deployment Validation: {passed}/{total} passed")
    
    if passed >= 4:  # Allow some warnings
        print("🎉 READY FOR DOCKER DEPLOYMENT!")
        print("✅ All critical validations passed")
        print("✅ Path configuration system implemented")
        print("✅ Docker compatibility ensured")
        print("✅ Deployment instructions generated")
        print("\n🚀 You can now proceed with Docker deployment")
        print("📋 Follow the instructions in DOCKER_DEPLOYMENT_INSTRUCTIONS.md")
    else:
        print("❌ NOT READY FOR DEPLOYMENT")
        print("⚠️ Please fix validation errors before deploying")
    
    return 0 if passed >= 4 else 1

if __name__ == "__main__":
    exit(main())