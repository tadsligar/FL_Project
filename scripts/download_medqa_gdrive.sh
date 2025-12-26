#!/bin/bash
# Download MedQA dataset from Google Drive (original source)
# This is the official dataset from the MedQA paper authors

set -e

echo "============================================================"
echo "MedQA Dataset Download from Google Drive"
echo "============================================================"
echo ""

cd "$(dirname "$0")/.."  # Go to project root

# Download from Google Drive
echo "Downloading MedQA dataset archive (~500MB)..."
curl -L "https://drive.google.com/uc?export=download&id=1ImYUSLk9JbgHXOemfvyiDiirluZHPeQw" \
  -o medqa_data.tar.gz

echo ""
echo "Extracting archive..."
tar -xzf medqa_data.tar.gz

echo ""
echo "Converting to project format..."

# Convert to our format using Python
python3 << 'EOF'
import json
from pathlib import Path

# Create data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Process each split and option type
configs = [
    ("test", "4_options", "test_4opt"),
    ("dev", "4_options", "dev_4opt"),
    ("train", "4_options", "train_4opt"),
]

for split, opt_type, output_name in configs:
    input_file = f"data_clean/questions/US/{opt_type}/{split}.jsonl"

    if not Path(input_file).exists():
        print(f"Warning: {input_file} not found, skipping")
        continue

    questions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            item = json.loads(line)
            options_dict = item.get("options", {})

            # Convert options dict to sorted list
            options_list = [
                f"{k}. {v}"
                for k, v in sorted(options_dict.items())
            ]

            questions.append({
                "question": item.get("question", ""),
                "options": options_list,
                "answer": item.get("answer", "")
            })

    # Save in our format
    output_file = data_dir / f"medqa_us_{output_name}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2)

    print(f"✓ Converted {len(questions):4d} questions -> {output_file.name}")

print("\nCleaning up...")
EOF

# Clean up
rm -f medqa_data.tar.gz
rm -rf data_clean  # Remove extracted folder, keep only converted data

echo ""
echo "============================================================"
echo "Download complete!"
echo "============================================================"
echo ""
echo "Available datasets:"
ls -lh data/medqa_us_*.json 2>/dev/null || echo "  (none created - check errors above)"
echo ""
