# RunPod Setup Guide

Complete guide to running your experiments on RunPod with Qwen2.5:32B.

## Step 1: Deploy a vLLM Pod on RunPod

1. Go to https://www.runpod.io/ and sign up/login

2. Click **"Deploy"** → **"GPU Pod"**

3. **Choose GPU:**
   - **Recommended:** RTX A6000 (48GB VRAM) - ~$0.79/hr
   - **Budget:** RTX 4090 (24GB VRAM) - ~$0.69/hr (will need quantization)
   - **Fast:** A100 80GB - ~$1.89/hr (fastest, overkill for 32B)

4. **Select Template:**
   - Search for "vLLM" in community templates
   - Choose: **"RunPod vLLM"** or **"vLLM OpenAI Compatible"**

5. **Configure:**
   - **Model:** `Qwen/Qwen2.5-32B-Instruct`
   - **Volume:** 50GB (enough for model weights)
   - **Ports:** Default (8000)

6. Click **"Deploy On-Demand"** or **"Deploy Spot"** (spot is 70% cheaper but can be interrupted)

7. **Wait 5-10 minutes** for model to download and load

## Step 2: Get Your Endpoint URL

Once deployed:
1. Click on your pod
2. Look for **"Connect"** button
3. Copy the **HTTP Service endpoint** (looks like: `https://xxxxx-8000.proxy.runpod.net`)

## Step 3: Update Your Config

Edit one of the RunPod configs (e.g., `configs/runpod_qwen25_32b_temp03.yaml`):

```yaml
vllm:
  base_url: https://YOUR_ACTUAL_POD_ID-8000.proxy.runpod.net  # Replace this!
  use_chat_api: true
  timeout: 300
```

## Step 4: Test Connection

Quick test to verify it works:

```bash
python -c "
import requests
url = 'https://YOUR_POD_ID-8000.proxy.runpod.net/v1/chat/completions'
response = requests.post(url, json={
    'model': 'Qwen/Qwen2.5-32B-Instruct',
    'messages': [{'role': 'user', 'content': 'Hello!'}],
    'max_tokens': 50
})
print(response.json())
"
```

If you see a response, you're ready!

## Step 5: Run Your Experiments

Now use the RunPod configs instead of local ones:

### Zero-Shot Test
```bash
python scripts/test_zero_shot.py \
  --n 100 \
  --config configs/runpod_qwen25_32b_temp03.yaml
```

### Single-Shot CoT
```bash
python scripts/test_single_shot_cot.py \
  --n 100 \
  --config configs/runpod_qwen25_32b_temp01.yaml
```

### Physician Role Debate (Full Dataset!)
```bash
python scripts/test_debate_physician_role.py \
  --n 1071 \
  --config configs/runpod_qwen25_32b_temp03.yaml \
  --output runs/debate_physician_role_temp03_runpod_full
```

## Cost Estimation

**For full 1,071 question test:**
- Local Ollama: ~37 hours (FREE, but ties up your machine)
- RunPod A6000: ~37 hours × $0.79/hr = **~$29**
- RunPod A6000 Spot: ~37 hours × $0.28/hr = **~$10** (can be interrupted)

**For 100 question tests:**
- RunPod A6000: ~3.5 hours × $0.79/hr = **~$2.77**
- RunPod A6000 Spot: ~3.5 hours × $0.28/hr = **~$0.98**

## Speed Comparison

**Questions per hour** (physician role debate method):

| Setup | Speed | Cost/Question |
|-------|-------|---------------|
| **Local Ollama** (your machine) | ~28 q/hr | FREE |
| **RunPod RTX 4090** | ~30-35 q/hr | $0.02/q |
| **RunPod A6000** | ~30-35 q/hr | $0.03/q |
| **RunPod A100 80GB** | ~40-50 q/hr | $0.05/q |

*A100 is faster due to better memory bandwidth, but not 2× the price better.*

## Tips

### Save Money
1. **Use Spot instances** (70% cheaper but can be interrupted)
2. **Stop pod when not using** (only pay when running)
3. **Run multiple experiments in one session** (batch your work)
4. **Download results frequently** (don't lose data if pod terminates)

### Go Faster
1. **Run experiments in parallel** on multiple pods
2. **Use smaller subset first** (n=10-20) to verify config works
3. **Monitor pod utilization** - if GPU isn't at 90%+, something's wrong

### Avoid Issues
1. **Save your endpoint URL** - pods can restart with different IDs
2. **Test with n=1 first** before running n=1071
3. **Check pod logs** if requests fail (RunPod dashboard → Logs)
4. **Increase timeout** if getting timeouts (already set to 300s in configs)

## Troubleshooting

### "Cannot connect to vLLM server"
- Check pod is "Running" (not "Stopped" or "Terminated")
- Verify endpoint URL is correct (copy from RunPod dashboard)
- Test with curl: `curl https://YOUR_POD_ID-8000.proxy.runpod.net/health`

### "Model not found"
- vLLM template might use different model name format
- Try: `Qwen2.5-32B-Instruct` or `qwen2.5-32b-instruct` (lowercase)
- Check pod logs to see what model loaded

### Slow performance
- Check GPU utilization in RunPod dashboard
- Verify you're using `use_chat_api: true` (more efficient)
- Consider switching to A100 if A6000 is saturated

### Pod terminated mid-run
- This happens with Spot instances (trade-off for cheaper price)
- Your script will error out - results up to that point are saved
- Resume from where it left off or switch to On-Demand instance

## What You've Set Up

✅ Enhanced vLLM client (supports RunPod endpoints)
✅ RunPod configs for temps 0.0, 0.1, 0.3
✅ All existing test scripts work with RunPod
✅ No code changes needed - just swap config files!

## Next Steps

1. Deploy pod on RunPod
2. Get endpoint URL
3. Update one config file
4. Run same tests you've been running locally
5. Results save to same `runs/` directory
6. Stop pod when done to save $$

Happy experimenting! 🚀
