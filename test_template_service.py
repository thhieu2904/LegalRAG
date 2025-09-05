import requests
import aiohttp
import asyncio

async def test_template_service():
    """Test template service communication"""
    
    # Test 1: Direct template download from rag_service
    print("=== Test 1: Direct template download ===")
    try:
        response = requests.get("http://localhost:8000/api/templates/application_template.docx")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ Direct template download: SUCCESS")
        else:
            print(f"❌ Direct template download failed: {response.text}")
    except Exception as e:
        print(f"❌ Exception in direct download: {e}")
    
    # Test 2: Async download như trong service
    print("\n=== Test 2: Async download (như trong service) ===")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/templates/application_template.docx") as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                
                if response.status == 200:
                    content = await response.read()
                    print(f"Content-Length: {len(content)} bytes")
                    print("✅ Async template download: SUCCESS")
                    
                    # Save để test
                    with open("async_template_test.docx", "wb") as f:
                        f.write(content)
                    print("Template saved as 'async_template_test.docx'")
                else:
                    error_text = await response.text()
                    print(f"❌ Async download failed: {error_text}")
                    
    except Exception as e:
        print(f"❌ Exception in async download: {e}")

# Run test
asyncio.run(test_template_service())
