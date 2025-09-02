import base64
import requests
import json

# Create a simple test image (1x1 pixel)
test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Test data
test_data = {
    "image_data": f"data:image/png;base64,{test_image_b64}",
    "scan_mode": "qr"
}

# Send request
try:
    response = requests.post("http://localhost:8002/api/v1/qr/scan", 
                           json=test_data,
                           headers={"Content-Type": "application/json"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
