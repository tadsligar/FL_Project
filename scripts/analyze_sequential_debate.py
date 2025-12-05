#!/usr/bin/env python3
"""
Analyze Sequential Specialist Debate results to understand failure patterns.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

def analyze_results(results_path: str):
    """Analyze the detailed results."""

    with open(results_path, 'r') as f:
        results = json.load(f)

    # Separate correct and incorrect
    correct = [r for r in results if r.get('is_correct')]
    incorrect = [r for r in results if not r.get('is_correct') and 'error' not in r]

    print("=" * 80)
    print("SEQUENTIAL SPECIALIST DEBATE - DETAILED ANALYSIS")
    print("=" * 80)
    print()

    # Overall stats
    print(f"Total Questions: {len(results)}")
    print(f"Correct: {len(correct)} ({len(correct)/len(results)*100:.1f}%)")
    print(f"Incorrect: {len(incorrect)} ({len(incorrect)/len(results)*100:.1f}%)")
    print()

    # Generalist type breakdown
    print("=" * 80)
    print("GENERALIST TYPE ANALYSIS")
    print("=" * 80)

    generalist_correct = defaultdict(int)
    generalist_total = defaultdict(int)

    for r in results:
        if 'error' in r:
            continue
        gen_type = r.get('generalist_type', 'Unknown')
        generalist_total[gen_type] += 1
        if r.get('is_correct'):
            generalist_correct[gen_type] += 1

    for gen_type in sorted(generalist_total.keys()):
        total = generalist_total[gen_type]
        correct_count = generalist_correct[gen_type]
        accuracy = correct_count / total * 100 if total > 0 else 0
        print(f"{gen_type:30s}: {correct_count:2d}/{total:2d} = {accuracy:5.1f}%")

    print()

    # Specialist usage
    print("=" * 80)
    print("SPECIALIST CONSULTATION PATTERNS")
    print("=" * 80)

    all_specialists = []
    correct_specialists = []
    incorrect_specialists = []

    for r in correct:
        specialists = r.get('specialists', [])
        all_specialists.extend(specialists)
        correct_specialists.extend(specialists)

    for r in incorrect:
        specialists = r.get('specialists', [])
        all_specialists.extend(specialists)
        incorrect_specialists.extend(specialists)

    specialist_counter = Counter(all_specialists)
    correct_counter = Counter(correct_specialists)
    incorrect_counter = Counter(incorrect_specialists)

    print(f"\nMost Frequently Consulted Specialists:")
    print(f"{'Specialty':<25} {'Total':>6} {'Correct':>8} {'Incorrect':>10} {'Accuracy':>10}")
    print("-" * 70)

    for specialist, count in specialist_counter.most_common(15):
        correct_count = correct_counter[specialist]
        incorrect_count = incorrect_counter[specialist]
        accuracy = correct_count / count * 100 if count > 0 else 0
        print(f"{specialist:<25} {count:>6} {correct_count:>8} {incorrect_count:>10} {accuracy:>9.1f}%")

    print()

    # Number of specialists consulted
    print("=" * 80)
    print("NUMBER OF SPECIALISTS CONSULTED")
    print("=" * 80)

    num_specialists_correct = defaultdict(int)
    num_specialists_total = defaultdict(int)

    for r in results:
        if 'error' in r:
            continue
        num_specs = len(r.get('specialists', []))
        num_specialists_total[num_specs] += 1
        if r.get('is_correct'):
            num_specialists_correct[num_specs] += 1

    for num in sorted(num_specialists_total.keys()):
        total = num_specialists_total[num]
        correct_count = num_specialists_correct[num]
        accuracy = correct_count / total * 100 if total > 0 else 0
        print(f"{num} specialist(s): {correct_count:2d}/{total:2d} = {accuracy:5.1f}%")

    print()

    # Debate rounds analysis
    print("=" * 80)
    print("DEBATE ROUNDS ANALYSIS")
    print("=" * 80)

    # Analyze consultation history for agreement patterns
    early_agreement_correct = 0
    early_agreement_total = 0
    max_rounds_correct = 0
    max_rounds_total = 0

    for r in results:
        if 'error' in r or 'full_result' not in r:
            continue

        consultation_history = r['full_result'].get('consultation_history', [])

        # Check debate consultations
        for item in consultation_history:
            if item.get('stage', '').startswith('consultation_'):
                total_rounds = item.get('total_rounds', 0)

                # Early agreement = rounds < 6 (less than max)
                if total_rounds < 6:
                    early_agreement_total += 1
                    if r.get('is_correct'):
                        early_agreement_correct += 1
                else:
                    max_rounds_total += 1
                    if r.get('is_correct'):
                        max_rounds_correct += 1

    print(f"Early Agreement (< 6 rounds): {early_agreement_correct}/{early_agreement_total} = {early_agreement_correct/early_agreement_total*100 if early_agreement_total > 0 else 0:.1f}%")
    print(f"Max Rounds (6 rounds):        {max_rounds_correct}/{max_rounds_total} = {max_rounds_correct/max_rounds_total*100 if max_rounds_total > 0 else 0:.1f}%")

    print()

    # Token usage analysis
    print("=" * 80)
    print("RESOURCE USAGE")
    print("=" * 80)

    correct_tokens = [r.get('tokens', 0) for r in correct]
    incorrect_tokens = [r.get('tokens', 0) for r in incorrect]

    print(f"Avg Tokens (Correct):   {sum(correct_tokens)/len(correct_tokens):.0f}")
    print(f"Avg Tokens (Incorrect): {sum(incorrect_tokens)/len(incorrect_tokens):.0f}")

    correct_latency = [r.get('latency', 0) for r in correct]
    incorrect_latency = [r.get('latency', 0) for r in incorrect]

    print(f"Avg Latency (Correct):   {sum(correct_latency)/len(correct_latency):.1f}s")
    print(f"Avg Latency (Incorrect): {sum(incorrect_latency)/len(incorrect_latency):.1f}s")

    print()

    # Sample some incorrect cases
    print("=" * 80)
    print("SAMPLE INCORRECT CASES (First 5)")
    print("=" * 80)

    for i, r in enumerate(incorrect[:5], 1):
        print(f"\nQuestion {r['question_idx']}:")
        print(f"  Question: {r['question']}")
        print(f"  Predicted: {r['predicted']}")
        print(f"  Correct: {r['correct']}")
        print(f"  Generalist: {r.get('generalist_type', 'Unknown')}")
        print(f"  Specialists: {', '.join(r.get('specialists', []))}")
        print(f"  Tokens: {r.get('tokens', 0)}, Latency: {r.get('latency', 0):.1f}s")

    print()
    print("=" * 80)


if __name__ == "__main__":
    results_path = Path("runs/sequential_debate/20251112_000220/results.json")
    analyze_results(results_path)
