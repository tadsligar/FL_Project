# Running Graph of Thoughts on RunPod

Complete guide to deploying and running the Graph of Thoughts architecture on RunPod for medical question answering.

## Overview

**Graph of Thoughts (GoT)** is a neurosymbolic reasoning framework that represents diagnostic reasoning as a directed graph with:
- **~15 LLM calls per question** (vs 5 for Progressive Temp baseline, 7 for Progressive Temp Parallel)
- **Feedback loops** for iterative refinement
- **Cross-pollination** between competing hypotheses
- **Temperature scheduling** per node type (1.0 → 0.7 → 0.5 → 0.0)

**Expected Performance:** Target is >73.6% (beating Progressive Temperature Parallel V4)

**Estimated Cost:**
- Full dataset (1,071 questions): ~$50-100 on RunPod A6000
- 100 questions: ~$5-10 on RunPod A6000
- Per question: ~$0.05-0.10

---

## Step 1: Deploy vLLM Pod on RunPod

### 1.1 Create Account
1. Go to https://www.runpod.io/
2. Sign up or log in
3. Add credits (minimum $10 recommended for testing)

### 1.2 Deploy GPU Pod

**Recommended Configuration:**

| GPU | VRAM | Speed | Cost (On-Demand) | Cost (Spot) | Best For |
|-----|------|-------|------------------|-------------|----------|
| **RTX A6000** | 48GB | Fast | ~$0.79/hr | ~$0.28/hr | **Recommended** |
| A100 80GB | 80GB | Fastest | ~$1.89/hr | ~$0.67/hr | Large batches |
| RTX 4090 | 24GB | Fast | ~$0.69/hr | ~$0.24/hr | Budget (needs quantization) |

**Steps:**
1. Click **"Deploy"** → **"GPU Pod"**
2. Choose GPU: **RTX A6000** (48GB recommended)
3. Select Template: Search for **"vLLM"** or **"vLLM OpenAI Compatible"**
4. Configure:
   - **Model:** `Qwen/Qwen2.5-32B-Instruct`
   - **Volume:** 50GB minimum
   - **Ports:** 8000 (default)
   - **Environment Variables:**
     ```
     MODEL_NAME=Qwen/Qwen2.5-32B-Instruct
     GPU_MEMORY_UTILIZATION=0.9
     MAX_MODEL_LEN=8192
     ```
5. Choose **On-Demand** (reliable) or **Spot** (70% cheaper, can be interrupted)
6. Click **"Deploy"**

### 1.3 Wait for Model to Load
- Initial deployment: 5-10 minutes to download model weights (~20GB)
- Watch the pod logs for: `"Application startup complete"`
- GPU utilization should show active

---

## Step 2: Configure Your Endpoint

### 2.1 Get RunPod URL
1. Click on your running pod
2. Find **"Connect"** section
3. Copy the **HTTP Service endpoint**:
   ```
   https://xxxxx-8000.proxy.runpod.net
   ```

### 2.2 Update Config File

Edit `configs/runpod_graph_of_thoughts.yaml`:

```yaml
vllm:
  base_url: https://YOUR_ACTUAL_POD_ID-8000.proxy.runpod.net  # Replace!
  use_chat_api: true
  timeout: 600
```

**Example:**
```yaml
vllm:
  base_url: https://abc123xyz-8000.proxy.runpod.net
  use_chat_api: true
  timeout: 600
```

### 2.3 Test Connection

Quick verification:

```bash
python -c "
import requests
url = 'https://YOUR_POD_ID-8000.proxy.runpod.net/v1/chat/completions'
response = requests.post(url, json={
    'model': 'Qwen/Qwen2.5-32B-Instruct',
    'messages': [{'role': 'user', 'content': 'Hello, are you working?'}],
    'max_tokens': 50
})
print('Status:', response.status_code)
print('Response:', response.json())
"
```

✅ Expected: Status 200 and a JSON response with generated text

---

## Step 3: Run Graph of Thoughts Evaluation

### 3.1 Small Test (1 question)

**Verify everything works:**

```bash
python scripts/test_graph_of_thoughts.py \
  --n 1 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --output runs/graph_of_thoughts_runpod_test
```

**Expected output:**
- Question answered in ~30-60 seconds
- Graph with ~15 nodes created
- Result saved to output directory

### 3.2 Medium Test (10 questions)

**Quick validation run:**

```bash
python scripts/test_graph_of_thoughts.py \
  --n 10 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --output runs/graph_of_thoughts_runpod_n10
```

**Estimated time:** ~5-10 minutes
**Estimated cost:** ~$0.10-0.20

### 3.3 Pilot Run (100 questions)

**Meaningful performance estimate:**

```bash
python scripts/test_graph_of_thoughts.py \
  --n 100 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --output runs/graph_of_thoughts_runpod_n100
```

