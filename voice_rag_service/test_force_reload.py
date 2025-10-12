#!/usr/bin/env python3
"""Force reload engine and test Vietnamese synthesis"""
import sys
sys.path.insert(0, ".")

from app.tts_engine import get_engine
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 60)
print("FORCE RELOAD ENGINE TEST")
print("=" * 60)

# Force reload to pick up new Vietnamese reference
engine = get_engine(force_reload=True)

info = engine.get_info()
print(f"\nEngine Info:")
for k, v in info.items():
    print(f"  {k}: {v}")

print(f"\nReference Audio: {engine.ref_audio_path}")
print(f"Reference Text: {engine.ref_text}")

print("\n" + "=" * 60)
print("Testing Vietnamese synthesis...")
print("=" * 60)

text = "Xin chào, đây là hệ thống tư vấn pháp luật bằng tiếng Việt."
print(f"Text: {text}")

try:
    audio, sr = engine.synthesize(text, speed=1.0)
    print(f"\n✅ Success!")
    print(f"   Duration: {len(audio)/sr:.2f}s")
    print(f"   Samples: {len(audio)}")
    
    # Save to file
    import soundfile as sf
    sf.write("test_force_reload.wav", audio, sr)
    print(f"   Saved to: test_force_reload.wav")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
