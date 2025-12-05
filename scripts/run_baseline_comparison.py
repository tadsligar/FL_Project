#!/usr/bin/env python3
"""
Baseline Comparison Evaluation Script

Compares your adaptive MAS system against three baselines:
1. Single-LLM Chain-of-Thought
2. Fixed Four-Agent Pipeline
3. Debate-Style Dual-Agent

For COMP 5970/6970 Course Project
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from src.baselines import run_single_llm_cot, run_fixed_pipeline, run_debate
from src.baselines.sequential_specialist_debate import run_sequential_specialist_debate
from src.config import Config, get_config
from src.llm_client import create_llm_client
from src.medqa import load_medqa_subset
from src.orchestration import run_case

console = Console()


def normalize_answer(answer: str) -> str:
    """
    Normalize an answer to just the letter choice.

    Handles formats like:
    - "A"
    - "A. Some diagnosis"
    - "A) Some diagnosis"
    - "Answer: A"
    - "The answer is A"

    Returns just the uppercase letter (A, B, C, D, etc.)
    """
    if not answer:
        return ""

    # Strip whitespace
    answer = answer.strip()

    # If already just a single letter, return it
    if len(answer) == 1 and answer.isalpha():
        return answer.upper()

    # Try to extract letter from patterns like "A. Text" or "A) Text"
    match = re.match(r'^([A-Za-z])[\.\)\:]', answer)
    if match:
        return match.group(1).upper()

    # Try to extract from "Answer: A" or "The answer is A"
    match = re.search(r'(?:answer|choice)[\s:is]*([A-Za-z])(?:\s|$|\.)', answer, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # If answer starts with a letter followed by space, use that
    match = re.match(r'^([A-Za-z])(?:\s)', answer)
    if match:
        return match.group(1).upper()

    # Last resort: just take the first letter
    for char in answer:
        if char.isalpha():
            return char.upper()

    return answer


def run_comparison(
    n_samples: int = 100,
    config_path: str = "configs/llama3_70b.yaml",
    dataset_path: str = None,
    output_dir: str = "runs/baseline_comparison"
):
    """
    Run comprehensive baseline comparison.

    Args:
        n_samples: Number of MedQA questions to evaluate
        config_path: Path to config file
        dataset_path: Path to MedQA dataset (optional)
        output_dir: Where to save results
    """

    console.print("\n[bold cyan]=" * 60)
    console.print("[bold cyan]Baseline Comparison Evaluation")
    console.print("[bold cyan]=" * 60 + "\n")

    # Load configuration
    console.print("[yellow]Loading configuration...[/yellow]")
    if Path(config_path).exists():
        config = Config.from_yaml(config_path)
    else:
        config = get_config()

    console.print(f"  Model: {config.model}")
    console.print(f"  Provider: {config.provider}")
    console.print(f"  Temperature: {config.temperature}\n")

    # Load dataset
    console.print(f"[yellow]Loading MedQA dataset ({n_samples} questions)...[/yellow]")
    if dataset_path:
        dataset = load_medqa_subset(path=dataset_path, n=n_samples)
    else:
        # Try to find downloaded dataset (check multiple possible filenames)
        possible_paths = [
            Path("data/medqa_us_test_4opt.json"),  # Converted from manual download
            Path("data/medqa_usmle_test_4opt.json"),
            Path("data/medqa_usmle_4_options.json"),
            Path("data/medqa_usmle_4_options.jsonl"),
            Path("data/medqa_usmle_test.json"),
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
            console.print("  [yellow]Using mock dataset (download real dataset with scripts/download_medqa.py)[/yellow]")
            dataset = load_medqa_subset(n=n_samples)

    console.print(f"  Loaded {len(dataset)} questions\n")

    # Create LLM client
    console.print("[yellow]Initializing LLM client...[/yellow]")
    llm_client = create_llm_client(config)
    console.print("  [OK] Client ready\n")

    # Warm up the model (especially important for large models like 70B)
    if config.provider in ["ollama", "llamacpp", "vllm"]:
        console.print("[yellow]Warming up model (first call loads model into memory)...[/yellow]")
        try:
            warmup_response = llm_client.complete("Hello, this is a test.")
            console.print(f"  [OK] Model loaded and ready (took {warmup_response.latency_seconds:.1f}s)\n")
        except Exception as e:
            console.print(f"  [yellow][!] Warmup failed: {e}[/yellow]")
            console.print(f"  [yellow]  Continuing anyway - first real call may be slow[/yellow]\n")

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / timestamp
    output_path.mkdir(exist_ok=True, parents=True)

    # Results storage
    results = {
        "adaptive_mas": [],
        "single_cot": [],
        "fixed_pipeline": [],
        "debate": [],
        "sequential_debate": []
    }

    # Methods to evaluate
    methods = [
        ("adaptive_mas", "Adaptive MAS (Your System)", run_case_wrapper),
        ("single_cot", "Single-LLM CoT", run_single_llm_cot),
        ("fixed_pipeline", "Fixed Pipeline (4 agents)", run_fixed_pipeline),
        ("debate", "Debate (2 agents, 3 rounds)", lambda q, o, c, cfg: run_debate(q, o, c, cfg, rounds=3)),
        ("sequential_debate", "Sequential Specialist Debate", run_sequential_specialist_debate)
    ]

    # Run evaluation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        overall_task = progress.add_task(
            "[cyan]Overall Progress",
            total=len(dataset) * len(methods)
        )

        for i, item in enumerate(dataset, 1):
            question = item["question"]
            options = item["options"]
            correct_answer = item["answer"]

            console.print(f"\n[bold]Question {i}/{len(dataset)}[/bold]")
            console.print(f"Correct Answer: {correct_answer}")

            for method_key, method_name, method_func in methods:
                progress.update(
                    overall_task,
                    description=f"[cyan]{method_name} - Q{i}/{len(dataset)}"
                )

                try:
                    start_time = time.time()

                    if method_key == "adaptive_mas":
                        # Run your adaptive MAS system
                        result = method_func(
                            question, options, correct_answer, config, llm_client
                        )
                        answer = result["answer"]
                        tokens = result.get("tokens", 0)
                        latency = result.get("latency", 0)
                        agents_used = result.get("agents_used", 7)
                    else:
                        # Run baseline method
                        result = method_func(question, options, llm_client, config)
                        answer = result["answer"]
                        tokens = result.get("tokens_used", 0)
                        latency = result.get("latency_seconds", 0)
                        agents_used = result.get("agents_used", result.get("debate_rounds", 1))

                    # Normalize both answers for comparison
                    normalized_answer = normalize_answer(answer)
                    normalized_correct = normalize_answer(correct_answer)
                    is_correct = normalized_answer == normalized_correct

                    results[method_key].append({
                        "question_idx": i,
                        "question": question[:100] + "..." if len(question) > 100 else question,
                        "predicted": answer,
                        "correct": correct_answer,
                        "is_correct": is_correct,
                        "tokens": tokens,
                        "latency": latency,
                        "agents_used": agents_used,
                        "full_result": result
                    })

                    status = "[OK]" if is_correct else "[X]"
                    console.print(f"  {status} {method_name}: {answer} ({latency:.1f}s)")

                except Exception as e:
                    console.print(f"  [red][X] {method_name}: Error - {e}[/red]")
                    results[method_key].append({
                        "question_idx": i,
                        "error": str(e)
                    })

                progress.advance(overall_task)

            # Save intermediate results every 10 questions
            if i % 10 == 0:
                _save_results(results, output_path)

    # Final save
    _save_results(results, output_path)

    # Compute and display summary
    _display_summary(results, output_path)

    console.print(f"\n[bold green]Results saved to: {output_path}[/bold green]\n")


def run_case_wrapper(question, options, correct_answer, config, llm_client):
    """Wrapper for adaptive MAS to match baseline interface."""
    final_decision, trace = run_case(
        question=question,
        options=options,
        correct_answer=correct_answer,
        config=config,
        llm_client=llm_client
    )

    return {
        "answer": final_decision.final_answer,
        "tokens": trace.total_tokens,
        "latency": trace.total_latency_seconds,
        "agents_used": 1 + len(trace.specialist_traces) + 1,  # planner + specialists + aggregator
        "trace": trace
    }


def _save_results(results: dict, output_path: Path):
    """Save results to JSON files."""
    # Full results
    with open(output_path / "full_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Summary stats
    summary = {}
    for method, data in results.items():
        valid_results = [r for r in data if "error" not in r]
        if not valid_results:
            continue

        n_correct = sum(1 for r in valid_results if r.get("is_correct"))
        n_total = len(valid_results)

        summary[method] = {
            "n_samples": n_total,
            "n_correct": n_correct,
            "accuracy": n_correct / n_total if n_total > 0 else 0,
            "avg_latency": sum(r.get("latency", 0) for r in valid_results) / n_total if n_total > 0 else 0,
            "avg_tokens": sum(r.get("tokens", 0) for r in valid_results if r.get("tokens")) / n_total if n_total > 0 else 0,
            "avg_agents": sum(r.get("agents_used", 0) for r in valid_results) / n_total if n_total > 0 else 0,
        }

    with open(output_path / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)


def _display_summary(results: dict, output_path: Path):
    """Display summary table."""
    console.print("\n[bold cyan]=" * 60)
    console.print("[bold cyan]RESULTS SUMMARY")
    console.print("[bold cyan]=" * 60 + "\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Method", style="cyan", width=25)
    table.add_column("Accuracy", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("Avg Tokens", justify="right")
    table.add_column("Avg Agents", justify="right")

    for method, data in results.items():
        valid_results = [r for r in data if "error" not in r]
        if not valid_results:
            continue

        n_correct = sum(1 for r in valid_results if r.get("is_correct"))
        n_total = len(valid_results)
        accuracy = n_correct / n_total if n_total > 0 else 0

        avg_latency = sum(r.get("latency", 0) for r in valid_results) / n_total if n_total > 0 else 0
        avg_tokens = sum(r.get("tokens", 0) for r in valid_results if r.get("tokens")) / n_total if n_total > 0 else 0
        avg_agents = sum(r.get("agents_used", 0) for r in valid_results) / n_total if n_total > 0 else 0

        method_names = {
            "adaptive_mas": "Adaptive MAS (Yours)",
            "single_cot": "Single-LLM CoT",
            "fixed_pipeline": "Fixed Pipeline",
            "debate": "Debate"
        }

        table.add_row(
            method_names.get(method, method),
            f"{accuracy:.1%} ({n_correct}/{n_total})",
            f"{avg_latency:.1f}s",
            f"{avg_tokens:.0f}" if avg_tokens > 0 else "N/A",
            f"{avg_agents:.1f}"
        )

    console.print(table)
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="Run baseline comparison for MAS evaluation"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of questions to evaluate (default: 10)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/llama3_70b.yaml",
        help="Path to config file"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to MedQA dataset JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="runs/baseline_comparison",
        help="Output directory for results"
    )

    args = parser.parse_args()

    run_comparison(
        n_samples=args.n,
        config_path=args.config,
        dataset_path=args.dataset,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
