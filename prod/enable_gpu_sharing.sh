#!/bin/bash

# Enable NVIDIA MPS (Multi-Process Service) for GPU sharing
# This allows both RAG and TTS services to use the same GPU efficiently

echo "🔧 Configuring NVIDIA MPS for GPU sharing..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "❌ Please run as root (sudo)"
   exit 1
fi

# Check if CUDA is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA driver not found"
    exit 1
fi

echo "✅ NVIDIA driver found"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

# Set GPU to EXCLUSIVE_PROCESS mode
echo "🔧 Setting GPU 0 to EXCLUSIVE_PROCESS mode..."
nvidia-smi -i 0 -c EXCLUSIVE_PROCESS

# Start MPS control daemon
echo "🚀 Starting NVIDIA MPS control daemon..."
nvidia-cuda-mps-control -d

# Verify MPS is running
sleep 2
if ps aux | grep -q "[n]vidia-cuda-mps"; then
    echo "✅ NVIDIA MPS is running"
    ps aux | grep "[n]vidia-cuda-mps"
else
    echo "❌ NVIDIA MPS failed to start"
    exit 1
fi

# Set environment variable for MPS
export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps
echo "export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps" >> /etc/environment

echo ""
echo "✅ NVIDIA MPS configuration complete!"
echo ""
echo "📊 GPU Status:"
nvidia-smi

echo ""
echo "🐳 Now you can start Docker services:"
echo "   cd prod"
echo "   docker-compose up -d"
echo ""
echo "⚠️ To stop MPS:"
echo "   echo quit | nvidia-cuda-mps-control"
echo "   nvidia-smi -i 0 -c DEFAULT"
