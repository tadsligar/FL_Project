# Batch Experiment Runner Guide

Run multiple experiments sequentially without manual intervention.

## Quick Start

```bash
# Run a batch of experiments
python scripts/run_batch_experiments.py --batch configs/batch/quick_validation.yaml

# Test what would run without actually running (dry run)
python scripts/run_batch_experiments.py --batch configs/batch/quick_validation.yaml --dry-run

# Stop entire batch if any experiment fails
python scripts/run_batch_experiments.py --batch configs/batch/quick_validation.yaml --stop-on-error
```

## How It Works

1. Create a batch configuration YAML file defining experiments to run
2. Run `scripts/run_batch_experiments.py` with your batch config
3. Experiments execute sequentially, one after another
4. Progress logged to both console and `logs/batch_runs/` directory
5. Results save to specified output directories

## Batch Configuration Format

```yaml
experiments:
  - name: "Human-readable experiment description"
    script: test_script_name.py  # Script in scripts/ directory
    config: configs/your_config.yaml  # Path to config file
    args: --n 100 --output runs/your_output  # Optional args

  - name: "Another experiment"
    script: test_another.py
    config: configs/another_config.yaml
    args: --n 50
```

## Pre-Made Batch Configurations

### 1. Quick Validation (`configs/batch/quick_validation.yaml`)
**Purpose:** Verify all methods work before long runs
**Size:** n=10 per test
**Time:** ~30 minutes
**Use case:** Testing after code changes

```bash
python scripts/run_batch_experiments.py --batch configs/batch/quick_validation.yaml
```

### 2. Temperature 0.3 Full Comparison (`configs/batch/temperature_sweep_temp03.yaml`)
**Purpose:** Compare all methods at optimal temperature
**Size:** n=100 per test
**Time:** ~8 hours
**Use case:** Building comprehensive comparison table

```bash
python scripts/run_batch_experiments.py --batch configs/batch/temperature_sweep_temp03.yaml
```

### 3. Physician Role Temperature Sweep (`configs/batch/physician_role_temperature_sweep.yaml`)
**Purpose:** Temperature sensitivity analysis for main method
**Size:** n=100 per temperature
**Time:** ~15 hours
**Use case:** Finding optimal temperature for physician role debate

```bash
python scripts/run_batch_experiments.py --batch configs/batch/physician_role_temperature_sweep.yaml
```

### 4. Full Dataset Main Results (`configs/batch/full_dataset_main_results.yaml`)
**Purpose:** Final paper results on complete test set
**Size:** n=1,071 per test
**Time:** ~50-60 hours
**Use case:** Generating final publication results

**WARNING:** This is a VERY long run. Consider using RunPod.

```bash
python scripts/run_batch_experiments.py --batch configs/batch/full_dataset_main_results.yaml
```

## Creating Custom Batch Configs

1. Create a new YAML file in `configs/batch/`
2. Define experiments following the format above
3. Run with `--dry-run` first to verify

Example:
```yaml
# configs/batch/my_custom_batch.yaml
experiments:
  - name: "Zero-shot small test"
    script: test_zero_shot.py
    config: configs/qwen25_32b_temp03.yaml
    args: --n 20 --output runs/custom/zero_shot

  - name: "Debate small test"
    script: test_debate_physician_role.py
    config: configs/qwen25_32b_temp03.yaml
    args: --n 20 --output runs/custom/physician_debate
```

## Command-Line Options

```bash
--batch BATCH_FILE      # Required: Path to batch configuration YAML
--dry-run               # Optional: Show what would run without executing
--stop-on-error         # Optional: Stop if any experiment fails (default: continue)
```

## Output and Logging

### Console Output
Real-time experiment progress displayed in terminal

### Log Files
Saved to: `logs/batch_runs/{batch_name}_{timestamp}.log`

Log includes:
- Start/end time for each experiment
- Success/failure status
- Duration of each experiment
- Final summary with statistics

### Results
Each experiment saves results to its specified output directory:
- `results.json` - Accuracy and detailed results
- `metrics.json` - Token usage, timing, agreement patterns
- Individual question results

