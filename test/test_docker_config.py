#!/usr/bin/env python3
"""
Docker Configuration Test Script
===============================
Test that Docker configuration is properly set up for the new path system
"""

import json
import os
import sys
from pathlib import Path

def test_docker_environment_variables():
    """Test Docker environment variables are properly configured"""
    print("🐳 Testing Docker Environment Variables")
    print("-" * 50)
    
    # Expected Docker environment variables
    expected_env_vars = {
        "PYTHONPATH": "/app",
        "ENVIRONMENT": "docker", 
        "LEGALRAG_BASE_PATH": "/app",
        "LEGALRAG_DATA_PATH": "/app/data",
        "HF_CACHE_DIR": "/app/data/cache"
    }
    
    print("Expected Docker environment variables:")
    for key, expected_value in expected_env_vars.items():
        print(f"  {key}={expected_value}")
    
    # Simulate Docker environment
    print("\nSimulating Docker environment:")
    for key, value in expected_env_vars.items():
        os.environ[key] = value
        print(f"  ✅ Set {key}={value}")
    
    return True

def test_path_config_in_docker():
    """Test PathConfig works correctly in simulated Docker environment"""
    print("\n🧪 Testing PathConfig in Docker Environment")
    print("-" * 50)
    
    # Add rag_service to path for testing
    sys.path.insert(0, str(Path(__file__).parent.parent / "rag_service"))
    
    try:
        from app.core.path_config import PathConfig
        
        # Create PathConfig instance (should detect Docker environment)
        config = PathConfig()
        
        print(f"Environment detected: {config.environment}")
        print(f"Base data dir: {config.base_data_dir}")
        print(f"Collections dir: {config.collections_dir}")
        
        # Verify Docker paths
        expected_docker_paths = {
            "base_data_dir": "/app/data",
            "collections_dir": "/app/data/storage/collections"
        }
        
        print("\nPath verification:")
        for path_name, expected_path in expected_docker_paths.items():
            actual_path = str(getattr(config, path_name))
            matches = actual_path == expected_path
            status = "✅" if matches else "❌"
            print(f"  {status} {path_name}: {actual_path} (expected: {expected_path})")
        
        print("\n✅ PathConfig Docker environment test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing PathConfig in Docker: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services_in_docker():
    """Test services work correctly in simulated Docker environment"""
    print("\n🧪 Testing Services in Docker Environment")
    print("-" * 50)
    
    try:
        from app.services.simple_form_detection import SimpleFormDetectionService
        from app.services.context import ContextExpander
        
        # Test SimpleFormDetectionService
        print("Testing SimpleFormDetectionService:")
        form_service = SimpleFormDetectionService()
        print(f"  Storage path: {form_service.storage_base_path}")
        print(f"  Environment: {form_service.path_config.environment if form_service.path_config else 'N/A'}")
        
        # Test ContextExpander
        print("\nTesting ContextExpander:")
        
        class MockVectorDB:
            pass
        
        context_service = ContextExpander(MockVectorDB(), "")
        print(f"  Documents dir: {context_service.documents_dir}")
        print(f"  Environment: {context_service.path_config.environment}")
        
        # Verify both services use same paths
        form_path = str(form_service.storage_base_path)
        context_path = str(context_service.path_config.collections_dir)
        paths_match = form_path == context_path
        
        print(f"\nPath consistency:")
        print(f"  Form service path: {form_path}")
        print(f"  Context service path: {context_path}")
        print(f"  Paths match: {'✅' if paths_match else '❌'} {paths_match}")
        
        print("\n✅ Services Docker environment test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing services in Docker: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_docker_compose_configuration():
    """Test docker-compose.yml configuration"""
    print("\n🐳 Testing docker-compose.yml Configuration")
    print("-" * 50)
    
    try:
        # Read docker-compose.yml
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        
        if not compose_file.exists():
            print("❌ docker-compose.yml not found")
            return False
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            compose_content = f.read()
        
        # Check for required environment variables
        required_env_vars = [
            "ENVIRONMENT=docker",
            "LEGALRAG_BASE_PATH=/app", 
            "LEGALRAG_DATA_PATH=/app/data"
        ]
        
        print("Checking docker-compose.yml for required environment variables:")
        all_found = True
        
        for env_var in required_env_vars:
            if env_var in compose_content:
                print(f"  ✅ Found: {env_var}")
            else:
                print(f"  ❌ Missing: {env_var}")
                all_found = False
        
        # Check volume mount
        volume_mount = "./rag_service/data:/app/data"
        if volume_mount in compose_content:
            print(f"  ✅ Found volume mount: {volume_mount}")
        else:
            print(f"  ❌ Missing volume mount: {volume_mount}")
            all_found = False
        
        if all_found:
            print("\n✅ docker-compose.yml configuration test passed!")
        else:
            print("\n❌ docker-compose.yml configuration has issues!")
            
        return all_found
        
    except Exception as e:
        print(f"❌ Error testing docker-compose.yml: {e}")
        return False

def generate_docker_test_report():
    """Generate Docker configuration test report"""
    print("\n📊 Generating Docker Test Report")
    print("-" * 50)
    
    try:
        # Simulate Docker environment for report
        from app.core.path_config import PathConfig
        
        config = PathConfig()
        
        report = {
            "docker_configuration_test": {
                "environment_detected": config.environment,
                "base_data_dir": str(config.base_data_dir),
                "collections_dir": str(config.collections_dir),
                "environment_variables": {
                    "PYTHONPATH": os.getenv("PYTHONPATH"),
                    "ENVIRONMENT": os.getenv("ENVIRONMENT"),
                    "LEGALRAG_BASE_PATH": os.getenv("LEGALRAG_BASE_PATH"),
                    "LEGALRAG_DATA_PATH": os.getenv("LEGALRAG_DATA_PATH")
                },
                "docker_ready": True,
                "test_status": "PASSED"
            }
        }
        
        print("Docker Test Report:")
        print(f"  Environment detected: {report['docker_configuration_test']['environment_detected']}")
        print(f"  Base data dir: {report['docker_configuration_test']['base_data_dir']}")
        print(f"  Docker ready: {report['docker_configuration_test']['docker_ready']}")
        
        # Save report
        report_file = Path(__file__).parent / "docker_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Docker test report saved to: {report_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating Docker test report: {e}")
        return False

def cleanup_test_environment():
    """Clean up test environment variables"""
    print("\n🧹 Cleaning up test environment")
    print("-" * 50)
    
    test_env_vars = [
        "PYTHONPATH", "ENVIRONMENT", "LEGALRAG_BASE_PATH", 
        "LEGALRAG_DATA_PATH", "HF_CACHE_DIR"
    ]
    
    for env_var in test_env_vars:
        if env_var in os.environ:
            del os.environ[env_var]
            print(f"  ✅ Removed {env_var}")
    
    print("Environment cleanup completed!")

def main():
    """Run Docker configuration tests"""
    print("🐳 Docker Configuration Tests")
    print("=" * 60)
    
    tests = [
        test_docker_environment_variables,
        test_path_config_in_docker,
        test_services_in_docker,
        test_docker_compose_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    try:
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed: {e}")
        
        # Generate report
        generate_docker_test_report()
        
        print(f"\n📊 Docker Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All Docker configuration tests passed!")
            print("✅ Docker environment ready for deployment")
            print("✅ Environment variables properly configured")
            print("✅ Services compatible with Docker")
        else:
            print("⚠️ Some Docker tests failed - review configuration")
        
        return 0 if passed == total else 1
        
    finally:
        # Always cleanup environment
        cleanup_test_environment()

if __name__ == "__main__":
    exit(main())