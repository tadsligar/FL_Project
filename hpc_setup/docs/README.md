# Auburn Easley HPC - Complete Documentation

This folder contains comprehensive guides for using Auburn University's Easley HPC cluster.

## Quick Navigation

| Guide | Description |
|-------|-------------|
| **[GPU_GUIDE.md](GPU_GUIDE.md)** | NVIDIA Tesla T4 GPUs, partitions, batch & interactive GPU jobs |
| **[SLURM_SCHEDULER.md](SLURM_SCHEDULER.md)** | Job submission, partitions, sbatch parameters, monitoring |
| **[INTERACTIVE_JOBS.md](INTERACTIVE_JOBS.md)** | salloc command, debugging, testing code |
| **[SOFTWARE_MODULES.md](SOFTWARE_MODULES.md)** | LMOD modules, Python, CUDA, custom modules |
| **[STORAGE_FILESYSTEMS.md](STORAGE_FILESYSTEMS.md)** | Home, scratch, quotas, file transfer |

## Quick Start

### 1. Connect
```bash
ssh tzs0128@easley.auburn.edu
```

### 2. Setup Environment
```bash
module load python/3.11
mkdir -p ~/FL_Project
mkdir -p /scratch/tzs0128/FL_Project_runs
```

### 3. Transfer Code
From local machine:
```bash
rsync -avz --exclude 'runs/' FL_Project/ tzs0128@easley.auburn.edu:~/FL_Project/
```

### 4. Test
```bash
sbatch hpc_setup/job_scripts/test_single_question.sh
```

## Key Resources

### GPU Resources
- **GPUs:** NVIDIA Tesla T4 (2,560 CUDA cores each)
- **Partitions:** gpu2 (2 GPUs), gpu4 (4 GPUs)
- **Request:** `--gres=gpu:tesla:1`

### Storage
- **Home:** ~/  (50GB, backed up)
- **Scratch:** /scratch/$USER (large, temporary)

### Modules
- **Python:** `module load python/3.11`
- **CUDA:** `module load cuda11.0/toolkit`

## Common Commands

```bash
# Submit job
sbatch job_script.sh

# Check status
squeue -u $USER

# Interactive session
salloc -N 1 -n 8 -t 02:00:00

# GPU interactive
salloc -N 1 -p gpu2 --gres=gpu:tesla:1 -t 02:00:00

# Check quota
quota

# Cancel job
scancel <job_id>
```

## Getting Help

- **Documentation:** See individual guides above
- **HPC Admin:** hpcadmin@auburn.edu
- **Account Requests:** https://aub.ie/hpcacct
- **Software Requests:** https://aub.ie/hpcsw

## Best Practices

1. **Test first:** Use interactive jobs or short test jobs
2. **Use scratch:** Write large output to /scratch/$USER
3. **Load modules:** Always specify modules in job scripts
4. **Monitor resources:** Check quotas and job status regularly
5. **Clean up:** Delete old files from scratch periodically

## Your Info

- **Username:** tzs0128
- **Home:** /home/tzs0128
- **Scratch:** /scratch/tzs0128
- **Email:** tzs0128@auburn.edu
