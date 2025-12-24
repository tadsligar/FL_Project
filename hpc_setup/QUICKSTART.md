# HPC Quick Start - Step by Step

## Prerequisites Checklist

- [ ] Auburn University account
- [ ] Easley HPC account approved (request at https://aub.ie/hpcacct)
- [ ] DUO two-factor authentication enabled
- [ ] VPN installed (if off-campus)
- [ ] SSH client available

## Step 1: First Connection

**Connect to Easley:**
```bash
ssh <your-auburn-id>@easley.auburn.edu
```

Replace `<your-auburn-id>` with your Auburn username (e.g., `abc0123`).

You'll be prompted for:
1. Your Auburn password
2. DUO push notification (approve on your phone)

## Step 2: Initial Setup on Easley

Once logged in, run the setup script:

```bash
# Create directories
mkdir -p ~/FL_Project
mkdir -p ~/scratch/medqa_runs

# Check your storage quota
quota

# View available partitions
sinfo -s

# Check available software
module avail python
```

## Step 3: Transfer Your Code

**From your LOCAL machine** (not on Easley), navigate to the parent directory of FL_Project:

```bash
cd /path/to/repos

# Transfer code (excluding runs/ and data/)
rsync -avz --exclude 'runs/' \
           --exclude 'data/' \
           --exclude '.git/' \
           --exclude '__pycache__/' \
           FL_Project/ <your-auburn-id>@easley.auburn.edu:~/FL_Project/
```

Or use the helper script:
```bash
cd FL_Project/hpc_setup
bash transfer_code.sh <your-auburn-id>
```

## Step 4: Install Dependencies on Easley

Back on Easley, install Python packages:

```bash
cd ~/FL_Project
module load python/3.11
pip install --user requests pyyaml tqdm
```

## Step 5: Run Test Job

Submit a test job to verify everything works:

```bash
cd ~/FL_Project
sbatch hpc_setup/job_scripts/test_single_question.sh
```

Check job status:
```bash
squeue -u <your-auburn-id>
```

View output when done:
```bash
cat test_*.out
cat test_*.err
```

## Step 6: Run Full Experiments

Once the test succeeds, submit full experiments:

**Progressive Temperature baseline (1,071 questions):**
```bash
sbatch hpc_setup/job_scripts/run_progressive_temp.sh
```

**Progressive Temperature Parallel V4 (1,071 questions):**
```bash
sbatch hpc_setup/job_scripts/run_parallel_v4.sh
```

## Important Notes

### LLM Backend on HPC

⚠️ **Important:** Your local setup uses Ollama running on localhost. On the HPC cluster, you'll need to either:

1. **Use a remote API** (OpenAI, Anthropic, etc.)
   - Modify `configs/qwen25_32b.yaml` to use API provider
   - Set API keys in environment or config

2. **Check if Ollama is available** on the cluster:
   ```bash
   module avail ollama
   ```

3. **Use a different local model** if available on HPC

You may need to modify your config files before running on HPC.

### Monitoring Jobs

```bash
# Check all your jobs
squeue -u <your-auburn-id>

# Detailed job info
scontrol show job <job_id>

# Cancel a job
scancel <job_id>

# View output in real-time
tail -f <output-file>.out
```

### Storage

- **Home** (`~/`): 50GB, backed up - code and configs
- **Scratch** (`~/scratch/`): Large temp space - results and data
- Move large results to scratch to avoid quota issues

### Getting Results Back

**Download results to your local machine:**
```bash
scp -r <your-auburn-id>@easley.auburn.edu:~/FL_Project/runs ./hpc_results
```

## Troubleshooting

**Can't connect:** Check VPN if off-campus

**Out of quota:** Move results to scratch
```bash
mv ~/FL_Project/runs ~/scratch/medqa_runs
ln -s ~/scratch/medqa_runs ~/FL_Project/runs
```

**Job fails immediately:** Check error file (`*.err`)

**Module not found:** Check available modules with `module avail`

## Next Steps

1. Connect to Easley
2. Set up environment
3. Transfer code
4. Run test job
5. Adjust configs for HPC environment
6. Submit full experiments
7. Download results

For detailed info, see `hpc_setup/README.md`
