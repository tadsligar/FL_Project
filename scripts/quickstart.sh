#!/bin/bash
# Quickstart script for Clinical MAS Planner
# Helps you set up local LLMs and download MedQA

set -e

echo "======================================"
echo "Clinical MAS Planner - Quickstart"
echo "======================================"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    MINGW*)     MACHINE=Windows;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: ${MACHINE}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Ollama
install_ollama() {
    echo "Installing Ollama..."
    echo ""

    if [ "${MACHINE}" = "Mac" ] || [ "${MACHINE}" = "Linux" ]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "Please download Ollama from: https://ollama.ai/download"
        echo "Then re-run this script."
        exit 1
    fi
}

# Check for Ollama
echo "Checking for Ollama..."
if command_exists ollama; then
    echo "✓ Ollama is installed"
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n1 || echo "unknown")
    echo "  Version: ${OLLAMA_VERSION}"
else
    echo "✗ Ollama not found"
    read -p "Would you like to install Ollama? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_ollama
    else
        echo "Skipping Ollama installation."
    fi
fi

echo ""

# Pull a model
if command_exists ollama; then
    echo "Available models:"
    echo "  1) llama3:8b (Recommended - 4.7GB, fast)"
    echo "  2) llama3:70b (Best quality - 40GB, slow)"
    echo "  3) mistral:7b (Lightweight - 4GB, very fast)"
    echo "  4) meditron (Medical-specific - 4GB)"
    echo "  5) Skip model download"
    echo ""

    read -p "Select model to download (1-5): " MODEL_CHOICE

    case $MODEL_CHOICE in
        1) MODEL="llama3:8b";;
        2) MODEL="llama3:70b";;
        3) MODEL="mistral:7b";;
        4) MODEL="meditron";;
        *) echo "Skipping model download"; MODEL="";;
    esac

    if [ ! -z "$MODEL" ]; then
        echo ""
        echo "Downloading ${MODEL}..."
        echo "This may take a few minutes..."
        ollama pull "${MODEL}"
        echo "✓ Model downloaded successfully"

        # Test the model
        echo ""
        echo "Testing model..."
        ollama run "${MODEL}" "What is myocardial infarction? Answer in one sentence." --verbose=false
    fi
fi

echo ""
echo "======================================"

# Check Python
echo "Checking Python..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ ${PYTHON_VERSION}"
else
    echo "✗ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo ""

# Install dependencies
echo "Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    if command_exists poetry; then
        echo "Using Poetry..."
        poetry install
    else
        echo "Using pip..."
        pip install -r requirements.txt
    fi
else
    echo "Error: Not in project directory"
    exit 1
fi

echo ""
echo "======================================"

# Download MedQA
echo "MedQA Dataset"
read -p "Would you like to download the MedQA dataset? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Downloading MedQA test set (~1,200 questions)..."
    python scripts/download_medqa.py --split test --options 4
    echo "✓ MedQA downloaded to data/"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""

# Show next steps
if [ ! -z "$MODEL" ]; then
    echo "Next steps:"
    echo ""
    echo "1. Run a test case:"
    echo "   poetry run mas run \\"
    echo "     --config configs/local_ollama.yaml \\"
    echo "     --question \"65yo man with chest pain radiating to arm\" \\"
    echo "     --options \"A. GERD||B. MI||C. PE||D. MSK\""
    echo ""
    echo "2. Evaluate on MedQA:"
    echo "   poetry run mas eval \\"
    echo "     --config configs/local_ollama.yaml \\"
    echo "     --n 10"
    echo ""
    echo "3. Start API server:"
    echo "   poetry run mas serve --port 8000"
else
    echo "Configure your API key in .env:"
    echo "  cp .env.example .env"
    echo "  # Edit .env and add OPENAI_API_KEY or ANTHROPIC_API_KEY"
    echo ""
    echo "Then run a test case:"
    echo "  poetry run mas run \\"
    echo "    --question \"65yo man with chest pain\" \\"
    echo "    --options \"A. GERD||B. MI||C. PE||D. MSK\""
fi

echo ""
echo "See SETUP_GUIDE.md for more details."
echo ""
