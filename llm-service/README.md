# LLM Service

Text generation using local Gemma 2 or Llama 3.1 models.

## Models

- **Gemma 2 9B**: Lightweight, good for legal Q&A
- **Llama 3.1 8B**: More powerful, better reasoning

## Requirements

- NVIDIA GPU with 12GB+ VRAM
- CUDA 12.1+
- ~16GB disk for model

## Configuration

```env
MODEL_NAME=google/gemma-2-9b-it
DEVICE=cuda
MAX_LENGTH=2048
```
