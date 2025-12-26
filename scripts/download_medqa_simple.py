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

    # Find where the data actually extracted to
    print("\nSearching for extracted files...")
    possible_paths = [
        "data_clean/questions/US",
        "MedQA/data_clean/questions/US",
        "questions/US",
        "US",
    ]

    base_path = None
    for p in possible_paths:
        path = Path(p)
        if path.exists():
            print(f"Found data at: {p}")
            base_path = path
            break

    if not base_path:
        # List what we actually have
        print("\nExtracted contents:")
        for item in Path(".").iterdir():
            if item.is_dir():
                print(f"  {item}/")
                # Check one level deep
                for subitem in item.iterdir():
                    print(f"    {subitem.name}")
                    if subitem.name == "questions":
                        base_path = subitem / "US"
                        print(f"Found data at: {base_path}")
                        break
                if base_path:
                    break

    if not base_path:
        print("\n✗ Could not find MedQA data files in extracted archive")
        return

    # List what's actually in the base path
    print(f"\nContents of {base_path}:")
    for item in sorted(base_path.rglob("*")):
        if item.is_file() and item.suffix in [".jsonl", ".json"]:
            rel_path = item.relative_to(base_path)
            print(f"  {rel_path}")

    # Process each split - files are directly in US/ directory
    configs = [
        ("test", "test_4opt"),
        ("dev", "dev_4opt"),
        ("train", "train_4opt"),
    ]

    for split, output_name in configs:
        input_file = base_path / f"{split}.jsonl"

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
    cleanup_paths = ["data_clean", "MedQA", "questions", "medqa_data.tar.gz"]
    for path_str in cleanup_paths:
        path = Path(path_str)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"Removed {path_str}")

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
