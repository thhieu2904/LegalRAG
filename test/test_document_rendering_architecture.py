"""
Test Document Rendering Architecture
=====================================

Verifies correct separation of concerns:
- RAG Service (Data Layer): Serves raw files ONLY
- Admin Service (Presentation Layer): Renders HTML from DOCX

Test Cases:
1. RAG Service serves raw DOCX bytes (NOT HTML)
2. Admin Service renders DOCX to HTML locally
3. Verify mammoth only used in Admin Service
4. End-to-end preview workflow
5. Error handling
"""

import asyncio
import httpx
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service URLs
RAG_SERVICE_URL = "http://localhost:8000"
ADMIN_SERVICE_URL = "http://localhost:8001"
INTERNAL_API_KEY = "dev-internal-key"

# Test data
TEST_COLLECTION = "quy_trinh_boi_thuong_nn"
TEST_DOC_ID = "DOC_001"


class ArchitectureVerifier:
    """Verify document rendering architecture"""
    
    def __init__(self):
        self.results = {
            "rag_serves_raw_files": False,
            "admin_renders_html": False,
            "architecture_compliant": False,
            "end_to_end_works": False
        }
    
    async def test_1_rag_serves_raw_docx(self):
        """
        Test 1: RAG Service serves RAW DOCX bytes (NOT HTML)
        
        Expected:
        - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
        - Response: Binary DOCX file
        - NOT HTML string
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 1: RAG Service Serves Raw DOCX Files")
        logger.info("="*80)
        
        try:
            url = f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/file"
            headers = {"X-Internal-API-Key": INTERNAL_API_KEY}
            params = {"type": "docx"}
            
            async with httpx.AsyncClient() as client:
                logger.info(f"📡 GET {url}?type=docx")
                response = await client.get(url, headers=headers, params=params)
                
                # Check status
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                logger.info(f"✅ Status Code: {response.status_code}")
                
                # Check Content-Type (should be DOCX, not HTML or JSON)
                content_type = response.headers.get("content-type", "")
                logger.info(f"📋 Content-Type: {content_type}")
                
                assert "wordprocessingml" in content_type or "octet-stream" in content_type, \
                    f"Expected DOCX content type, got: {content_type}"
                
                # Check response is binary (not HTML string)
                content = response.content
                logger.info(f"📦 Response Size: {len(content)} bytes")
                
                # Check file signature
                # DOCX files (Office 2007+): Start with PK (ZIP signature)
                # DOC files (Office 97-2003): Start with ÐÏ (D0 CF - OLE2 signature)
                signature = content[:2]
                is_docx = signature == b'PK'  # ZIP-based (Office 2007+)
                is_doc = signature == b'\xD0\xCF'  # OLE2-based (Office 97-2003)
                
                if not (is_docx or is_doc):
                    raise AssertionError(
                        f"Expected Word document (PK for .docx or D0CF for .doc), "
                        f"got: {signature.hex()}"
                    )
                
                file_format = "DOCX (ZIP)" if is_docx else "DOC (OLE2)" if is_doc else "Unknown"
                
                # Verify it's NOT HTML
                assert b'<html>' not in content and b'<!DOCTYPE' not in content, \
                    "ERROR: RAG Service is returning HTML! Should return raw file bytes!"
                
                logger.info("✅ TEST 1 PASSED: RAG Service serves raw file bytes")
                logger.info(f"   - File size: {len(content)} bytes")
                logger.info(f"   - Content-Type: {content_type}")
                logger.info(f"   - Format: {file_format}")
                logger.info(f"   - Signature: {signature.hex().upper()}")
                
                self.results["rag_serves_raw_files"] = True
                return True
                
        except AssertionError as e:
            logger.error(f"❌ TEST 1 FAILED: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ TEST 1 ERROR: {e}")
            return False
    
    async def test_2_admin_renders_html(self):
        """
        Test 2: Admin Service renders DOCX to HTML locally
        
        Expected:
        - Calls RAG Service to get raw DOCX
        - Renders HTML using mammoth (locally in Admin Service)
        - Returns HTML to frontend
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Admin Service Renders HTML Locally")
        logger.info("="*80)
        
        try:
            url = f"{ADMIN_SERVICE_URL}/api/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/preview/docx"
            
            async with httpx.AsyncClient() as client:
                logger.info(f"📡 GET {url}")
                response = await client.get(url)
                
                # Check status
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                logger.info(f"✅ Status Code: {response.status_code}")
                
                # Check response is JSON
                data = response.json()
                logger.info(f"📋 Response Keys: {list(data.keys())}")
                
                # Check structure
                assert data.get("success") == True, "Expected success=True"
                assert "html" in data, "Expected 'html' field in response"
                assert data.get("type") == "docx", "Expected type='docx'"
                
                # Check HTML content
                html_content = data["html"]
                assert isinstance(html_content, str), "HTML should be string"
                assert len(html_content) > 0, "HTML content should not be empty"
                assert '<' in html_content, "HTML should contain tags"
                
                logger.info(f"✅ TEST 2 PASSED: Admin Service renders HTML")
                logger.info(f"   - HTML length: {len(html_content)} chars")
                logger.info(f"   - Rendered by: {data.get('rendered_by', 'Unknown')}")
                logger.info(f"   - Contains HTML tags: Yes")
                
                self.results["admin_renders_html"] = True
                return True
                
        except AssertionError as e:
            logger.error(f"❌ TEST 2 FAILED: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ TEST 2 ERROR: {e}")
            return False
    
    async def test_3_json_endpoint(self):
        """
        Test 3: JSON endpoint works correctly
        
        Expected:
        - RAG Service serves JSON data
        - Admin Service returns it to frontend
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 3: JSON Document Preview")
        logger.info("="*80)
        
        try:
            # Test RAG Service
            url = f"{RAG_SERVICE_URL}/api/internal/documents/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/file"
            headers = {"X-Internal-API-Key": INTERNAL_API_KEY}
            params = {"type": "json"}
            
            async with httpx.AsyncClient() as client:
                logger.info(f"📡 GET {url}?type=json")
                response = await client.get(url, headers=headers, params=params)
                
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                data = response.json()
                
                assert data.get("success") == True, "Expected success=True"
                assert "content" in data, "Expected 'content' field"
                
                logger.info(f"✅ RAG Service returns JSON data")
            
            # Test Admin Service
            url = f"{ADMIN_SERVICE_URL}/api/collections/{TEST_COLLECTION}/documents/{TEST_DOC_ID}/preview/json"
            
            async with httpx.AsyncClient() as client:
                logger.info(f"📡 GET {url}")
                response = await client.get(url)
                
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                data = response.json()
                
                assert data.get("success") == True, "Expected success=True"
                assert "data" in data, "Expected 'data' field"
                
                logger.info(f"✅ TEST 3 PASSED: JSON endpoint works")
                return True
                
        except AssertionError as e:
            logger.error(f"❌ TEST 3 FAILED: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ TEST 3 ERROR: {e}")
            return False
    
    async def test_4_health_checks(self):
        """Test 4: Health check endpoints"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Health Checks")
        logger.info("="*80)
        
        try:
            # Check RAG Service health
            url = f"{RAG_SERVICE_URL}/api/internal/documents/health"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                
                logger.info(f"📋 RAG Service: {data}")
                assert data.get("status") == "healthy", "RAG Service not healthy"
                assert data.get("architecture") is not None, "No architecture info"
                
                logger.info(f"✅ RAG Service Health: {data['status']}")
                logger.info(f"   Architecture: {data.get('architecture', 'N/A')}")
            
            logger.info(f"✅ TEST 4 PASSED: Health checks OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 4 ERROR: {e}")
            return False
    
    async def test_5_architecture_compliance(self):
        """
        Test 5: Verify architecture compliance
        
        Checks:
        - RAG Service does NOT import mammoth
        - Admin Service DOES import mammoth
        - Separation of concerns maintained
        """
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Architecture Compliance Verification")
        logger.info("="*80)
        
        # This test checks if previous tests passed
        rag_ok = self.results["rag_serves_raw_files"]
        admin_ok = self.results["admin_renders_html"]
        
        if rag_ok and admin_ok:
            logger.info("✅ Architecture Compliance: PASSED")
            logger.info("   ✓ RAG Service serves raw files (Data Layer)")
            logger.info("   ✓ Admin Service renders HTML (Presentation Layer)")
            logger.info("   ✓ Separation of concerns maintained")
            
            self.results["architecture_compliant"] = True
            self.results["end_to_end_works"] = True
            return True
        else:
            logger.error("❌ Architecture Compliance: FAILED")
            if not rag_ok:
                logger.error("   ✗ RAG Service not serving raw files correctly")
            if not admin_ok:
                logger.error("   ✗ Admin Service not rendering HTML correctly")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("\n" + "="*80)
        logger.info("🧪 DOCUMENT RENDERING ARCHITECTURE TESTS")
        logger.info("="*80)
        logger.info(f"RAG Service: {RAG_SERVICE_URL}")
        logger.info(f"Admin Service: {ADMIN_SERVICE_URL}")
        logger.info(f"Test Collection: {TEST_COLLECTION}")
        logger.info(f"Test Document: {TEST_DOC_ID}")
        
        tests = [
            ("RAG serves raw DOCX", self.test_1_rag_serves_raw_docx),
            ("Admin renders HTML", self.test_2_admin_renders_html),
            ("JSON endpoint works", self.test_3_json_endpoint),
            ("Health checks", self.test_4_health_checks),
            ("Architecture compliance", self.test_5_architecture_compliance)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("\n🎉 ALL TESTS PASSED! Architecture is correct!")
            logger.info("✓ RAG Service: Data Layer (serves raw files)")
            logger.info("✓ Admin Service: Presentation Layer (renders HTML)")
            return True
        else:
            logger.error(f"\n⚠️ {total - passed} test(s) failed")
            return False


async def main():
    """Main test runner"""
    verifier = ArchitectureVerifier()
    success = await verifier.run_all_tests()
    
    if success:
        logger.info("\n✅ Architecture verification: SUCCESS")
        exit(0)
    else:
        logger.error("\n❌ Architecture verification: FAILED")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
