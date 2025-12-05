#!/usr/bin/env python3
"""
Download the MedQA-USMLE dataset.

The MedQA dataset is available at: https://github.com/jind11/MedQA
This script downloads and converts it to our expected format.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm


MEDQA_URLS = {
    "train_4opt": "https://raw.githubusercontent.com/jind11/MedQA/master/data_clean/questions/US/4_options/train.jsonl",
    "dev_4opt": "https://raw.githubusercontent.com/jind11/MedQA/master/data_clean/questions/US/4_options/dev.jsonl",
    "test_4opt": "https://raw.githubusercontent.com/jind11/MedQA/master/data_clean/questions/US/4_options/test.jsonl",
    "train_5opt": "https://raw.githubusercontent.com/jind11/MedQA/master/data_clean/questions/US/5_options/train.jsonl",
    "dev_5opt": "https://raw.githubusercontent.com/jind11/MedQA/master/data_clean/questions/US/5_options/dev.jsonl",
    "test_5opt": "https://raw.githubusercontent.com/jind11/MedQA/master/data_clean/questions/US/5_options/test.jsonl",
}


def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress bar."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f, tqdm(
            desc=output_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def convert_medqa_format(input_path: Path, output_path: Path) -> int:
    """
    Convert MedQA JSONL to our expected format.

    MedQA format:
    {"question": "...", "answer": "A", "options": {"A": "...", "B": "...", ...}, ...}

    Our format:
    {"question": "...", "answer": "A", "options": ["A. ...", "B. ...", ...]}
    """
    converted_items = []

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            try:
                item = json.loads(line)

                # Extract options in order
                options_dict = item.get("options", {})
                answer_letter = item.get("answer", "")

                # Convert to list format
                options_list = [
                    f"{key}. {value}"
                    for key, value in sorted(options_dict.items())
                ]

                converted_item = {
                    "question": item.get("question", ""),
                    "options": options_list,
                    "answer": answer_letter,
                }

                converted_items.append(converted_item)

            except json.JSONDecodeError as e:
                print(f"Error parsing line: {e}")
                continue

    # Save as JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted_items, f, indent=2)

    return len(converted_items)


def main():
    parser = argparse.ArgumentParser(description="Download MedQA dataset")
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test", "all"],
        default="all",
        help="Which split to download"
    )
    parser.add_argument(
        "--options",
        choices=["4", "5", "both"],
        default="4",
        help="4-option or 5-option questions"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory"
    )

    args = parser.parse_args()

    args.output_dir.mkdir(exist_ok=True, parents=True)

    # Determine which files to download
    splits = ["train", "dev", "test"] if args.split == "all" else [args.split]
    opt_types = ["4opt", "5opt"] if args.options == "both" else [f"{args.options}opt"]

    print("=" * 60)
    print("MedQA Dataset Download")
    print("=" * 60)
    print(f"Splits: {', '.join(splits)}")
    print(f"Option types: {', '.join(opt_types)}")
    print(f"Output directory: {args.output_dir}")
    print()

    for opt_type in opt_types:
        for split in splits:
            key = f"{split}_{opt_type}"
            url = MEDQA_URLS.get(key)

            if not url:
                print(f"Warning: No URL for {key}")
                continue

            # Download JSONL
            jsonl_path = args.output_dir / f"medqa_usmle_{key}.jsonl"
            print(f"Downloading {key}...")

            if download_file(url, jsonl_path):
                # Convert to our format
                json_path = args.output_dir / f"medqa_usmle_{key}.json"
                print(f"Converting to {json_path.name}...")

                n_items = convert_medqa_format(jsonl_path, json_path)
                print(f"✓ Converted {n_items} questions")

                # Optionally remove JSONL
                # jsonl_path.unlink()
            else:
                print(f"✗ Failed to download {key}")

            print()

    print("=" * 60)
    print("Download complete!")
    print("=" * 60)
    print()
    print("Available datasets:")
    for f in sorted(args.output_dir.glob("medqa_usmle_*.json")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
