#!/usr/bin/env python3
"""
Simple MedQA dataset downloader using only Python built-ins.
Works on minimal environments without unzip/file commands.
"""

import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


def download_file():
    """Download using gdown."""
    print("=" * 60)
    print("MedQA Dataset Download")
    print("=" * 60)
    print()

    # Install gdown if needed
    try:
        import gdown
    except ImportError:
        print("Installing gdown...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "gdown"])
        import gdown

    print("Downloading from Google Drive (~132MB)...")
    output_file = "medqa_data.tar.gz"
    gdown.download(
        "https://drive.google.com/uc?id=1ImYUSLk9JbgHXOemfvyiDiirluZHPeQw",
        output_file,
        quiet=False
    )

    return output_file


def extract_archive(archive_path):
    """Extract archive using Python built-in libraries."""
    print("\nExtracting archive...")

    # Try as zip first
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            print("Detected ZIP format")
            zip_ref.extractall('.')
            print("✓ Extracted successfully")
            return True
    except zipfile.BadZipFile:
        pass

    # Try as tar.gz
    try:
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            print("Detected tar.gz format")
            tar_ref.extractall('.')
            print("✓ Extracted successfully")
            return True
    except (tarfile.TarError, OSError):
        pass

    # Try as plain tar
    try:
        with tarfile.open(archive_path, 'r') as tar_ref:
            print("Detected tar format")
            tar_ref.extractall('.')
            print("✓ Extracted successfully")
            return True
    except (tarfile.TarError, OSError):
        pass

    print("✗ Could not extract archive")
    return False


def convert_to_format():
    """Convert MedQA data to our format."""
    print("\nConverting to project format...")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Process each split
    configs = [
        ("test", "4_options", "test_4opt"),
        ("dev", "4_options", "dev_4opt"),
        ("train", "4_options", "train_4opt"),
    ]

    for split, opt_type, output_name in configs:
        input_file = Path(f"data_clean/questions/US/{opt_type}/{split}.jsonl")

        if not input_file.exists():
            print(f"Warning: {input_file} not found, skipping")
            continue

        questions = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
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
                except json.JSONDecodeError:
                    continue

        # Save in our format
        output_file = data_dir / f"medqa_us_{output_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2)

        print(f"✓ Converted {len(questions):4d} questions -> {output_file.name}")

    # Cleanup
    print("\nCleaning up...")
    import shutil
    if Path("data_clean").exists():
        shutil.rmtree("data_clean")
    if Path("medqa_data.tar.gz").exists():
        Path("medqa_data.tar.gz").unlink()

    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)
    print("\nAvailable datasets:")
    for f in sorted(data_dir.glob("medqa_us_*.json")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name} ({size_kb:.1f} KB)")


def main():
    # Download
    archive_file = download_file()

    # Extract
    if not extract_archive(archive_file):
        print("Error: Could not extract archive")
        sys.exit(1)

    # Convert
    convert_to_format()


if __name__ == "__main__":
    main()
