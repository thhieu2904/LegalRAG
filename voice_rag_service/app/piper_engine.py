import os
import subprocess
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import soundfile as sf


class PiperNotAvailable(Exception):
    pass


class PiperTTSEngine:
    """
    Minimal Piper TTS wrapper for Vietnamese.
    Requires environment variables:
      - PIPER_EXE: path to the piper executable (piper or piper.exe)
      - PIPER_MODEL: path to the Vietnamese voice model (.onnx)
      - PIPER_CONFIG (optional): path to corresponding .json config
    """

    def __init__(self) -> None:
        self.piper_exe = os.environ.get("PIPER_EXE")
        self.model_path = os.environ.get("PIPER_MODEL")
        self.config_path = os.environ.get("PIPER_CONFIG")
        self.sample_rate = 22050  # most vi voices are 22.05kHz or 24kHz; we'll infer after first run

        if not self.piper_exe or not self.model_path:
            raise PiperNotAvailable("Piper executable or model is not configured")

        if not Path(self.piper_exe).exists():
            raise PiperNotAvailable(f"Piper executable not found: {self.piper_exe}")
        if not Path(self.model_path).exists():
            raise PiperNotAvailable(f"Piper model not found: {self.model_path}")

    def synthesize(self, text: str, *, speed: float = 1.0) -> Tuple[np.ndarray, int]:
        # Map speed to length_scale (inverse relation)
        length_scale = max(0.5, min(2.0, 1.0 / max(0.25, min(3.0, speed))))

        cmd = [self.piper_exe, "--model", self.model_path, "--output_raw"]
        if self.config_path and Path(self.config_path).exists():
            cmd += ["--config", self.config_path]
        cmd += ["--length_scale", str(length_scale)]

        # Run Piper and capture 16-bit PCM little-endian raw audio and header with sample rate
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if proc.returncode != 0 or not proc.stdout:
            raise RuntimeError(f"Piper synthesis failed: {proc.stderr.decode(errors='ignore')}")

        # Piper --output_raw outputs header 'RATE=xxxxx\n' followed by raw PCM
        data = proc.stdout
        header_end = data.find(b"\n")
        if header_end == -1:
            # Fallback assume 22050Hz
            rate = self.sample_rate
            pcm = data
        else:
            header = data[:header_end].decode("utf-8", errors="ignore").strip()
            rate = int(header.split("=")[-1]) if header.startswith("RATE=") else self.sample_rate
            pcm = data[header_end + 1 :]

        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        self.sample_rate = rate
        return audio, rate

    def synthesize_to_bytes(self, text: str, *, speed: float = 1.0) -> bytes:
        audio, sr = self.synthesize(text, speed=speed)
        buf = BytesIO()
        sf.write(buf, audio, sr, format="WAV")
        buf.seek(0)
        return buf.read()
