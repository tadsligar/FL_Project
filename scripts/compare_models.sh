#!/bin/bash
# Compare models on the same test case to help you choose

set -e

echo "=================================================="
echo "Model Comparison Tool"
echo "=================================================="
echo ""

# Test question
QUESTION="A 65-year-old man presents with sudden onset chest pain radiating to the left arm, diaphoresis, and nausea. Pain started 30 minutes ago. Which of the following is the most likely diagnosis?"
OPTIONS="A. Gastroesophageal reflux disease||B. Acute myocardial infarction||C. Pulmonary embolism||D. Musculoskeletal pain"

echo "Test Question:"
echo "$QUESTION"
echo ""
echo "Options: $OPTIONS"
echo ""
echo "Correct Answer: B (Acute MI)"
echo ""
echo "=================================================="
echo ""

# Function to test a model
test_model() {
    local MODEL=$1
    local CONFIG=$2
    local NAME=$3

    echo "Testing: $NAME"
    echo "Model: $MODEL"
    echo ""

    # Check if model is pulled
    if ! ollama list | grep -q "$MODEL"; then
        echo "Model not found. Pulling $MODEL..."
        echo "This may take a while..."
        ollama pull "$MODEL"
    fi

    echo "Running inference..."
    START_TIME=$(date +%s)

    poetry run mas run \
        --config "$CONFIG" \
        --question "$QUESTION" \
        --options "$OPTIONS" \
        > /tmp/mas_output_$MODEL.txt 2>&1

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo "✓ Complete in ${DURATION}s"
    echo ""

    # Extract answer
    ANSWER=$(grep "Final Answer:" /tmp/mas_output_$MODEL.txt | head -1 || echo "Not found")
    echo "Result: $ANSWER"
    echo ""
    echo "--------------------------------------------------"
    echo ""
}

# Check system RAM
echo "System Information:"
echo ""

if command -v free &> /dev/null; then
    RAM=$(free -h | grep Mem | awk '{print $2}')
    echo "System RAM: $RAM"
elif command -v vm_stat &> /dev/null; then
    # macOS
    RAM=$(sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}')
    echo "System RAM: $RAM"
fi

if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "GPU Info:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

echo ""
echo "=================================================="
echo ""

# Ask which models to test
echo "Which models would you like to compare?"
echo ""
echo "1. Llama3:8B only (fast, ~30s per case)"
echo "2. Mixtral:8x7B only (balanced, ~2-4 min per case)"
echo "3. Llama3:70B only (best quality, ~5-10 min per case)"
echo "4. Llama3:8B vs Mixtral:8x7B (recommended comparison)"
echo "5. All three models (takes ~15-20 min total)"
echo ""

read -p "Select option (1-5): " CHOICE

echo ""
echo "=================================================="
echo "Starting Comparison"
echo "=================================================="
echo ""

case $CHOICE in
    1)
        test_model "llama3:8b" "configs/local_ollama.yaml" "Llama3:8B"
        ;;
    2)
        test_model "mixtral:8x7b" "configs/mixtral_8x7b.yaml" "Mixtral:8x7B"
        ;;
    3)
        test_model "llama3:70b" "configs/llama3_70b.yaml" "Llama3:70B"
        ;;
    4)
        test_model "llama3:8b" "configs/local_ollama.yaml" "Llama3:8B"
        test_model "mixtral:8x7b" "configs/mixtral_8x7b.yaml" "Mixtral:8x7B"
        ;;
    5)
        test_model "llama3:8b" "configs/local_ollama.yaml" "Llama3:8B"
        test_model "mixtral:8x7b" "configs/mixtral_8x7b.yaml" "Mixtral:8x7B"
        test_model "llama3:70b" "configs/llama3_70b.yaml" "Llama3:70B"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "Comparison Complete!"
echo "=================================================="
echo ""
echo "Full outputs saved to /tmp/mas_output_*.txt"
echo ""
echo "Review the results and choose your model:"
echo ""
echo "  • Llama3:8B    - Fastest, good for development"
echo "  • Mixtral:8x7B - Balanced speed/quality (RECOMMENDED for RTX 4090)"
echo "  • Llama3:70B   - Best quality, slower (needs 32GB+ RAM)"
echo ""
echo "For your 1-month project, I recommend:"
echo "  • Week 1-3: Use Mixtral:8x7B for fast iteration"
echo "  • Week 4:   Run Llama3:70B for final results"
echo ""
