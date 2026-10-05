"""LOCAL TEST FIXTURE, not an application server or a QR decoder.

Uses synthetic identity data and the real Word replacement code. Preview HTML
is a text-only fixture, not Mammoth/Word layout. Does not save images or drafts.
"""
import base64
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import re
import sys

from docx import Document

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'form-service'))
from src.services.docx_fields import extract_docx_fields, fill_docx_fields, iter_paragraph_elements

CONTENT = (ROOT / 'thesis/refs/forms/Giấy đăng ký khai sinh.docx').read_bytes()
HASH = hashlib.sha256(CONTENT).hexdigest()
FIELDS = extract_docx_fields(CONTENT)
DOC = Document(io.BytesIO(CONTENT))
PREVIEW = '<p><strong>LOCAL TEST FIXTURE — dữ liệu giả, không phải bản preview Word chính xác.</strong></p>'
for paragraph in iter_paragraph_elements(DOC):
    text = ''.join(node.text or '' for node in paragraph.iter() if node.tag.endswith('}t'))
    PREVIEW += '<p>' + re.sub(r'\{\{([a-zA-Z0-9_]+)\}\}', lambda match:
        f'<span class="placeholder_{match[1]}">{match[0]}</span>', html.escape(text)) + '</p>'
PREVIEW += '<p>Kiểm thử ô lặp: <span class="placeholder_scan_ho_ten">{{scan_ho_ten}}</span></p>'
STATE = {'fill_calls': 0, 'save_calls': 0, 'last_fill_data': {}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log images, transcripts or field values.

    def reply(self, data, status=200):
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:3006')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.reply({})

    def do_GET(self):
        if self.path == '/test/state':
            self.reply(STATE)
        else:
            self.reply({'message': 'local form test fixture'}, 404)

    def do_POST(self):
        size = int(self.headers.get('Content-Length', 0))
        if size > 2_000_000:
            self.reply({'success': False}, 413)
            return
        data = json.loads(self.rfile.read(size))
        if self.path == '/forms/render':
            self.reply({'success': True, 'message': 'fixture', 'html_content': PREVIEW,
                        'placeholders': FIELDS, 'template_sha256': HASH})
        elif self.path == '/forms/fill':
            STATE['fill_calls'] += 1
            STATE['last_fill_data'] = data.get('data', {})
            if data.get('template_sha256') != HASH:
                self.reply({'success': False, 'message': 'Mẫu đã thay đổi'})
                return
            values = {field: str(data.get('data', {}).get(field, '')) for field in FIELDS}
            filled = sum(bool(value.strip()) for value in values.values())
            self.reply({'success': True, 'message': 'fixture', 'filename': 'khai-sinh-demo.docx',
                        'file_bytes': base64.b64encode(fill_docx_fields(CONTENT, values)).decode('ascii'),
                        'total_fields': len(FIELDS), 'filled_fields': filled,
                        'missing_fields': [field for field, value in values.items() if not value.strip()]})
        elif self.path == '/forms/cccd/scan':
            # Deliberately a stub. It does not decode the supplied image.
            self.reply({'success': True, 'message': 'SYNTHETIC TEST CARD', 'data': {
                'field_cccd': '000000000001', 'field_cmnd': '', 'field_ho_ten': 'NGUOI THU NGHIEM',
                'field_ngay_sinh': '01/01/1990', 'field_gioi_tinh': 'Nam',
                'field_dia_chi': 'DIA CHI DEMO', 'field_ngay_cap': '01/01/2021',
            }})
        elif self.path == '/forms/save':
            STATE['save_calls'] += 1
            self.reply({'success': False, 'message': 'Fixture must not save'}, 400)
        else:
            self.reply({'success': False}, 404)


if __name__ == '__main__':
    print('LOCAL TEST FIXTURE at http://127.0.0.1:8766 — no real QR or storage', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()
