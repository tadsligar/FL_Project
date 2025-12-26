# RunPod GPU Selection Guide - Spot vs On-Demand & Cost Optimization

## Spot vs On-Demand Instances

### On-Demand Instances
**What it is:** Guaranteed availability - your pod runs until you stop it.

**Pros:**
- ✅ **Reliable:** Won't be interrupted
- ✅ **Predictable:** Runs until completion
- ✅ **Best for:** Long runs (20+ hours), critical experiments

**Cons:**
- ❌ **Expensive:** Full price (~$0.79/hr for A6000, ~$1.89/hr for A100)
- ❌ **Overkill:** If you can tolerate interruptions

**Best for:**
- Full dataset runs (1,071 questions, ~20 hours)
- When you need guaranteed completion
- Production workloads
- When you're sleeping/away and can't monitor

### Spot Instances (Community Cloud)
**What it is:** Spare capacity that can be reclaimed if someone needs it.

**Pros:**
- ✅ **70% cheaper:** ~$0.28/hr for A6000, ~$0.67/hr for A100
- ✅ **Same hardware:** Identical GPUs, just interruptible
- ✅ **Best for:** Testing, development, resumable workloads

**Cons:**
- ❌ **Can be interrupted:** Your pod can be stopped without warning
- ❌ **Availability varies:** May not always be available
- ❌ **Need resume logic:** Must checkpoint progress

**Best for:**
- Pilot runs (100 questions, ~2 hours)
- Testing and development
- Budget-conscious experiments
- Workloads with good checkpointing (our scripts do this!)

### How Spot Interruptions Work

When a Spot instance is reclaimed:
1. ⚠️ **Warning:** RunPod gives ~60 seconds notice (usually)
2. 🛑 **Shutdown:** Pod is stopped (not deleted)
3. 💾 **Data preserved:** Your volume/storage remains
4. 🔄 **Resume:** Restart pod and resume from checkpoint

**Our scripts handle this well:**
```bash
# Results are checkpointed every 10 questions
# If interrupted at question 47, you only lose at most 10 questions of work
python scripts/test_graph_of_thoughts.py \
  --n 1071 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --resume runs/graph_of_thoughts_runpod_full
```

### Cost Comparison Example

**Full dataset (1,071 questions, ~20 hours):**

| Instance Type | GPU | Cost/hr | Total Cost | Risk |
|---------------|-----|---------|------------|------|
| On-Demand | A6000 | $0.79 | ~$15.80 | None |
| **Spot** | A6000 | $0.28 | **~$5.60** | Can be interrupted |
| On-Demand | A100 | $1.89 | ~$37.80 | None |
| **Spot** | A100 | $0.67 | **~$13.40** | Can be interrupted |

**Savings:** Spot saves you **$10-24** on a full run!

### Recommendation

**For Graph of Thoughts:**
1. **Testing (n=1-10):** Use Spot - cheap, quick, interruption unlikely
2. **Pilot (n=100):** Use Spot - 2 hours, unlikely to be interrupted
3. **Full run (n=1071):**
   - **Budget:** Spot (~$5-13) - accept possible interruptions
   - **Reliability:** On-Demand (~$15-37) - guaranteed completion
   - **Hybrid:** Start with Spot, switch to On-Demand if interrupted

---

## Multi-GPU Support with vLLM

### Can vLLM Use Multiple GPUs?

**Yes!** vLLM supports tensor parallelism to split a single model across multiple GPUs.

### How It Works

**Tensor Parallelism:**
- Splits model layers across GPUs
- All GPUs work together on each request
- **Does NOT** increase throughput (requests/sec)
- **Does** allow larger models or faster inference

**Example:**
```bash
# Single A6000 (48GB)
vllm serve Qwen/Qwen2.5-32B-Instruct

# 2x A6000 (96GB total)
vllm serve Qwen/Qwen2.5-32B-Instruct --tensor-parallel-size 2
```

### When You Need Multi-GPU

| Scenario | GPUs Needed | Why |
|----------|-------------|-----|
| **Qwen 2.5 32B** (our model) | **1x A6000** ✅ | Fits in 48GB with quantization |
| Qwen 2.5 72B | 2x A6000 or 1x A100 | Needs ~80GB |
| Llama 3 70B | 2x A6000 or 1x A100 | Needs ~80GB |
| Mixtral 8x22B | 2-3x A6000 or 2x A100 | Needs ~160GB |

**For our use case (Qwen 2.5 32B):**
- ✅ **Single GPU is sufficient**
- ❌ Multi-GPU won't help (model already fits)
- ❌ Multi-GPU = 2x cost with no speed benefit

### Multi-GPU Throughput (Batch Processing)

**Important:** vLLM's tensor parallelism does NOT double throughput!

**Example:**
- 1x A6000: Process 1 question at a time
- 2x A6000 (tensor parallel): Still process 1 question at a time
- 2x A6000 (separate instances): Process 2 questions in parallel ✅

