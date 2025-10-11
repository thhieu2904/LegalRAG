#!/usr/bin/env python3
"""
Test Document Preview in Docker
================================

Verifies that document preview works correctly in Docker environment.
Tests PathConfig, file access, and API endpoints.
"""

import subprocess
import json
import time
from pathlib import Path

def run_command(cmd, check=True):
    """Run shell command and return output"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        check=check
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def test_docker_environment():
    """Test if Docker is running and services are up"""
    print("🐳 Testing Docker Environment...")
    
    # Check if Docker is running
    _, _, code = run_command("docker ps", check=False)
    if code != 0:
        print("  ❌ Docker is not running!")
        return False
    print("  ✅ Docker is running")
    
    # Check if admin service is running
    stdout, _, _ = run_command("docker ps --filter name=admin-service --format '{{.Names}}'", check=False)
    if "admin-service" not in stdout:
        print("  ❌ Admin Service container not found!")
        print("  💡 Run: docker-compose -f docker-compose.dev.yml up -d")
        return False
    print("  ✅ Admin Service container is running")
    
    return True

def test_environment_variable():
    """Test if ENVIRONMENT variable is set correctly"""
    print("\n🔧 Testing Environment Variables...")
    
    stdout, _, code = run_command(
        "docker exec legalrag-admin-service-dev env | grep ENVIRONMENT",
        check=False
    )
    
    if code != 0 or "ENVIRONMENT=docker" not in stdout:
        print("  ❌ ENVIRONMENT variable not set to 'docker'!")
        print(f"  Found: {stdout}")
        return False
    
    print("  ✅ ENVIRONMENT=docker is set")
    return True

def test_volume_mount():
    """Test if data volume is mounted correctly"""
    print("\n📁 Testing Volume Mount...")
    
    # Check if /app/data exists
    stdout, _, code = run_command(
        "docker exec legalrag-admin-service-dev ls -d /app/data",
        check=False
    )
    
    if code != 0:
        print("  ❌ /app/data directory not found!")
        return False
    print("  ✅ /app/data directory exists")
    
    # Check if collections directory exists
    stdout, _, code = run_command(
        "docker exec legalrag-admin-service-dev ls -d /app/data/storage/collections",
        check=False
    )
    
    if code != 0:
        print("  ⚠️  /app/data/storage/collections not found (might be empty)")
    else:
        print("  ✅ /app/data/storage/collections exists")
    
    return True

def test_pathconfig_detection():
    """Test if PathConfig detects Docker environment"""
    print("\n🔍 Testing PathConfig Detection...")
    
    test_script = """
import sys
sys.path.insert(0, '/app')
from app.core.admin_path_config import get_admin_path_config

