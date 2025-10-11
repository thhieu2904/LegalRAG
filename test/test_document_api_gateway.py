"""
Test Document API Gateway Implementation
=========================================

Test suite for document preview via API Gateway pattern.
Tests both RAG Service internal endpoint and Admin Service proxy endpoint.
"""

import asyncio
import httpx
import json
from pathlib import Path

# Configuration
RAG_SERVICE_URL = "http://localhost:8000"
ADMIN_SERVICE_URL = "http://localhost:8001"
INTERNAL_API_KEY = "dev-internal-key"

# Test data (actual collection in project)
TEST_COLLECTION = "quy_trinh_cap_ho_tich_cap_xa"
TEST_DOC_ID = "DOC_001"


async def test_rag_service_internal_endpoint():
    """Test RAG Service internal documents endpoint"""
    print("\n" + "="*80)
    print("🧪 TEST 1: RAG Service Internal Documents Endpoint")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1.1: DOCX content with API key
        print("\n📝 Test 1.1: Get DOCX content (with API key)")
        try:
            response = await client.get(
                f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/content",
                params={"type": "docx"},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success')}")
                print(f"Content Type: {data.get('content_type')}")
                print(f"Filename: {data.get('filename')}")
                print(f"HTML Length: {len(data.get('content', ''))} chars")
                assert data["success"] == True
                assert data["content_type"] == "html"
                assert "<" in data["content"]  # Check for HTML tags
                print("✅ PASSED: DOCX content retrieved")
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Test 1.2: JSON content with API key
        print("\n📋 Test 1.2: Get JSON content (with API key)")
        try:
            response = await client.get(
                f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/content",
                params={"type": "json"},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success')}")
                print(f"Content Type: {data.get('content_type')}")
                print(f"Filename: {data.get('filename')}")
                print(f"JSON Keys: {list(data.get('content', {}).keys())[:5]}")
                assert data["success"] == True
                assert data["content_type"] == "json"
                assert isinstance(data["content"], dict)
                print("✅ PASSED: JSON content retrieved")
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Test 1.3: Security - No API key (should fail)
        print("\n🔐 Test 1.3: Security check (no API key)")
        try:
            response = await client.get(
                f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/content",
                params={"type": "docx"}
                # No API key header
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 403:
                print("✅ PASSED: Correctly rejected (403 Forbidden)")
            else:
                print(f"❌ FAILED: Expected 403, got {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Test 1.4: Invalid document type
        print("\n⚠️  Test 1.4: Invalid document type")
        try:
            response = await client.get(
                f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/content",
                params={"type": "pdf"},  # Invalid type
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 422:  # Validation error
                print("✅ PASSED: Correctly rejected invalid type")
            else:
                print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Test 1.5: Non-existent document
        print("\n🔍 Test 1.5: Non-existent document")
        try:
            response = await client.get(
                f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/DOC_999/content",
                params={"type": "docx"},
                headers={"X-Internal-API-Key": INTERNAL_API_KEY}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 404:
                print("✅ PASSED: Correctly returned 404")
            else:
                print(f"⚠️  Status {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR: {e}")


async def test_admin_service_preview_endpoint():
    """Test Admin Service preview endpoint (calls RAG Service internally)"""
    print("\n" + "="*80)
    print("🧪 TEST 2: Admin Service Preview Endpoint")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 2.1: DOCX preview
        print("\n📝 Test 2.1: DOCX preview via Admin Service")
        try:
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/api/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/preview/docx"
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success')}")
                print(f"Type: {data.get('type')}")
                print(f"HTML Length: {len(data.get('html', ''))} chars")
                assert data["success"] == True
                assert data["type"] == "docx"
                assert "html" in data
                print("✅ PASSED: Admin Service successfully proxied request")
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Test 2.2: JSON preview
        print("\n📋 Test 2.2: JSON preview via Admin Service")
        try:
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/api/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/preview/json"
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success')}")
                print(f"Type: {data.get('type')}")
                print(f"Data Keys: {list(data.get('data', {}).keys())[:5]}")
                assert data["success"] == True
                assert data["type"] == "json"
                assert "data" in data
                print("✅ PASSED: Admin Service successfully proxied request")
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ ERROR: {e}")


async def test_health_endpoints():
    """Test health endpoints"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Health Checks")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # RAG Service health
        print("\n❤️  Test 3.1: RAG Service health")
        try:
            response = await client.get(f"{RAG_SERVICE_URL}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ RAG Service is healthy")
            else:
                print(f"⚠️  RAG Service health check failed")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Admin Service health
        print("\n❤️  Test 3.2: Admin Service health")
        try:
            response = await client.get(f"{ADMIN_SERVICE_URL}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Admin Service is healthy")
            else:
                print(f"⚠️  Admin Service health check failed")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        # Internal Documents health
        print("\n❤️  Test 3.3: Internal Documents API health")
        try:
            response = await client.get(f"{RAG_SERVICE_URL}/api/internal/documents/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service: {data.get('service')}")
                print(f"Endpoints: {len(data.get('endpoints', []))}")
            else:
                print(f"⚠️  Health check failed")
        except Exception as e:
            print(f"❌ ERROR: {e}")


async def main():
    """Run all tests"""
    print("\n" + "🚀"*40)
    print("DOCUMENT PREVIEW API GATEWAY - TEST SUITE")
    print("🚀"*40)
    
    print(f"\n📌 Configuration:")
    print(f"   RAG Service: {RAG_SERVICE_URL}")
    print(f"   Admin Service: {ADMIN_SERVICE_URL}")
    print(f"   Test Collection: {TEST_COLLECTION}")
    print(f"   Test Document: {TEST_DOC_ID}")
    
    # Run tests
    await test_health_endpoints()
    await test_rag_service_internal_endpoint()
    await test_admin_service_preview_endpoint()
    
    print("\n" + "🏁"*40)
    print("TEST SUITE COMPLETED")
    print("🏁"*40)
    print("\n📊 Summary:")
    print("   - Review logs above for detailed results")
    print("   - Check Docker logs: docker-compose -f docker-compose.dev.yml logs")
    print("   - Verify no direct file access in Admin Service logs")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
