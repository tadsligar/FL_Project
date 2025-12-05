# Model Recommendations for RTX 4090 (24GB VRAM)

## TL;DR - Best Choices

### 🥇 **RECOMMENDED: Llama3.1:70B** (if available) or **Llama3:70B**
- **Will work**: Yes, with Q4 quantization
- **Quality**: Excellent (top-tier reasoning)
- **Speed**: Moderate (5-15 tok/s on your 4090)
- **Best for**: Final evaluation, publication results

### 🥈 **Alternative 1: Qwen2.5:72B**
- **Will work**: Yes, similar to Llama3:70B
- **Quality**: Excellent (possibly better than Llama3:70B for some tasks)
- **Speed**: Similar to Llama3:70B
- **Advantage**: Sometimes better at structured outputs (JSON)

### 🥉 **Alternative 2: Mixtral-8x7B**
- **Will work**: Perfect fit (13GB with Q4)
- **Quality**: Very good (between 8B and 70B)
- **Speed**: Fast (20-40 tok/s) - 3x faster than 70B!
- **Advantage**: Great balance of speed and quality

---

## Detailed Comparison

| Model | Size (Q4) | VRAM Usage | Speed (tok/s) | Quality | Fits 4090? | Time per Case |
|-------|-----------|------------|---------------|---------|------------|---------------|
| **Llama3:70B** | 42GB | 24GB + offload | 5-15 | ⭐⭐⭐⭐⭐ | ✅ Yes* | 5-10 min |
| **Qwen2.5:72B** | 44GB | 24GB + offload | 5-15 | ⭐⭐⭐⭐⭐ | ✅ Yes* | 5-10 min |
| **Mixtral-8x7B** | 13GB | 13GB only | 20-40 | ⭐⭐⭐⭐ | ✅ Perfect | 2-4 min |
| **Llama3.1:70B** | 42GB | 24GB + offload | 5-15 | ⭐⭐⭐⭐⭐ | ✅ Yes* | 5-10 min |
| Llama3:8B | 4.7GB | 5GB only | 50-100 | ⭐⭐⭐ | ✅ Perfect | 30-60 sec |

*Requires CPU RAM offloading (~18-20GB system RAM)

---

## My Honest Recommendation

For your RTX 4090 and 1-month academic project:

### Option A: **Start with Mixtral-8x7B** (Recommended)

**Why?**
- ✅ **Fits perfectly** in 24GB (no offloading needed)
- ✅ **3-4x faster** than 70B models
- ✅ **Very good quality** (better than 8B, close to 70B)
- ✅ **Great for iteration** during development
- ✅ **Good for JSON outputs** (important for our multi-agent system)

**Downsides:**
- ❌ Not quite as good as 70B for complex reasoning
- ❌ Less "prestige" for publication

```bash
# Quick setup
ollama pull mixtral:8x7b

# Test it
poetry run mas run \
  --config configs/mixtral_8x7b.yaml \
  --question "65yo with chest pain" \
  --options "A. GERD||B. MI||C. PE||D. MSK"
```

### Option B: **Use Llama3:70B for Final Evaluation**

**Why?**
- ✅ **Best quality** available locally
- ✅ **Better for publication** (can cite as "large model")
- ✅ **Will work** on your 4090 (with patience)

**Downsides:**
- ❌ **Slower** (5-10 min per case vs 2-4 min)
- ❌ **Requires 32GB+ system RAM** for offloading
- ❌ **100 questions = 10-15 hours** (vs 3-5 hours with Mixtral)

```bash
# Setup
ollama pull llama3:70b

# Test it (be patient, 5-10 min)
poetry run mas run \
  --config configs/llama3_70b.yaml \
  --question "65yo with chest pain" \
  --options "A. GERD||B. MI||C. PE||D. MSK"
```

---

## Recommended Workflow

### Week 1-3: Development with Mixtral-8x7B

```bash
# Fast iteration
ollama pull mixtral:8x7b

# Run experiments quickly
poetry run mas eval --config configs/mixtral_8x7b.yaml --n 100
# Takes ~3-5 hours instead of 10-15 hours
```

**Benefits:**
- Test prompts, temperatures, Top-K values quickly
- Run multiple ablation studies
- Iterate on agent design

### Week 4: Final Evaluation with Llama3:70B

