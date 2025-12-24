#!/bin/bash
#SBATCH -J medqa_prog_temp         # Job name
#SBATCH -N 1                       # Number of nodes
#SBATCH -n 16                      # Number of cores
#SBATCH -t 48:00:00                # Time limit (48 hours)
#SBATCH -p general                 # Partition
#SBATCH --mem=32G                  # Memory
#SBATCH -o progtemp_%j.out         # Standard output
#SBATCH -e progtemp_%j.err         # Standard error
#SBATCH --mail-type=END,FAIL       # Email notifications
#SBATCH --mail-user=<your-email>   # Your email

# Run Progressive Temperature baseline on full MedQA dataset (1,071 questions)
# Estimated runtime: ~20 hours

echo "Starting Progressive Temperature baseline on $(hostname) at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo ""

# Load required modules
module purge
module load python/3.11
module list

echo ""
echo "Running Progressive Temperature on 1,071 questions..."
cd ~/FL_Project

python scripts/test_progressive_temperature.py \
    --n 1071 \
    --config configs/qwen25_32b.yaml \
    --output runs/hpc_progressive_temp_full

echo ""
echo "Job completed at $(date)"

# Print summary
if [ -f "runs/hpc_progressive_temp_full/*/results.json" ]; then
    echo "SUCCESS: Run completed"
    python -c "
import json
from pathlib import Path
results_file = list(Path('runs/hpc_progressive_temp_full').glob('*/results.json'))[0]
results = json.load(open(results_file))
correct = sum(1 for r in results if r.get('is_correct', r.get('correct', False)))
print(f'Accuracy: {correct}/{len(results)} = {correct/len(results)*100:.2f}%')
"
fi
