# Setup Guide: MedQA Dataset & Local LLMs

This guide covers two important setup options for the Clinical MAS Planner:
1. Downloading the MedQA-USMLE dataset
2. Using local LLMs (no API costs!)

---

## Option 1: Download MedQA Dataset

The MedQA dataset contains thousands of USMLE-style medical questions for evaluation.

### Quick Start

```bash
# Install dependencies (if not already)
pip install requests tqdm

# Download all splits (train, dev, test) with 4 options
python scripts/download_medqa.py --split all --options 4

# Or download just the test set
python scripts/download_medqa.py --split test --options 4
```

### Dataset Statistics

After downloading, you'll have:
- **Training set**: ~10,000 questions
- **Development set**: ~1,200 questions
- **Test set**: ~1,200 questions

Files will be in `data/`:
```
data/
├── medqa_usmle_train_4opt.json  (~10,000 questions)
├── medqa_usmle_dev_4opt.json    (~1,200 questions)
├── medqa_usmle_test_4opt.json   (~1,200 questions)
└── medqa_mock_sample.json       (10 sample questions)
```

### Using the Dataset

```bash
# Evaluate on 100 test questions
poetry run mas eval --config configs/eval_medqa.yaml --n 100

# Or use the test set directly
python -c "
from src.medqa import evaluate_on_subset
result = evaluate_on_subset(
    n=100,
    dataset_path='data/medqa_usmle_test_4opt.json'
)
print(f'Accuracy: {result.accuracy:.2%}')
"
```

### Manual Download (Alternative)

If the script doesn't work, download manually:

1. Visit: https://github.com/jind11/MedQA
2. Download files from `data_clean/questions/US/4_options/`
3. Convert JSONL to JSON format (see script for conversion logic)

---

## Option 2: Use Local LLMs (Recommended for Budget)

Running models locally eliminates API costs and allows offline development.

### Why Use Local LLMs?

✅ **Zero API costs** - No per-token charges
✅ **Privacy** - Data stays on your machine
✅ **Offline** - Work without internet
✅ **Faster iteration** - No rate limits
✅ **Medical models** - Use domain-specific models like Meditron

❌ **Requires**: GPU (8-24GB VRAM) or CPU (16-32GB RAM)
❌ **Slower**: Especially on CPU
❌ **Setup**: Initial model download (~4-40GB)

---

## Setup Method 1: Ollama (Easiest - Recommended)

Ollama makes running local LLMs as easy as Docker.

### Install Ollama

**macOS/Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows**:
Download from https://ollama.ai/download

### Pull a Model

```bash
# General-purpose (8B parameters, ~4.7GB)
ollama pull llama3:8b

# Or larger model (70B parameters, ~40GB, needs powerful GPU)
ollama pull llama3:70b

# Medical-specific model
ollama pull meditron

# Lightweight option (7B, ~4GB)
ollama pull mistral:7b
```

### Configure Clinical MAS Planner

```bash
# Use the local Ollama config
poetry run mas run \
  --config configs/local_ollama.yaml \
  --question "65yo man with chest pain radiating to arm" \
  --options "A. GERD||B. MI||C. PE||D. MSK"
```

Or edit `configs/default.yaml`:
```yaml
provider: "ollama"
model: "llama3:8b"
```

### Start Ollama Server (if not auto-started)

```bash
ollama serve
```

### Verify Setup

```bash
# Test Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "What is acute myocardial infarction?",
  "stream": false
}'

# Test with Clinical MAS Planner
poetry run mas run \
  --config configs/local_ollama.yaml \
  --question "Test question"
```

---

## Setup Method 2: llama.cpp (Lightweight)

Good for CPU-only machines or when you want more control.

### Install llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Or with GPU support (CUDA)
make LLAMA_CUBLAS=1
```

### Download a GGUF Model

Visit https://huggingface.co and search for GGUF models:

```bash
# Example: Download Llama-3-8B quantized
wget https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
```

### Start Server

```bash
./server -m Meta-Llama-3-8B-Instruct.Q4_K_M.gguf \
  --port 8080 \
  --ctx-size 4096 \
  --threads 8
```

### Configure Clinical MAS Planner

Create `configs/local_llamacpp.yaml`:
```yaml
provider: "llamacpp"
model: "llama-3-8b"
temperature: 0.3
max_output_tokens: 800
```

---

## Setup Method 3: vLLM (High-Performance GPU)

Best for production or batch evaluation. Requires NVIDIA GPU.

### Install vLLM

```bash
pip install vllm
```

### Start vLLM Server

```bash
vllm serve meta-llama/Llama-3-8B-Instruct \
  --port 8000 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096
