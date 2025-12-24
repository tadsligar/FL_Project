# Auburn Easley HPC - Interactive Jobs Guide

## Overview

Interactive jobs enable debugging and testing before submitting batch jobs. The documentation states: **"Interactive jobs are an effective way to debug and troubleshoot workload steps."**

## salloc (Preferred Method)

### Basic Interactive Session

```bash
# Request 1 node with 16 cores
salloc -N 1 -n 16

# With time limit (default is partition limit)
salloc -N 1 -n 16 -t 04:00:00

# With specific partition
salloc -N 1 -n 8 -p general -t 02:00:00

# With memory specification
salloc -N 1 -n 16 --mem=32G -t 04:00:00
```

### Example Output

```
salloc: Granted job allocation 588384
salloc: Waiting for resource configuration
salloc: Nodes node123 are ready for job
[tzs0128@node123 ~]$
```

Once allocated, you're on the compute node and can run commands interactively.

### Exit Interactive Session

```bash
exit
```

## GPU Interactive Sessions

### Request GPU Session

```bash
# 1 GPU on gpu2 partition
salloc -N 1 -n 8 -p gpu2 --gres=gpu:tesla:1 -t 04:00:00

# 2 GPUs on gpu2 partition
salloc -N 1 -n 16 -p gpu2 --gres=gpu:tesla:2 -t 04:00:00

# 1 GPU on gpu4 partition with more memory
salloc -N 1 -n 8 -p gpu4 --gres=gpu:tesla:1 --mem=64G -t 04:00:00
```

### Once Allocated

```bash
# Load CUDA
module load cuda11.0/toolkit

# Check GPU
nvidia-smi

# Test your code
python test_gpu.py

# Exit when done
exit
```

## srun (Legacy Method)

**Note:** As of March 31, 2023, using srun for interactive jobs requires loading a special module.

### Setup for srun

```bash
module load slurm/auhpc
```

### Basic srun Interactive

```bash
srun -N 1 -n 16 --pty /bin/bash
```

**Recommendation:** Use `salloc` instead of `srun` for interactive jobs.

## Common Interactive Use Cases

### 1. Debug Python Code

```bash
# Request resources
salloc -N 1 -n 4 -t 01:00:00

# Load Python
module load python/3.11

# Run interactively
python
>>> import numpy as np
>>> # test your code
>>> exit()

# Or run script
python my_script.py

# Exit session
exit
```

### 2. Test GPU Code

```bash
# Request GPU
salloc -N 1 -n 8 -p gpu2 --gres=gpu:tesla:1 -t 02:00:00

# Load modules
module load cuda11.0/toolkit
module load python/3.11

# Verify GPU
nvidia-smi

# Test PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# Run your GPU code
python train_model.py --epochs 1

# Exit
exit
```

### 3. Compile Code

```bash
# Request resources for compilation
salloc -N 1 -n 8 -t 01:00:00

# Load compiler
module load gcc/9.3.0

# Compile
./configure --prefix=$HOME/software
make -j 8
make install

# Test
./my_program --test

# Exit
exit
```

### 4. Test MPI Code

```bash
# Request multiple cores
salloc -N 1 -n 16 -t 01:00:00

# Load MPI
module load openmpi/4.0.3

# Test MPI code
mpirun -np 4 ./my_mpi_program

# Exit
exit
```

## Interactive Job Parameters

All sbatch parameters work with salloc:

```bash
salloc [OPTIONS]
  -N, --nodes=<count>              Number of nodes
  -n, --ntasks=<count>             Number of tasks
  -c, --cpus-per-task=<count>      CPUs per task
  -t, --time=<time>                Time limit (HH:MM:SS)
  -p, --partition=<name>           Partition
  --mem=<size>                     Memory (e.g., 32G)
  --mem-per-cpu=<size>             Memory per CPU
  --gres=gpu:tesla:<count>         GPUs
  -J, --job-name=<name>            Job name
```

## Recommended Workflow

1. **Acquire software** - Identify what you need
2. **Test on login node** - Quick checks (don't run compute-intensive tasks!)
3. **Request interactive job** - `salloc` with appropriate resources
4. **Load modules** - `module load ...`
5. **Test and debug** - Run commands, identify errors
6. **Iterate** - Fix issues, test again
7. **Create batch script** - Once working, convert to sbatch
8. **Submit batch job** - `sbatch script.sh`
9. **Production runs** - Scale up with verified code

## Best Practices

1. **Keep sessions short**: Request only the time you need (1-4 hours typical)
2. **Don't waste resources**: Exit when done, don't leave idle
3. **Use appropriate partition**:
   - general: Standard testing
   - gpu2/gpu4: GPU debugging
   - bigmem: Memory-intensive testing
4. **Load modules after allocation**: Wait until on compute node
5. **Test small first**: Use small datasets/short runs for testing
6. **Save commands**: Keep track of working commands for batch script

## Troubleshooting

### Session Pending Forever

```bash
# Check queue
squeue -p general

# Try different partition
salloc -p bigmem2 -N 1 -n 8

# Reduce resources
salloc -N 1 -n 4 -t 01:00:00
```

### Can't Load Modules

Wait until you're on the compute node:
```bash
[tzs0128@login01 ~]$ salloc -N 1 -n 4
salloc: Granted job allocation 12345
[tzs0128@node123 ~]$ module load python/3.11  # NOW load modules
```

### Session Disconnects

Interactive sessions end if you disconnect. For long-running tasks:
- Use `screen` or `tmux`
- Or submit as batch job instead

### Out of Memory

```bash
# Request more memory
salloc -N 1 -n 8 --mem=64G

# Or use bigmem partition
salloc -N 1 -n 8 -p bigmem2
```

## Example: Full Debug Workflow

```bash
# 1. Request interactive session
salloc -N 1 -n 8 -p general -t 02:00:00

# 2. Wait for allocation
# salloc: Granted job allocation 12345
# [tzs0128@node123 ~]$

# 3. Load required modules
module load python/3.11
module list

# 4. Navigate to project
cd ~/FL_Project

# 5. Test code
python scripts/test_progressive_temperature.py --n 1

# 6. Debug if needed
python -m pdb scripts/test_progressive_temperature.py --n 1

# 7. Test works! Create batch script
# (copy working commands to job script)

# 8. Exit interactive session
exit

# 9. Submit batch job
sbatch my_job.sh
```

## Quick Reference

| Task | Command |
|------|---------|
| Standard session | `salloc -N 1 -n 16 -t 04:00:00` |
| GPU session | `salloc -N 1 -p gpu2 --gres=gpu:tesla:1 -t 02:00:00` |
| High memory | `salloc -N 1 -n 8 -p bigmem2 --mem=128G -t 04:00:00` |
| Check status | `squeue -u $USER` |
| Exit session | `exit` |
| Cancel if stuck | `scancel <job_id>` |
