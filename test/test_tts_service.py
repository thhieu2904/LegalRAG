"""
Test script for TTS Service
Verify TTS functionality and performance
"""

import requests
import time
from pathlib import Path

# Configuration
TTS_API_URL = "http://localhost:8003/api/tts"
TEST_OUTPUT_DIR = Path("test_output")

# Test cases
TEST_CASES = [
    {
        "name": "Short legal text",
        "text": "Theo quy định tại Điều 123 Bộ luật Dân sự năm 2015.",
        "expected_duration_ms": 150
    },
    {
        "name": "Medium legal text",
        "text": "Giao dịch dân sự là sự thỏa thuận giữa các bên về việc xác lập, thay đổi hoặc chấm dứt quyền, nghĩa vụ dân sự theo quy định của pháp luật.",
        "expected_duration_ms": 300
    },
    {
        "name": "Long legal text",
        "text": "Theo quy định tại Điều 123 Bộ luật Dân sự năm 2015, giao dịch dân sự là sự thỏa thuận giữa các bên về việc xác lập, thay đổi hoặc chấm dứt quyền, nghĩa vụ dân sự. Giao dịch dân sự phải được xác lập trên cơ sở tự nguyện, bình đẳng, thiện chí, hợp tác và trung thực.",
        "expected_duration_ms": 500
    },
    {
        "name": "Legal terms pronunciation",
        "text": "Bộ luật Dân sự, Bộ luật Hình sự, Bộ luật Lao động, Luật Đất đai, Luật Doanh nghiệp.",
        "expected_duration_ms": 200
    }
]

def test_health_check():
    """Test TTS service health"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{TTS_API_URL.replace('/api/tts', '')}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Model Info")
    print("="*60)
    
    try:
        response = requests.get(f"{TTS_API_URL}/model-info")
        data = response.json()
        print(f"✅ Model: {data['model_info']['model_name']}")
        print(f"✅ Device: {data['model_info']['device']}")
        print(f"✅ Sample Rate: {data['model_info']['sample_rate']}")
        print(f"✅ Loaded: {data['model_info']['loaded']}")
        return True
    except Exception as e:
        print(f"❌ Model info failed: {e}")
        return False

def test_synthesis(test_case: dict, output_dir: Path):
    """Test speech synthesis"""
    text = test_case["text"]
    name = test_case["name"]
    expected_duration = test_case["expected_duration_ms"]
    
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"Text: {text[:50]}...")
    print(f"{'='*60}")
    
    try:
        # Synthesize
        start_time = time.time()
        response = requests.post(
            f"{TTS_API_URL}/synthesize",
            json={"text": text, "format": "wav"}
        )
        duration_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            # Save audio file
            output_file = output_dir / f"{name.replace(' ', '_')}.wav"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            # Get metrics from headers
            audio_size = int(response.headers.get('X-Audio-Size', 0))
            text_length = int(response.headers.get('X-Text-Length', 0))
            
            # Results
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Duration: {duration_ms:.0f}ms (expected: {expected_duration}ms)")
            print(f"✅ Audio Size: {audio_size / 1024:.1f} KB")
            print(f"✅ Text Length: {text_length} chars")
            print(f"✅ Output: {output_file}")
            
            # Performance check
            if duration_ms <= expected_duration * 1.5:
                print(f"✅ Performance: GOOD (within 150% of expected)")
            else:
                print(f"⚠️ Performance: SLOW ({duration_ms / expected_duration:.1f}x expected)")
            
            return True
        else:
            print(f"❌ Synthesis failed: {response.status_code}")
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Synthesis error: {e}")
        return False

def test_voices():
    """Test available voices endpoint"""
    print("\n" + "="*60)
    print("TEST: Available Voices")
    print("="*60)
    
    try:
        response = requests.get(f"{TTS_API_URL}/voices")
        data = response.json()
        
        print(f"✅ Available voices: {len(data['voices'])}")
        for voice in data['voices']:
            print(f"   • {voice['name']} ({voice['language']})")
            print(f"     Model: {voice['model']}")
        
        return True
    except Exception as e:
        print(f"❌ Voices endpoint failed: {e}")
        return False

def run_all_tests():
    """Run all TTS tests"""
    print("\n" + "#"*60)
    print("# TTS SERVICE TEST SUITE")
    print("#"*60)
    
    # Create output directory
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Model Info
    results.append(("Model Info", test_model_info()))
    
    # Test 3: Available Voices
    results.append(("Available Voices", test_voices()))
    
    # Test 4-7: Synthesis tests
    for test_case in TEST_CASES:
        result = test_synthesis(test_case, TEST_OUTPUT_DIR)
        results.append((test_case["name"], result))
    
    # Summary
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print(f"Audio files saved to: {TEST_OUTPUT_DIR.absolute()}")
        return 0
    else:
        print(f"\n⚠️ {total - passed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
