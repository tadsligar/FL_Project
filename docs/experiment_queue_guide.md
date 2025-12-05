# Experiment Queue Guide

Run experiments continuously with a dynamic queue system. Add new experiments while others are running!

## Quick Start

**1. Start the queue runner:**
```bash
python scripts/run_experiment_queue.py
```

**2. Add experiments to the queue:**
Just drop `.yaml` config files into `configs/batch/queue/`

**3. Keep adding more:**
While experiments run, add more configs - they'll automatically start when ready!

## How It Works

```
configs/batch/
├── queue/              ← Add experiment configs here
├── completed/          ← Successful experiments moved here
└── failed/            ← Failed experiments moved here
```

1. Queue runner monitors `configs/batch/queue/`
2. Picks up oldest config first (by creation time)
3. Runs the experiment
4. Moves config to `completed/` or `failed/`
5. Checks for next experiment (every 30 seconds)
6. Keeps running until:
   - You press Ctrl+C, OR
   - Queue empty for 5 minutes (configurable)

## Experiment Config Format

Same as batch runner, but **one experiment per file**:

```yaml
name: "Descriptive name for logs"
script: test_script_name.py
config: configs/your_config.yaml
args: --n 1071 --output runs/your_output
```

## Example Workflow

**Terminal 1: Start queue runner**
```bash
python scripts/run_experiment_queue.py
```

**Terminal 2: Add experiments as you think of them**
```bash
# Add first experiment
cat > configs/batch/queue/01_zero_shot.yaml <<EOF
name: "Zero-shot baseline"
script: test_zero_shot.py
config: configs/qwen25_32b_temp00.yaml
args: --n 1071 --output runs/zero_shot_full
EOF

# Later, add another while first is running
cat > configs/batch/queue/02_physician_role.yaml <<EOF
name: "Physician role debate"
script: test_debate_physician_role.py
config: configs/qwen25_32b_temp03.yaml
args: --n 1071 --output runs/physician_debate_full
EOF

# Keep adding more as you plan them...
```

## Command-Line Options

```bash
# Default behavior (5 min timeout)
python scripts/run_experiment_queue.py

# Custom queue directory
python scripts/run_experiment_queue.py --queue my_experiments/queue

# Check more frequently
python scripts/run_experiment_queue.py --check-interval 15

# Longer idle timeout (10 minutes)
python scripts/run_experiment_queue.py --idle-timeout 600

# Stop immediately when queue is empty (don't wait)
python scripts/run_experiment_queue.py --stop-when-empty
```

## Queue Management

### Check Queue Status
```bash
# See what's in queue
ls configs/batch/queue/

# See completed
ls configs/batch/completed/

# See failed
ls configs/batch/failed/
```

### Add Experiment While Running
```bash
# Create new config file in queue directory
cat > configs/batch/queue/new_experiment.yaml <<EOF
name: "My new experiment"
script: test_zero_shot.py
config: configs/qwen25_32b_temp03.yaml
args: --n 100 --output runs/new_test
EOF
```

### Prioritize an Experiment
Rename to start with earlier number:
```bash
mv configs/batch/queue/experiment.yaml configs/batch/queue/00_urgent.yaml
```
(Oldest file by creation time runs first, but you can also use prefixes for clarity)

### Remove from Queue
Just delete the file:
```bash
rm configs/batch/queue/unwanted_experiment.yaml
```

### Rerun Failed Experiment
Move from failed back to queue:
```bash
mv configs/batch/failed/experiment_20250115_*.yaml configs/batch/queue/experiment_retry.yaml
```

## Example Queue Setup

Here's a typical research workflow:

```bash
# Start with baseline (n=10 for quick validation)
configs/batch/queue/01_quick_validation.yaml

# Then full baselines
configs/batch/queue/02_zero_shot_full.yaml
configs/batch/queue/03_zero_shot_physician_full.yaml
configs/batch/queue/04_single_shot_cot_full.yaml

# Then multi-agent methods
configs/batch/queue/05_debate_baseline_full.yaml
configs/batch/queue/06_physician_role_temp03_full.yaml

# Temperature sweep (add these later as you analyze results)
configs/batch/queue/07_physician_role_temp00_full.yaml
configs/batch/queue/08_physician_role_temp07_full.yaml
```

## Monitoring Progress

### Watch the log in real-time
```bash
tail -f logs/experiment_queue/queue_run_*.log
```

### Check if runner is still active
```bash
# Windows
tasklist | findstr python

# Linux/Mac
ps aux | grep run_experiment_queue
```

### See current experiment output
Output streams directly to console where you started the queue runner.

## Tips

### 1. Use Numbered Prefixes
```
01_baseline.yaml
02_improved.yaml
03_advanced.yaml
```
Makes it clear what order you want (even though oldest file runs first).

### 2. Start Small, Scale Up
```yaml
# First: Quick validation (n=10)
name: "Validation run"
args: --n 10 --output runs/validate

# If successful, add full dataset (n=1071)
name: "Full dataset run"
args: --n 1071 --output runs/full
```

### 3. Overnight/Weekend Runs
```bash
# Friday afternoon: Fill queue with week's experiments
ls configs/batch/queue/
# 01_baseline_full.yaml
# 02_physician_role_full.yaml
# 03_temperature_sweep_00.yaml
# 04_temperature_sweep_01.yaml
# ... 10 experiments total

# Start queue
python scripts/run_experiment_queue.py --idle-timeout 3600  # 1 hour timeout

# Monday: Check results
ls configs/batch/completed/
```

### 4. Parallel Queues (Advanced)
If you have multiple GPUs or RunPod instances:

```bash
# Terminal 1: Local queue
python scripts/run_experiment_queue.py --queue configs/batch/queue_local

# Terminal 2: RunPod queue
python scripts/run_experiment_queue.py --queue configs/batch/queue_runpod
```

## Comparison: Queue vs Batch Runner

| Feature | Batch Runner | Queue Runner |
|---------|--------------|--------------|
| Config format | Multiple experiments in one file | One experiment per file |
| Dynamic additions | No | Yes |
| When to use | Pre-planned experiment sets | Exploratory research, add as you go |
| Best for | Reproducible runs | Iterative development |

## Troubleshooting

### "Queue runner stopped unexpectedly"
- Check log file: `logs/experiment_queue/queue_run_*.log`
- Look for errors in most recent entries
- Verify experiments in failed directory

### "Experiment validated but didn't run"
- Check script path: `scripts/{script}` must exist
- Check config path: must exist and be valid YAML
- Check for typos in config file

### "Can't add experiments while running"
- Just create .yaml files in queue directory
- No need to restart queue runner
- Files are checked every 30 seconds (by default)

### "Want to stop queue but not lose progress"
- Press Ctrl+C (clean shutdown)
- Completed experiments are saved
- Remaining queue files stay in queue directory
- Restart later and it will continue

## What You Have Now

Your first experiment is ready to run:
- **Queue runner:** `scripts/run_experiment_queue.py`
- **First experiment:** `configs/batch/queue/01_zero_shot_physician_full.yaml`
  - Tests zero-shot with physician role
  - Full 1,071 questions
  - Temperature 0.0
  - Runs after current zero-shot completes (or you can start queue now)

## Next Steps

1. **Start the queue:**
   ```bash
   python scripts/run_experiment_queue.py
   ```

2. **Add more experiments as you think of them:**
   Create new .yaml files in `configs/batch/queue/`

3. **Monitor progress:**
   Watch the console output or check the log file

4. **Let it run:**
   Go do other work, experiments run automatically!

Happy queuing!
