#!/bin/bash
# Check Graph of Thoughts results across multiple runs

echo "============================================================"
echo "Graph of Thoughts Results Summary"
echo "============================================================"
echo ""

cd "$(dirname "$0")/.."

RESULTS_DIR="runs/graph_of_thoughts"

if [ ! -d "$RESULTS_DIR" ]; then
    echo "No results directory found at $RESULTS_DIR"
    exit 1
fi

echo "Checking all run directories..."
echo ""

for dir in "$RESULTS_DIR"/*/; do
    if [ -d "$dir" ]; then
        dir_name=$(basename "$dir")
        dir_size=$(du -sh "$dir" 2>/dev/null | cut -f1)

        echo "=== Run: $dir_name ==="
        echo "Size: $dir_size"

        # Check for results.json
        if [ -f "$dir/results.json" ]; then
            # Count questions using Python
            count=$(python3 -c "
import json
try:
    with open('$dir/results.json', 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        print(len(data))
    elif isinstance(data, dict) and 'results' in data:
        print(len(data['results']))
    else:
        print('Unknown format')
except Exception as e:
    print(f'Error: {e}')
" 2>&1)

            echo "Questions completed: $count"

            # Show accuracy if available
            python3 -c "
import json
try:
    with open('$dir/results.json', 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        results = data
    elif isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        exit(0)

    correct = sum(1 for r in results if r.get('correct', False))
    total = len(results)
    if total > 0:
        accuracy = (correct / total) * 100
        print(f'Accuracy: {correct}/{total} = {accuracy:.1f}%')
except:
    pass
" 2>/dev/null
        else
            echo "No results.json found (run incomplete or failed)"
        fi

        # List other files
        echo "Files:"
        ls -lh "$dir/" 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'

        echo ""
    fi
done

echo "============================================================"
echo "Summary Complete"
echo "============================================================"
