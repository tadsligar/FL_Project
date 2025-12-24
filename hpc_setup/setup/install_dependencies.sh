#!/bin/bash
# Install Python dependencies on Easley HPC cluster
# Run this after connecting and transferring code

echo "Installing Python dependencies for FL_Project..."
echo ""

# Load Python module
module load python/3.11

echo "Python version:"
python --version
echo ""

echo "Installing packages..."
pip install --user requests pyyaml tqdm

echo ""
echo "Installed packages:"
pip list --user | grep -E "(requests|pyyaml|tqdm)"

echo ""
echo "Installation complete!"
echo ""
echo "Note: Ollama will need to be configured separately."
echo "Check if Ollama is available as a module:"
echo "  module avail ollama"
echo ""
echo "Or you may need to use a different LLM provider on the cluster."
