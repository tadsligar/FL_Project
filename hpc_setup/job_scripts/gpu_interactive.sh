#!/bin/bash
# Start an interactive GPU session on Easley
# Usage: ./gpu_interactive.sh

echo "Requesting interactive GPU session..."
echo "Parameters:"
echo "  1 node, 8 cores, 1 GPU"
echo "  4 hours time limit"
echo "  32GB memory"
echo ""

salloc -N 1 -n 8 --gres=gpu:1 -t 04:00:00 --mem=32G

# Once allocated, you can:
# - module load cuda/12.0
# - nvidia-smi (check GPU)
# - Run your code with GPU support
