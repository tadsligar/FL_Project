# RunPod Pricing Quick Reference - Graph of Thoughts

## TL;DR - What Should I Use?

**🎯 Recommended: RTX A6000 Spot**
- **Cost:** $4.62 for full 1,071 questions
- **Time:** ~16.5 hours
- **Why:** Best value, checkpointing handles interruptions

---

## Spot vs On-Demand Explained

### Spot (Community Cloud) - 70% Cheaper ⚡
**What it is:** Spare GPU capacity that can be reclaimed if needed

**Think of it like:** Standby airline tickets
- Much cheaper
- Can be bumped if someone pays full price
- Great if you're flexible

**For our use case:**
- ✅ Scripts checkpoint every 10 questions
- ✅ Easy to resume if interrupted
- ✅ Interruptions are rare for short-medium runs
- ✅ **Save $8-24 on full dataset!**

### On-Demand (Secure Cloud) - Guaranteed 🛡️
**What it is:** Reserved GPU that runs until you stop it

**Think of it like:** Regular airline tickets
- More expensive
- Guaranteed to complete
- No surprises

**For our use case:**
- ✅ Best for overnight runs when you can't monitor
- ✅ Best for time-sensitive experiments
- ❌ Overkill for testing/pilots

---

## Full Dataset Cost Comparison (1,071 questions)

| GPU | Spot Cost | On-Demand Cost | Time | Speed Rank |
|-----|-----------|----------------|------|------------|
| **A6000** | **$4.62** | $13.03 | 16.5h | 🥈 Good |
| A100 80GB | $8.04 | $22.68 | 12h | 🥇 Fast |
| RTX 4090 | $4.32 | $12.42 | 18h | 🥉 Slower |

**Savings (Spot vs On-Demand):**
- A6000: Save **$8.41** (65% off)
- A100: Save **$14.64** (65% off)

---

## Multi-GPU Question Answered

### Does vLLM split across multiple GPUs?

**Yes, but not helpful for us!**

**How vLLM multi-GPU works:**
- Called "tensor parallelism"
- Splits model layers across GPUs
- All GPUs work together on each question
- **Does NOT increase throughput** (questions/sec)

**Example:**
```
1x A6000: Process 1 question in 55 seconds
2x A6000: Still process 1 question in 55 seconds (same speed!)
```

**Why?** Qwen 2.5 32B already fits on single GPU
- Model size: ~20GB (quantized)
- Peak memory: ~38GB (with long context)
- A6000 has 48GB ✅

**When multi-GPU helps:**
- Large models (70B+) that don't fit on single GPU
- Need >48GB VRAM
- Not our case!

### Better approach for speed: Parallel pods

Instead of 2 GPUs on one pod, use 2 separate pods:

```bash
# Pod 1: Questions 1-535
python scripts/test_graph_of_thoughts.py --n 535 --config ...

# Pod 2: Questions 536-1071
python scripts/test_graph_of_thoughts.py --n 535 --config ...

# Result: Finish in ~8 hours instead of ~16 hours
# Cost: 2x pods = 2x cost (but done 2x faster)
```

**Trade-off:**
- Time: 8 hours (2x faster)
- Cost: ~$9 (2x more)
- Same total compute, just parallelized

---

## A100 vs A6000 - Is faster worth it?

### Speed Difference

| Metric | A6000 | A100 80GB | Improvement |
|--------|-------|-----------|-------------|
| Tokens/sec | ~50 | ~70 | +40% |
| Time/question | ~55s | ~40s | **27% faster** |
| Questions/hr | 65 | 90 | +38% |
| Full dataset | 16.5h | 12h | **Save 4.5 hours** |

### Cost Analysis (Spot instances)

**A6000:**
- Time: 16.5 hours
- Cost: **$4.62**
- Cost per question: $0.0043

**A100:**
- Time: 12 hours
- Cost: **$8.04**
- Cost per question: $0.0075

**Difference:**
- A100 costs **$3.42 more** (74% premium)
- A100 saves **4.5 hours** (27% faster)
- **Cost per hour saved: $0.76/hour**

### When is A100 worth it?

✅ **Use A100 if:**
- Time is critical (need results tomorrow morning)
- Running multiple full evaluations (3+ runs)
- Your time is worth >$0.76/hr
- Budget is not a concern

❌ **Stick with A6000 if:**
- Budget conscious
- Not time-sensitive (ok with 16 vs 12 hours)
- Running one experiment
- Testing/development

**Most common choice: A6000 Spot** 🎯

---

## Practical Scenarios

### Scenario 1: Testing (n=10)
**Recommendation:** A6000 Spot
- Cost: $0.05
- Time: 10 minutes
- Risk: Zero (too short to be interrupted)

