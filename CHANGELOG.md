# Changelog

## [Unreleased] - 2025-10-30

### Added - MedQA Dataset & Local LLM Support

#### Local LLM Support
- ✅ **Ollama integration** (`src/llm_client_local.py`)
  - Easy-to-use local inference
  - Supports llama3, mistral, meditron, and other models
  - Zero API costs

- ✅ **llama.cpp integration**
  - Lightweight CPU/GPU inference
  - GGUF model support

- ✅ **vLLM integration**
  - High-performance batch inference
  - Optimized for NVIDIA GPUs

- ✅ **Configuration files**
  - `configs/local_ollama.yaml` - Pre-configured for Ollama
  - Updated `src/config.py` to support new providers
  - Updated `src/llm_client.py` factory

#### MedQA Dataset Tools
- ✅ **Dataset downloader** (`scripts/download_medqa.py`)
  - Downloads from official MedQA GitHub
  - Converts JSONL to our JSON format
  - Supports train/dev/test splits
  - Handles 4-option and 5-option questions

- ✅ **Mock dataset** (`data/medqa_mock_sample.json`)
  - 10 sample questions for testing
  - Ready to use without download

#### Documentation
- ✅ **SETUP_GUIDE.md** - Comprehensive setup instructions
  - MedQA dataset download guide
  - Local LLM setup (Ollama, llama.cpp, vLLM)
  - Model recommendations
  - Cost comparison
  - Troubleshooting

- ✅ **Quickstart script** (`scripts/quickstart.sh`)
  - Interactive setup wizard
  - Installs Ollama
  - Downloads models
  - Downloads MedQA
  - Tests installation

#### Updated Dependencies
- Added `requests>=2.31.0`
- Added `tqdm>=4.66.0`

### Changed
- Updated README.md to reference SETUP_GUIDE.md
- Enhanced provider support in config.py
- Factory pattern supports 6 providers now (openai, anthropic, mock, ollama, llamacpp, vllm)

---

## Summary for Users

### What This Means

**Before**: You needed to pay for OpenAI/Anthropic API calls ($0.50-$60 per 1M tokens).

**Now**: You can run everything locally for free!

### Quick Start

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model (one-time, ~5GB)
ollama pull llama3:8b

# Download MedQA dataset
python scripts/download_medqa.py --split test --options 4

# Run evaluation with local model (zero cost!)
poetry run mas eval --config configs/local_ollama.yaml --n 100
```

### Cost Savings Example

**100 MedQA questions @ ~50k tokens each = 5M tokens**

- GPT-4: ~$150
- GPT-3.5-turbo: ~$2.50
- **Llama3 (local): $0** ⭐

### Recommended Models

1. **llama3:8b** - Best balance (4.7GB, fast, good quality)
2. **meditron** - Medical-specific (4GB, domain knowledge)
3. **llama3:70b** - Best quality (40GB, requires powerful GPU)

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for full details.
