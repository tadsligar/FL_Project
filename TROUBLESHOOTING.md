# Troubleshooting Guide

This document covers common issues and solutions encountered during setup and execution.

---

## Installation Issues

### Issue 1: "no module named src"

**Error:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
Install the package in editable mode:
```bash
pip install -e .
```

---

## Ollama Issues

### Issue 2: "Ollama request timed out"

**Error:**
```
RuntimeError: Ollama request timed out after 180s
```

**Cause:** Large models (70B) take 1-5 minutes to load on first call.

**Solutions:**

1. **Config timeout increased** - Already set to 600 seconds in `configs/llama3_70b.yaml`

2. **Model warmup added** - The evaluation script now automatically warms up the model before starting

3. **Manual pre-warm** (if needed):
```bash
ollama run llama3:70b "Hello"
```
Wait for response, then immediately run your script.

4. **Use smaller model for testing**:
```bash
ollama pull llama3:8b
python scripts/run_baseline_comparison.py --n 10 --config configs/llama3_8b.yaml
```

### Issue 3: "Cannot connect to Ollama"

**Error:**
```
RuntimeError: Cannot connect to Ollama. Make sure Ollama is running: 'ollama serve'
```

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434

# If not running, start it
ollama serve

# Or on Windows, check Services app and restart "Ollama" service
```

---

## Dataset Issues

### Issue 4: MedQA download returns 404

**Error:**
```
Error downloading https://raw.githubusercontent.com/.../test.jsonl: 404 Client Error
```

**Cause:** MedQA GitHub repository structure changed or files moved.

**Solution - Manual Download:**

1. Clone MedQA repository:
```bash
git clone https://github.com/jind11/MedQA.git
cd MedQA
```

2. Copy questions to your project:
```bash
cp -r data_clean/questions /path/to/FL_Project/data/
```

3. Convert to 4-option format:
```bash
cd /path/to/FL_Project
python scripts/convert_medqa_5to4.py
```

This creates `data/medqa_us_test_4opt.json` with ~1,071 questions.

### Issue 5: JSON parsing errors with MedQA file

**Error:**
```
json.decoder.JSONDecodeError: Extra data: line 1 column 4 (char 3)
```

**Cause:** File contains error message (e.g., "404: Not Found") instead of actual data.

**Solution:** The loader now automatically detects invalid files and falls back to mock data. To fix:
```bash
# Delete invalid file
del data/medqa_usmle_4_options.jsonl

# Re-download or use manual download method (see Issue 4)
```

---

## Model Issues

### Issue 6: JSON output truncated

**Error:**
```
ValueError: Failed to parse planner response: Expecting property name enclosed in double quotes
```

**Cause:** Model output was truncated because token limit too small for planner (needs to enumerate 30+ specialties).

**Solution:** Already fixed in `configs/llama3_70b.yaml`:
- Config: `max_output_tokens: 2000` (increased from 800)
- Planner code: Explicitly requests 2500 tokens

### Issue 7: Out of memory

**Symptoms:**
- System freezes
- Ollama crashes
- "CUDA out of memory" error

**Solutions:**

1. **Close other applications** - Free up RAM and VRAM

2. **Use quantized model** (already using Q4 by default with Ollama)

3. **Use smaller model**:
```bash
ollama pull llama3:8b
python scripts/run_baseline_comparison.py --config configs/llama3_8b.yaml
```

4. **Check resources**:
```bash
# Monitor GPU
nvidia-smi -l 1

# Check RAM
# Task Manager > Performance > Memory
```

**Expected usage for llama3:70b:**
- GPU: 20-24GB VRAM
- System RAM: 18-24GB
- Total: ~44GB

---

## Performance Issues

### Issue 8: Evaluation too slow

**Expected times for llama3:70b:**
- First call: 1-5 minutes (loading model)
- Subsequent calls: 30-90 seconds per agent
- Per case (7 agents): 5-10 minutes
- 10 questions (4 methods): ~2 hours
- 100 questions: ~15-20 hours

**Solutions:**

1. **Start with small test**:
```bash
python scripts/run_baseline_comparison.py --n 1
```

2. **Use faster model** (llama3:8b is 10x faster):
```bash
python scripts/run_baseline_comparison.py --n 10 --config configs/llama3_8b.yaml
```

3. **Run overnight** for large evaluations

---

## Test Script Issues

### Issue 9: test_installation.py fails

**Error:**
```
ValueError: Failed to parse aggregator response: Field required
```

**Cause:** MockLLMClient not properly configured for all agent types.

**Solution:** Already fixed in `src/llm_client.py` - MockLLMClient now handles:
- Planner responses
- Specialist responses
- Aggregator responses
- Baseline method responses (CoT, Fixed Pipeline, Debate)

Run test again:
```bash
python test_installation.py
```

Should see:
```
[SUCCESS] ALL TESTS PASSED!
```

---

## Results Issues

### Issue 10: Results not saved

**Check:**
```bash
ls runs/baseline_comparison/
```

**If empty:** Check for errors in evaluation script output.

**If exists:** Results saved to timestamped folder:
```
runs/baseline_comparison/20250102_153045/
├── full_results.json      # Detailed results
└── summary.json           # Aggregate stats
```

---

## Next Steps After Errors

1. **Check logs** - Error messages usually indicate the issue
2. **Start small** - Test with `--n 1` before large runs
3. **Monitor resources** - Use `nvidia-smi` and Task Manager
4. **Use mock mode** - Set `provider: "mock"` in config for testing without models
5. **Ask for help** - Open GitHub issue with error message and system specs

---

## Verification Checklist

Before running full evaluation, verify:

- [ ] `python test_installation.py` passes all tests
- [ ] `ollama list` shows llama3:70b installed
- [ ] `curl http://localhost:11434` returns "Ollama is running"
- [ ] `ls data/medqa_us_test_4opt.json` shows dataset file exists
- [ ] `nvidia-smi` shows GPU available
- [ ] Sufficient free space: ~50GB disk, ~64GB RAM

---

## System Requirements Met

Your system (verified):
- ✅ 64GB RAM
- ✅ NVIDIA RTX 4090 (24GB VRAM)
- ✅ Windows with Ollama installed
- ✅ Python 3.12
- ✅ llama3:70b model downloaded
- ✅ MedQA dataset converted

You're good to go! 🚀
