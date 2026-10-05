"""Local form-only entry point. The production RAG entry point is unchanged."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import forms


@asynccontextmanager
async def lifespan(_app):
    yield
    if forms._http_client is not None:
        await forms._http_client.aclose()
        forms._http_client = None


app = FastAPI(title="LegalRAG Form Dev (QR only)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3006', 'http://127.0.0.1:3006'],
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Content-Type'],
)


@app.middleware('http')
async def no_dossier_storage(request: Request, call_next):
    # This isolated stack has no database and must not persist user drafts.
    if request.url.path.rstrip('/') == '/forms/save':
        return JSONResponse(status_code=403, content={
            'success': False, 'message': 'Bản dev không lưu hồ sơ.',
        })
    return await call_next(request)


app.include_router(forms.router)


@app.get('/health')
async def health():
    return {'status': 'healthy', 'mode': 'form-dev', 'scan_mode': 'qr', 'rag_enabled': False}
