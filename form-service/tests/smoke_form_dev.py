"""In-container integration probe: real QR decoding and Query/Form/Storage.

All identities are synthetic. No file, image, draft or transcript is persisted.
Run only with docker-compose.form-dev.yml (see the task launcher).
"""
import base64
import io
from zipfile import ZipFile

import cv2
import httpx
import numpy as np


QUERY = 'http://query-service:8002'
PAYLOAD = '000000000001||NGUOI DEMO|01011990|Nam|DIA CHI DEMO|01012021'
TEMPLATE = 'forms/demo/Giấy đăng ký khai sinh.docx'
EXPECTED_HASH = '527768935ee88fa1e3b167c2a9300fc5b0a2ba7605cd79e75808d7e6db77b3c0'


def encoded(image):
    ok, content = cv2.imencode('.png', image)
    assert ok
    return base64.b64encode(content).decode('ascii')


def main():
    with httpx.Client(base_url=QUERY, timeout=90) as client:
        health = client.get('/health').json()
        assert health.get('mode') == 'form-dev', 'Refusing a non-dev endpoint'
        qr = cv2.QRCodeEncoder_create().encode(PAYLOAD)
        qr = cv2.resize(qr, None, fx=10, fy=10, interpolation=cv2.INTER_NEAREST)
        qr = cv2.copyMakeBorder(qr, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
        scan = client.post('/forms/cccd/scan', json={'image_data': encoded(qr), 'scan_mode': 'qr'})
        scan.raise_for_status()
        result = scan.json()
        assert result['scan_mode'] == 'qr' and result['success']
        assert result['data']['field_cccd'] == '000000000001'
        assert result['data']['field_ho_ten'] == 'NGUOI DEMO'
        print('PASS real generated QR -> Query -> Form decoder (synthetic data)', flush=True)

        padded_qr = cv2.QRCodeEncoder_create().encode(PAYLOAD + '||||')
        padded_qr = cv2.resize(padded_qr, None, fx=7, fy=7, interpolation=cv2.INTER_NEAREST)
        padded_qr = cv2.copyMakeBorder(padded_qr, 28, 28, 28, 28, cv2.BORDER_CONSTANT, value=255)
        padded_result = client.post('/forms/cccd/scan', json={'image_data': encoded(padded_qr)}).json()
        assert padded_result['success'] and padded_result['data'] == result['data']
        assert padded_result['processing_time'] >= 0
        print('PASS empty reserved QR columns -> same validated core identity', flush=True)

        text_only = np.full((250, 800, 3), 255, np.uint8)
        cv2.putText(text_only, 'NGUOI DEMO 000000000001', (15, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        assert not client.post('/forms/cccd/scan', json={'image_data': encoded(text_only)}).json()['success']
        assert client.post('/forms/cccd/scan', json={'image_data': encoded(qr), 'scan_mode': 'ocr'}).status_code == 422
        print('PASS text-only image rejected; OCR mode rejected', flush=True)

        rendered = client.post('/forms/render', json={'template_path': TEMPLATE})
        rendered.raise_for_status()
        preview = rendered.json()
        assert preview['success'] and preview['template_sha256'] == EXPECTED_HASH
        assert len(preview['placeholders']) == 37 and 'form_38' in preview['placeholders']
        assert 'placeholder_form_38' in preview['html_content']
        assert all('placeholder_' + marker in preview['html_content']
                   for marker in ('scan_ho_ten', 'scan_ngay_sinh', 'scan_dia_chi', 'scan_cccd'))
        print('PASS local read-only template store -> Mammoth preview/hash/37 fields', flush=True)

        filled = client.post('/forms/fill', json={
            'template_path': TEMPLATE, 'template_sha256': EXPECTED_HASH,
            'data': {'scan_ho_ten': 'NGUOI DEMO', 'form_38': '2'},
        })
        filled.raise_for_status()
        output = filled.json()
        assert output['success'] and output['filled_fields'] == 2 and output['total_fields'] == 37
        with ZipFile(io.BytesIO(base64.b64decode(output['file_bytes']))) as archive:
            xml = archive.read('word/document.xml').decode('utf-8')
        assert 'NGUOI DEMO' in xml and '{{form_38}}' not in xml and '{{scan_ho_ten}}' not in xml
        changed = client.post('/forms/fill', json={
            'template_path': TEMPLATE, 'template_sha256': '0' * 64, 'data': {},
        }).json()
        assert not changed['success']
        assert client.post('/forms/save', json={}).status_code == 403
        print('PASS Word export in RAM, nested field, changed hash rejected, dossier saving blocked', flush=True)


if __name__ == '__main__':
    main()
