#!/usr/bin/env python3
"""Test F5-TTS directly to debug synthesis"""
import sys
sys.path.insert(0, ".")

from app.tts_engine import get_engine
import logging

logging.basicConfig(level=logging.DEBUG)

print("=" * 60)
print("Testing F5-TTS Engine Directly")
print("=" * 60)

engine = get_engine()
info = engine.get_info()
print(f"\nEngine Info:")
for k, v in info.items():
    print(f"  {k}: {v}")

print("\n" + "=" * 60)
print("Test 1: English text (should work)")
print("=" * 60)
try:
    audio, sr = engine.synthesize("Hello, this is a test.", speed=1.0)
    print(f"✅ English: {len(audio)} samples, {len(audio)/sr:.2f}s")
except Exception as e:
    print(f"❌ English failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test 2: Vietnamese (ASCII, no diacritics)")
print("=" * 60)
try:
    audio, sr = engine.synthesize("Xin chao, day la he thong.", speed=1.0)
    print(f"✅ Vietnamese ASCII: {len(audio)} samples, {len(audio)/sr:.2f}s")
except Exception as e:
    print(f"❌ Vietnamese ASCII failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test 3: Vietnamese (with diacritics)")
print("=" * 60)
try:
    audio, sr = engine.synthesize("Xin chào, đây là hệ thống.", speed=1.0)
    print(f"✅ Vietnamese diacritics: {len(audio)} samples, {len(audio)/sr:.2f}s")
except Exception as e:
    print(f"❌ Vietnamese diacritics failed: {e}")
    import traceback
    traceback.print_exc()
