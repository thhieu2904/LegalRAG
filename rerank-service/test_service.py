"""
Test script for Rerank Service.
Run this to verify the service is working correctly.
"""
import requests
import json
import time

# Service URL
BASE_URL = "http://localhost:8013"

def test_health():
    """Test health endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Status: {data['status']}")
        print(f"✓ Service: {data['service']}")
        print(f"✓ Model Loaded: {data['model_loaded']}")
        print(f"✓ Device: {data['device']}")
        return True
        
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_rerank():
    """Test reranking with Vietnamese legal documents."""
    print("\n" + "="*60)
    print("TEST 2: Reranking Vietnamese Legal Documents")
    print("="*60)
    
    # Sample query and documents
    request_data = {
        "query": "điều kiện thành lập công ty trách nhiệm hữu hạn",
        "documents": [
            "Văn bản về quy trình đăng ký kinh doanh cho hộ cá thể",
            "Điều kiện thành lập công ty trách nhiệm hữu hạn theo Luật Doanh nghiệp 2020",
            "Hướng dẫn nộp hồ sơ đăng ký thuế cho doanh nghiệp",
            "Quy định về vốn điều lệ tối thiểu khi thành lập công ty TNHH",
            "Thủ tục thay đổi đăng ký kinh doanh đối với công ty cổ phần"
        ],
        "top_k": 3
    }
    
    print(f"\nQuery: {request_data['query']}")
    print(f"Documents: {len(request_data['documents'])} candidates")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/rerank",
            json=request_data,
            timeout=30
        )
        elapsed = time.time() - start
        
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✓ Reranking completed in {elapsed:.3f}s")
        print(f"✓ Processing time (server): {data['processing_time']:.3f}s")
        print(f"✓ Model: {data['model_name']}")
        print(f"\nTop {len(data['results'])} Results:")
        
        for result in data['results']:
            print(f"\n  Rank {result['rank']}: (Score: {result['score']:.4f})")
            print(f"  Original Index: {result['index']}")
            print(f"  Text: {result['text'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Reranking test failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid input."""
    print("\n" + "="*60)
    print("TEST 3: Error Handling")
    print("="*60)
    
    # Test with empty documents
    print("\n3.1 Empty documents list...")
    try:
        response = requests.post(
            f"{BASE_URL}/rerank",
            json={"query": "test", "documents": []},
            timeout=5
        )
        
        if response.status_code == 400:
            print("✓ Correctly rejected empty documents")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    # Test with too many documents
    print("\n3.2 Too many documents (>100)...")
    try:
        response = requests.post(
            f"{BASE_URL}/rerank",
            json={
                "query": "test",
                "documents": ["doc"] * 101
            },
            timeout=5
        )
        
        if response.status_code == 400:
            print("✓ Correctly rejected >100 documents")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RERANK SERVICE TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    
    results = {
        "health": test_health(),
        "rerank": test_rerank(),
        "errors": test_error_handling()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.ljust(20)}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