**For batching 1,071 questions:**
- Better to run **2 separate pods** with different question subsets
- Each pod runs 535-536 questions
- Finish in ~10 hours instead of ~20 hours

### Batch Processing Strategy

**Option 1: Single GPU (Simple)**
```bash
# One pod, sequential
python scripts/test_graph_of_thoughts.py --n 1071 --config ...
# Time: ~20 hours
# Cost: $5.60 (Spot A6000) or $13.40 (Spot A100)
```

**Option 2: Parallel Pods (2x Speed)**
```bash
# Pod 1: Questions 0-535
python scripts/test_graph_of_thoughts.py --n 536 --config ... --output runs/got_pod1

# Pod 2: Questions 536-1071
# Modify script to start at offset 536
python scripts/test_graph_of_thoughts.py --n 535 --config ... --output runs/got_pod2

# Combine results afterward
# Time: ~10 hours
# Cost: $11.20 (2x Spot A6000) or $26.80 (2x Spot A100)
```

**Trade-off:**
- 2x pods = 2x speed but 2x cost
- Total cost same, but finish faster
- Good if you're time-constrained

---

## GPU Speed Comparison

### Throughput Benchmarks (Estimated)

For **Qwen 2.5 32B** with **Graph of Thoughts** (~15 LLM calls, ~12K tokens/question):

| GPU | VRAM | Tokens/sec | Time/Question | Questions/Hour | Best For |
|-----|------|------------|---------------|----------------|----------|
| RTX 4090 | 24GB | ~45 | ~60s | ~60 | Budget (needs quant) |
| **RTX A6000** | 48GB | ~50 | **~55s** | **~65** | **Best value** ✅ |
| A100 40GB | 40GB | ~60 | ~45s | ~80 | Not worth it |
| **A100 80GB** | 80GB | ~70 | **~40s** | **~90** | Fastest |
| H100 | 80GB | ~100 | ~30s | ~120 | Overkill $$$ |

### Cost Efficiency Analysis

**Metric: Cost per 1,071 questions**

| GPU | Spot $/hr | Time (hours) | Total Cost | Cost/Question | Efficiency Rank |
|-----|-----------|--------------|------------|---------------|-----------------|
| **RTX A6000** | **$0.28** | **16.5** | **$4.62** | **$0.0043** | **🥇 Best** |
| A100 80GB | $0.67 | 12 | $8.04 | $0.0075 | 🥈 Second |
| RTX 4090 | $0.24 | 18 | $4.32 | $0.0040 | 🥉 Third* |

*RTX 4090 is slightly cheaper but needs quantization and has less VRAM headroom

### A100 Speed Advantage

**Is A100 worth 2.4x the cost?**

Let's calculate:

**A6000 Spot:**
- Time: 16.5 hours
- Cost: $4.62
- Speed: 65 questions/hr

**A100 Spot:**
- Time: 12 hours
- Cost: $8.04
- Speed: 90 questions/hr

**Analysis:**
- A100 saves **4.5 hours** (27% faster)
- A100 costs **$3.42 more** (74% more expensive)
- **Verdict:** Only worth it if your time is worth >$0.76/hour saved

**When A100 makes sense:**
1. ⏰ **Time-sensitive:** Need results urgently (overnight run)
2. 💰 **High budget:** Cost is not a concern
3. 🔬 **Many experiments:** Running multiple full evaluations
4. 🎯 **Large batches:** Processing >5,000 questions

**For most cases: A6000 Spot is the sweet spot** ✅

---

## Memory Requirements

### Qwen 2.5 32B Model Size

| Format | Size | VRAM Needed | Fits On |
|--------|------|-------------|---------|
| FP16 (full precision) | ~64GB | ~70GB | A100 80GB only |
| **Q4_K_M (4-bit)** | **~20GB** | **~24GB** | **RTX 4090+ ✅** |
| Q8_0 (8-bit) | ~34GB | ~38GB | A6000, A100 |

**We use Q4_K_M quantization:**
- Fits comfortably on RTX 4090 (24GB)
- Leaves room for context on A6000 (48GB)
- Minimal accuracy loss (<1%)

### Context Length Considerations

**Graph of Thoughts** has long prompts due to multi-stage reasoning:

| Stage | Context Tokens | Output Tokens | Total |
|-------|----------------|---------------|-------|
| Initialize | ~800 | ~500 | ~1,300 |
| Hypotheses (x4) | ~1,000 | ~800 | ~7,200 |
| Evidence (x4) | ~1,500 | ~600 | ~8,400 |
| Refinement (x4) | ~2,000 | ~700 | ~10,800 |
| Aggregation | ~3,000 | ~800 | ~3,800 |
| Decision | ~1,500 | ~300 | ~1,800 |

**Peak VRAM usage:** ~32GB (model) + ~6GB (context/KV cache) = **~38GB**

