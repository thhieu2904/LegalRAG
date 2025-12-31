# Form Service

Internal microservice for form processing in LegalRAG system.

## Features

- **CCCD Scanning**: Scan Vietnamese Citizen ID (CCCD) QR codes
- **Form Rendering**: Convert DOCX templates to HTML
- **Form Filling**: Fill DOCX templates with data

## Port

`8015` (Internal microservice)

## API Endpoints

| Endpoint     | Method | Description             |
| ------------ | ------ | ----------------------- |
| `/health`    | GET    | Health check            |
| `/cccd/scan` | POST   | Scan CCCD QR code       |
| `/render`    | POST   | Render DOCX to HTML     |
| `/fill`      | POST   | Fill template with data |

## Usage

### CCCD Scanning

```bash
curl -X POST http://localhost:8015/cccd/scan \
  -H "Content-Type: application/json" \
  -d '{"image_data": "base64_encoded_image"}'
```

### Form Rendering

```bash
curl -X POST http://localhost:8015/render \
  -H "Content-Type: application/json" \
  -d '{"template_path": "forms/doc-id/form-file.docx"}'
```

### Form Filling

```bash
curl -X POST http://localhost:8015/fill \
  -H "Content-Type: application/json" \
  -d '{
    "template_path": "forms/doc-id/form-file.docx",
    "data": {
      "scan_ho_ten": "Nguyễn Văn A",
      "scan_ngay_sinh": "01/01/1990",
      "form_nghe_nghiep": "Kỹ sư"
    }
  }'
```

## Environment Variables

| Variable              | Default                     | Description               |
| --------------------- | --------------------------- | ------------------------- |
| `SERVICE_PORT`        | 8015                        | Service port              |
| `STORAGE_SERVICE_URL` | http://storage-service:8010 | Storage service URL       |
| `STORAGE_TIMEOUT`     | 30                          | Request timeout (seconds) |
| `LOG_LEVEL`           | INFO                        | Logging level             |

## Docker

```bash
# Build
docker build -t form-service:latest .

# Run
docker run -p 8015:8015 form-service:latest
```

## Integration

This service is called by:

- `query-service` - For user-facing form operations

This service calls:

- `storage-service` - To download templates and upload filled forms
