"""
FastAPI Voice Service - Vietnamese TTS
Simple and direct implementation
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import TTS engine
from app.tts_engine import get_engine
from app.piper_engine import PiperTTSEngine, PiperNotAvailable

app = FastAPI(title="Voice RAG Service", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoiceRequest(BaseModel):
    text: str
    speed: float = 1.0
    voice: Optional[str] = None  # allow clients to pass voice even if unused
    engine: Optional[str] = None  # "f5tts" (default) or "piper-vi"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Voice RAG Service"}

@app.get("/api/voice/info")
async def get_voice_info():
    """Get TTS engine information"""
    try:
        engine = get_engine()
        info = engine.get_info()
        return {"success": True, "info": info}
    except Exception as e:
        logger.error(f"❌ Error getting info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/synthesize", response_class=Response)
async def synthesize_speech(request: VoiceRequest):
    """
    Synthesize Vietnamese speech from text
    Returns WAV audio file directly
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        logger.info(f"🎙️ Synthesizing: {request.text[:50]}...")
        
        # Get TTS engine
        preferred = (request.engine or "").lower()
        audio_bytes = None

        # Try F5-TTS first unless Piper explicitly requested
        if preferred != "piper-vi":
            try:
                engine = get_engine()
                audio_bytes = engine.synthesize_to_bytes(request.text, speed=request.speed)
            except Exception as e:
                logger.warning(f"F5-TTS failed, will try Piper if available: {e}")

        # If failed or Piper explicitly requested, try Piper
        if audio_bytes is None:
            try:
                piper = PiperTTSEngine()
                audio_bytes = piper.synthesize_to_bytes(request.text, speed=request.speed)
            except PiperNotAvailable:
                if preferred == "piper-vi":
                    raise HTTPException(status_code=500, detail="Piper not configured. Set PIPER_EXE and PIPER_MODEL.")
            except Exception as e:
                logger.error(f"Piper synthesis failed: {e}")
                if preferred == "piper-vi":
                    raise HTTPException(status_code=500, detail=str(e))
        
        if audio_bytes is None:
            raise HTTPException(status_code=500, detail="No TTS engine produced audio")
        
        logger.info(f"✅ Generated {len(audio_bytes)} bytes audio")
        
        # Return WAV file
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=vietnamese_speech.wav",
                "X-Audio-Size": str(len(audio_bytes)),
                "X-Text-Length": str(len(request.text))
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice/voices")
async def get_available_voices():
    """Get available voices"""
    voices = [
        {"id": "f5tts-vietnamese", "name": "F5-TTS Vietnamese", "language": "vi-VN", "engine": "F5-TTS"}
    ]
    try:
        PiperTTSEngine()
        voices.append({"id": "piper-vi", "name": "Piper Vietnamese", "language": "vi-VN", "engine": "Piper"})
    except Exception:
        pass
    return {"success": True, "voices": voices}

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Voice RAG Service...")
    logger.info("   Port: 8003")
    logger.info("   Engine: F5-TTS Vietnamese")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=False
    )