**Safe GPUs:**
- ✅ A6000 (48GB) - 10GB headroom
- ✅ A100 80GB (80GB) - 42GB headroom
- ⚠️ RTX 4090 (24GB) - Tight fit, may need shorter context
- ❌ A100 40GB (40GB) - Too tight

**Recommendation: RTX A6000** - Best balance of cost and safety margin

---

## RunPod Pricing (December 2024)

### Spot Pricing (Community Cloud)

| GPU | VRAM | Spot $/hr | Typical Availability |
|-----|------|-----------|---------------------|
| RTX 4090 | 24GB | $0.24 | High |
| RTX A6000 | 48GB | $0.28 | High |
| A100 40GB | 40GB | $0.54 | Medium |
| A100 80GB | 80GB | $0.67 | Medium |
| A100 80GB SXM | 80GB | $0.89 | Low |
| H100 | 80GB | $1.49 | Very Low |

### On-Demand Pricing (Secure Cloud)

| GPU | VRAM | On-Demand $/hr |
|-----|------|----------------|
| RTX 4090 | 24GB | $0.69 |
| RTX A6000 | 48GB | $0.79 |
| A100 40GB | 40GB | $1.14 |
| A100 80GB | 80GB | $1.89 |

*Prices vary by region and availability*

---

## Recommendations by Use Case

### 1. Testing & Development (n=1-10)
**Best:** RTX 4090 or A6000 Spot
- Cost: $0.01-0.10
- Time: <30 min
- Why: Cheapest, interruption unlikely

### 2. Pilot Validation (n=100)
**Best:** RTX A6000 Spot
- Cost: ~$0.50
- Time: ~2 hours
- Why: Best value, unlikely to be interrupted

### 3. Full Evaluation (n=1071) - Budget
**Best:** RTX A6000 Spot
- Cost: **~$4.62**
- Time: ~16.5 hours
- Why: Cheapest, checkpointing handles interruptions
- Risk: May be interrupted 0-2 times

### 4. Full Evaluation (n=1071) - Reliable
**Best:** RTX A6000 On-Demand
- Cost: ~$13.03
- Time: ~16.5 hours
- Why: Guaranteed completion, moderate price

### 5. Full Evaluation (n=1071) - Fast
**Best:** A100 80GB Spot
- Cost: ~$8.04
- Time: ~12 hours
- Why: 27% faster, still reasonable cost

### 6. Multiple Full Runs (3x for stability)
**Best:** 2x RTX A6000 Spot (parallel)
- Cost: ~$8.40 per run (x3 = $25.20 total)
- Time: ~8 hours per run (parallel), ~24 hours total
- Why: Split workload, finish 3 runs in 1 day

### 7. Production / Time-Critical
**Best:** A100 80GB On-Demand
- Cost: ~$22.68
- Time: ~12 hours
- Why: Fastest + guaranteed completion

---

## Final Recommendations

### For Graph of Thoughts Evaluation

**🥇 Best Overall: RTX A6000 Spot**
- Cost: $4.62 for full dataset
- Time: 16.5 hours
- Reliability: High (use resume if interrupted)
- Value: Best cost/performance ratio

**🥈 Best Reliability: RTX A6000 On-Demand**
- Cost: $13.03 for full dataset
- Time: 16.5 hours
- Reliability: Guaranteed
- Value: Good balance

**🥉 Best Speed: A100 80GB Spot**
- Cost: $8.04 for full dataset
- Time: 12 hours
- Reliability: Medium (use resume)
- Value: Good if time matters

### Multi-GPU? No.

**For Qwen 2.5 32B:**
- ❌ Don't use tensor parallelism (model fits on single GPU)
- ❌ Don't use multiple GPUs on one pod (no benefit)
- ✅ Use single GPU per pod
- ✅ Consider multiple pods in parallel (2x speed, 2x cost)

### Cost Optimization Strategy

**Recommended approach:**

1. **Start with Spot** (~$4.62)
   - Deploy A6000 Spot
   - Run full 1,071 questions
   - Checkpoint every 10 questions

2. **If interrupted:**
   - Resume from checkpoint
   - Continue on Spot if cheap
   - Or switch to On-Demand to guarantee completion

3. **Expected cost:**
   - Best case: $4.62 (no interruption)
   - Typical: $5-7 (1 interruption)
   - Worst case: $13 (switch to On-Demand)

**You'll likely save $5-10 vs always using On-Demand!**

---

## Quick Decision Matrix

| Priority | GPU Choice | Instance Type | Cost | Time |
|----------|------------|---------------|------|------|
| **Cheapest** | A6000 | Spot | $4.62 | 16.5h |
| **Reliable** | A6000 | On-Demand | $13.03 | 16.5h |
| **Fastest** | A100 80GB | Spot | $8.04 | 12h |
| **Balanced** | A6000 | Spot → On-Demand | $5-13 | 16.5h |

**My recommendation: Start with A6000 Spot** 🎯