### Scenario 2: Pilot (n=100)
**Recommendation:** A6000 Spot
- Cost: $0.50
- Time: 1.7 hours
- Risk: Low (interruption unlikely)

### Scenario 3: Full Run (n=1071) - Budget
**Recommendation:** A6000 Spot
- Cost: $4.62
- Time: 16.5 hours
- Risk: Medium (might be interrupted once)
- Plan: Use resume if needed

### Scenario 4: Full Run - Overnight
**Recommendation:** A6000 On-Demand
- Cost: $13.03
- Time: 16.5 hours
- Risk: Zero (guaranteed completion)
- Plan: Start before bed, done by morning

### Scenario 5: Full Run - Fast
**Recommendation:** A100 Spot
- Cost: $8.04
- Time: 12 hours
- Risk: Medium (might be interrupted)
- Plan: Done by dinner instead of midnight

### Scenario 6: Multiple Runs (3x for stability)
**Recommendation:** 2x A6000 Spot (parallel)
- Cost: $9 per run × 3 = $27
- Time: 8 hours per run, 24 hours total
- Strategy: Run 2 pods in parallel, repeat 3 times

---

## Interruption Risk & Resume

### How often are Spot instances interrupted?

**Typical experience:**
- Short runs (<2 hours): **<5% chance**
- Medium runs (2-8 hours): **10-20% chance**
- Long runs (8-24 hours): **30-50% chance**

**For our 16.5 hour run:**
- Expect 0-2 interruptions
- Each interruption costs ~10 questions of work
- Resume takes ~5 minutes

### What happens when interrupted?

1. **Warning:** ~60 seconds notice (usually)
2. **Save:** Checkpoint at question boundary
3. **Stop:** Pod goes offline
4. **Restart:** Redeploy or wait for availability
5. **Resume:** Continue from checkpoint

```bash
# Automatic resume
python scripts/test_graph_of_thoughts.py \
  --n 1071 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --resume runs/graph_of_thoughts_runpod_full

# Picks up from last checkpoint (every 10 questions)
```

### Expected total cost with interruptions

**A6000 Spot scenario:**

| Interruptions | Lost Work | Extra Time | Total Cost |
|---------------|-----------|------------|------------|
| 0 (60% likely) | 0 questions | 0h | **$4.62** |
| 1 (30% likely) | ~10 questions | +0.5h | **$4.76** |
| 2 (10% likely) | ~20 questions | +1h | **$4.90** |

**Average expected cost: ~$4.70** (still way cheaper than $13 On-Demand!)

---

## My Recommendation

### For Graph of Thoughts Full Evaluation:

**🥇 Best Choice: RTX A6000 Spot**

**Why:**
1. ✅ **Cheapest:** $4.62 vs $8+ for alternatives
2. ✅ **Sufficient:** Qwen 2.5 32B fits easily (20GB model, 48GB VRAM)
3. ✅ **Reliable:** Interruptions rare + easy resume
4. ✅ **Fast enough:** 16.5 hours is reasonable
5. ✅ **Most available:** High Spot availability

**Strategy:**
1. Start with A6000 Spot
2. If interrupted, restart Spot instance
3. If interrupted 2+ times, switch to On-Demand
4. Expected total cost: $5-7

**When to use A100 instead:**
- You need results in <12 hours
- Running 3+ full evaluations
- Time is more valuable than $3.42

**When to use On-Demand:**
- Running overnight while sleeping
- Can't monitor for interruptions
- Need guaranteed completion

---

## Quick Commands

### Check Current RunPod Pricing
https://www.runpod.io/console/gpu-cloud

### Deploy A6000 Spot (Recommended)
1. RunPod Console → Deploy
2. Choose: **RTX A6000 (48GB)**
3. Type: **Community Cloud (Spot)**
4. Template: **vLLM**
5. Model: `Qwen/Qwen2.5-32B-Instruct`

### Monitor Cost While Running
RunPod Dashboard → Billing → Current Usage

---

## Summary Table

| GPU | Type | Cost | Time | Best For |
|-----|------|------|------|----------|
| **A6000** | **Spot** | **$4.62** | **16.5h** | **Most people** ✅ |
| A6000 | On-Demand | $13.03 | 16.5h | Guaranteed completion |
| A100 | Spot | $8.04 | 12h | Need speed |
| A100 | On-Demand | $22.68 | 12h | Time-critical + guaranteed |

**Multi-GPU:** Not needed for Qwen 2.5 32B (already fits on single GPU)

---

**Questions?** See detailed guide: `docs/runpod_gpu_selection_guide.md`
