#!/bin/bash
#SBATCH --job-name=got_full
#SBATCH --output=/scratch/tzs0128/logs/got_full_%j.out
#SBATCH --error=/scratch/tzs0128/logs/got_full_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tzs0128@auburn.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=48:00:00
#SBATCH --partition=general

# Graph of Thoughts Full Evaluation
# 1,071 questions × 15 LLM calls = ~16,000 calls
# Estimated: 30-40 hours

echo "=================================================="
echo "Graph of Thoughts - Full Dataset Evaluation"
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

# Create output directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/scratch/tzs0128/FL_Project_runs/graph_of_thoughts_${TIMESTAMP}"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Run full evaluation
echo "Running Graph of Thoughts on full dataset (1071 questions)..."
echo "Expected runtime: 30-40 hours"
echo "LLM calls per question: ~15"
echo ""

python scripts/test_graph_of_thoughts.py \
    --n 1071 \
    --config configs/qwen25_32b.yaml \
    --output "$OUTPUT_DIR"

EXIT_CODE=$?

echo ""
echo "=================================================="
echo "Job completed: $(date)"
echo "Exit code: $EXIT_CODE"
echo "Results saved to: $OUTPUT_DIR"
echo "=================================================="

# Print final summary if it exists
if [ -f "$OUTPUT_DIR/summary.json" ]; then
    echo ""
    echo "Final Results:"
    cat "$OUTPUT_DIR/summary.json"
fi

exit $EXIT_CODE