**Estimated time:** ~1-2 hours
**Estimated cost:** ~$1-2 (A6000), ~$0.40-0.80 (Spot)

### 3.4 Full Dataset (1,071 questions)

**Complete evaluation:**

```bash
python scripts/test_graph_of_thoughts.py \
  --n 1071 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --output runs/graph_of_thoughts_runpod_full
```

**Estimated time:** ~12-24 hours
**Estimated cost:** ~$10-20 (On-Demand), ~$3-7 (Spot)

⚠️ **Important:**
- Results are checkpointed every 10 questions
- If interrupted, resume with: `--resume runs/graph_of_thoughts_runpod_full`
- Download results periodically to avoid data loss

---

## Step 4: Monitor Progress

### 4.1 Real-Time Monitoring

**Terminal output shows:**
```
Question 1/100
Correct Answer: B
  [OK] Predicted: B (45.2s, 12,450 tokens)
  Graph: 15 nodes, 14 edges
```

### 4.2 Check Results

**During run:**
```bash
# View checkpoint
cat runs/graph_of_thoughts_runpod_full/checkpoint.json | jq '.[-1]'

# Count correct so far
cat runs/graph_of_thoughts_runpod_full/checkpoint.json | jq '[.[] | select(.is_correct == true)] | length'
```

**After completion:**
```bash
# View summary
cat runs/graph_of_thoughts_runpod_full/summary.json

# Example output:
{
  "accuracy": 0.752,
  "correct": 752,
  "total": 1000,
  "avg_tokens": 12450,
  "avg_latency": 45.3,
  "avg_nodes": 15.2,
  "avg_edges": 14.1
}
```

### 4.3 RunPod Dashboard

Monitor in RunPod:
- **GPU Utilization:** Should be 85-95%
- **Pod Logs:** Check for errors
- **Network Traffic:** Active during inference
- **Cost Tracker:** Running total

---

## Step 5: Resume from Interruption

If your run gets interrupted (especially with Spot instances):

```bash
python scripts/test_graph_of_thoughts.py \
  --n 1071 \
  --config configs/runpod_graph_of_thoughts.yaml \
  --resume runs/graph_of_thoughts_runpod_full
```

The script will:
✅ Load checkpoint.json
✅ Skip completed questions
✅ Continue from where it left off
✅ Append to existing results

---

## Cost Optimization Tips

### Save Money 💰

1. **Use Spot Instances** (70% cheaper)
   - Trade-off: Can be interrupted
   - Solution: Use resume functionality
   - Best for: Non-urgent batch jobs

2. **Stop Pod When Idle**
   - Only pay when running
   - Redeploy when needed (takes ~5 min)
   - Volume persists (keeps model downloaded)

3. **Run Multiple Experiments in One Session**
   ```bash
   # Small test first
   python scripts/test_graph_of_thoughts.py --n 10 --config ...

   # If successful, run full batch
   python scripts/test_graph_of_thoughts.py --n 1071 --config ...
   ```

4. **Use Smaller Subset for Development**
   - n=10 for testing: ~$0.20
   - n=100 for validation: ~$2
   - n=1071 for final: ~$20

### Speed Up ⚡

1. **Monitor GPU Utilization**
   - Should be >85% during inference
   - If lower, check for network bottlenecks

2. **Increase Batch Size** (if model supports)
   ```yaml
   vllm:
     max_batch_size: 64
   ```

3. **Reduce Timeout** (if responses are fast)
   ```yaml
   vllm:
     timeout: 300  # 5 minutes instead of 10
   ```

---

## Troubleshooting

### Connection Errors

**"Cannot connect to vLLM server"**
- ✅ Check pod is "Running" (not stopped)
- ✅ Verify endpoint URL is correct
- ✅ Test with curl: `curl https://YOUR_POD_ID-8000.proxy.runpod.net/health`

**Solution:**
```bash
# Test endpoint
curl https://YOUR_POD_ID-8000.proxy.runpod.net/v1/models

# Should return:
{"object":"list","data":[{"id":"Qwen/Qwen2.5-32B-Instruct",...}]}
```

### Model Errors

**"Model not found"**
- Check pod logs for actual model name loaded
- Try: `Qwen2.5-32B-Instruct` (without slash)

**Solution:**
```yaml
model: Qwen2.5-32B-Instruct  # Try without Qwen/ prefix
```

### Timeout Errors

**"vLLM request timed out"**
- GoT makes 15+ calls per question
- Increase timeout in config

**Solution:**
```yaml
vllm:
  timeout: 900  # 15 minutes
budgets:
  timeout_seconds: 900
```

### Performance Issues

**Slow inference (>60s per question)**
- Check GPU utilization in RunPod dashboard
- Verify network latency
- Consider upgrading to A100

