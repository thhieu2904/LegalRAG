#!/usr/bin/env python3
"""Check WAV file details"""
import soundfile as sf
import numpy as np

wav_file = "test_vietnamese_python.wav"
print(f"Analyzing {wav_file}...")

try:
    audio, sr = sf.read(wav_file)
    duration = len(audio) / sr
    
    print(f"✅ Sample Rate: {sr} Hz")
    print(f"✅ Duration: {duration:.2f}s")
    print(f"✅ Shape: {audio.shape}")
    print(f"✅ Range: [{audio.min():.3f}, {audio.max():.3f}]")
    
    # Check if it's sine wave (fallback)
    if audio.shape[0] > 1000:
        sample = audio[:1000]
        fft = np.fft.fft(sample)
        freqs = np.fft.fftfreq(len(sample), 1/sr)
        peak_freq = abs(freqs[np.argmax(np.abs(fft))])
        
        print(f"\n🔍 Peak frequency: {peak_freq:.1f} Hz")
        
        if 430 < peak_freq < 450:
            print("⚠️  WARNING: This looks like a SINE WAVE (440Hz fallback)")
            print("❌ F5-TTS synthesis FAILED - using fallback tone")
        else:
            print("✅ Audio has varied frequency content (likely real speech)")
    
except Exception as e:
    print(f"❌ Error: {e}")
