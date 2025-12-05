#!/bin/bash
# Evaluation script for MedQA dataset

set -e

echo "========================================="
echo "Clinical MAS Planner - MedQA Evaluation"
echo "========================================="
echo ""

# Default values
N_SAMPLES=100
CONFIG="configs/eval_medqa.yaml"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--samples)
            N_SAMPLES="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-n|--samples N] [-c|--config CONFIG]"
            exit 1
            ;;
    esac
done

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and add your API keys."
    exit 1
fi

# Check if config exists
if [ ! -f "$CONFIG" ]; then
    echo "Warning: Config file $CONFIG not found, using defaults"
fi

echo "Configuration:"
echo "  Samples: $N_SAMPLES"
echo "  Config:  $CONFIG"
echo ""

# Run evaluation
echo "Starting evaluation..."
poetry run mas eval --config "$CONFIG" --n "$N_SAMPLES"

echo ""
echo "========================================="
echo "Evaluation complete!"
echo "========================================="
