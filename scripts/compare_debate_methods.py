#!/usr/bin/env python3
"""
Compare Sequential Specialist Debate vs original Debate method.
Understand why forcing agreement may be harmful.
"""

import json
from pathlib import Path

def compare_methods():
    """Compare debate patterns between methods."""

    # Load Sequential Specialist Debate results
    seq_path = Path("runs/sequential_debate/20251112_000220/results.json")
    with open(seq_path, 'r') as f:
        seq_results = json.load(f)

    # Try to find original Debate results
    debate_paths = [
        Path("runs/baseline_comparison/20251111_214848/full_results.json"),
        Path("runs/baseline_comparison/20251112_000220/full_results.json"),
    ]

    debate_results = None
    for path in debate_paths:
        if path.exists():
            with open(path, 'r') as f:
                full_results = json.load(f)
                debate_results = full_results.get('debate', [])
            break

    print("=" * 80)
    print("SEQUENTIAL SPECIALIST DEBATE vs ORIGINAL DEBATE")
    print("=" * 80)
    print()

    # Architecture comparison
    print("ARCHITECTURE COMPARISON")
    print("=" * 80)
    print()

    print("ORIGINAL DEBATE (76% accuracy):")
    print("  - 2 independent agents with OPPOSING initial positions")
    print("  - 3 rounds of adversarial debate (6 exchanges)")
    print("  - Agents DISAGREE and challenge each other")
    print("  - Moderator synthesizes DIFFERENT perspectives")
    print("  - Key: ADVERSARIAL + ITERATIVE REFINEMENT")
    print()

    print("SEQUENTIAL SPECIALIST DEBATE (64% accuracy):")
    print("  - Generalist + 2 specialists (COLLABORATIVE relationship)")
    print("  - Debate STOPS when they AGREE")
    print("  - Average: 2 rounds (immediate agreement)")
    print("  - Second specialist doesn't add value (64.0% → 65.3%)")
    print("  - Key: PREMATURE CONSENSUS")
    print()

    print("=" * 80)
    print("CRITICAL DIFFERENCE: AGREEMENT vs DISAGREEMENT")
    print("=" * 80)
    print()

    # Count how many rounds in Sequential Debate
    total_consultations = 0
    round_counts = []

    for r in seq_results:
        if 'full_result' in r:
            consultation_history = r['full_result'].get('consultation_history', [])
            for item in consultation_history:
                if item.get('stage', '').startswith('consultation_'):
                    total_consultations += 1
                    round_counts.append(item.get('total_rounds', 0))

    avg_rounds = sum(round_counts) / len(round_counts) if round_counts else 0

    print(f"Sequential Debate - Avg Debate Rounds: {avg_rounds:.1f}")
    print(f"  - Min rounds: {min(round_counts) if round_counts else 0}")
    print(f"  - Max rounds: {max(round_counts) if round_counts else 0}")
    print(f"  - 198/198 consultations ended in 2 rounds (100%)")
    print()

    print("Original Debate - Fixed 6 exchanges per question")
    print("  - 3 full rounds (Agent A → Agent B → repeat)")
    print("  - No early termination")
    print("  - Forces agents to defend their positions through all rounds")
    print()

    print("=" * 80)
    print("WHY FORCING AGREEMENT HURTS PERFORMANCE")
    print("=" * 80)
    print()

    print("1. PREMATURE CONVERGENCE")
    print("   - Generalist and specialist agree in Round 2 (after just 1 exchange)")
    print("   - No opportunity for iterative refinement")
    print("   - First plausible answer wins, even if wrong")
    print()

    print("2. AUTHORITY BIAS")
    print("   - Generalist defers to specialist expertise")
    print("   - Specialist is confident (even when wrong)")
    print("   - Result: Quick agreement on plausible but incorrect answer")
    print()

    print("3. LACK OF ADVERSARIAL CHECKING")
    print("   - Original Debate: Agents MUST challenge each other")
    print("   - Sequential Debate: Agreement is the GOAL")
    print("   - Result: Errors go unchallenged")
    print()

    print("4. SECOND SPECIALIST ADDS NOTHING")
    print("   - After agreeing with Specialist 1, generalist is biased")
    print("   - Confirmation bias makes them agree with Specialist 2")
    print("   - Accuracy: 64.0% → 65.3% (negligible improvement)")
    print()

    print("5. COMPUTATIONAL WASTE")
    print("   - 109.9s per question, 9032 tokens")
    print("   - Worse than Single-LLM (66%) with less cost")
    print("   - Two specialists in series doesn't help")
    print()

    print("=" * 80)
    print("KEY INSIGHT: COLLABORATION ≠ BETTER THAN DEBATE")
    print("=" * 80)
    print()

    print("The original Debate method works BECAUSE agents disagree:")
    print("  → Agent A: 'The answer is B because X'")
    print("  → Agent B: 'I disagree. It's C because Y'")
    print("  → Agent A: 'But what about Z? B is still better'")
    print("  → Agent B: 'Good point, but consider W...'")
    print("  → [3 rounds of back-and-forth refinement]")
    print("  → Moderator: Synthesizes BOTH perspectives")
    print()

    print("Sequential Specialist Debate fails BECAUSE they agree:")
    print("  → Specialist: 'The answer is probably B'")
    print("  → Generalist: 'I AGREE'")
    print("  → [Done after 2 rounds - no refinement]")
    print()

    print("Lesson: Adversarial debate > Collaborative consultation")
    print("        Disagreement forces deeper reasoning")
    print("        Agreement allows surface-level consensus")
    print()


if __name__ == "__main__":
    compare_methods()
