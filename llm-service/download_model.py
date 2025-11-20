#!/usr/bin/env python3
"""
Download PhoGPT-4B-Chat model from HuggingFace.

This script downloads the quantized GGUF model file for PhoGPT-4B-Chat
from the HuggingFace repository.

Usage:
    python download_model.py [--output-dir /path/to/models]
"""
import os
import sys
import argparse
from pathlib import Path


def download_model(output_dir: str = "/app/models"):
    """
    Download PhoGPT model from HuggingFace.
    
    Args:
        output_dir: Directory to save the model file
    """
    try:
        from huggingface_hub import hf_hub_download
        print("✓ huggingface_hub found")
    except ImportError:
        print("✗ huggingface_hub not installed")
        print("Install with: pip install huggingface-hub")
        sys.exit(1)
    
    # Model configuration
    repo_id = "uonlp/Vistral-7B-Chat-gguf"
    filename = "ggml-vistral-7B-chat-q4_0.gguf"
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model_file = output_path / "PhoGPT-4B-Chat-Q4_K_M.gguf"
    
    # Check if already downloaded
    if model_file.exists():
        size_gb = model_file.stat().st_size / (1024**3)
        print(f"\n✓ Model already exists: {model_file}")
        print(f"  Size: {size_gb:.2f} GB")
        
        response = input("\nRe-download? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping download.")
            return str(model_file)
    
    # Download model
    print("\n" + "="*60)
    print(f"Downloading {repo_id.split('/')[-1]}")
    print("="*60)
    print(f"Repository: {repo_id}")
    print(f"File: {filename}")
    print(f"Output: {model_file}")
    print("\nThis may take a while (~4 GB download)...")
    print("="*60 + "\n")
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            local_dir_use_symlinks=False
        )
        
        # Move to expected location if needed
        downloaded_file = Path(downloaded_path)
        if downloaded_file != model_file:
            downloaded_file.rename(model_file)
        
        size_gb = model_file.stat().st_size / (1024**3)
        
        print("\n" + "="*60)
        print("✓ Download Complete!")
        print("="*60)
        print(f"Model saved to: {model_file}")
        print(f"Size: {size_gb:.2f} GB")
        print("\nYou can now start the LLM service.")
        print("="*60 + "\n")
        
        return str(model_file)
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download PhoGPT-4B-Chat model from HuggingFace"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/app/models",
        help="Directory to save the model (default: /app/models)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Vietnamese LLM Model Downloader")
    print("="*60 + "\n")
    
    model_path = download_model(args.output_dir)
    
    print(f"\n✓ Model ready at: {model_path}")
    print("\nTo use in LLM service, set environment variable:")
    print(f"  MODEL_PATH={model_path}")
    print()


if __name__ == "__main__":
    main()
