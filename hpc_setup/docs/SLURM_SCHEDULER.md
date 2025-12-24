# Auburn Easley HPC - Slurm Scheduler Guide

## Sbatch Command

Primary job submission: `sbatch [OPTIONS] script.sh [args]`

## Common Sbatch Parameters

| Parameter | Short | Function | Example |
|-----------|-------|----------|---------|
| `--job-name` | `-J` | Job identifier | `-J "my_job"` |
| `--time` | `-t` | Runtime limit | `-t 24:00:00` (24 hrs) |
| `--nodes` | `-N` | Node count | `-N 2` |
| `--ntasks` | `-n` | Task quantity | `-n 16` |
| `--ntasks-per-node` | — | Tasks per node | `--ntasks-per-node=8` |
| `--cpus-per-task` | `-c` | CPUs per task | `-c 4` |
| `--partition` | `-p` | Resource partition | `-p general` |
| `--mem` | — | Memory allocation | `--mem=32G` |
| `--mem-per-cpu` | — | Memory per CPU | `--mem-per-cpu=4G` |
| `--gres` | — | Generic resources | `--gres=gpu:tesla:1` |
| `--array` | `-a` | Job array | `-a 0-9` |
| `--output` | `-o` | Output file | `-o job_%j.out` |
| `--error` | `-e` | Error file | `-e job_%j.err` |
| `--mail-type` | — | Email events | `--mail-type=END,FAIL` |
| `--mail-user` | — | Email address | `--mail-user=you@auburn.edu` |

## Partitions

### General Purpose Partitions

| Partition | Nodes | Default Memory | Total Memory | Priority |
|-----------|-------|----------------|--------------|----------|
| **general** | 126 | 3GB | 192GB | Community (lowest) |
| **bigmem2** | 21 | 7GB | 384GB | Department |
| **bigmem4** | — | 15GB | 768GB | Department |
| **AMD** | — | 1GB | 256GB | Investor |

### GPU Partitions

| Partition | GPUs/Node | Memory | Use Case |
|-----------|-----------|--------|----------|
| **gpu2** | 2 | 384GB | 1-2 GPU jobs |
| **gpu4** | 4 | 768GB | 3-4 GPU jobs, high memory |

### Partition Priority Tiers

1. **Dedicated** - Highest priority, no preemption
2. **Department** - High priority
3. **Investor** - Medium priority
4. **Community** (general) - Lowest priority, may be preempted

## Job States

| State | Code | Meaning |
|-------|------|---------|
| Pending | PD | Queued, waiting for resources |
| Running | R | Currently executing |
| Completing | CG | Finishing up |
| Completed | CD | Finished successfully |
| Cancelled | CA | User cancelled |
| Failed | F | Exited with error |
| Stopped | ST | Job stopped |
| Configuring | CF | Resources being allocated |

## Essential Commands

### Submit Jobs
```bash
sbatch job_script.sh
```

### Monitor Jobs
```bash
# View your jobs
squeue -u $USER

# View all jobs
squeue

# View specific partition
squeue -p general

# Detailed job info
scontrol show job <JOB_ID>
```

### Cancel Jobs
```bash
# Cancel specific job
scancel <JOB_ID>

# Cancel all your jobs
scancel -u $USER

# Cancel all jobs in partition
scancel -p general -u $USER
```

### Check Partitions
```bash
# Summary view
sinfo -s

# Detailed view
sinfo

# Specific partition
sinfo -p general
```

## Example Job Script

### Basic CPU Job

```bash
#!/bin/bash
#SBATCH -J my_job                # Job name
#SBATCH -N 1                     # 1 node
#SBATCH -n 16                    # 16 tasks (cores)
#SBATCH -t 24:00:00              # 24 hours
#SBATCH -p general               # Partition
#SBATCH --mem=32G                # 32GB memory
#SBATCH -o output_%j.out         # Output file (%j = job ID)
#SBATCH -e error_%j.err          # Error file
#SBATCH --mail-type=END,FAIL     # Email on completion/failure
#SBATCH --mail-user=tzs0128@auburn.edu

# Load modules
module load python/3.11

# Print job info
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start time: $(date)"

# Run your code
python my_script.py

echo "End time: $(date)"
```

### High Memory Job

```bash
#!/bin/bash
#SBATCH -J bigmem_job
#SBATCH -N 1
#SBATCH -n 32
#SBATCH -t 48:00:00
#SBATCH -p bigmem4               # High memory partition
#SBATCH --mem=512G               # 512GB memory
#SBATCH -o bigmem_%j.out

module load python/3.11
python memory_intensive.py
```

## Job Arrays

Submit multiple related jobs efficiently:

### Array Job Script

```bash
#!/bin/bash
#SBATCH -J array_job
#SBATCH --array=0-9              # Creates 10 jobs (0 through 9)
#SBATCH -N 1
#SBATCH -n 4
#SBATCH -t 02:00:00
#SBATCH -p general
#SBATCH -o array_%A_%a.out       # %A = master job ID, %a = task ID

# SLURM_ARRAY_TASK_ID contains the current array index
echo "Processing task $SLURM_ARRAY_TASK_ID"

python process.py --task_id $SLURM_ARRAY_TASK_ID
```

This creates 10 separate jobs, each with its own task ID (0-9).

### Array with File List

```bash
#!/bin/bash
#SBATCH --array=1-100            # 100 files
#SBATCH -t 01:00:00

# Get filename from list
FILE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" file_list.txt)

echo "Processing: $FILE"
python analyze.py $FILE
```

## Environment Variables

Key Slurm environment variables available in jobs:

| Variable | Description |
|----------|-------------|
| `$SLURM_JOB_ID` | Unique job ID |
| `$SLURM_JOB_NAME` | Job name |
| `$SLURM_ARRAY_JOB_ID` | Array master job ID |
| `$SLURM_ARRAY_TASK_ID` | Array task index |
| `$SLURM_CPUS_ON_NODE` | CPUs allocated |
| `$SLURM_JOB_NODELIST` | Nodes assigned |
| `$SLURM_NTASKS` | Number of tasks |

## Job Dependencies

Submit jobs that depend on other jobs:

```bash
# Submit first job
JOB1=$(sbatch job1.sh | awk '{print $4}')

# Submit second job that starts after first completes
sbatch --dependency=afterok:$JOB1 job2.sh

# Or after any completion (success or failure)
sbatch --dependency=afterany:$JOB1 job3.sh
```

## Best Practices

1. **Request appropriate resources**: Don't over-request memory/cores
2. **Use checkpoints**: Save progress for long jobs
3. **Test with short jobs first**: Use `-t 00:10:00` for testing
4. **Use job arrays** for multiple similar tasks
5. **Set email notifications** for long jobs
6. **Use appropriate partition**:
   - general: Standard jobs
   - bigmem2/4: Memory-intensive jobs
   - gpu2/4: GPU jobs
7. **Name jobs clearly**: Makes tracking easier
8. **Capture output**: Use `-o` and `-e` to save logs

## Troubleshooting

**Job pending forever:**
- Check partition availability: `sinfo -p general`
- Reduce resource requests
- Check priority queue: `squeue -p general -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"`

**Job fails immediately:**
- Check error file: `cat error_<job_id>.err`
- Verify paths are absolute
- Check module loads

**Out of memory:**
- Increase `--mem` request
- Use bigmem partition
- Check actual usage: `sacct -j <job_id> --format=JobID,MaxRSS`

**Job cancelled:**
- Exceeded time limit: increase `-t`
- Exceeded memory: increase `--mem`
- Check: `sacct -j <job_id> --format=JobID,State,ExitCode`
