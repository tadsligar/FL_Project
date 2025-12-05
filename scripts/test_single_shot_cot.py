#!/usr/bin/env python3
"""
Test Single-Shot CoT Baseline on MedQA questions.

This fills the gap between zero-shot (54%) and multi-agent debate (71-75%).
Tests if structured CoT helps WITHOUT adversarial interaction.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from src.baselines.single_shot_cot import run_single_shot_cot
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

    match = re.match(r'^([A-Za-z])[\\.\\)\\:]', answer)
    if match:
        return match.group(1).upper()

    match = re.search(r'(?:answer|choice)[\\s:is]*([A-Za-z])(?:\\s|$|\\.)', answer, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.match(r'^([A-Za-z])(?:\\s)', answer)
    if match:
        return match.group(1).upper()

    for char in answer:
        if char.isalpha():
            return char.upper()

    return answer


def test_single_shot_cot(
    n_samples: int = 100,
    config_path: str = "configs/qwen25_32b_temp01.yaml",
    dataset_path: str = None,
    output_dir: str = "runs/single_shot_cot"
):
    """
    Test single-shot CoT baseline on N questions.
    """

    console.print("\\n[bold cyan]=" * 60)
    console.print("[bold cyan]Single-Shot CoT Baseline - Test")
    console.print("[bold cyan]=" * 60 + "\\n")

    # Load configuration
    console.print("[yellow]Loading configuration...[/yellow]")
    if Path(config_path).exists():
        config = Config.from_yaml(config_path)
    else:
        console.print(f"[red]Config file not found: {config_path}[/red]")
        return

    console.print(f"  Model: {config.model}")
    console.print(f"  Provider: {config.provider}")
    console.print(f"  Temperature: {config.temperature}\\n")

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

    console.print(f"  Loaded {len(dataset)} questions\\n")

    # Create LLM client
    console.print("[yellow]Initializing LLM client...[/yellow]")
    llm_client = create_llm_client(config)
    console.print("  [OK] Client ready\\n")

    # Warm up model
    if config.provider in ["ollama", "llamacpp", "vllm"]:
        console.print("[yellow]Warming up model...[/yellow]")
        try:
            warmup_response = llm_client.complete("Hello, this is a test.")
            console.print(f"  [OK] Model loaded (took {warmup_response.latency_seconds:.1f}s)\\n")
        except Exception as e:
            console.print(f"  [yellow][!] Warmup failed: {e}[/yellow]\\n")

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / timestamp
    output_path.mkdir(exist_ok=True, parents=True)

    # Results storage
    results = []

    # Run evaluation
    console.print("\\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task(
            "[cyan]Evaluating Single-Shot CoT...",
            total=len(dataset)
        )

        for i, item in enumerate(dataset, 1):
            question = item["question"]
            options = item.get("options", [])
            correct_answer = item["answer"]

            console.print(f"\\n[bold]Question {i}/{len(dataset)}[/bold]")
            console.print(f"Correct Answer: {correct_answer}")

            try:
                start_time = time.time()

                result = run_single_shot_cot(question, options, llm_client, config)

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
        "method": "single_shot_cot",
        "n_samples": n_total,
        "n_correct": n_correct,
        "accuracy": accuracy,
        "avg_tokens": avg_tokens,
        "avg_latency": avg_latency,
        "config": {
            "model": config.model,
            "temperature": config.temperature,
            "provider": config.provider
        }
    }

    with open(output_path / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Display summary
    console.print("\\n[bold green]=" * 60)
    console.print("[bold green]Results Summary")
    console.print("[bold green]=" * 60 + "\\n")

    console.print(f"Accuracy: [bold]{n_correct}/{n_total} = {accuracy:.1%}[/bold]")
    console.print(f"Avg Latency: {avg_latency:.1f}s")
    console.print(f"Avg Tokens: {avg_tokens:.0f}")
    console.print(f"\\nResults saved to: [cyan]{output_path}[/cyan]\\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Single-Shot CoT Baseline")
    parser.add_argument("--n", type=int, default=100, help="Number of questions")
    parser.add_argument("--config", type=str, default="configs/qwen25_32b_temp01.yaml", help="Config file")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset path")
    parser.add_argument("--output", type=str, default="runs/single_shot_cot", help="Output directory")

    args = parser.parse_args()

    test_single_shot_cot(
        n_samples=args.n,
        config_path=args.config,
        dataset_path=args.dataset,
        output_dir=args.output
    )
