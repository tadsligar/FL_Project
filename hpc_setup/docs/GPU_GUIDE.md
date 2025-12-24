# Auburn Easley HPC - GPU Guide

## GPU Hardware Specifications

Easley cluster nodes feature **NVIDIA Tesla T4 devices** with:

### Core Specifications
- **40 Multiprocessors** with **64 CUDA Cores per MP**
- **Total CUDA cores**: 2,560
- **Clock rate**: 1.59 GHz (GPU), 5001 MHz (memory)
- **Memory Bus Width**: 256-bit
- **L2 Cache**: 4 MB
- **Shared memory per block**: 49,152 bytes
- **Registers per block**: 65,536

### Threading Capabilities
- **Warp size**: 32 threads
- **Max threads per block**: 1,024
- **Max thread block dimensions**: (1024, 1024, 64)

### Features
- **ECC Support**: Enabled
- **Unified Addressing**: Yes
- **Managed Memory**: Yes

## GPU Partitions

Two GPU partitions are available:

| Partition | GPUs per Node | Memory | Example Submission |
|-----------|---------------|--------|-------------------|
| **gpu2** | 2 | 384GB | `sbatch -p gpu2 --gres=gpu:tesla:1` |
| **gpu4** | 4 | 768GB | `sbatch -p gpu4 --gres=gpu:tesla:2` |

**Note:** You can request 1-2 GPUs on gpu2, or 1-4 GPUs on gpu4.

## Batch GPU Job Example

Create a file `gpu_job.sh`:

```bash
#!/bin/bash
#SBATCH --partition=gpu2              # Use gpu2 partition
#SBATCH --time=00:15:00               # 15 minute time limit
#SBATCH --nodes=1                     # 1 node
#SBATCH --ntasks-per-node=1           # 1 task
#SBATCH --gres=gpu:tesla:1            # Request 1 Tesla GPU
#SBATCH --job-name="my_gpu_job"       # Job name
#SBATCH --output=gpu_job_%j.out       # Output file
#SBATCH --error=gpu_job_%j.err        # Error file
#SBATCH --mail-type=END,FAIL          # Email notifications
#SBATCH --mail-user=your@email.com    # Your email

# Load CUDA module
module load cuda11.0/toolkit

# Check GPU availability
nvidia-smi

# Run your GPU code
python my_gpu_script.py
```

Submit with:
```bash
sbatch gpu_job.sh
```

## Interactive GPU Session

Request an interactive GPU session:

```bash
# Request 1 GPU on gpu2 partition for 4 hours
salloc -N 1 -p gpu2 --gres=gpu:tesla:1 -t 04:00:00

# Once allocated, load CUDA
module load cuda11.0/toolkit

# Check GPU
nvidia-smi

# Run commands interactively
python test_gpu.py

# Exit when done
exit
```

## CUDA Modules Available

Check available CUDA versions:
```bash
module avail cuda
```

Load CUDA:
```bash
module load cuda11.0/toolkit
# or
module load cuda/12.0  # (if available)
```

## GPU Programming Concepts

### CUDA (Compute Unified Device Architecture)
Programming model designed to support GPUs for general-purpose computing.

### Key Terms

**Kernel**: The parallel portion executing on the GPU device

**Streaming Multiprocessor (SM)**: Comparable to a small CPU with its own cores, registers, and caches

**CUDA Core**: Individual execution units within each SM that process thread instructions

**Warp**: A collection of 32 threads executing identical instructions on different data

### Thread Hierarchy

1. **Grid**: Multiple thread blocks organized as a matrix, mapping to the GPU device
2. **Block**: 1D, 2D, or 3D matrix of threads executed by an SM
3. **Thread**: Basic execution unit processed by a CUDA core

## GPU vs CPU Architecture

GPUs employ significantly more cores than CPUs but with:
- Less emphasis on instruction set (control)
- Less internal memory per core (cache)
- **Result**: Higher parallelism for specialized workloads
- **Trade-off**: Greater latency tolerance required

## Monitoring GPU Usage

### Check GPU Status
```bash
nvidia-smi
```

### Watch GPU Usage in Real-Time
```bash
watch -n 1 nvidia-smi
```

### Check GPU in Job
Add to your job script:
```bash
nvidia-smi >> gpu_status_$SLURM_JOB_ID.txt
```

## Best Practices

1. **Test on 1 GPU first** before requesting multiple GPUs
2. **Use interactive sessions** for debugging
3. **Load appropriate CUDA module** before running GPU code
4. **Check GPU availability** with `nvidia-smi` before running
5. **Request appropriate partition**:
   - gpu2 for 1-2 GPUs
   - gpu4 for 3-4 GPUs or higher memory needs
6. **Set reasonable time limits** - GPU partitions are in high demand

## Example: PyTorch GPU Job

```bash
#!/bin/bash
#SBATCH --partition=gpu2
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --gres=gpu:tesla:1
#SBATCH --job-name="pytorch_training"
#SBATCH --output=train_%j.out

module load cuda11.0/toolkit
module load python/3.11

# Verify GPU is available
nvidia-smi

# Run PyTorch training
python train_model.py
```

## Troubleshooting

**GPU not found:**
- Verify you're on a GPU partition: `squeue -j $SLURM_JOB_ID`
- Check CUDA module is loaded: `module list`
- Run `nvidia-smi` to verify GPU allocation

**Out of memory:**
- Reduce batch size
- Request gpu4 partition (more memory)
- Use gradient checkpointing

**Job pending:**
- GPU partitions may have queues
- Check queue: `squeue -p gpu2`
- Consider requesting fewer GPUs