**High cost**
- GoT uses ~15 calls vs 5-7 for other methods
- This is expected for the architecture
- Cost per question: $0.05-0.10 is normal

### Pod Terminated Mid-Run

**Spot instance interrupted**
- Results up to last checkpoint are saved
- Resume with `--resume` flag
- Or switch to On-Demand instance

---

## Performance Expectations

### Baseline Comparisons

| Method | Accuracy | Calls/Q | Tokens/Q | Estimated Cost/Q |
|--------|----------|---------|----------|------------------|
| Zero-Shot | 57.8% | 1 | 513 | $0.01 |
| Progressive Temp | 72.2% | 5 | 7,089 | $0.02 |
| Prog Temp Parallel V4 | **73.6%** | 7 | 11,049 | $0.03 |
| **Graph of Thoughts** | **TBD** | **15** | **~12,000** | **$0.05** |

### Target Metrics

**Hypothesis:** GoT should beat 73.6% due to:
1. ✅ Feedback loops for iterative refinement
2. ✅ Cross-pollination between hypotheses
3. ✅ Explicit evidence gathering per option
4. ✅ Temperature schedule optimized per stage

**Success Criteria:**
- 🎯 Primary: Accuracy >74.0% (beat V4 by >0.4%)
- 🎯 Secondary: Accuracy >75.0% (significant improvement)
- ⚠️ Threshold: Accuracy <73.6% = architecture doesn't justify cost

### Expected Timeline

| Dataset Size | Estimated Time | Cost (On-Demand) | Cost (Spot) |
|--------------|----------------|------------------|-------------|
| 1 question | 30-60s | $0.01 | $0.005 |
| 10 questions | 5-10 min | $0.10 | $0.04 |
| 100 questions | 1-2 hours | $1-2 | $0.40 |
| 1,071 questions | 12-24 hours | $10-20 | $4-7 |

---

## Analysis After Completion

### 1. Compare to Baselines

```bash
# Run comparison script
python scripts/summarize_all_architectures.py

# This will update ARCHITECTURE_PERFORMANCE_SUMMARY.md with GoT results
```

### 2. Analyze Graph Structure

```python
import json

# Load results
with open('runs/graph_of_thoughts_runpod_full/results.json') as f:
    results = json.load(f)

# Analyze graph patterns
for r in results[:10]:
    print(f"Q{r['question_idx']}: {r['graph_summary']}")
    # Shows node types, edge counts, etc.
```

### 3. Ablation Studies (Optional)

Test architecture variants:
- Remove refinement iteration
- Remove cross-pollination
- Different temperature schedules
- Confidence-based pruning

---

## Next Steps After Testing

### If GoT Beats V4 (>73.6%)

✅ Document key architectural insights
✅ Run multiple trials (3x) to verify stability
✅ Analyze which graph patterns correlate with correctness
✅ Publish results in ARCHITECTURE_PERFORMANCE_SUMMARY.md

### If GoT Underperforms (<73.6%)

🔍 Analyze failure modes
🔍 Check if feedback loops helped or hurt
🔍 Consider simplifications (reduce to 10 calls instead of 15)
🔍 Test ablations to find what didn't work

---

## Quick Reference Commands

```bash
# Test connection
curl https://YOUR_POD_ID-8000.proxy.runpod.net/health

# Run 1 question test
python scripts/test_graph_of_thoughts.py --n 1 --config configs/runpod_graph_of_thoughts.yaml

# Run 100 questions
python scripts/test_graph_of_thoughts.py --n 100 --config configs/runpod_graph_of_thoughts.yaml

# Run full dataset
python scripts/test_graph_of_thoughts.py --n 1071 --config configs/runpod_graph_of_thoughts.yaml

# Resume interrupted run
python scripts/test_graph_of_thoughts.py --n 1071 --config configs/runpod_graph_of_thoughts.yaml \
  --resume runs/graph_of_thoughts_runpod_full

# Check current accuracy
cat runs/graph_of_thoughts_runpod_full/summary.json | jq '.accuracy'
```

---

## Summary Checklist

- [ ] Deploy vLLM pod on RunPod with Qwen 2.5 32B
- [ ] Get endpoint URL from RunPod dashboard
- [ ] Update `configs/runpod_graph_of_thoughts.yaml` with your URL
- [ ] Test connection with curl or Python
- [ ] Run n=1 test to verify setup
- [ ] Run n=10 or n=100 pilot
- [ ] Run full n=1071 evaluation
- [ ] Monitor progress and download checkpoints
- [ ] Analyze results and compare to baselines
- [ ] Stop pod when done to save money

**Good luck with your Graph of Thoughts evaluation!** 🚀

Questions? Check the main [RunPod Setup Guide](runpod_setup.md) or [Troubleshooting](../TROUBLESHOOTING.md).
