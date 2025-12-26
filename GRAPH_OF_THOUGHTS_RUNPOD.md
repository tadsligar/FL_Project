# Graph of Thoughts on RunPod - Quick Start

This guide gets you running Graph of Thoughts on RunPod in under 10 minutes.

## What is Graph of Thoughts?

Graph of Thoughts (GoT) is a neurosymbolic reasoning architecture that represents diagnostic reasoning as a directed graph:

- **15+ LLM calls per question** (vs 7 for current best method)
- **Feedback loops** for iterative hypothesis refinement
- **Cross-pollination** between competing diagnoses
- **Temperature scheduling** optimized per reasoning stage (1.0 → 0.7 → 0.5 → 0.0)

**Goal:** Beat current best accuracy of 73.6% (Progressive Temperature Parallel V4)

## Architecture Overview

```
INITIALIZE (temp=0.7)
    ↓ generates
HYPOTHESES [A,B,C,D] (temp=1.0)
    ↓ supports
EVIDENCE [A,B,C,D] (temp=0.7)
    ↓ informs + cross-pollination
REFINEMENT [A,B,C,D] (temp=0.5)
    ↓ aggregates
AGGREGATION (temp=0.0)
    ↓ concludes
DECISION (temp=0.0)
```

**Key Innovation:** Hypotheses are refined with access to ALL competing hypotheses and their evidence, enabling cross-pollination of diagnostic reasoning.

## Quick Start (5 Steps)

### Step 1: Deploy RunPod

1. Go to https://www.runpod.io/
2. Deploy GPU Pod → Choose **RTX A6000** (48GB)
3. Template: **vLLM**
4. Model: `Qwen/Qwen2.5-32B-Instruct`
5. Deploy and wait ~5 minutes for model to load

**Cost:** ~$0.79/hr (On-Demand) or ~$0.28/hr (Spot)

### Step 2: Get Your Endpoint

From RunPod dashboard:
```
Connect → HTTP Service → Copy URL
Example: https://abc123-8000.proxy.runpod.net
```

### Step 3: Update Config

Edit `configs/runpod_graph_of_thoughts.yaml`:

```yaml
vllm:
  base_url: https://YOUR_ACTUAL_POD_ID-8000.proxy.runpod.net  # Paste your URL here!
```

### Step 4: Test Connection

```bash
# Quick test
./scripts/runpod_got_quickstart.sh
```

Or manually:
```bash
python scripts/test_graph_of_thoughts.py \
  --n 1 \
  --config configs/runpod_graph_of_thoughts.yaml
```

### Step 5: Run Evaluation

**Recommended: Start with 100 questions (~2 hours, ~$2)**

```bash
python scripts/test_graph_of_thoughts.py \
  --n 100 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --output runs/graph_of_thoughts_runpod_n100
```

**Full dataset: 1,071 questions (~20 hours, ~$20)**

```bash
python scripts/test_graph_of_thoughts.py \
  --n 1071 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --output runs/graph_of_thoughts_runpod_full
```

## Cost & Time Estimates

| Questions | Time | Cost (On-Demand) | Cost (Spot) |
|-----------|------|------------------|-------------|
| 1 | 1 min | $0.01 | $0.005 |
| 10 | 10 min | $0.10 | $0.04 |
| 100 | 2 hrs | $2 | $0.80 |
| 1,071 | 20 hrs | $20 | $7 |

💡 **Tip:** Use Spot instances to save 70% (but can be interrupted)

## Monitoring Progress

### Real-time
```bash
# Terminal shows live updates
Question 15/100
Correct Answer: B
  [OK] Predicted: B (52.3s, 13,200 tokens)
  Graph: 15 nodes, 14 edges
```

### Current Accuracy
```bash
cat runs/graph_of_thoughts_runpod_full/summary.json | jq '.accuracy'
```

### Resume if Interrupted
```bash
python scripts/test_graph_of_thoughts.py \
  --n 1071 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --resume runs/graph_of_thoughts_runpod_full
```

## Expected Performance