## Monitoring Progress

### Check Current Progress
```bash
# View log file (example)
tail -f logs/batch_runs/quick_validation_20250115_140532.log
```

### Check If Experiments Are Running
```bash
# On Windows
tasklist | findstr python

# On Linux/Mac
ps aux | grep python
```

## Tips

### Save Time
1. **Use dry run first:** Verify batch config before long runs
   ```bash
   python scripts/run_batch_experiments.py --batch configs/batch/my_batch.yaml --dry-run
   ```

2. **Start with small n:** Test with n=10 before full dataset
3. **Run validation batch** after code changes

### Save Money (RunPod)
1. **Batch your work:** Queue up multiple experiments in one pod session
2. **Download results frequently:** Don't lose data if pod terminates
3. **Use spot instances:** 70% cheaper for batch jobs that can handle interruptions

### Recover from Failures
By default, batch runner **continues on error**:
- If one experiment fails, others still run
- Check log file to see which failed
- Re-run failed experiments individually or create new batch

To **stop on first failure**:
```bash
python scripts/run_batch_experiments.py --batch my_batch.yaml --stop-on-error
```

## Example Workflow

### Quick Test → Full Run Workflow

1. **Validate setup** (30 min):
   ```bash
   python scripts/run_batch_experiments.py --batch configs/batch/quick_validation.yaml
   ```

2. **Temperature sweep** (15 hours):
   ```bash
   python scripts/run_batch_experiments.py --batch configs/batch/physician_role_temperature_sweep.yaml
   ```

3. **Full dataset** (50+ hours, overnight/weekend):
   ```bash
   python scripts/run_batch_experiments.py --batch configs/batch/full_dataset_main_results.yaml
   ```

### Overnight Run Strategy

Before bed:
```bash
# Start batch, redirect output to log
python scripts/run_batch_experiments.py \
  --batch configs/batch/temperature_sweep_temp03.yaml \
  2>&1 | tee overnight_run.log
```

Next morning:
```bash
# Check what completed
grep "✓\|✗" overnight_run.log

# Check final summary
tail -n 20 logs/batch_runs/*.log
```

## Troubleshooting

### "Batch file not found"
- Verify path: `ls configs/batch/your_batch.yaml`
- Use correct relative path from project root

### "Script not found"
- Scripts must be in `scripts/` directory
- Batch config should only specify filename, not full path
- Example: `script: test_zero_shot.py` (not `scripts/test_zero_shot.py`)

### "Config not found"
- Check config file exists: `ls configs/your_config.yaml`
- Use relative path from project root
- Example: `config: configs/qwen25_32b_temp03.yaml`

### Experiment hangs/freezes
- Check if Ollama server is running: `ollama list`
- Check for timeout in config (default: 300s)
- Monitor system resources (GPU memory, RAM)

### Partial results from failed batch
- Results are saved incrementally, even if batch fails
- Check individual output directories
- Re-run failed experiments individually

## Advanced Usage

### Combining with RunPod

1. Update batch config to use RunPod configs:
   ```yaml
   experiments:
     - name: "Zero-shot on RunPod"
       script: test_zero_shot.py
       config: configs/runpod_qwen25_32b_temp03.yaml  # Use RunPod config
       args: --n 1071 --output runs/runpod_results/zero_shot
   ```

2. Deploy RunPod pod and update endpoint in config
3. Run batch on your local machine (calls RunPod API)

### Running Multiple Batches in Parallel

**NOT RECOMMENDED** unless you have multiple GPUs/pods.

If you have 2 RunPod pods:
```bash
# Terminal 1
python scripts/run_batch_experiments.py --batch configs/batch/batch1.yaml

# Terminal 2 (with different RunPod config)
python scripts/run_batch_experiments.py --batch configs/batch/batch2.yaml
```

## What's Next?

After running batches:
1. **Analyze results:** Use `scripts/analyze_results.py` (if exists)
2. **Compare methods:** Create comparison tables from results.json files
3. **Statistical testing:** Check if differences are significant
4. **Qualitative analysis:** Review specific question examples

Happy batching!
