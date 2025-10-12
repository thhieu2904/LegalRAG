"""
Simple Vietnamese TTS Engine using F5-TTS
Direct integration - no complex wrappers
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Tuple
import numpy as np
import soundfile as sf
from io import BytesIO
import unicodedata

# Add F5-TTS to Python path
f5tts_path = str(Path(__file__).parent.parent / "f5_tts")
sys.path.insert(0, f5tts_path)

try:
    from f5_tts.api import F5TTS
    F5TTS_AVAILABLE = True
    print(f"✅ F5-TTS available from: {f5tts_path}")
except ImportError as e:
    F5TTS_AVAILABLE = False
    print(f"⚠️ F5-TTS not available: {e}")
    print(f"   Searched in: {f5tts_path}")

logger = logging.getLogger(__name__)

class VietnameseTTSEngine:
    """Simple Vietnamese TTS using F5-TTS"""
    
    def __init__(self):
        self.f5tts = None
        self.sample_rate = 24000  # default; will sync from model after init
        self.is_ready = False
        
        # Use Vietnamese reference audio for proper Vietnamese pronunciation
        self.ref_audio_path = Path(__file__).parent.parent / "f5_tts" / "infer" / "examples" / "basic" / "basic_ref_vi.wav"
        self.ref_text = ""  # Leave empty to auto-transcribe Vietnamese audio
        
        self._initialize()
    
    def _initialize(self):
        """Initialize F5-TTS model"""
        if not F5TTS_AVAILABLE:
            logger.error("❌ F5-TTS not available")
            return False
            
        try:
            logger.info("🎙️ Initializing F5-TTS Vietnamese engine...")
            
            # Initialize F5-TTS (use supported model id)
            self.f5tts = F5TTS(
                model="F5TTS_Base",  # supported by API (v1 config not recognized here)
                device="cuda" if self._check_cuda() else "cpu"
            )
            # sync sample rate from model config
            try:
                self.sample_rate = int(getattr(self.f5tts, "target_sample_rate", self.sample_rate))
            except Exception:
                pass
            
            self.is_ready = True
            logger.info("✅ F5-TTS Vietnamese engine ready!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize F5-TTS: {e}")
            return False
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def synthesize(self, text: str, *, speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """
        Synthesize Vietnamese speech from text
        Returns: (audio_array, sample_rate)
        """
        if not self.is_ready:
            raise RuntimeError("TTS Engine not initialized")
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        logger.info(f"🎯 Synthesizing Vietnamese: {text[:50]}...")
        # normalize vietnamese text to ascii (strip diacritics) for tokenizer compatibility
        def strip_diacritics(s: str) -> str:
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        gen_text = strip_diacritics(text)
        
        try:
            # Use F5-TTS inference
            wav, sr, _ = self.f5tts.infer(
                ref_file=str(self.ref_audio_path),
                ref_text=self.ref_text,  # Reference text (can be any language)
                gen_text=gen_text,  # Vietnamese text (ascii normalized)
                remove_silence=False,
                speed=float(speed)
            )
            
            # Convert to numpy if needed
            if hasattr(wav, 'numpy'):
                wav = wav.numpy()
            elif hasattr(wav, 'cpu'):
                wav = wav.cpu().numpy()
            
            # Ensure 1D array
            if wav.ndim > 1:
                wav = wav.squeeze()
            
            logger.info(f"✅ Generated {len(wav)/sr:.2f}s Vietnamese audio")
            return wav.astype(np.float32), sr
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Synthesis failed: {e}\n{traceback.format_exc()}")
            # Fallback to simple tone
            duration = max(len(text) * 0.1, 1.0)
            samples = int(duration * self.sample_rate)
            t = np.linspace(0, duration, samples, False)
            fallback_audio = 0.3 * np.sin(2 * np.pi * 440 * t)
            logger.warning(f"⚠️ Using fallback audio: {duration:.2f}s")
            return fallback_audio.astype(np.float32), self.sample_rate
    
    def synthesize_to_bytes(self, text: str, *, speed: float = 1.0) -> bytes:
        """Synthesize and return WAV bytes"""
        audio, sr = self.synthesize(text, speed=speed)
        
        # Convert to WAV bytes
        buffer = BytesIO()
        sf.write(buffer, audio, sr, format="WAV")
        buffer.seek(0)
        return buffer.read()
    
    def get_info(self) -> dict:
        """Get engine information"""
        return {
            "engine": "F5-TTS",
            "model": "F5TTS_Base",
            "language": "Vietnamese",
            "sample_rate": self.sample_rate,
            "status": "Ready" if self.is_ready else "Not Ready",
            "cuda_available": self._check_cuda(),
            "f5tts_available": F5TTS_AVAILABLE
        }

# Global engine instance
_engine = None

def get_engine(force_reload: bool = False):
    """Get global TTS engine instance"""
    global _engine
    if _engine is None or force_reload:
        _engine = VietnameseTTSEngine()
    return _engine