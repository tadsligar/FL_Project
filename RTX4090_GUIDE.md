# Llama3:70B on RTX 4090 - Optimization Guide

Your RTX 4090 (24GB VRAM) is perfect for running Llama3:70B with quantization!

---

## Hardware Specs

- **GPU**: RTX 4090
- **VRAM**: 24GB GDDR6X
- **Bandwidth**: 1008 GB/s
- **CUDA Cores**: 16,384

**Verdict**: Excellent for ML inference, but 70B needs quantization to fit.

---

## Quantization Strategy

### What is Quantization?

Quantization reduces model precision from 16-bit (FP16) to 4-bit or 8-bit, cutting memory usage by 2-4x with minimal quality loss.

### Model Size Comparison

| Quantization | Size   | Quality | Fits 4090? | Recommended |
|-------------|--------|---------|------------|-------------|
| FP16        | ~140GB | 100%    | ❌ No      | -           |
| Q8          | ~70GB  | 99%     | ❌ No      | -           |
| Q6_K        | ~53GB  | 95%     | ⚠️ Partial | -           |
| Q5_K_M      | ~48GB  | 92%     | ⚠️ Partial | -           |
| **Q4_K_M**  | **~42GB** | **90%**   | **✅ Yes** | **⭐ Best** |
| Q4_0        | ~39GB  | 85%     | ✅ Yes     | Alternative |

**Recommended**: **Q4_K_M** - Best balance of quality and memory

---

## Memory Strategy

With Q4_K_M (~42GB), your 4090 will use:
- **GPU**: 24GB (model weights + KV cache)
- **CPU RAM**: 18-20GB (overflow via unified memory or offloading)

### System Requirements

Minimum:
- 32GB System RAM
- RTX 4090 (24GB VRAM)
- Fast SSD (for model loading)

Recommended:
- **64GB System RAM** (for smooth offloading)
- RTX 4090
- NVMe SSD

---

## Installation & Setup

### 1. Install Ollama with GPU Support

Ollama automatically detects and uses your 4090:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verify GPU detection
nvidia-smi
```

### 2. Download Llama3:70B

```bash
# Pull the model (Ollama uses Q4_K_M by default for 70B)
ollama pull llama3:70b

# This downloads ~42GB, takes 10-30 minutes
```

### 3. Verify Installation

```bash
# Quick test
ollama run llama3:70b "What is myocardial infarction? One sentence."

# Monitor GPU usage during test
watch -n 1 nvidia-smi
```

### 4. Run Clinical MAS Planner

```bash
# Single case test
poetry run mas run \
  --config configs/llama3_70b.yaml \
  --question "65yo man with chest pain radiating to left arm, diaphoresis, nausea" \
  --options "A. GERD||B. Acute MI||C. PE||D. MSK pain"
```

---

## Performance Expectations

### Speed Benchmarks (RTX 4090 + Q4_K_M)

| Operation | Time | Notes |
|-----------|------|-------|
| Model loading (first call) | 10-20s | One-time per session |
| Token generation | 5-15 tok/s | Depends on context length |
| Planner call (~500 tokens) | 30-60s | Including scoring all specialties |
| Specialist call (~300 tokens) | 20-40s | Per specialist |
| Aggregator call (~400 tokens) | 25-50s | Final decision |
| **Full case (7 agents)** | **5-10 min** | Planner + 5 specialists + aggregator |

### Evaluation Time Estimates

| Questions | Time | Best For |
|-----------|------|----------|
| 10 questions | ~1 hour | Quick testing |
| 50 questions | ~5 hours | Development |
| 100 questions | ~10-15 hours | Overnight run |
| 1,200 questions (full test) | ~5-7 days | Weekend/batch |

---

## Optimization Tips

### 1. Keep Model Loaded

Ollama keeps the model in memory between calls:

```bash
# The model stays loaded for 5 minutes after last use
# Adjust timeout (in seconds):
export OLLAMA_KEEP_ALIVE=3600  # Keep for 1 hour

ollama serve
```

### 2. Batch Processing

For large evaluations, use continuous execution:

```bash
# Run overnight
nohup poetry run mas eval \
  --config configs/llama3_70b.yaml \
  --n 100 \
  > eval_70b.log 2>&1 &

# Monitor progress
tail -f eval_70b.log
```

### 3. Monitor GPU Usage

```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# Or use nvtop (prettier)
sudo apt install nvtop
nvtop
```

### 4. Temperature Settings

```yaml
# In configs/llama3_70b.yaml

# For deterministic results (better for research)
temperature: 0.1

# For more diverse reasoning (default)
temperature: 0.3

# For creative exploration
temperature: 0.7
```

### 5. Reduce Token Budget (if needed)

If inference is too slow:

```yaml
# configs/llama3_70b.yaml
max_output_tokens: 600  # Instead of 800
```

---

## Memory Management

### If You Get OOM (Out of Memory) Errors

1. **Close other GPU applications**
   ```bash
   # Check what's using GPU
   nvidia-smi

   # Kill processes if needed
   kill -9 <PID>
   ```

2. **Increase system swap (Linux)**
   ```bash
   # Create 64GB swap file
   sudo fallocate -l 64G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Use a smaller quantization**
   ```bash
   # Try Q4_0 instead of Q4_K_M (saves ~3GB)
   ollama pull llama3:70b-q4_0
   ```

