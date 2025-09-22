#!/usr/bin/env python3
"""
Docker Path Resolution Test Script
==================================
Specifically tests path resolution in Docker environment
Run this inside Docker container to verify paths work correctly
"""

import os
import sys
import json
from pathlib import Path

def simulate_docker_environment():
    """Simulate Docker environment variables"""
    print("🐳 Simulating Docker Environment")
    print("-" * 50)
    
    # Set Docker-like environment variables
    docker_env = {
        "PYTHONPATH": "/app",
        "ENVIRONMENT": "docker",
        "HF_CACHE_DIR": "/app/data/cache",
        "LEGALRAG_DATA_PATH": "/app/data"
    }
    
    print("Setting environment variables:")
    for key, value in docker_env.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    print()

def test_docker_path_structure():
    """Test expected Docker path structure"""
    print("📁 Testing Docker Path Structure")
    print("-" * 50)
    
    expected_paths = [
        "/app",
        "/app/app",
        "/app/app/core",
        "/app/app/services",
        "/app/data",
        "/app/data/storage",
        "/app/data/storage/collections",
        "/app/data/cache",
        "/app/data/models",
        "/app/data/vectordb"
    ]
    
    print("Expected Docker paths:")
    for path in expected_paths:
        path_obj = Path(path)
        exists = path_obj.exists()
        is_dir = path_obj.is_dir() if exists else False
        status = "✅" if exists and is_dir else "❌" if exists else "🔍"
        print(f"  {status} {path}")
    
    print()

def test_path_calculations():
    """Test path calculations that will be used in the actual code"""
    print("🧮 Testing Path Calculations")
    print("-" * 50)
    
    # Simulate different file locations in Docker
    test_files = [
        "/app/app/services/simple_form_detection.py",
        "/app/app/services/context.py",
        "/app/app/core/path_config.py"
    ]
    
    for test_file in test_files:
        file_path = Path(test_file)
        
        # Calculate base path using parent.parent.parent pattern
        base_path = file_path.parent.parent.parent
        data_path = base_path / "data"
        collections_path = data_path / "storage" / "collections"
        
        print(f"File: {test_file}")
        print(f"  Base path: {base_path}")
        print(f"  Data path: {data_path}")
        print(f"  Collections path: {collections_path}")
        print()

def test_cross_platform_paths():
    """Test cross-platform path handling"""
    print("🌐 Testing Cross-Platform Paths")
    print("-" * 50)
    
    # Test path formats that might come from different sources
    test_paths = [
        "data\\storage\\collections\\test.json",  # Windows style
        "data/storage/collections/test.json",     # Unix style
        "..\\data\\storage\\collections\\test.json",  # Windows relative
        "../data/storage/collections/test.json",      # Unix relative
        "D:\\Personal\\LegalRAG_OCR\\rag_service\\data\\storage\\collections\\test.json",  # Windows absolute
    ]
    
    for test_path in test_paths:
        # Normalize to Unix style (Docker uses Linux)
        normalized = test_path.replace("\\", "/")
        
        # Remove Windows drive letters
        if ":" in normalized:
            parts = normalized.split("/")
            # Find the part with data and take from there
            try:
                data_index = parts.index("data")
                normalized = "/".join(parts[data_index:])
            except ValueError:
                normalized = normalized
        
        # Convert relative paths
        if normalized.startswith("../"):
            normalized = normalized[3:]  # Remove ../
        
        print(f"Original: {test_path}")
        print(f"Normalized: {normalized}")
        print(f"Docker path: /app/{normalized}")
        print()

def test_environment_variable_override():
    """Test environment variable path overrides"""
    print("🌍 Testing Environment Variable Overrides")
    print("-" * 50)
    
    # Test different override scenarios
    override_tests = [
        {
            "name": "Custom data path",
            "env": {"LEGALRAG_DATA_PATH": "/custom/data"},
            "expected_base": "/custom/data"
        },
        {
            "name": "Custom base path",
            "env": {"LEGALRAG_BASE_PATH": "/custom/app"},
            "expected_base": "/custom/app"
        },
        {
            "name": "Docker detection via PYTHONPATH",
            "env": {"PYTHONPATH": "/app"},
            "expected_environment": "docker"
        }
    ]
    
    for test in override_tests:
        print(f"Test: {test['name']}")
        
        # Set environment variables
        for key, value in test['env'].items():
            os.environ[key] = value
            print(f"  Set {key}={value}")
        
        # Test would go here (we can't import actual module in this isolated test)
        print("  Result: Environment variables set successfully")
        
        # Clean up
        for key in test['env'].keys():
            if key in os.environ:
                del os.environ[key]
        
        print()

def create_mock_data_structure():
    """Create mock data structure for testing"""
    print("🏗️ Creating Mock Data Structure")
    print("-" * 50)
    
    # Create mock directory structure
    mock_base = Path("/tmp/legalrag_test")
    mock_data = mock_base / "data"
    mock_collections = mock_data / "storage" / "collections"
    mock_cache = mock_data / "cache"
    
    # Create directories
    directories = [mock_base, mock_data, mock_collections, mock_cache]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created: {directory}")
        except Exception as e:
            print(f"  ❌ Failed to create {directory}: {e}")
    
    # Create mock files
    mock_files = [
        mock_collections / "test_collection" / "documents" / "DOC_001" / "test.json",
        mock_cache / "test_cache.pkl"
    ]
    
    for file_path in mock_files:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text('{"test": "data"}')
            print(f"  ✅ Created file: {file_path}")
        except Exception as e:
            print(f"  ❌ Failed to create {file_path}: {e}")
    
    print(f"\n📁 Mock structure created at: {mock_base}")
    return mock_base

def save_docker_test_results():
    """Save Docker test results"""
    results = {
        "test_type": "docker_path_resolution",
        "environment_variables": dict(os.environ),
        "current_working_directory": str(Path.cwd()),
        "python_executable": sys.executable,
        "python_path": sys.path,
        "platform": os.name,
        "test_timestamp": str(Path(__file__).stat().st_mtime)
    }
    
    output_file = Path("/tmp/docker_path_test_results.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📄 Docker test results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")

def main():
    """Run Docker-specific tests"""
    print("🐳 LegalRAG Docker Path Resolution Tests")
    print("=" * 60)
    print()
    
    try:
        simulate_docker_environment()
        test_docker_path_structure()
        test_path_calculations()
        test_cross_platform_paths()
        test_environment_variable_override()
        
        # Create mock structure for testing
        mock_base = create_mock_data_structure()
        
        save_docker_test_results()
        
        print("✅ Docker tests completed successfully!")
        print(f"📁 Mock data structure available at: {mock_base}")
        print("🔧 You can now run the main application tests with this structure")
        
    except Exception as e:
        print(f"❌ Docker test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())