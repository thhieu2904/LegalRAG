# IDentifill Service - QR Code Scanner for CCCD

## 🎯 Overview

IDentifill Service là một service chuyên dụng để quét QR code từ thẻ Căn cước công dân (CCCD) Việt Nam và tự động phát hiện thẻ từ ảnh.

## 🚀 Features

- **QR Code Scanner**: Quét và parse QR code từ thẻ CCCD
- **Card Detection**: Tự động phát hiện và crop thẻ từ ảnh
- **Image Enhancement**: Cải thiện chất lượng ảnh để tăng độ chính xác
- **Fast Processing**: Xử lý nhanh chóng với API đơn giản

## 📦 Installation

### Prerequisites

- Python 3.11
- Conda environment: `identifill_env`

### Setup

```bash
conda activate identifill_env
cd identifill_service
pip install -r requirements.txt
```

### Run Server

```bash
conda activate identifill_env && cd "d:\Personal\LegalRAG_OCR\identifill_service" && uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

## 📚 API Documentation

### Base URL

```
http://localhost:8002
```

### Endpoints

#### 1. Health Check

```http
GET /health
```

#### 2. QR Code Scanning

```http
POST /api/v1/qr/scan
```

**Request Body:**

```json
{
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
  "scan_mode": "qr"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "citizen_id": "084xxxxxxxxx",
    "old_id": "334xxxxxx",
    "full_name": "Nguyễn Văn A,
    "date_of_birth": "28/10/2000",
    "gender": "Nam",
    "address": "Ấp Trung, Đại Phước, Càng Long, Trà Vinh",
    "issue_date": "09/08/2021"
  },
  "message": "QR code scanned successfully",
  "processing_time": 0.15,
  "confidence": 1.0
}
```

#### 3. Enhanced QR Scanning

```http
POST /api/v1/qr/scan-enhanced
```

#### 4. Card Detection

```http
POST /api/v1/card/detect
```

**Request Body:**

```json
{
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
  "auto_crop": true
}
```

## 🔗 Integration with Frontend

### JavaScript/TypeScript Example

```javascript
// QR Code Scanning
const scanQRCode = async (imageBase64) => {
  try {
    const response = await fetch("http://localhost:8002/api/v1/qr/scan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_data: imageBase64,
        scan_mode: "qr",
      }),
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Error scanning QR code:", error);
    return null;
  }
};

// Card Detection
const detectCard = async (imageBase64) => {
  try {
    const response = await fetch("http://localhost:8002/api/v1/card/detect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_data: imageBase64,
        auto_crop: true,
      }),
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Error detecting card:", error);
    return null;
  }
};
```

## 🛠 Development

### Project Structure

```
identifill_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── qr_scanner.py
│   │       │   └── card_detector.py
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── qr_scanner.py
│   │   ├── qr_parser.py
│   │   └── card_detector.py
│   └── utils/
│       └── image_utils.py
├── main.py
├── requirements.txt
└── environment.yml
```

### QR Code Format

CCCD QR code contains data in this format:

```
084201006077|334994717|Nguyễn Thanh Hiếu|02032001|Nam|Ấp Trung, Đại Phước, Càng Long, Trà Vinh|09082021
```

Fields:

1. Citizen ID (12 digits)
2. Old ID (CMND)
3. Full Name
4. Date of Birth (DDMMYYYY)
5. Gender
6. Address
7. Issue Date (DDMMYYYY)

## 🔧 Troubleshooting

### Common Issues

1. **NumPy compatibility**: Install `numpy<2` if OpenCV fails to import
2. **Port conflicts**: Change port in uvicorn command if 8002 is busy
3. **CORS issues**: Add your frontend URL to `BACKEND_CORS_ORIGINS` in config

### Debug Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8002 --log-level debug
```
