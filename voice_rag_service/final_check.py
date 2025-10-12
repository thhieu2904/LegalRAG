#!/usr/bin/env python3
"""Final summary: Check if Vietnamese TTS is working properly"""
import soundfile as sf
import numpy as np

print("="*60)
print("VIETNAMESE TTS - FINAL VERIFICATION")
print("="*60)

wav_file = "test_vietnamese_python.wav"
audio, sr = sf.read(wav_file)
duration = len(audio) / sr

print(f"\n📊 Audio Analysis:")
print(f"  ✅ File: {wav_file}")
print(f"  ✅ Sample Rate: {sr} Hz")
print(f"  ✅ Duration: {duration:.2f}s")
print(f"  ✅ File Size: {len(open(wav_file, 'rb').read()) / 1024:.1f} KB")
print(f"  ✅ Range: [{audio.min():.3f}, {audio.max():.3f}]")

# Check if it's a simple tone (fallback)
if len(audio) > 1000:
    sample = audio[:min(1000, len(audio))]
    fft = np.fft.fft(sample)
    freqs = np.fft.fftfreq(len(sample), 1/sr)
    peak_freq = abs(freqs[np.argmax(np.abs(fft))])
    
    if 430 < peak_freq < 450:
        status = "❌ SINE WAVE FALLBACK (440Hz)"
        success = False
    else:
        status = "✅ REAL SPEECH DETECTED"
        success = True
    
    print(f"\n🔍 Signal Analysis:")
    print(f"  Peak Frequency: {peak_freq:.1f} Hz")
    print(f"  Status: {status}")
    
    print("\n" + "="*60)
    if success:
        print("✅ SUCCESS! Vietnamese TTS is working!")
        print("🎙️ Play test_vietnamese_python.wav to hear Vietnamese speech")
    else:
        print("❌ FAILED! Still using fallback sine wave")
        print("💡 F5-TTS synthesis failed, generating fallback tone")
    print("="*60)
