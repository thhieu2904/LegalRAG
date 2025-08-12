#!/usr/bin/env python3
"""
Download VinAI PhoGPT-4B-Chat-gguf Model
Official model from VinAI Research for better Vietnamese performance
"""

import requests
import os
from pathlib import Path
from app.core.config import settings
import time

def download_vinai_model():
    """Download VinAI PhoGPT-4B-Chat-Q4_K_M model"""
    
    print("="*70)
    print("📥 DOWNLOADING VINAI PHOGPT-4B-CHAT MODEL")
    print("="*70)
    print(f"🏢 Source: VinAI Research (Official)")
    print(f"📦 Model: PhoGPT-4B-Chat-Q4_K_M.gguf")
    print(f"📏 Size: ~2.36 GB")
    print(f"🎯 URL: {settings.llm_model_url}")
    print()
    
    # Tạo thư mục nếu chưa có
    model_path = Path(settings.llm_model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Kiểm tra nếu model đã tồn tại
    if model_path.exists():
        file_size_mb = model_path.stat().st_size / (1024**2)
        print(f"⚠️  Model already exists: {model_path}")
        print(f"📏 Current size: {file_size_mb:.1f} MB")
        
        response = input("🤔 Download again? (y/N): ").lower().strip()
        if response != 'y':
            print("✅ Using existing model")
            return str(model_path)
    
    try:
        print("🚀 Starting download...")
        start_time = time.time()
        
        # Download với progress tracking
        response = requests.get(settings.llm_model_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Progress indicator mỗi 50MB
                    if downloaded_size % (1024 * 1024 * 50) == 0 or downloaded_size == total_size:
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            elapsed = time.time() - start_time
                            speed = downloaded_size / elapsed / (1024**2)  # MB/s
                            print(f"   📈 {progress:.1f}% ({downloaded_size / (1024**3):.2f} GB) - {speed:.1f} MB/s")
        
        elapsed_time = time.time() - start_time
        final_size_gb = downloaded_size / (1024**3)
        avg_speed = downloaded_size / elapsed_time / (1024**2)
        
        print()
        print("✅ Download completed!")
        print(f"   📏 Size: {final_size_gb:.2f} GB")
        print(f"   ⏱️  Time: {elapsed_time:.1f}s")
        print(f"   🚀 Avg Speed: {avg_speed:.1f} MB/s")
        print(f"   📍 Saved to: {model_path}")
        
        return str(model_path)
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        # Xóa file lỗi nếu có
        if model_path.exists():
            model_path.unlink()
        raise

if __name__ == "__main__":
    try:
        model_path = download_vinai_model()
        print(f"\n🎉 Model ready for use: {model_path}")
    except Exception as e:
        print(f"\n💥 Failed to download model: {e}")
        exit(1)
