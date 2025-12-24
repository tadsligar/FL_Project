#!/bin/bash
# Initial environment setup on Easley HPC cluster
# Run this script after first login

echo "Setting up environment on Easley HPC cluster..."
echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p ~/FL_Project
mkdir -p ~/scratch/medqa_runs
mkdir -p ~/scratch/data

echo ""
echo "Checking storage quotas..."
quota

echo ""
echo "Checking available modules..."
echo "Python modules:"
module avail python

echo ""
echo "CUDA modules (for GPU):"
module avail cuda

echo ""
echo "Checking Slurm partitions..."
sinfo -s

echo ""
echo "Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Transfer your FL_Project code:"
echo "   (From your local machine)"
echo "   ./transfer_code.sh <your-auburn-id>"
echo ""
echo "2. Install Python dependencies:"
echo "   bash ~/FL_Project/hpc_setup/setup/install_dependencies.sh"
echo ""
echo "3. Submit a test job:"
echo "   cd ~/FL_Project"
echo "   sbatch hpc_setup/job_scripts/test_single_question.sh"