### Comparison to Baselines

| Method | Accuracy | Calls/Q | Tokens/Q |
|--------|----------|---------|----------|
| Zero-Shot | 57.8% | 1 | 513 |
| Progressive Temp | 72.2% | 5 | 7,089 |
| **Prog Temp Parallel V4** | **73.6%** | 7 | 11,049 |
| **Graph of Thoughts** | **?** | **15** | **~12,000** |

**Success Criteria:**
- 🎯 **Target:** >74.0% (beat current best)
- 🏆 **Stretch:** >75.0% (significant improvement)
- ⚠️ **Threshold:** <73.6% = architecture doesn't justify cost

### Why GoT Might Win

1. ✅ **Feedback loops:** Hypotheses refined based on evidence
2. ✅ **Cross-pollination:** Each option informed by all others
3. ✅ **Explicit evidence:** Dedicated stage for pro/con analysis
4. ✅ **Optimized temps:** 1.0 for diversity, 0.0 for synthesis

### Why GoT Might Lose

1. ❌ **Error accumulation:** 15 calls = 15 chances for mistakes
2. ❌ **Overcomplexity:** Simple cases might suffer from overthinking
3. ❌ **Sequential bottleneck:** Can't parallelize refinement stage
4. ❌ **Prompt engineering:** Multi-stage prompts harder to optimize

## Troubleshooting

### Connection Failed
```bash
# Test endpoint
curl https://YOUR_POD_ID-8000.proxy.runpod.net/health
```

✅ Should return: `{"status":"ok"}` or similar

### Slow Performance
- Check RunPod GPU utilization (should be >85%)
- Increase timeout in config if getting timeout errors
- Consider upgrading to A100 for faster inference

### Out of Memory
- Graph of Thoughts uses ~12K tokens per question
- Qwen 2.5 32B needs 48GB VRAM minimum
- RTX A6000 (48GB) or A100 (80GB) recommended

## After Completion

### Analyze Results
```bash
# View summary
cat runs/graph_of_thoughts_runpod_full/summary.json

# Compare to all baselines
python scripts/summarize_all_architectures.py
```

### Stop RunPod Pod
⚠️ **Important:** Stop your pod to avoid charges!

RunPod Dashboard → Your Pod → Stop

## Files Created

✅ `configs/runpod_graph_of_thoughts.yaml` - RunPod configuration
✅ `scripts/runpod_got_quickstart.sh` - Interactive setup script
✅ `docs/runpod_graph_of_thoughts_guide.md` - Detailed documentation
✅ `paper_sections/graph_of_thoughts.md` - Architecture description
✅ `src/baselines/graph_of_thoughts.py` - Implementation

## Resources

- **Detailed Guide:** [docs/runpod_graph_of_thoughts_guide.md](docs/runpod_graph_of_thoughts_guide.md)
- **General RunPod Setup:** [docs/runpod_setup.md](docs/runpod_setup.md)
- **GoT Architecture:** [paper_sections/graph_of_thoughts.md](paper_sections/graph_of_thoughts.md)
- **RunPod:** https://www.runpod.io/

## Quick Commands

```bash
# Test 1 question
python scripts/test_graph_of_thoughts.py --n 1 --config configs/runpod_graph_of_thoughts.yaml

# Run 100 questions
python scripts/test_graph_of_thoughts.py --n 100 --config configs/runpod_graph_of_thoughts.yaml

# Run full dataset
python scripts/test_graph_of_thoughts.py --n 1071 --config configs/runpod_graph_of_thoughts.yaml

# Interactive setup
./scripts/runpod_got_quickstart.sh

# Resume interrupted run
python scripts/test_graph_of_thoughts.py --n 1071 --config configs/runpod_graph_of_thoughts.yaml \
  --resume runs/graph_of_thoughts_runpod_full
```

---

**Questions?** See the [detailed guide](docs/runpod_graph_of_thoughts_guide.md) or check [troubleshooting](TROUBLESHOOTING.md).

Good luck beating 73.6%! 🚀
