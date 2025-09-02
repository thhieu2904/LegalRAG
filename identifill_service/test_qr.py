import qrcode
import base64
import io
import requests

# Generate test QR code with CCCD format
cccd_data = "084201006077|334994717|Nguyễn Thanh Hiếu|02032001|Nam|Ấp Trung, Đại Phước, Càng Long, Trà Vinh|09082021"

# Create QR code
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(cccd_data)
qr.make(fit=True)

# Generate QR code image
qr_image = qr.make_image(fill_color="black", back_color="white")

# Convert to base64
buffered = io.BytesIO()
qr_image.save(buffered, format="PNG")
qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

# Test data
test_data = {
    "image_data": f"data:image/png;base64,{qr_base64}",
    "scan_mode": "qr"
}

# Send request
try:
    response = requests.post("http://localhost:8002/api/v1/qr/scan", 
                           json=test_data,
                           headers={"Content-Type": "application/json"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
