#!/usr/bin/env python3
"""
Convert MedQA 5-option format to 4-option format.
Takes the first 4 options (A, B, C, D) and only keeps questions where the answer is in A-D.
"""

import json
from pathlib import Path

input_file = Path("data/questions/US/test.jsonl")
output_file = Path("data/medqa_us_test_4opt.json")

converted = []
skipped = 0

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue

        item = json.loads(line)

        # Only keep if answer is in A, B, C, or D (skip E)
        answer_idx = item.get('answer_idx', '')
        if answer_idx not in ['A', 'B', 'C', 'D']:
            skipped += 1
            continue

        # Get options dict
        options_dict = item.get('options', {})

        # Create 4-option list (A, B, C, D only)
        options_list = []
        for letter in ['A', 'B', 'C', 'D']:
            if letter in options_dict:
                options_list.append(f"{letter}. {options_dict[letter]}")

        # Only include if we have all 4 options
        if len(options_list) != 4:
            skipped += 1
            continue

        converted_item = {
            "question": item.get('question', ''),
            "options": options_list,
            "answer": answer_idx
        }

        converted.append(converted_item)

# Save as JSON array
output_file.parent.mkdir(exist_ok=True, parents=True)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(converted, f, indent=2, ensure_ascii=False)

print(f"Converted {len(converted)} questions to 4-option format")
print(f"Skipped {skipped} questions (answer was E or missing options)")
print(f"Saved to: {output_file}")
