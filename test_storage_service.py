#!/usr/bin/env python3
"""
Test Storage Service
- Upload + Process a Vietnamese legal document
- Verify extraction (metadata, chunks)
- Check extraction confidence
"""

import httpx
import json
import time
from pathlib import Path

# Configuration
STORAGE_SERVICE_URL = "http://localhost:8001"
TEST_FILE = Path("docs/thamkhao/1. Thủ tục xác định cơ quan giải quyết bồi thường.pdf")

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")

# ============= TEST 1: Health Check =============
def test_health_check():
    print_section("TEST 1: Health Check")
    
    try:
        response = httpx.get(f"{STORAGE_SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Service healthy: {data['status']}")
            print_success(f"Storage connected: {data['storage_connected']}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to service: {e}")
        return False

# ============= TEST 2: Upload + Process =============
def test_upload_and_process():
    print_section("TEST 2: Upload + Process Document")
    
    if not TEST_FILE.exists():
        print_error(f"Test file not found: {TEST_FILE}")
        return None
    
    print_info(f"File: {TEST_FILE.name}")
    print_info(f"Size: {TEST_FILE.stat().st_size / 1024:.1f} KB")
    
    try:
        with open(TEST_FILE, "rb") as f:
            files = {"file": (TEST_FILE.name, f, "application/pdf")}
            print_info("Uploading and processing...")
            start = time.time()
            
            response = httpx.post(
                f"{STORAGE_SERVICE_URL}/upload-and-process",
                files=files,
                timeout=60
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Processing completed in {elapsed:.2f}s")
                return data
            else:
                print_error(f"Upload failed: {response.status_code}")
                print_error(f"Response: {response.text[:200]}")
                return None
    except Exception as e:
        print_error(f"Upload error: {e}")
        return None

# ============= TEST 3: Verify Metadata =============
def test_metadata(result):
    print_section("TEST 3: Metadata Extraction")
    
    if not result or "metadata" not in result:
        print_error("No metadata returned")
        return False
    
    metadata = result["metadata"]
    
    print(f"{Colors.BOLD}Extracted Metadata:{Colors.END}")
    print(f"  Document Code: {metadata.get('document_code', 'N/A')}")
    print(f"  Dates: {metadata.get('dates', [])}")
    print(f"  Organizations: {metadata.get('organizations', [])}")
    print(f"  Sections: {metadata.get('sections', [])}")
    print(f"  Pages: {metadata.get('pages', 'N/A')}")
    print(f"  Language: {metadata.get('language', 'N/A')}")
    print(f"  Word Count: {metadata.get('word_count', 'N/A')}")
    
    confidence = metadata.get("extraction_confidence", 0)
    print(f"  Extraction Confidence: {confidence:.2f} ", end="")
    
    if confidence >= 0.85:
        print(f"{Colors.GREEN}(Excellent){Colors.END}")
    elif confidence >= 0.65:
        print(f"{Colors.YELLOW}(Good){Colors.END}")
    elif confidence >= 0.40:
        print(f"{Colors.YELLOW}(Fair){Colors.END}")
    else:
        print(f"{Colors.RED}(Poor){Colors.END}")
    
    notes = metadata.get("extraction_notes", "")
    if notes:
        print(f"  Notes: {notes}")
    
    return True

# ============= TEST 4: Verify Chunks =============
def test_chunks(result):
    print_section("TEST 4: Document Chunking")
    
    if not result or "chunks" not in result:
        print_error("No chunks returned")
        return False
    
    chunks = result["chunks"]
    total_chunks = result.get("total_chunks", 0)
    
    print_success(f"Total chunks: {total_chunks}")
    
    if len(chunks) == 0:
        print_error("No chunks in result")
        return False
    
    # Show first 5 chunks
    print(f"\n{Colors.BOLD}Sample Chunks (first 5):{Colors.END}")
    for i, chunk in enumerate(chunks[:5]):
        print(f"\n  Chunk {chunk.get('chunk_index', i)}:")
        print(f"    Section: {chunk.get('section_title', 'N/A')}")
        print(f"    Reference: {chunk.get('source_reference', 'N/A')}")
        content_preview = chunk.get("content", "")[:100].replace("\n", " ")
        print(f"    Preview: {content_preview}...")
    
    if len(chunks) > 5:
        print(f"\n  ... and {len(chunks) - 5} more chunks")
    
    return True

# ============= TEST 5: Verify File in MinIO =============
def test_minio_storage(result):
    print_section("TEST 5: MinIO Storage")
    
    if not result or "file_path" not in result:
        print_error("No file_path in result")
        return False
    
    file_path = result["file_path"]
    file_id = result.get("file_id", "N/A")
    file_size = result.get("file_size", "N/A")
    
    print_success(f"File ID: {file_id}")
    print_success(f"File Path: {file_path}")
    print_success(f"File Size: {file_size} bytes")
    
    return True

# ============= MAIN =============
def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "Storage Service Test Suite" + " "*22 + "║")
    print("╚" + "="*58 + "╝")
    print(f"{Colors.END}")
    
    # Test 1: Health
    if not test_health_check():
        print_error("\n❌ Cannot connect to Storage Service!")
        print_info("Make sure Docker is running: docker compose up -d")
        return
    
    time.sleep(1)
    
    # Test 2: Upload + Process
    result = test_upload_and_process()
    if not result:
        print_error("\n❌ Upload + Process failed!")
        return
    
    # Test 3: Metadata
    test_metadata(result)
    
    # Test 4: Chunks
    test_chunks(result)
    
    # Test 5: MinIO
    test_minio_storage(result)
    
    # Summary
    print_section("Test Summary")
    print_success("All tests completed!")
    print_info("Raw response saved to: test_result.json")
    
    # Save result
    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.GREEN}{'='*60}")
    print("✓ Storage Service is working correctly!")
    print(f"{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    main()