```

### Configure Clinical MAS Planner

```yaml
provider: "vllm"
model: "meta-llama/Llama-3-8B-Instruct"
```

---

## Recommended Models for Medical Reasoning

### General-Purpose Models
1. **Llama-3-8B** (recommended for development)
   - Size: ~4.7GB
   - Speed: Fast on modern GPUs
   - Quality: Good reasoning

2. **Llama-3-70B** (best quality)
   - Size: ~40GB
   - Speed: Slower, needs powerful GPU
   - Quality: Excellent reasoning

3. **Mistral-7B** (lightweight)
   - Size: ~4GB
   - Speed: Very fast
   - Quality: Good for prototyping

### Medical-Specific Models

1. **Meditron-7B/70B**
   - Specialized for medical text
   - Pre-trained on medical literature
   - Download: https://huggingface.co/epfl-llm/meditron

2. **Med42**
   - Medical Llama variant
   - Good for clinical reasoning

3. **BioMistral**
   - Medical version of Mistral
   - Balanced speed/quality

### Pull Medical Models with Ollama

```bash
# Check available medical models
ollama search medical

# Pull a medical model
ollama pull meditron
```

---

## Cost Comparison

### Cloud APIs (per 1M tokens)
- GPT-4: ~$30-60
- GPT-3.5-turbo: ~$0.50-2
- Claude-3: ~$3-15

### Local (one-time cost)
- Initial download: 4-40GB storage
- Inference: $0 (electricity only)
- Hardware: GPU recommended ($500-2000) or CPU (slower)

**For 100 MedQA evaluations (~5M tokens)**:
- Cloud: $15-300
- Local: $0 (after setup)

---

## Performance Tips

### For Faster Inference

1. **Use quantized models** (Q4, Q5 instead of FP16)
   - 4x smaller, 80-90% quality
   - Example: `llama3:8b-q4` instead of `llama3:8b`

2. **GPU acceleration**
   - CUDA: 10-100x faster than CPU
   - Requires NVIDIA GPU with 8GB+ VRAM

3. **Reduce max_output_tokens**
   ```yaml
   max_output_tokens: 512  # Instead of 800
   ```

4. **Lower temperature for consistency**
   ```yaml
   temperature: 0.1  # More deterministic
   ```

### For Better Quality

1. **Use larger models**
   - llama3:70b > llama3:8b > mistral:7b

2. **Increase context window**
   - Allows longer prompts with more examples

3. **Medical-specific models**
   - Meditron, Med42 for domain knowledge

---

## Troubleshooting

### Ollama Issues

**"Cannot connect to Ollama"**
```bash
# Check if running
ollama serve

# Or check status
curl http://localhost:11434/api/tags
```

**"Model not found"**
```bash
# List installed models
ollama list

# Pull the model
ollama pull llama3:8b
```

### Memory Issues

**"Out of memory"**
- Use smaller model (8B instead of 70B)
- Use quantized version (Q4 instead of FP16)
- Reduce context window: `--ctx-size 2048`

### Slow Inference

- Enable GPU support in llama.cpp
- Use vLLM instead of llama.cpp for batch processing
- Reduce `max_output_tokens`

---

## Full Example: End-to-End Setup

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull a medical model
ollama pull meditron

# 3. Download MedQA dataset
python scripts/download_medqa.py --split test --options 4

# 4. Create local config
cat > configs/my_local.yaml << EOF
provider: "ollama"
model: "meditron"
temperature: 0.3
max_output_tokens: 600
EOF

# 5. Run evaluation
poetry run mas eval \
  --config configs/my_local.yaml \
  --n 50

# 6. Check results
ls runs/medqa_eval/
```

---

## Next Steps

Once set up:

1. **Baseline evaluation**: Run on 100 test questions with mock/local model
2. **Compare models**: Try GPT-4, Claude, Llama-3, Meditron
3. **Optimize prompts**: Adjust temperature, examples, instructions
4. **Scale up**: Full evaluation on 1,200 test questions
5. **Publish**: Document results, ablations, insights

---

## Resources

- **Ollama**: https://ollama.ai/
- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **vLLM**: https://github.com/vllm-project/vllm
- **MedQA**: https://github.com/jind11/MedQA
- **Hugging Face Models**: https://huggingface.co/models?search=medical

---

**Questions?** Check the main README.md or open an issue on GitHub.