4. **Reduce context window**
   ```yaml
   # Add to config
   max_context_length: 2048  # Default is 4096
   ```

---

## Alternative: Use vLLM for Maximum Performance

For even better performance, use vLLM instead of Ollama:

### Setup vLLM

```bash
# Install vLLM
pip install vllm

# Serve Llama3:70B with optimizations
vllm serve meta-llama/Meta-Llama-3-70B-Instruct \
  --port 8000 \
  --gpu-memory-utilization 0.95 \
  --quantization awq \
  --max-model-len 4096 \
  --tensor-parallel-size 1
```

### Configure Clinical MAS Planner

```yaml
# configs/llama3_70b_vllm.yaml
provider: "vllm"
model: "meta-llama/Meta-Llama-3-70B-Instruct"
```

**vLLM Benefits**:
- 2-3x faster than Ollama
- Better batching
- More optimization options

**vLLM Drawbacks**:
- More complex setup
- Requires Hugging Face model download
- Less user-friendly

---

## Comparison: 70B vs 8B

For your reference:

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **Llama3:8B** | 4.7GB | Fast (50 tok/s) | Good | Development, iteration |
| **Llama3:70B** | 42GB (Q4) | Slower (10 tok/s) | Excellent | Final evaluation, publication |

**Recommendation**:
- Use **8B for development** (fast iteration, testing prompts)
- Use **70B for final results** (paper-quality accuracy)

---

## Expected Results on MedQA

Based on published benchmarks:

| Model | MedQA Accuracy (estimate) |
|-------|---------------------------|
| GPT-4 | 85-90% |
| GPT-3.5-turbo | 60-65% |
| **Llama3:70B** | **75-80%** |
| Llama3:8B | 55-60% |

With multi-agent system, you may see **+5-10%** improvement over single-agent.

---

## Workflow for Your 1-Month Project

### Week 1: Setup & Baseline
```bash
# Day 1-2: Setup
ollama pull llama3:70b
python scripts/download_medqa.py --split all --options 4

# Day 3-5: Small-scale testing (8B for speed)
poetry run mas eval --config configs/local_ollama.yaml --n 50

# Day 6-7: First 70B run (10 questions)
poetry run mas eval --config configs/llama3_70b.yaml --n 10
```

### Week 2: Development with 8B
```bash
# Fast iteration on prompts, Top-K selection, etc.
# Use llama3:8b for speed (50+ questions per hour)
```

### Week 3: Ablations with 8B
```bash
# Test different configurations
# Temperature: 0.1, 0.3, 0.7
# Top-K: 3, 5, 7
# Specialty selection strategies
```

### Week 4: Final Evaluation with 70B
```bash
# Run overnight/weekend
nohup poetry run mas eval \
  --config configs/llama3_70b.yaml \
  --n 1200 \
  > final_eval.log 2>&1 &

# Analyze results
python scripts/export_traces.py runs/llama3_70b --csv results.csv
```

---

## Troubleshooting

### Model loads but generation is very slow

**Cause**: CPU offloading (not enough VRAM)

**Solution**:
- Close browser/other apps
- Use Q4_0 instead of Q4_K_M
- Increase system RAM

### "Error: CUDA out of memory"

**Solution**:
```bash
# Clear VRAM
ollama stop
pkill ollama
nvidia-smi

# Try again with fresh start
ollama serve
ollama pull llama3:70b
```

### Generation speed < 5 tokens/second

**Check**:
```bash
# Is model using GPU?
nvidia-smi  # Should show ~20GB VRAM usage

# Is CPU being used instead?
htop  # Should show moderate CPU usage
```

---

## Cost Analysis

### Your Setup (RTX 4090 + Llama3:70B)

**One-time costs**:
- Model download: Free
- Disk space: ~42GB

**Ongoing costs**:
- Electricity: ~$0.50-1.00 per 24 hours (at $0.12/kWh, 450W TDP)

**For 100 MedQA evaluations (~15 hours)**:
- **Total cost**: ~$0.75-1.50 in electricity

Compare to GPT-4: **$150** for same evaluations!

**ROI**: You save the cost of your 4090 after ~10-20 large evaluations 😄

---

## Next Steps

1. **Run the setup script**:
   ```bash
   bash scripts/setup_llama3_70b.sh
   ```

2. **Test a single case** (~5-10 min):
   ```bash
   poetry run mas run --config configs/llama3_70b.yaml \
     --question "65yo with chest pain" \
     --options "A. GERD||B. MI||C. PE||D. MSK"
   ```

3. **Small eval** (10 questions, ~1 hour):
   ```bash
   poetry run mas eval --config configs/llama3_70b.yaml --n 10
   ```

4. **Overnight run** (100 questions):
   ```bash
   nohup poetry run mas eval --config configs/llama3_70b.yaml --n 100 > eval.log 2>&1 &
   ```

---

You're all set! Your 4090 is perfect for this project. 🚀
