#!/usr/bin/env python3
"""
Test Progressive Temperature with Parallel Exploration on MedQA questions.

Architecture:
- Stage 1a-e (temp=1.0 x5): 5 parallel diverse explorations
- Stage 1-merge (temp=0.5): Synthesize all explorations
- Stage 2-5: Standard progression (0.7 → 0.5 → 0.3 → 0.0)
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from src.baselines.progressive_temperature_parallel import run_progressive_temperature_parallel
from src.config import Config
from src.llm_client import create_llm_client
from src.medqa import load_medqa_subset

console = Console()


def normalize_answer(answer: str) -> str:
    """Normalize answer to single letter."""
    import re

    if not answer:
        return "UNKNOWN"

    answer = answer.strip()

    if len(answer) == 1 and answer.isalpha():
        return answer.upper()

    match = re.match(r'^([A-Za-z])[\.\)\:]', answer)
    if match:
        return match.group(1).upper()

    match = re.search(r'(?:answer|choice)[\s:is]*([A-Za-z])(?:\s|$|\.)', answer, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.match(r'^([A-Za-z])(?:\s)', answer)
    if match:
        return match.group(1).upper()

    for char in answer:
        if char.isalpha():
            return char.upper()

    return answer


def test_progressive_temperature_parallel(
    n_samples: int = 10,
    n_parallel: int = 5,
    config_path: str = "configs/qwen25_32b.yaml",
    dataset_path: str = None,
    output_dir: str = "runs/progressive_temperature_parallel",
    resume_from: str = None
):
    """
    Test Progressive Temperature with Parallel Exploration on N questions.
    """

    console.print("\n[bold cyan]=" * 60)
    console.print("[bold cyan]Progressive Temperature with Parallel Exploration - Test")
    console.print("[bold cyan]=" * 60 + "\n")

    # Load configuration
    console.print("[yellow]Loading configuration...[/yellow]")
    if Path(config_path).exists():
        config = Config.from_yaml(config_path)
    else:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        return

    console.print(f"  Model: {config.model}")
    console.print(f"  Provider: {config.provider}")
    console.print(f"  Parallel explorations: {n_parallel} at temp=1.0")
    console.print(f"  Then merge + standard progression (0.7 -> 0.5 -> 0.3 -> 0.0)\n")

    # Load dataset
    console.print(f"[yellow]Loading MedQA dataset ({n_samples} questions)...[/yellow]")
    if dataset_path:
        dataset = load_medqa_subset(path=dataset_path, n=n_samples)
    else:
        possible_paths = [
            Path("data/medqa_us_test_4opt.json"),
            Path("data/medqa_usmle_test_4opt.json"),
        ]

        found_path = None
        for test_path in possible_paths:
            if test_path.exists():
                found_path = test_path
                break

        if found_path:
            console.print(f"  Found dataset: {found_path}")
            dataset = load_medqa_subset(path=found_path, n=n_samples)
        else:
            console.print("[red]Dataset not found![/red]")
            return

    console.print(f"  Loaded {len(dataset)} questions\n")

    # Create LLM client
    console.print("[yellow]Initializing LLM client...[/yellow]")
    llm_client = create_llm_client(config)
    console.print("  [OK] Client ready\n")

    # Warm up model
    if config.provider in ["ollama", "llamacpp", "vllm"]:
        console.print("[yellow]Warming up model...[/yellow]")
        try:
            warmup_response = llm_client.complete("Hello, this is a test.")
            console.print(f"  [OK] Model loaded (took {warmup_response.latency_seconds:.1f}s)\n")
        except Exception as e:
            console.print(f"  [yellow][!] Warmup failed: {e}[/yellow]\n")

    # Create output directory (or use resume path)
    if resume_from:
        output_path = Path(resume_from)
        if not output_path.exists():
            console.print(f"[red]Resume path not found: {resume_from}[/red]")
            return
        console.print(f"[yellow]Resuming from: {output_path}[/yellow]\n")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / timestamp
        output_path.mkdir(exist_ok=True, parents=True)

    # Results storage
    results = []
    checkpoint_file = output_path / "checkpoint.json"

    # Try to load from checkpoint if it exists
    start_idx = 0
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)
                results = checkpoint_data.get("results", [])
                start_idx = len(results)
                console.print(f"[yellow]Resuming from checkpoint: {start_idx}/{len(dataset)} questions completed[/yellow]\n")
        except Exception as e:
            console.print(f"[yellow]Could not load checkpoint: {e}. Starting fresh.[/yellow]\n")

    # Run evaluation
    console.print("\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task(
            "[cyan]Evaluating Progressive Temperature (Parallel)...",
            total=len(dataset)
        )

        for i, item in enumerate(dataset, 1):
            # Skip already processed questions
            if i <= start_idx:
                progress.advance(task)
                continue

            question = item["question"]
            options = item.get("options", [])
            correct_answer = item["answer"]

            console.print(f"\n[bold]Question {i}/{len(dataset)}[/bold]")
            console.print(f"Correct Answer: {correct_answer}")

            try:
                start_time = time.time()

                result = run_progressive_temperature_parallel(
                    question, options, llm_client, config, n_parallel=n_parallel
                )

                answer = result["answer"]
                tokens = result.get("tokens_used", 0)
                latency = result.get("latency_seconds", 0)

                # Normalize answers
                normalized_answer = normalize_answer(answer)
                normalized_correct = normalize_answer(correct_answer)
                is_correct = normalized_answer == normalized_correct

                results.append({
                    "question_idx": i,
                    "question": question[:100] + "..." if len(question) > 100 else question,
                    "predicted": answer,
                    "correct": correct_answer,
                    "is_correct": is_correct,
                    "tokens": tokens,
                    "latency": latency,
                    "full_result": result
                })

                # Save checkpoint every 50 questions
                if i % 50 == 0 or i == len(dataset):
                    try:
                        with open(checkpoint_file, "w") as f:
                            json.dump({"results": results}, f, indent=2, default=str)
                        console.print(f"  [dim]Checkpoint saved ({i}/{len(dataset)})[/dim]")
                    except Exception as e:
                        console.print(f"  [yellow]Warning: Could not save checkpoint: {e}[/yellow]")

                status = "[OK]" if is_correct else "[X]"
                console.print(f"  {status} Answer: {answer} ({latency:.1f}s, {tokens} tokens)")

            except Exception as e:
                console.print(f"  [red][X] Error: {e}[/red]")
                import traceback
                console.print(f"  [red]{traceback.format_exc()}[/red]")
                results.append({
                    "question_idx": i,
                    "error": str(e)
                })

            progress.advance(task)

    # Final save
    with open(output_path / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Compute summary
    valid_results = [r for r in results if "error" not in r]
    n_correct = sum(1 for r in valid_results if r.get("is_correct"))
    n_total = len(valid_results)
    accuracy = n_correct / n_total if n_total > 0 else 0

    avg_tokens = sum(r.get("tokens", 0) for r in valid_results) / n_total if n_total > 0 else 0
    avg_latency = sum(r.get("latency", 0) for r in valid_results) / n_total if n_total > 0 else 0

    summary = {
        "method": "progressive_temperature_parallel",
        "n_parallel": n_parallel,
        "n_samples": n_total,
        "n_correct": n_correct,
        "accuracy": accuracy,
        "avg_tokens": avg_tokens,
        "avg_latency": avg_latency,
        "temperature_schedule": f"{n_parallel}x temp=1.0 -> merge(0.5) -> 0.7 -> 0.5 -> 0.3 -> 0.0",
        "config": {
            "model": config.model,
            "provider": config.provider
        }
    }

    with open(output_path / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Display summary
    console.print("\n[bold green]=" * 60)
    console.print("[bold green]Results Summary")
    console.print("[bold green]=" * 60 + "\n")

    console.print(f"Accuracy: [bold]{n_correct}/{n_total} = {accuracy:.1%}[/bold]")
    console.print(f"Parallel explorations: {n_parallel} at temp=1.0")
    console.print(f"Then: merge(0.5) -> 0.7 -> 0.5 -> 0.3 -> 0.0")
    console.print(f"Avg Latency: {avg_latency:.1f}s")
    console.print(f"Avg Tokens: {avg_tokens:.0f}")
    console.print(f"\nResults saved to: [cyan]{output_path}[/cyan]\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Progressive Temperature with Parallel Exploration")
    parser.add_argument("--n", type=int, default=10, help="Number of questions")
    parser.add_argument("--parallel", type=int, default=5, help="Number of parallel explorations at temp=1.0")
    parser.add_argument("--config", type=str, default="configs/qwen25_32b.yaml", help="Config file")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset path")
    parser.add_argument("--output", type=str, default="runs/progressive_temperature_parallel", help="Output directory")
    parser.add_argument("--resume", type=str, default=None, help="Resume from existing run directory (full path)")

    args = parser.parse_args()

    test_progressive_temperature_parallel(
        n_samples=args.n,
        n_parallel=args.parallel,
        config_path=args.config,
        dataset_path=args.dataset,
        output_dir=args.output,
        resume_from=args.resume
    )
