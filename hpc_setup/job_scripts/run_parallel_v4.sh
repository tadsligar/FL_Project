#!/bin/bash
#SBATCH -J medqa_parallel_v4       # Job name
#SBATCH -N 1                       # Number of nodes
#SBATCH -n 32                      # Number of cores (for parallel exploration)
#SBATCH -t 72:00:00                # Time limit (72 hours)
#SBATCH -p general                 # Partition
#SBATCH --mem=64G                  # Memory
#SBATCH -o parallel_v4_%j.out      # Standard output
#SBATCH -e parallel_v4_%j.err      # Standard error
#SBATCH --mail-type=END,FAIL       # Email notifications
#SBATCH --mail-user=<your-email>   # Your email

# Run Progressive Temperature Parallel V4 on full MedQA dataset (1,071 questions)
# 5 parallel agents at temp=1.0, then deterministic merge and final decision
# Estimated runtime: ~40 hours

echo "Starting Progressive Temperature Parallel V4 on $(hostname) at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo ""

# Load required modules
module purge
module load python/3.11
module list

echo ""
echo "System info:"
echo "  Cores allocated: $SLURM_CPUS_ON_NODE"
echo "  Memory allocated: 64GB"
echo "  Node: $(hostname)"
echo ""

echo "Running Progressive Temperature Parallel V4 (5 parallel agents, 1,071 questions)..."
cd ~/FL_Project

python scripts/test_progressive_temperature_parallel.py \
    --n 1071 \
    --parallel 5 \
    --config configs/qwen25_32b.yaml \
    --output runs/hpc_parallel_v4

echo ""
echo "Job completed at $(date)"

# Print summary
if [ -f "runs/hpc_parallel_v4/*/results.json" ]; then
    echo "SUCCESS: Run completed"
    python -c "
import json
from pathlib import Path
results_file = list(Path('runs/hpc_parallel_v4').glob('*/results.json'))[0]
results = json.load(open(results_file))
correct = sum(1 for r in results if r.get('is_correct', r.get('correct', False)))
print(f'Accuracy: {correct}/{len(results)} = {correct/len(results)*100:.2f}%')
"
else
    echo "ERROR: Results file not found"
    exit 1
fi
