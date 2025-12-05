# Quick Start Guide for 64GB RAM + RTX 4090

**Your Hardware: PERFECT for this project!**
- 64GB RAM ✅ (Llama3:70B needs ~42GB total, 24GB GPU + 18GB RAM)
- RTX 4090 (24GB VRAM) ✅
- Expected performance: 5-15 tokens/second
- Full case (7 agents): 5-10 minutes

---

## Step 1: Install Ollama & Pull Model (10-30 minutes)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Option A: Try Meditron:70B first (medical-specific)
ollama pull meditron:70b

# Option B: If Meditron not available, use Llama3:70B
ollama pull llama3:70b

# Verify installation
ollama list
```

---

## Step 2: Download MedQA Dataset (2-5 minutes)

```bash
cd C:\Users\Tad\OneDrive\Documents\repos\FL_Project

# Download test set (~1,200 questions)
python scripts/download_medqa.py --split test --options 4

# Optional: Download all sets (~12,000 questions)
python scripts/download_medqa.py --split all --options 4
```

---

## Step 3: Test Your MAS System (5-10 minutes)

```bash
# Test with a single case
poetry run mas run \
  --config configs/llama3_70b.yaml \
  --question "65-year-old man with sudden chest pain radiating to left arm, diaphoresis, nausea" \
  --options "A. GERD||B. Acute MI||C. PE||D. MSK pain"

# This will take 5-10 minutes for first run (model loading)
# Subsequent runs will be faster (model stays in memory)
```

---

## Step 4: Run Baseline Comparisons (1-2 hours for 10 questions)

```bash
# Run comparison on 10 questions (pilot test)
python scripts/run_baseline_comparison.py --n 10

# This will test:
# 1. Your adaptive MAS (what you built)
# 2. Single-LLM Chain-of-Thought
# 3. Fixed 4-agent pipeline
# 4. Debate-style dual-agent

# Results saved to runs/baseline_comparison/
```

---

## Step 5: Run Full Evaluation (Overnight)

```bash
# Full evaluation on 100 questions (~10-15 hours)
nohup python scripts/run_baseline_comparison.py --n 100 > eval.log 2>&1 &

# Monitor progress
tail -f eval.log

# Results will be in runs/baseline_comparison/
```

---

## Expected Performance on Your Hardware

| Operation | Time | GPU Usage | RAM Usage |
|-----------|------|-----------|-----------|
| Model load (first time) | 10-20s | 24GB | 18-20GB |
| Single agent call | 30-90s | 24GB | 18-20GB |
| Full case (7 agents) | 5-10 min | 24GB | 18-20GB |
| 10 questions (all 4 methods) | ~2 hours | 24GB | 18-20GB |
| 100 questions (all 4 methods) | ~15-20 hours | 24GB | 18-20GB |

---

## Monitor GPU/RAM Usage

```bash
# Terminal 1: Run evaluation
python scripts/run_baseline_comparison.py --n 10

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi

# Terminal 3: Monitor RAM
watch -n 1 free -h
```

---

## Troubleshooting

### If model loads slowly
- First load always takes longer (downloading to VRAM)
- Keep Ollama running: `ollama serve`
- Set keep-alive: `export OLLAMA_KEEP_ALIVE=3600`

### If out of memory
- Close browser and other apps
- Use swap: Already have 64GB RAM, should be fine
- If still issues, try Q4 quantization instead of default

### If generation is slow
- Expected: 5-15 tok/s on 4090 is normal for 70B
- First token latency: 10-20s (model loading)
- Check GPU usage: Should show ~20-24GB in nvidia-smi

---

## Quick Commands Reference

```bash
# Start Ollama server
ollama serve

# Check which models are installed
ollama list

# Test model directly
ollama run llama3:70b "What is acute MI?"

# Run your MAS system
poetry run mas run --config configs/llama3_70b.yaml --question "..."

# Run baseline comparison
python scripts/run_baseline_comparison.py --n 10

# Monitor GPU
nvidia-smi

# Monitor logs
tail -f eval.log
```

---

## Next: Implement Baselines

Now let's implement the 3 baseline methods from your proposal!
