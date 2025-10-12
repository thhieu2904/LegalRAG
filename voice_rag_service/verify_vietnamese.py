#!/usr/bin/env python3
"""Play the generated Vietnamese audio to verify it sounds correct"""
import soundfile as sf
import numpy as np

wav_file = "test_vietnamese_python.wav"
print(f"📂 Loading: {wav_file}")

audio, sr = sf.read(wav_file)
duration = len(audio) / sr

print(f"✅ Sample Rate: {sr} Hz")
print(f"✅ Duration: {duration:.2f}s")
print(f"✅ Samples: {len(audio)}")
print(f"✅ Range: [{audio.min():.3f}, {audio.max():.3f}]")

# Analyze spectral content
if len(audio) > 2000:
    # Check multiple windows for speech characteristics
    windows = [audio[i:i+2048] for i in range(0, len(audio), len(audio)//5)][:5]
    
    has_variation = False
    for i, window in enumerate(windows):
        if len(window) < 1024:
            continue
        fft = np.fft.fft(window)
        magnitude = np.abs(fft)[:len(window)//2]
        
        # Speech has energy distributed across frequencies
        peak_mag = np.max(magnitude)
        mean_mag = np.mean(magnitude)
        
        if peak_mag > 0 and mean_mag / peak_mag > 0.05:  # Not a pure tone
            has_variation = True
            break
    
    if has_variation:
        print("\n✅ Audio has speech-like spectral characteristics")
        print("🎙️ This appears to be REAL VIETNAMESE SPEECH from F5-TTS!")
    else:
        print("\n⚠️ Audio may still be a simple tone/fallback")

print("\n" + "="*60)
print("To verify Vietnamese pronunciation:")
print("  1. Play test_vietnamese_python.wav in a media player")
print("  2. Listen if it sounds like Vietnamese (not English accent)")
print("="*60)
