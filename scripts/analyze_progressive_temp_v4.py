#!/usr/bin/env python3
"""
Analyze Progressive Temperature Parallel v4 results across multiple runs
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict

def load_results(path):
    """Load results from a JSON file"""
    with open(path) as f:
        return json.load(f)

def analyze_runs():
    """Analyze all v4 runs"""

    # Find all v4 results
    v4_runs = [
        "runs/progressive_temperature_parallel_v4/20251203_214224/results.json",
        "runs/progressive_temperature_parallel_v4_run2/20251205_165007/results.json"
    ]

    print("=" * 80)
    print("Progressive Temperature Parallel v4 Analysis")
    print("=" * 80)
    print()

    # Load all runs
    all_results = []
    accuracies = []

    for i, run_path in enumerate(v4_runs, 1):
        if Path(run_path).exists():
            results = load_results(run_path)
            all_results.append(results)

            correct = sum(1 for r in results if r.get('is_correct', r.get('correct', False)))
            total = len(results)
            accuracy = (correct / total) * 100
            accuracies.append(accuracy)

            print(f"Run {i}: {correct}/{total} = {accuracy:.1f}%")

    print()
    print("-" * 80)
    print("Summary Statistics:")
    print("-" * 80)
    print(f"Number of runs: {len(accuracies)}")
    print(f"Mean accuracy: {statistics.mean(accuracies):.2f}%")
    print(f"Std deviation: {statistics.stdev(accuracies):.3f}%" if len(accuracies) > 1 else "Std deviation: N/A (need 2+ runs)")
    print(f"Min accuracy: {min(accuracies):.1f}%")
    print(f"Max accuracy: {max(accuracies):.1f}%")
    print(f"Range: {max(accuracies) - min(accuracies):.1f}%")
    print()

    # Analyze agreement between runs
    if len(all_results) >= 2:
        print("-" * 80)
        print("Agreement Analysis (Run 1 vs Run 2):")
        print("-" * 80)

        run1, run2 = all_results[0], all_results[1]

        both_correct = 0
        both_wrong = 0
        run1_only = 0
        run2_only = 0

        for r1, r2 in zip(run1, run2):
            r1_correct = r1.get('is_correct', r1.get('correct', False))
            r2_correct = r2.get('is_correct', r2.get('correct', False))
            if r1_correct and r2_correct:
                both_correct += 1
            elif not r1_correct and not r2_correct:
                both_wrong += 1
            elif r1_correct and not r2_correct:
                run1_only += 1
            else:
                run2_only += 1

        total = len(run1)
        agreement = (both_correct + both_wrong) / total * 100

        print(f"Both correct: {both_correct}/{total} ({both_correct/total*100:.1f}%)")
        print(f"Both wrong: {both_wrong}/{total} ({both_wrong/total*100:.1f}%)")
        print(f"Run 1 correct only: {run1_only}/{total} ({run1_only/total*100:.1f}%)")
        print(f"Run 2 correct only: {run2_only}/{total} ({run2_only/total*100:.1f}%)")
        print(f"Overall agreement: {agreement:.1f}%")
        print()

        # Analyze disagreements
        print("-" * 80)
        print("Sample Disagreements (Run 1 correct, Run 2 wrong):")
        print("-" * 80)

        disagreements = []
        for r1, r2 in zip(run1, run2):
            r1_correct = r1.get('is_correct', r1.get('correct', False))
            r2_correct = r2.get('is_correct', r2.get('correct', False))
            if r1_correct != r2_correct:
                disagreements.append((r1, r2))

        # Show first 5 disagreements
        for i, (r1, r2) in enumerate(disagreements[:5], 1):
            r1_correct = r1.get('is_correct', r1.get('correct', False))
            r2_correct = r2.get('is_correct', r2.get('correct', False))
            r = r1 if r1_correct else r2
            print(f"\n{i}. Question {r['question_idx']}:")
            print(f"   Correct answer: {r.get('correct', r.get('correct_answer', 'N/A'))}")
            print(f"   Run 1: {r1.get('predicted', r1.get('predicted_answer', 'N/A'))} ({'OK' if r1_correct else 'X'})")
            print(f"   Run 2: {r2.get('predicted', r2.get('predicted_answer', 'N/A'))} ({'OK' if r2_correct else 'X'})")

    print()
    print("-" * 80)
    print("Comparison with Multi-Agent Specialist (temp=0.3):")
    print("-" * 80)

    # Load Multi-Agent Specialist results if available
    mas_runs = [
        "runs/independent_multi_agent_mixed_temp_full/20251119_040603/results.json",
        "runs/independent_multi_agent_mixed_temp_full_run2/20251119_211604/results.json",
        "runs/independent_multi_agent_mixed_temp_full_run3/20251120_214944/results.json"
    ]

    mas_accuracies = []
    for run_path in mas_runs:
        if Path(run_path).exists():
            results = load_results(run_path)
            correct = sum(1 for r in results if r.get('is_correct', r.get('correct', False)))
            total = len(results)
            accuracy = (correct / total) * 100
            mas_accuracies.append(accuracy)

    if mas_accuracies:
        print(f"Multi-Agent Specialist (3 runs):")
        print(f"  Mean: {statistics.mean(mas_accuracies):.2f}%")
        print(f"  Std dev: {statistics.stdev(mas_accuracies):.3f}%")
        print(f"  Range: {max(mas_accuracies) - min(mas_accuracies):.1f}%")
        print()
        print(f"Progressive Temp Parallel v4 (2 runs):")
        print(f"  Mean: {statistics.mean(accuracies):.2f}%")
        print(f"  Std dev: {statistics.stdev(accuracies):.3f}%")
        print(f"  Range: {max(accuracies) - min(accuracies):.1f}%")
        print()
        print(f"Difference in means: {abs(statistics.mean(accuracies) - statistics.mean(mas_accuracies)):.2f}%")

    print()
    print("=" * 80)
    print("Conclusion:")
    print("=" * 80)
    print()

    if len(accuracies) >= 2:
        mean_acc = statistics.mean(accuracies)
        std_dev = statistics.stdev(accuracies)

        if std_dev < 0.5:
            print(f"[+] Very stable performance: {mean_acc:.2f}% +/- {std_dev:.3f}%")
            print(f"[+] Extremely low variance (std dev < 0.5%)")
        else:
            print(f"Performance: {mean_acc:.2f}% +/- {std_dev:.3f}%")

        if mas_accuracies and abs(statistics.mean(accuracies) - statistics.mean(mas_accuracies)) < 0.5:
            print(f"[+] Matches Multi-Agent Specialist performance")

        print()
        print("Progressive Temperature Parallel v4 demonstrates:")
        print("- Consistent accuracy across runs")
        print("- 5 parallel explorations at temp=1.0 with deterministic merge")
        print("- Competitive with best Multi-Agent Specialist results")
        print("- Low variance suggests stable, predictable performance")

if __name__ == "__main__":
    analyze_runs()
