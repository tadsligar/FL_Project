#!/bin/bash
# Quick Start Script for Graph of Thoughts on RunPod
# This script helps you set up and run GoT evaluation on RunPod

set -e  # Exit on error

echo "=========================================="
echo "Graph of Thoughts - RunPod Quick Start"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if config file exists
CONFIG_FILE="configs/runpod_graph_of_thoughts.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Check if RunPod URL is configured
if grep -q "YOUR_POD_ID" "$CONFIG_FILE"; then
    echo -e "${RED}Error: You need to update your RunPod endpoint URL first!${NC}"
    echo ""
    echo "Steps:"
    echo "1. Deploy a vLLM pod on RunPod with Qwen/Qwen2.5-32B-Instruct"
    echo "2. Get your endpoint URL (e.g., https://xxxxx-8000.proxy.runpod.net)"
    echo "3. Edit $CONFIG_FILE and replace YOUR_POD_ID with your actual pod ID"
    echo ""
    echo "See docs/runpod_graph_of_thoughts_guide.md for detailed instructions"
    exit 1
fi

# Extract base URL from config
BASE_URL=$(grep "base_url:" "$CONFIG_FILE" | awk '{print $2}')
echo -e "${BLUE}RunPod Endpoint:${NC} $BASE_URL"
echo ""

# Test connection
echo -e "${YELLOW}Testing connection to RunPod...${NC}"
HEALTH_URL="${BASE_URL}/health"

if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connection successful!${NC}"
else
    echo -e "${RED}✗ Cannot connect to RunPod endpoint${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check that your pod is running (not stopped)"
    echo "2. Verify the endpoint URL in $CONFIG_FILE"
    echo "3. Try: curl $HEALTH_URL"
    exit 1
fi
echo ""

# Test model availability
echo -e "${YELLOW}Checking model availability...${NC}"
MODELS_URL="${BASE_URL}/v1/models"

if curl -s -f "$MODELS_URL" | grep -q "Qwen"; then
    echo -e "${GREEN}✓ Model loaded and ready!${NC}"
else
    echo -e "${YELLOW}⚠ Model check uncertain (but might still work)${NC}"
fi
echo ""

# Ask user what they want to run
echo -e "${BLUE}What would you like to run?${NC}"
echo ""
echo "1) Quick test (1 question) - ~1 min, ~$0.01"
echo "2) Small validation (10 questions) - ~10 min, ~$0.10"
echo "3) Pilot run (100 questions) - ~2 hours, ~$2"
echo "4) Full evaluation (1,071 questions) - ~20 hours, ~$20"
echo "5) Resume interrupted run"
echo "6) Exit"
echo ""

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        N=1
        OUTPUT="runs/graph_of_thoughts_runpod_test_$(date +%Y%m%d_%H%M%S)"
        ;;
    2)
        N=10
        OUTPUT="runs/graph_of_thoughts_runpod_n10_$(date +%Y%m%d_%H%M%S)"
        ;;
    3)
        N=100
        OUTPUT="runs/graph_of_thoughts_runpod_n100_$(date +%Y%m%d_%H%M%S)"
        ;;
    4)
        N=1071
        OUTPUT="runs/graph_of_thoughts_runpod_full_$(date +%Y%m%d_%H%M%S)"
        echo ""
        echo -e "${YELLOW}WARNING: This will take ~20 hours and cost ~$20${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Cancelled."
            exit 0
        fi
        ;;
    5)
        read -p "Enter path to resume from (e.g., runs/graph_of_thoughts_runpod_full): " RESUME_PATH
        if [ ! -d "$RESUME_PATH" ]; then
            echo -e "${RED}Error: Directory not found: $RESUME_PATH${NC}"
            exit 1
        fi
        echo ""
        echo -e "${GREEN}Resuming from: $RESUME_PATH${NC}"
        python scripts/test_graph_of_thoughts.py \
            --n 1071 \
            --config "$CONFIG_FILE" \
            --resume "$RESUME_PATH"
        exit 0
        ;;
    6)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Confirm and run
echo ""
echo "=========================================="
echo -e "${GREEN}Ready to run Graph of Thoughts!${NC}"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Questions: $N"
echo "  Output: $OUTPUT"
echo "  Config: $CONFIG_FILE"
echo ""

# Estimate
if [ "$N" -eq 1 ]; then
    TIME="~1 minute"
    COST="~$0.01"
elif [ "$N" -eq 10 ]; then
    TIME="~10 minutes"
    COST="~$0.10"
elif [ "$N" -eq 100 ]; then
    TIME="~2 hours"
    COST="~$2"
else
    TIME="~20 hours"
    COST="~$20"
fi

echo "Estimated:"
echo "  Time: $TIME"
echo "  Cost: $COST"
echo ""

read -p "Press Enter to start, or Ctrl+C to cancel..."
echo ""

# Run the evaluation
echo -e "${BLUE}Starting Graph of Thoughts evaluation...${NC}"
echo ""

python scripts/test_graph_of_thoughts.py \
    --n "$N" \
    --config "$CONFIG_FILE" \
    --output "$OUTPUT"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ Evaluation complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Results saved to: $OUTPUT"
    echo ""

    # Show summary if available
    if [ -f "$OUTPUT/summary.json" ]; then
        echo "Summary:"
        cat "$OUTPUT/summary.json"
        echo ""
    fi

    echo "Next steps:"
    echo "1. Review results in $OUTPUT/"
    echo "2. Compare to baselines: python scripts/summarize_all_architectures.py"
    echo "3. Don't forget to STOP your RunPod pod to avoid charges!"
else
    echo ""
    echo -e "${RED}✗ Evaluation failed${NC}"
    echo ""
    echo "Check the error messages above for details."
    echo "Results up to the failure point are saved in $OUTPUT/"
fi
