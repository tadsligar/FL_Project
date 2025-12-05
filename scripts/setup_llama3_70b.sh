#!/bin/bash
# Setup script for Llama3:70B on RTX 4090 (24GB VRAM)

set -e

echo "=================================================="
echo "Llama3:70B Setup for RTX 4090 (24GB VRAM)"
echo "=================================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama not installed"
    echo "Install with: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

echo "✓ Ollama found"
echo ""

# Check GPU
echo "Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo ""
else
    echo "Warning: nvidia-smi not found. Make sure CUDA is installed."
    echo ""
fi

# Explain quantization options
echo "=================================================="
echo "Quantization Options for 70B on 24GB VRAM"
echo "=================================================="
echo ""
echo "Full model (FP16):     ~140GB - Won't fit in 24GB"
echo "Q8 quantization:       ~70GB  - Won't fit in 24GB"
echo "Q6_K quantization:     ~53GB  - Won't fit in 24GB"
echo "Q5_K_M quantization:   ~48GB  - Won't fit in 24GB"
echo "Q4_K_M quantization:   ~42GB  - WILL FIT with offloading"
echo "Q4_0 quantization:     ~39GB  - WILL FIT with offloading"
echo ""
echo "Recommended for RTX 4090: Q4_K_M (best quality that fits)"
echo ""
echo "Quality comparison:"
echo "  Q8:    ~99% of FP16 quality"
echo "  Q6_K:  ~95% of FP16 quality"
echo "  Q5_K:  ~92% of FP16 quality"
echo "  Q4_K:  ~85-90% of FP16 quality (still excellent!)"
echo ""

read -p "Download llama3:70b-q4_K_M? (Recommended, ~42GB) [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Downloading llama3:70b with Q4_K_M quantization..."
    echo "This will take 10-30 minutes depending on your internet speed."
    echo ""

    # For Ollama, we pull the default 70b which is Q4 quantized
    ollama pull llama3:70b

    echo ""
    echo "✓ Model downloaded successfully!"
else
    echo "Skipping download. You can download later with:"
    echo "  ollama pull llama3:70b"
    exit 0
fi

echo ""
echo "=================================================="
echo "Testing Model"
echo "=================================================="
echo ""

echo "Running a quick test..."
echo ""

ollama run llama3:70b "What is acute myocardial infarction? Answer in 2 sentences." <<< ""

echo ""
echo "=================================================="
echo "Performance Optimization Tips"
echo "=================================================="
echo ""
echo "Your RTX 4090 setup:"
echo "  • VRAM: 24GB"
echo "  • Model size: ~42GB (Q4_K_M)"
echo "  • Strategy: GPU + CPU offloading"
echo ""
echo "Expected performance:"
echo "  • First token: ~10-20 seconds (model loading)"
echo "  • Generation: ~5-15 tokens/second"
echo "  • Per agent call: 30-90 seconds"
echo "  • Full case (7 agents): 5-10 minutes"
echo ""
echo "Optimization options:"
echo "  1. Increase GPU layers in Ollama (if using Modelfile)"
echo "  2. Use batch processing for multiple questions"
echo "  3. Keep model loaded between calls (Ollama does this automatically)"
echo "  4. Consider Q5_K_M if you have swap space"
echo ""

echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test with a single case:"
echo "   poetry run mas run \\"
echo "     --config configs/llama3_70b.yaml \\"
echo "     --question \"65-year-old man with chest pain radiating to left arm and diaphoresis\" \\"
echo "     --options \"A. GERD||B. Acute MI||C. PE||D. MSK pain\""
echo ""
echo "2. Download MedQA dataset:"
echo "   python scripts/download_medqa.py --split test --options 4"
echo ""
echo "3. Run small evaluation (10 questions, ~1 hour):"
echo "   poetry run mas eval --config configs/llama3_70b.yaml --n 10"
echo ""
echo "4. Run full evaluation (100 questions, ~10-15 hours):"
echo "   nohup poetry run mas eval --config configs/llama3_70b.yaml --n 100 > eval.log 2>&1 &"
echo ""
