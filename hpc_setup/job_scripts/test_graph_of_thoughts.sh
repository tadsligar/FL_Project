#!/bin/bash
#SBATCH --job-name=got_test
#SBATCH --output=/scratch/tzs0128/logs/got_test_%j.out
#SBATCH --error=/scratch/tzs0128/logs/got_test_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tzs0128@auburn.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=general

# Graph of Thoughts Test Job - Small Sample
# Tests GoT implementation on 10 questions

echo "=================================================="
echo "Graph of Thoughts - Test Run"
echo "Started: $(date)"
echo "Node: $(hostname)"
echo "=================================================="
echo ""

# Load required modules
module purge
module load python/3.11

echo "Python version:"
python --version
echo ""

# Navigate to project directory
cd ~/FL_Project

# Run test on 10 questions
echo "Running Graph of Thoughts test (10 questions)..."
python scripts/test_graph_of_thoughts.py \
    --n 10 \
    --config configs/qwen25_32b.yaml \
    --output /scratch/tzs0128/FL_Project_runs/got_test

EXIT_CODE=$?

echo ""
echo "=================================================="
echo "Job completed: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=================================================="

exit $EXIT_CODE
