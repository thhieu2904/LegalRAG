#!/usr/bin/env python3
"""
Path Resolution Test Script
===========================
Tests path resolution in both local and Docker environments
Run this script to verify that path configuration works correctly
"""

import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from app.core.path_config import PathConfig

def test_environment_detection():
    """Test environment detection logic"""
    print("🔍 Testing Environment Detection")
    print("-" * 50)
    
    # Test 1: Auto detection
    config = PathConfig()
    print(f"Auto-detected environment: {config.environment}")
    print(f"Base data dir: {config.base_data_dir}")
    
    # Test 2: Force local
    config_local = PathConfig(force_environment="local")
    print(f"Forced local environment: {config_local.environment}")
    print(f"Local base data dir: {config_local.base_data_dir}")
    
    # Test 3: Force docker
    config_docker = PathConfig(force_environment="docker")
    print(f"Forced docker environment: {config_docker.environment}")
    print(f"Docker base data dir: {config_docker.base_data_dir}")
    
    print()

def test_path_resolution():
    """Test path resolution for different scenarios"""
    print("🛣️ Testing Path Resolution")
    print("-" * 50)
    
    config = PathConfig()
    
    # Test different path formats
    test_paths = [
        "data/storage/collections/",
        "../data/storage/collections/",
        "storage/collections/",
        "collections/",
        "data/storage/collections/HCC_collection/documents/DOC_001/test.json"
    ]
    
    for test_path in test_paths:
        try:
            resolved = config.resolve_cross_platform_path(test_path)
            print(f"'{test_path}' -> {resolved}")
        except Exception as e:
            print(f"'{test_path}' -> ERROR: {e}")
    
    print()

def test_path_verification():
    """Test path verification"""
    print("✅ Testing Path Verification")
    print("-" * 50)
    
    config = PathConfig()
    results = config.verify_paths()
    
    print(f"Environment: {results['environment']}")
    print(f"All paths exist: {results['all_paths_exist']}")
    
    print("\nPath Status:")
    for name, status in results['paths_status'].items():
        exists_icon = "✅" if status['exists'] else "❌"
        dir_icon = "📁" if status['is_directory'] else "📄"
        print(f"  {exists_icon} {dir_icon} {name}: {status['path']}")
    
    if results['warnings']:
        print("\n⚠️ Warnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    print()

def test_collections_access():
    """Test collections access functionality"""
    print("📂 Testing Collections Access")
    print("-" * 50)
    
    config = PathConfig()
    
    try:
        collections = config.list_collections()
        print(f"Found {len(collections)} collections:")
        for collection in collections[:5]:  # Show first 5
            print(f"  - {collection}")
            
            # Test document listing
            docs = config.list_documents(collection)
            print(f"    Documents: {len(docs)}")
            
            if docs:
                first_doc = docs[0]
                print(f"    First doc: {first_doc['doc_id']}")
                print(f"    Has forms: {first_doc['has_forms']}")
    
    except Exception as e:
        print(f"Error accessing collections: {e}")
    
    print()

def test_environment_variables():
    """Test environment variable support"""
    print("🌍 Testing Environment Variables")
    print("-" * 50)
    
    # Test with different environment variables
    test_envs = [
        ("LEGALRAG_DATA_PATH", "/custom/data/path"),
        ("PYTHONPATH", "/app"),
        ("ENVIRONMENT", "docker")
    ]
    
    for env_var, env_value in test_envs:
        # Set environment variable
        os.environ[env_var] = env_value
        
        try:
            config = PathConfig()
            print(f"With {env_var}={env_value}:")
            print(f"  Environment: {config.environment}")
            print(f"  Base data dir: {config.base_data_dir}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Clean up
        del os.environ[env_var]
    
    print()

def test_compatibility_with_old_code():
    """Test compatibility with old path resolution patterns"""
    print("🔄 Testing Compatibility with Old Code")
    print("-" * 50)
    
    config = PathConfig()
    
    # Simulate old Path(__file__).parent.parent.parent pattern
    current_file = Path(__file__)
    old_style_base = current_file.parent.parent  # test/ -> rag_service/
    old_style_data = old_style_base / "data" / "storage" / "collections"
    
    # New style
    new_style_collections = config.collections_dir
    
    print(f"Old style path: {old_style_data}")
    print(f"New style path: {new_style_collections}")
    print(f"Paths match: {old_style_data.resolve() == new_style_collections.resolve()}")
    
    # Test if both point to same files
    try:
        old_exists = old_style_data.exists()
        new_exists = new_style_collections.exists()
        print(f"Old path exists: {old_exists}")
        print(f"New path exists: {new_exists}")
        
        if old_exists and new_exists:
            old_files = list(old_style_data.iterdir()) if old_style_data.is_dir() else []
            new_files = list(new_style_collections.iterdir()) if new_style_collections.is_dir() else []
            print(f"Files accessible via old path: {len(old_files)}")
            print(f"Files accessible via new path: {len(new_files)}")
    except Exception as e:
        print(f"Error checking file access: {e}")
    
    print()

def save_test_results():
    """Save test results to file for analysis"""
    config = PathConfig()
    results = {
        "environment": config.environment,
        "base_data_dir": str(config.base_data_dir),
        "collections_dir": str(config.collections_dir),
        "verification": config.verify_paths(),
        "collections_found": len(config.list_collections()),
        "python_path": sys.path,
        "current_working_dir": str(Path.cwd()),
        "script_location": str(Path(__file__))
    }
    
    output_file = Path(__file__).parent / "path_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Test results saved to: {output_file}")

def main():
    """Run all tests"""
    print("🧪 LegalRAG Path Resolution Tests")
    print("=" * 60)
    print()
    
    try:
        test_environment_detection()
        test_path_resolution()
        test_path_verification()
        test_collections_access()
        test_environment_variables()
        test_compatibility_with_old_code()
        save_test_results()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())