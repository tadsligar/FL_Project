# Auburn HPC Easley Cluster Setup

This folder contains setup and deployment scripts for running experiments on Auburn's Easley HPC cluster.

## Prerequisites

- **Auburn University Account**: Your Auburn email/username
- **Easley Cluster Account**: Request at https://aub.ie/hpcacct
- **DUO Two-Factor Authentication**: Must be enabled on your account
- **VPN Access**: Required if connecting off-campus
- **SSH Client**:
  - Windows: PuTTY or built-in SSH
  - Mac/Linux: Built-in terminal

## Quick Start

### 1. Connect to Easley

```bash
ssh <your-auburn-id>@easley.auburn.edu
```

Example:
```bash
ssh abc0123@easley.auburn.edu
```

You'll be prompted for:
1. Your Auburn password
2. DUO two-factor authentication

### 2. Check Available Resources

Once connected, check what's available:

```bash
# View partition information
sinfo

# View available software modules
module avail

# Check GPU availability
sinfo -p gpu
```

### 3. Transfer Files

**From your local machine to Easley:**
```bash
scp -r FL_Project <your-auburn-id>@easley.auburn.edu:~/
```

**From Easley to your local machine:**
```bash
scp -r <your-auburn-id>@easley.auburn.edu:~/results ./
```

## Storage Locations

- **Home Directory** (`~/`): 50GB quota, backed up
- **Scratch Space** (`/scratch/<username>`): Large temporary storage, not backed up
- **Project Space**: Shared team storage (if applicable)

## Slurm Job Commands

### Submit a Batch Job
```bash
sbatch job_script.sh
```

### Check Job Status
```bash
squeue -u <your-auburn-id>
```

### View Detailed Job Info
```bash
scontrol show job <job_id>
```

### Cancel a Job
```bash
scancel <job_id>
```

### Interactive Session
```bash
salloc -N 1 -n 4 -t 01:00:00
```

### Interactive GPU Session
```bash
salloc -N 1 -n 4 --gres=gpu:1 -t 01:00:00
```

## Module System

Load required software using modules:

```bash
# See available modules
module avail

# Load Python
module load python/3.11

# Load CUDA (for GPU jobs)
module load cuda/12.0

# See loaded modules
module list

# Unload a module
module unload python/3.11

# Unload all modules
module purge
```

## File Structure

```
hpc_setup/
├── README.md                          # This file
├── connect.sh                         # Helper script to connect
├── transfer_code.sh                   # Transfer project to HPC
├── job_scripts/
│   ├── test_single_question.sh       # Test job (1 question)
│   ├── run_progressive_temp.sh       # Full progressive temp run
│   ├── run_parallel_v4.sh            # Progressive temp parallel V4
│   └── gpu_interactive.sh            # Start interactive GPU session
└── setup/
    ├── install_dependencies.sh        # Install Python packages
    └── setup_environment.sh           # Configure environment
```

## Next Steps

1. Connect to Easley cluster
2. Transfer your FL_Project code
3. Set up Python environment
4. Submit test job
5. Run full experiments

See individual scripts in `job_scripts/` folder for examples.
