#!/usr/bin/env python3
"""
Analyze token usage across all tested architectures
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict

def load_results(path):
    """Load results from a JSON file"""
    with open(path) as f:
        return json.load(f)

def get_token_stats(results):
    """Calculate token statistics from results"""
    tokens_list = []
    for r in results:
        # Try different token field names
        tokens = r.get('tokens', r.get('tokens_used', r.get('total_tokens', 0)))
        if tokens > 0:
            tokens_list.append(tokens)

    if not tokens_list:
        return None

    return {
        'mean': statistics.mean(tokens_list),
        'median': statistics.median(tokens_list),
        'min': min(tokens_list),
        'max': max(tokens_list),
        'total': sum(tokens_list),
        'n_questions': len(tokens_list)
    }

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

    print("=" * 100)
    print("TOKEN USAGE ANALYSIS - ALL ARCHITECTURES")
    print("=" * 100)
    print()

    # Group by architecture
    architecture_tokens = defaultdict(list)

    for results_path in results_files:
        try:
            results = load_results(results_path)
            token_stats = get_token_stats(results)

            if token_stats is None:
                continue

            architecture = categorize_run(str(results_path))
            architecture_tokens[architecture].append({
                'path': str(results_path),
                'stats': token_stats
            })
        except Exception as e:
            continue

    # Calculate aggregate statistics per architecture
    arch_summary = []
    for arch_name, runs in architecture_tokens.items():
        if not runs:
            continue

        # Filter for full dataset runs (1071 questions)
        full_runs = [r for r in runs if r['stats']['n_questions'] == 1071]
        all_runs = runs

        if full_runs:
            mean_tokens = statistics.mean([r['stats']['mean'] for r in full_runs])
            total_tokens = sum([r['stats']['total'] for r in full_runs])
            n_runs = len(full_runs)
            is_full = True
        else:
            mean_tokens = statistics.mean([r['stats']['mean'] for r in all_runs])
            total_tokens = sum([r['stats']['total'] for r in all_runs])
            n_runs = len(all_runs)
            is_full = False

        arch_summary.append({
            'name': arch_name,
            'mean_tokens': mean_tokens,
            'total_tokens': total_tokens,
            'n_runs': n_runs,
            'is_full': is_full,
            'runs': full_runs if full_runs else all_runs
        })

    # Sort by mean tokens (ascending - more efficient first)
    arch_summary.sort(key=lambda x: x['mean_tokens'])

    print("=" * 100)
    print("FULL DATASET TOKEN USAGE (1,071 Questions)")
    print("=" * 100)
    print()
    print(f"{'Architecture':<45} {'Avg Tokens/Q':<15} {'Total Tokens':<15} {'Runs':<6} {'Full?'}")
    print("-" * 100)

    for arch in arch_summary:
        if arch['is_full']:
            full_marker = "[YES]"
        else:
            full_marker = "[Pilot]"

        avg_tokens = f"{arch['mean_tokens']:,.0f}"
        total_tokens = f"{arch['total_tokens']:,.0f}"

        print(f"{arch['name']:<45} {avg_tokens:>13}  {total_tokens:>13}  {arch['n_runs']:<6} {full_marker}")

    print()
    print("=" * 100)
    print("EFFICIENCY RANKING (Lower tokens = More efficient)")
    print("=" * 100)
    print()

    full_dataset_archs = [a for a in arch_summary if a['is_full']]

    print(f"{'Rank':<6} {'Architecture':<45} {'Tokens/Q':<15} {'vs Zero-Shot'}")
    print("-" * 90)

    # Find zero-shot baseline
    zero_shot_tokens = next((a['mean_tokens'] for a in full_dataset_archs if 'Zero-Shot' in a['name']), None)

    for i, arch in enumerate(full_dataset_archs, 1):
        if zero_shot_tokens:
            ratio = arch['mean_tokens'] / zero_shot_tokens
            ratio_str = f"{ratio:.1f}x"
        else:
            ratio_str = "N/A"

        print(f"{i:<6} {arch['name']:<45} {arch['mean_tokens']:>13,.0f}  {ratio_str:>12}")

    print()
    print("=" * 100)
    print("DETAILED BREAKDOWN - TOP ARCHITECTURES")
    print("=" * 100)
    print()

    for arch in full_dataset_archs[:10]:
        print(f"\n{arch['name']}")
        print("-" * 80)
        print(f"  Average tokens per question: {arch['mean_tokens']:,.0f}")
        print(f"  Number of runs: {arch['n_runs']}")

        if arch['n_runs'] <= 5:
            print(f"  Individual run stats:")
            for run in arch['runs']:
                stats = run['stats']
                print(f"    - {stats['mean']:,.0f} avg tokens/q ({stats['total']:,.0f} total, {stats['n_questions']} questions)")

    print()
    print("=" * 100)
    print("COST ANALYSIS (Relative to Zero-Shot)")
    print("=" * 100)
    print()

    if zero_shot_tokens:
        print(f"Zero-Shot baseline: {zero_shot_tokens:,.0f} tokens/question")
        print()
        print("Token multiplier by architecture:")
        print()

        categories = {
            'Most Efficient (1-2x)': [],
            'Moderate (2-5x)': [],
            'Expensive (5-10x)': [],
            'Very Expensive (>10x)': []
        }

        for arch in full_dataset_archs:
            ratio = arch['mean_tokens'] / zero_shot_tokens

            if ratio < 2:
                categories['Most Efficient (1-2x)'].append((arch, ratio))
            elif ratio < 5:
                categories['Moderate (2-5x)'].append((arch, ratio))
            elif ratio < 10:
                categories['Expensive (5-10x)'].append((arch, ratio))
            else:
                categories['Very Expensive (>10x)'].append((arch, ratio))

        for cat_name, archs in categories.items():
            if archs:
                print(f"\n{cat_name}:")
                for arch, ratio in archs:
                    print(f"  {arch['name']:<45} {ratio:>5.1f}x  ({arch['mean_tokens']:>8,.0f} tokens/q)")

    print()
    print("=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    print()

    if full_dataset_archs:
        all_means = [a['mean_tokens'] for a in full_dataset_archs]
        print(f"Across all full-dataset architectures:")
        print(f"  Most efficient: {min(all_means):,.0f} tokens/question")
        print(f"  Least efficient: {max(all_means):,.0f} tokens/question")
        print(f"  Average: {statistics.mean(all_means):,.0f} tokens/question")
        print(f"  Median: {statistics.median(all_means):,.0f} tokens/question")
        print(f"  Range: {max(all_means) - min(all_means):,.0f} tokens/question")

if __name__ == "__main__":
    main()
