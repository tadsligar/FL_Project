#!/bin/bash
#SBATCH -J test_medqa              # Job name
#SBATCH -N 1                       # Number of nodes
#SBATCH -n 8                       # Number of cores
#SBATCH -t 00:30:00                # Time limit (30 minutes)
#SBATCH -p general                 # Partition
#SBATCH --mem=16G                  # Memory
#SBATCH -o test_%j.out             # Standard output
#SBATCH -e test_%j.err             # Standard error

# Test job: Run Progressive Temperature Parallel on 1 question
# This verifies that everything is working before running full experiments

echo "Starting test job on $(hostname) at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Working directory: $(pwd)"
echo ""

# Load required modules
module purge
module load python/3.11
module list

echo ""
echo "Python version:"
python --version

echo ""
echo "Installing dependencies..."
pip install --user -q requests pyyaml tqdm

echo ""
echo "Testing Progressive Temperature Parallel (1 question)..."
cd ~/FL_Project

python scripts/test_progressive_temperature_parallel.py \
    --n 1 \
    --parallel 5 \
    --config configs/qwen25_32b.yaml \
    --output runs/hpc_test

echo ""
echo "Job completed at $(date)"

# Check if results exist
if [ -f "runs/hpc_test/*/results.json" ]; then
    echo "SUCCESS: Results file created"
    ls -lh runs/hpc_test/*/results.json
else
    echo "ERROR: No results file found"
    exit 1
fi
