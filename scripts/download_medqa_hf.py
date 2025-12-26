#!/usr/bin/env python3
"""
Download MedQA dataset from Hugging Face.
More reliable than GitHub raw URLs.
"""

import json
from pathlib import Path


def download_medqa_from_hf():
    """Download MedQA using Hugging Face datasets library."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Installing datasets library...")
        import subprocess
        subprocess.check_call(["pip", "install", "-q", "datasets"])
        from datasets import load_dataset

    print("=" * 60)
    print("Downloading MedQA from Hugging Face")
    print("=" * 60)
    print()

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Download dataset
    print("Loading MedQA dataset from Hugging Face...")
    print("(This may take a few minutes on first download)")
    print()

    try:
        # Try the GBaker/MedQA-USMLE dataset which is commonly used
        dataset = load_dataset("GBaker/MedQA-USMLE", "4_options")

        # Process each split
        for split_name in ["train", "validation", "test"]:
            if split_name not in dataset:
                print(f"Warning: {split_name} split not found")
                continue

            split_data = dataset[split_name]

            # Convert to our format
            questions = []
            for item in split_data:
                # Hugging Face format varies, adapt as needed
                question_text = item.get("question", "")
                options_dict = item.get("options", {})
                answer = item.get("answer", item.get("answer_idx", ""))

                # Convert answer index to letter if needed
                if isinstance(answer, int):
                    answer = chr(65 + answer)  # 0->A, 1->B, etc.

                # Format options as list
                if isinstance(options_dict, dict):
                    options_list = [
                        f"{key}. {value}"
                        for key, value in sorted(options_dict.items())
                    ]
                elif isinstance(options_dict, list):
                    options_list = [
                        f"{chr(65 + i)}. {opt}"
                        for i, opt in enumerate(options_dict)
                    ]
                else:
                    print(f"Warning: Unknown options format: {type(options_dict)}")
                    continue

                questions.append({
                    "question": question_text,
                    "options": options_list,
                    "answer": answer
                })

            # Map validation -> dev for consistency
            output_name = "dev" if split_name == "validation" else split_name

            # Save to file
            output_path = data_dir / f"medqa_us_{output_name}_4opt.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2)

            print(f"✓ Saved {len(questions)} questions to {output_path.name}")

        print()
        print("=" * 60)
        print("Download complete!")
        print("=" * 60)

    except Exception as e:
        print(f"Error loading from Hugging Face: {e}")
        print()
        print("Trying alternative dataset source...")

        # Try alternative: bigbio/med_qa
        try:
            dataset = load_dataset("bigbio/med_qa", "med_qa_en_4options_source")

            for split_name in dataset.keys():
                split_data = dataset[split_name]
                questions = []

                for item in split_data:
                    # bigbio format
                    question_text = item.get("question", "")
                    options = item.get("choices", [])
                    answer_idx = item.get("answer", 0)

                    # Convert to our format
                    options_list = [
                        f"{chr(65 + i)}. {opt}"
                        for i, opt in enumerate(options)
                    ]
                    answer = chr(65 + answer_idx) if isinstance(answer_idx, int) else answer_idx

                    questions.append({
                        "question": question_text,
                        "options": options_list,
                        "answer": answer
                    })

                # Save
                output_name = split_name.replace("validation", "dev")
                output_path = data_dir / f"medqa_us_{output_name}_4opt.json"

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(questions, f, indent=2)

                print(f"✓ Saved {len(questions)} questions to {output_path.name}")

            print()
            print("=" * 60)
            print("Download complete!")
            print("=" * 60)

        except Exception as e2:
            print(f"Error with alternative source: {e2}")
            print()
            print("Please manually download the dataset from:")
            print("https://huggingface.co/datasets/GBaker/MedQA-USMLE")
            print("or")
            print("https://huggingface.co/datasets/bigbio/med_qa")
            return False

    return True


if __name__ == "__main__":
    download_medqa_from_hf()
