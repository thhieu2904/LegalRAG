import requests
import json

# Test data - với structure đúng cho API v1
data = {
    "scan_ho_ten": "Nguyen Van A",
    "scan_ngay_sinh": "01/01/1990", 
    "scan_dia_chi": "123 Nguyen Trai, Quan 1, TP.HCM",
    "scan_cccd": "123456789012",
    "scan_gioi_tinh": "Nam",
    "template_name": "application_template.docx"
}

# Test form filling endpoint - sử dụng test collection/doc id
try:
    print("Testing form filling endpoint...")
    response = requests.post(
        "http://localhost:8002/api/v1/forms/fill-and-download/legal/test_doc",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        # Save the filled form
        with open("filled_form_final_test.docx", "wb") as f:
            f.write(response.content)
        print("✅ Success! Filled form saved as 'filled_form_final_test.docx'")
        print(f"File size: {len(response.content)} bytes")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