```bash
# Pull the big model
ollama pull llama3:70b

# Run final evaluation overnight
nohup poetry run mas eval --config configs/llama3_70b.yaml --n 100 > final.log 2>&1 &
```

**Benefits:**
- Best quality results for publication
- Can report: "Evaluated on Llama3:70B, a 70-billion parameter model"
- Compare Mixtral vs Llama3 results in your paper

---

## What Do I Think You Should Do?

Given your setup, here's my honest advice:

### 🎯 **Best Strategy: Use Both**

1. **Primary model: Mixtral-8x7B**
   - Use for all development (weeks 1-3)
   - Fast enough to run 100s of evaluations
   - Good enough quality for system development
   - Perfect fit for your GPU

2. **Validation model: Llama3:70B**
   - Use for final results (week 4)
   - Run on subset (50-100 questions)
   - Include in paper as "high-quality validation"
   - Shows you tested on state-of-the-art

3. **Comparison model: GPT-4 (via API)**
   - Run on small subset (20-30 questions) for comparison
   - Costs ~$5-10 for 30 questions
   - Shows your system works with commercial models too

---

## Expected MedQA Accuracy

Based on benchmarks:

| Model | Expected Accuracy | Your Multi-Agent System |
|-------|-------------------|-------------------------|
| GPT-4 | 85-90% | 88-92% (estimated +3-5%) |
| **Llama3:70B** | **75-80%** | **78-83%** |
| **Mixtral-8x7B** | **68-73%** | **71-76%** |
| Llama3:8B | 55-60% | 58-63% |

The multi-agent approach should give you a few percentage points boost!

---

## Other Models Worth Considering

### Medical-Specific Models

1. **Meditron:70B** (if available)
   - Medical domain fine-tuned
   - May perform better on clinical questions
   - Check: `ollama search meditron`

2. **Med42:70B**
   - Another medical variant
   - Worth testing if available

### General Strong Models

1. **Qwen2.5:72B**
   - Very strong reasoning
   - Excellent at structured outputs
   - Similar to Llama3:70B in size

```bash
# Check what's available
ollama search qwen
ollama search medical
ollama search clinical
```

---

## Configuration Files I'll Create

Let me create configs for both recommended models:

### configs/mixtral_8x7b.yaml
```yaml
model: "mixtral:8x7b"
provider: "ollama"
temperature: 0.3
max_output_tokens: 800

budgets:
  timeout_seconds: 90  # Faster than 70B
logging:
  traces_dir: "runs/mixtral_8x7b"
```

### configs/llama3_70b.yaml
```yaml
model: "llama3:70b"
provider: "ollama"
temperature: 0.3
max_output_tokens: 800

budgets:
  timeout_seconds: 180  # Longer for 70B
logging:
  traces_dir: "runs/llama3_70b"
```

---

## My Final Recommendation

### If you have 64GB system RAM: ✅ Go ahead with Llama3:70B

**Pros:**
- Will work smoothly
- Best quality
- Great for publication

**Setup:**
```bash
ollama pull llama3:70b
poetry run mas eval --config configs/llama3_70b.yaml --n 10
```

### If you have 32GB system RAM: ⚠️ Use Mixtral-8x7B instead

**Pros:**
- No offloading needed (fits in VRAM)
- 3x faster
- Still very good quality
- Can run way more experiments in 1 month

**Setup:**
```bash
ollama pull mixtral:8x7b
poetry run mas eval --config configs/mixtral_8x7b.yaml --n 10
```

### If you have 16GB system RAM: ⛔ Don't use 70B

Use Mixtral-8x7B or Llama3:8B only.

---

## Check Your System RAM

```bash
# Linux/Mac
free -h

# Windows (PowerShell)
Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum | Select-Object Sum

# Or just check Task Manager / Activity Monitor
```

**Tell me how much RAM you have, and I'll give you the final recommendation!**

---

## Bottom Line

- **32GB+ RAM**: Llama3:70B will work fine ✅
- **16-32GB RAM**: Use Mixtral-8x7B instead (better choice) ⭐
- **16GB RAM**: Use Llama3:8B only ⚠️

The difference between 70B and Mixtral is **~5-7% accuracy** but **3-4x speed**.

For a 1-month project, **speed matters** for iteration!
