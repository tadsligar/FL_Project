#!/usr/bin/env python3
"""
Summarize all tested architectures and their best performance
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict

def load_results(path):
    """Load results from a JSON file"""
    with open(path) as f:
        return json.load(f)

def get_accuracy(results):
    """Calculate accuracy from results"""
    correct = sum(1 for r in results if r.get('is_correct', r.get('correct', False)))
    total = len(results)
    return (correct / total) * 100

def categorize_run(path_str):
    """Categorize run by architecture type"""
    if 'progressive_temperature_parallel' in path_str:
        return 'Progressive Temperature Parallel'
    elif 'progressive_temperature' in path_str:
        return 'Progressive Temperature'
    elif 'independent_multi_agent_synthesis' in path_str:
        return 'Multi-Agent Specialist (Synthesis)'
    elif 'independent_multi_agent_majority' in path_str:
        return 'Multi-Agent Specialist (Majority)'
    elif 'independent_multi_agent_mixed_temp' in path_str:
        if 'specialist07' in path_str:
            return 'Multi-Agent Specialist (Mixed temp=0.7)'
        else:
            return 'Multi-Agent Specialist (Mixed temp=0.3)'
    elif 'independent_multi_agent' in path_str:
        return 'Multi-Agent Specialist'
    elif 'adaptive_triple_specialist' in path_str:
        return 'Adaptive Triple Specialist'
    elif 'answer_space_consultation' in path_str:
        return 'Answer Space Consultation'
    elif 'debate_physician_role' in path_str:
        return 'Debate (Physician Role)'
    elif 'debate_forced_disagreement' in path_str:
        return 'Debate (Forced Disagreement)'
    elif 'debate_cot_enhanced' in path_str:
        return 'Debate (CoT Enhanced)'
    elif 'debate_plus' in path_str:
        return 'Debate Plus'
    elif 'debate' in path_str:
        return 'Debate (Standard)'
    elif 'zero_shot_physician' in path_str:
        return 'Zero-Shot (Physician)'
    elif 'zero_shot' in path_str:
        return 'Zero-Shot'
    elif 'single_shot_cot' in path_str or 'single_llm_cot' in path_str:
        return 'Single-Shot CoT'
    elif 'independent_binary' in path_str:
        return 'Independent Binary Agents'
    elif 'independent_confidence' in path_str:
        return 'Independent Confidence Agents'
    else:
        return 'Other'

def main():
    # Find all results files
    results_files = list(Path('runs').rglob('results.json'))

    print("=" * 80)
    print("COMPREHENSIVE ARCHITECTURE PERFORMANCE SUMMARY")
    print("=" * 80)
    print()

    # Group by architecture
    architecture_results = defaultdict(list)

    for results_path in results_files:
        try:
            results = load_results(results_path)
            accuracy = get_accuracy(results)
            architecture = categorize_run(str(results_path))

            architecture_results[architecture].append({
                'path': str(results_path),
                'accuracy': accuracy,
                'n_questions': len(results)
            })
        except Exception as e:
            print(f"Error processing {results_path}: {e}")
            continue

    # Sort architectures by best performance
    arch_summary = []
    for arch_name, runs in architecture_results.items():
        if not runs:
            continue

        accuracies = [r['accuracy'] for r in runs]
        best_acc = max(accuracies)
        mean_acc = statistics.mean(accuracies)
        n_runs = len(runs)

        arch_summary.append({
            'name': arch_name,
            'best': best_acc,
            'mean': mean_acc,
            'n_runs': n_runs,
            'std': statistics.stdev(accuracies) if n_runs > 1 else 0,
            'runs': runs
        })

    # Sort by best accuracy
    arch_summary.sort(key=lambda x: x['best'], reverse=True)

    # Print summary table
    print(f"{'Rank':<5} {'Architecture':<45} {'Best %':<10} {'Mean %':<10} {'Runs':<6} {'Std Dev'}")
    print("-" * 90)

    for i, arch in enumerate(arch_summary, 1):
        print(f"{i:<5} {arch['name']:<45} {arch['best']:>6.2f}%   {arch['mean']:>6.2f}%   {arch['n_runs']:<6} {arch['std']:>6.3f}%")

    print()
    print("=" * 80)
    print("TOP 10 ARCHITECTURES - DETAILED BREAKDOWN")
    print("=" * 80)
    print()

    for i, arch in enumerate(arch_summary[:10], 1):
        print(f"{i}. {arch['name']}")
        print(f"   Best Accuracy: {arch['best']:.2f}%")
        print(f"   Mean Accuracy: {arch['mean']:.2f}% (± {arch['std']:.3f}%)")
        print(f"   Number of Runs: {arch['n_runs']}")

        if arch['n_runs'] <= 5:
            print(f"   Individual Runs:")
            for run in sorted(arch['runs'], key=lambda x: x['accuracy'], reverse=True):
                print(f"      - {run['accuracy']:.2f}% ({run['n_questions']} questions)")

        print()

    # Print category summary
    print("=" * 80)
    print("ARCHITECTURE CATEGORIES")
    print("=" * 80)
    print()

    categories = {
        'Progressive Temperature': [],
        'Multi-Agent': [],
        'Debate': [],
        'Single-Shot': [],
        'Zero-Shot': [],
        'Other': []
    }

    for arch in arch_summary:
        name = arch['name']
        if 'Progressive' in name:
            categories['Progressive Temperature'].append(arch)
        elif 'Multi-Agent' in name or 'Specialist' in name:
            categories['Multi-Agent'].append(arch)
        elif 'Debate' in name:
            categories['Debate'].append(arch)
        elif 'Single' in name or 'CoT' in name:
            categories['Single-Shot'].append(arch)
        elif 'Zero' in name:
            categories['Zero-Shot'].append(arch)
        else:
            categories['Other'].append(arch)

    for cat_name, archs in categories.items():
        if not archs:
            continue
        print(f"\n{cat_name}:")
        print("-" * 60)
        for arch in archs:
            print(f"  {arch['name']:<45} Best: {arch['best']:>6.2f}%  Mean: {arch['mean']:>6.2f}%")

if __name__ == "__main__":
    main()
