"""
Pre-deployment verification script for LegalRAG v1.0.2
Tests core functionality without TTS service
"""
import requests
import sys

print("=" * 80)
print("🔍 LegalRAG v1.0.2 Pre-Deployment Verification")
print("=" * 80)

services = {
    "RAG Service": "http://localhost:8000/health",
    "Admin Service": "http://localhost:8001/health", 
    "Identifill Service": "http://localhost:8002/health",
    "Frontend": "http://localhost:5173"
}

all_ok = True

for name, url in services.items():
    try:
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ {name} is healthy")
        else:
            print(f"   ⚠️  {name} returned status {response.status_code}")
            all_ok = False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ {name} is not running")
        all_ok = False
    except Exception as e:
        print(f"   ❌ Error testing {name}: {e}")
        all_ok = False

print("\n" + "=" * 80)

if all_ok:
    print("✅ All services are healthy - Ready for v1.0.2 deployment!")
    sys.exit(0)
else:
    print("⚠️  Some services are not available")
    print("Note: This is expected if you haven't started the dev environment yet.")
    print("\nTo start services:")
    print("  Terminal 1: cd frontend && npm run dev")
    print("  Terminal 2: cd rag_service && python main.py")
    print("  Terminal 3: cd admin_service && python main.py")
    print("  Terminal 4: cd identifill_service && python main.py")
    sys.exit(1)
