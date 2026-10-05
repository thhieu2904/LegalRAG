"""Dev-only read-only template store. Does not import or modify MinIO/DB."""
import hashlib
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response


app = FastAPI(title='Form Dev Local Template Store')
TEMPLATE = Path('/templates/birth.docx')
KEY = 'forms/demo/Giấy đăng ký khai sinh.docx'
EXPECTED_HASH = '527768935ee88fa1e3b167c2a9300fc5b0a2ba7605cd79e75808d7e6db77b3c0'


def read_template():
    content = TEMPLATE.read_bytes()
    if hashlib.sha256(content).hexdigest() != EXPECTED_HASH:
        raise HTTPException(status_code=409, detail='Template changed; review TS mapping first')
    return content


@app.get('/health')
async def health():
    read_template()
    return {'status': 'healthy', 'storage_connected': True, 'mode': 'form-dev-local-template'}


@app.get('/download')
async def download(file_path: str):
    # Fixed allowlist, not arbitrary filesystem paths or production files.
    if file_path != KEY:
        raise HTTPException(status_code=404, detail='Only the supplied dev template is available')
    return Response(read_template(),
                    media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
