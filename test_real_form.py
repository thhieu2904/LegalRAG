import requests
import json

# Test với form thật từ DOC_001
data = {
    "scan_ho_ten": "Trần Thảo Ly",
    "scan_ngay_sinh": "02/03/1977", 
    "scan_dia_chi": "Ấp Trang, Đại Phước, Cần Giờ, Trà Vinh",
    "scan_cccd": "084177012353",
    "scan_gioi_tinh": "Nữ",
    "template_name": "Khai_sinh_template.docx"  # Template tương ứng với form
}

# Test với DOC_001 thật
try:
    print("Testing with real Khai_sinh form and template...")
    print(f"Collection: quy_trinh_cap_ho_tich_cap_xa")
    print(f"Document: DOC_001") 
    print(f"Template: {data['template_name']}")
    
    response = requests.post(
        "http://localhost:8002/api/v1/forms/fill-and-download/quy_trinh_cap_ho_tich_cap_xa/DOC_001",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        # Save the filled form
        with open("khai_sinh_filled_test.docx", "wb") as f:
            f.write(response.content)
        print("✅ Success! Khai sinh form saved as 'khai_sinh_filled_test.docx'")
        print(f"File size: {len(response.content)} bytes")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
