# Setting Up FL_Project on Easley HPC - Step by Step

## Step 1: Initial Environment Check

**On Easley SSH terminal**, run these commands:

```bash
# Check where you are
pwd
# Should show: /home/tzs0128

# Check your quota
quota -s

# Check available partitions
sinfo -s

# Check available Python
module avail python

# Check available modules
module avail | less
```

## Step 2: Create Directory Structure

```bash
# Create project directory
mkdir -p ~/FL_Project

# Create scratch directories for large files
mkdir -p /scratch/tzs0128/FL_Project_runs
mkdir -p /scratch/tzs0128/FL_Project_data
mkdir -p /scratch/tzs0128/logs

# Verify
ls -la ~/
ls -la /scratch/tzs0128/
```

## Step 3: Transfer Your Code to Easley

**On your LOCAL machine** (open a NEW terminal/PowerShell, don't close SSH):

```bash
# Navigate to parent directory
cd C:\Users\Tad\OneDrive\Documents\repos

# Transfer code (excluding large files)
rsync -avz --exclude 'runs/' ^
           --exclude 'data/' ^
           --exclude '.git/' ^
           --exclude '__pycache__/' ^
           --exclude '*.pyc' ^
           --exclude 'nul' ^
           FL_Project/ tzs0128@easley.auburn.edu:~/FL_Project/
```

Or if rsync isn't available on Windows, use scp:
```bash
scp -r FL_Project tzs0128@easley.auburn.edu:~/
```

## Step 4: Install Python Dependencies

**Back on Easley SSH terminal:**

```bash
# Load Python module
module purge
module load python/3.11

# Verify Python
python --version
which python

# Install required packages
pip install --user requests pyyaml tqdm

# Verify installation
pip list --user | grep -E "(requests|pyyaml|tqdm)"
```

## Step 5: Check for Ollama/LLM Options

**CRITICAL:** Your local setup uses Ollama. We need to check what's available on HPC:

```bash
# Check if Ollama is available
module avail ollama
module spider ollama

# Check for other LLM options
module avail | grep -i llama
module avail | grep -i llm

# Check CUDA for GPU inference
module avail cuda
```

**If Ollama is NOT available**, you have these options:

### Option A: Use OpenAI API (Recommended for initial testing)
You'll need to modify configs to use OpenAI API instead of local Ollama.

### Option B: Use vLLM or llama.cpp (if available)
Check if HPC has other inference engines available.

### Option C: Request Ollama installation
Email hpcadmin@auburn.edu to request Ollama installation.

## Step 6: Transfer MedQA Dataset

**On Easley:**

First, check if you have the dataset locally. If yes:

**From your LOCAL machine:**
```bash
# Transfer dataset to scratch
scp C:\Users\Tad\OneDrive\Documents\repos\FL_Project\data\medqa_us_test_4opt.json ^
    tzs0128@easley.auburn.edu:/scratch/tzs0128/FL_Project_data/

# Or use rsync
rsync -avz FL_Project/data/ tzs0128@easley.auburn.edu:/scratch/tzs0128/FL_Project_data/
```

**On Easley, create symlink:**
```bash
cd ~/FL_Project
ln -s /scratch/tzs0128/FL_Project_data data
ls -la data/
```

## Step 7: Configure for HPC Environment

### Option 1: If using OpenAI API

**On Easley:**

```bash
cd ~/FL_Project

# Create HPC-specific config
cat > configs/hpc_openai.yaml << 'EOF'
model: "gpt-4o-mini"
provider: "openai"
api_key: "your-api-key-here"  # Replace with actual key
temperature: 1.0
max_output_tokens: 2048
timeout: 300
EOF
```

### Option 2: If Ollama is available

```bash
# Load Ollama module (if exists)
module load ollama

# Check if it's running
curl http://localhost:11434/api/tags

# Use existing config
# configs/qwen25_32b.yaml should work
```

## Step 8: Submit Test Job

```bash
cd ~/FL_Project

# Edit test job script to use correct config
nano hpc_setup/job_scripts/test_single_question.sh
```

Modify the last line based on your LLM backend:
```bash
# If using OpenAI:
python scripts/test_progressive_temperature_parallel.py \
    --n 1 \
    --parallel 5 \
    --config configs/hpc_openai.yaml \
    --output /scratch/tzs0128/FL_Project_runs/hpc_test

# If using Ollama (and it's available):
python scripts/test_progressive_temperature_parallel.py \
    --n 1 \
    --parallel 5 \
    --config configs/qwen25_32b.yaml \
    --output /scratch/tzs0128/FL_Project_runs/hpc_test
```

Save (Ctrl+O, Enter, Ctrl+X), then submit:
```bash
sbatch hpc_setup/job_scripts/test_single_question.sh
```

Check status:
```bash
squeue -u tzs0128
```

View output when done:
```bash
ls -la test_*.out test_*.err
cat test_*.out
cat test_*.err
```

## Step 9: If Test Succeeds - Submit Full Run

Once test works, submit full experiment:

```bash
# Edit run script if needed
nano hpc_setup/job_scripts/run_parallel_v4.sh

# Update email address in script
# Update config file path if using OpenAI

# Submit
sbatch hpc_setup/job_scripts/run_parallel_v4.sh

# Check status
squeue -u tzs0128

# Monitor output
tail -f parallel_v4_*.out
```

## Troubleshooting

### No Ollama Available

**Immediate solution:** Use OpenAI API for testing
```bash
# Install openai package
pip install --user openai

# Create config with your OpenAI key
cat > configs/hpc_openai.yaml << 'EOF'
model: "gpt-4o-mini"
provider: "openai"
api_key: "sk-YOUR-KEY-HERE"
temperature: 1.0
max_output_tokens: 2048
EOF

# Modify scripts to use this config
```

**Long-term solution:** Email hpcadmin@auburn.edu requesting Ollama installation

### Job Fails

```bash
# Check error file
cat error_*.err

# Check job details
scontrol show job <job_id>

# Check if modules loaded
module list
```

### Out of Quota

```bash
# Check usage
quota -s

# Move runs to scratch
mv ~/FL_Project/runs /scratch/tzs0128/FL_Project_runs
ln -s /scratch/tzs0128/FL_Project_runs ~/FL_Project/runs
```

### Import Errors

```bash
# Make sure Python module is loaded
module load python/3.11

# Reinstall packages
pip install --user --force-reinstall requests pyyaml tqdm
```

## Next Steps After Successful Test

1. **Run full Progressive Temperature baseline** (~20 hours):
   ```bash
   sbatch hpc_setup/job_scripts/run_progressive_temp.sh
   ```

2. **Run full Progressive Temperature Parallel V4** (~40 hours):
   ```bash
   sbatch hpc_setup/job_scripts/run_parallel_v4.sh
   ```

3. **Monitor jobs**:
   ```bash
   squeue -u tzs0128
   tail -f /scratch/tzs0128/logs/*.out
   ```

4. **Download results when complete**:
   From your LOCAL machine:
   ```bash
   rsync -avz tzs0128@easley.auburn.edu:/scratch/tzs0128/FL_Project_runs/ ./hpc_results/
   ```

## Quick Reference

```bash
# Connect
ssh tzs0128@easley.auburn.edu

# Check jobs
squeue -u tzs0128

# Cancel job
scancel <job_id>

# Check quota
quota -s

# Load Python
module load python/3.11

# Submit job
sbatch job_script.sh

# Interactive session
salloc -N 1 -n 8 -t 02:00:00
```