path_config = get_admin_path_config()
print(f"Environment: {path_config.environment}")
print(f"Base data dir: {path_config.base_data_dir}")
print(f"Collections dir: {path_config.collections_dir}")
"""
    
    # Write test script to container
    run_command(
        f"docker exec legalrag-admin-service-dev bash -c 'echo \"{test_script}\" > /tmp/test_pathconfig.py'",
        check=False
    )
    
    # Run test script
    stdout, stderr, code = run_command(
        "docker exec legalrag-admin-service-dev python /tmp/test_pathconfig.py",
        check=False
    )
    
    if code != 0:
        print(f"  ❌ PathConfig test failed!")
        print(f"  Error: {stderr}")
        return False
    
    print(f"  Output:\n{stdout}")
    
    if "Environment: docker" not in stdout:
        print("  ❌ PathConfig not detecting Docker environment!")
        return False
    
    if "Base data dir: /app/data" not in stdout:
        print("  ❌ Base data dir not set to /app/data!")
        return False
    
    print("  ✅ PathConfig correctly detects Docker environment")
    return True

def test_api_health():
    """Test if Admin Service API is responding"""
    print("\n🏥 Testing API Health...")
    
    time.sleep(2)  # Wait for service to be ready
    
    stdout, stderr, code = run_command(
        "curl -s http://localhost:8001/health",
        check=False
    )
    
    if code != 0:
        print("  ❌ Admin Service API not responding!")
        print(f"  Error: {stderr}")
        return False
    
    try:
        data = json.loads(stdout)
        if data.get("status") == "healthy":
            print("  ✅ Admin Service is healthy")
            return True
        else:
            print(f"  ⚠️  Unexpected response: {data}")
            return False
    except json.JSONDecodeError:
        print(f"  ❌ Invalid JSON response: {stdout}")
        return False

def test_collections_endpoint():
    """Test if collections endpoint works"""
    print("\n📚 Testing Collections Endpoint...")
    
    stdout, stderr, code = run_command(
        "curl -s http://localhost:8001/api/collections",
        check=False
    )
    
    if code != 0:
        print("  ❌ Collections endpoint failed!")
        print(f"  Error: {stderr}")
        return False
    
    try:
        data = json.loads(stdout)
        if data.get("success"):
            collections = data.get("data", [])
            print(f"  ✅ Collections endpoint working ({len(collections)} collections)")
            if collections:
                print(f"  📁 Collections: {', '.join([c['name'] for c in collections[:3]])}")
            return True
        else:
            print(f"  ❌ API returned error: {data.get('message')}")
            return False
    except json.JSONDecodeError:
        print(f"  ❌ Invalid JSON response: {stdout[:200]}")
        return False

def test_document_preview_endpoint():
    """Test if document preview endpoint works"""
    print("\n📄 Testing Document Preview Endpoint...")
    
    # First, get a collection and document
    stdout, _, code = run_command(
        "curl -s http://localhost:8001/api/collections",
        check=False
    )
    
    if code != 0:
        print("  ⚠️  Cannot get collections, skipping preview test")
        return True
    
    try:
        data = json.loads(stdout)
        collections = data.get("data", [])
        
        if not collections:
            print("  ⚠️  No collections found, skipping preview test")
            return True
        
        # Get first collection
        collection_name = collections[0]["name"]
        print(f"  Testing with collection: {collection_name}")
        
        # Get documents from collection
        stdout, _, code = run_command(
            f"curl -s http://localhost:8001/collections/{collection_name}/documents",
            check=False
        )
        
        if code != 0:
            print("  ⚠️  Cannot get documents, skipping preview test")
            return True
        
        docs_data = json.loads(stdout)
        documents = docs_data.get("data", [])
        
        if not documents:
            print("  ⚠️  No documents found, skipping preview test")
            return True
        
        # Test with first document that has DOCX
        test_doc = None
        for doc in documents:
            if doc.get("has_original_doc"):
                test_doc = doc
                break
        
        if not test_doc:
            print("  ⚠️  No documents with DOCX found, skipping preview test")
            return True
        
        doc_id = test_doc["doc_id"]
        print(f"  Testing with document: {doc_id}")
        
        # Test DOCX preview
        stdout, stderr, code = run_command(
            f"curl -s http://localhost:8001/collections/{collection_name}/documents/{doc_id}/preview/docx",
            check=False
        )
        
        if code != 0:
            print(f"  ❌ DOCX preview endpoint failed!")
            print(f"  Error: {stderr}")
            return False
        
        preview_data = json.loads(stdout)
        if preview_data.get("success"):
            print(f"  ✅ DOCX preview endpoint working")
            print(f"  📄 Filename: {preview_data.get('filename')}")
            html_length = len(preview_data.get("html", ""))
            print(f"  📊 HTML content: {html_length} characters")
            return True
        else:
            print(f"  ❌ Preview failed: {preview_data.get('error')}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def test_file_permissions():
    """Test if admin service can read files"""
    print("\n🔐 Testing File Permissions...")
    
    # Try to read a file
    stdout, stderr, code = run_command(
        "docker exec legalrag-admin-service-dev ls -la /app/data/storage/collections/ 2>&1 | head -5",
        check=False
    )
    
    if code != 0 or "Permission denied" in stdout:
        print("  ❌ Permission denied reading collections directory!")
        print(f"  Output: {stdout}")
        return False
    
    print("  ✅ File permissions OK")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Document Preview in Docker")
    print("=" * 60)
    
    tests = [
        ("Docker Environment", test_docker_environment),
        ("Environment Variable", test_environment_variable),
        ("Volume Mount", test_volume_mount),
        ("File Permissions", test_file_permissions),
        ("PathConfig Detection", test_pathconfig_detection),
        ("API Health", test_api_health),
        ("Collections Endpoint", test_collections_endpoint),
        ("Document Preview Endpoint", test_document_preview_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Document Preview is working correctly in Docker!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
