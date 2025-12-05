#!/usr/bin/env python3
"""
Analyze Debate Dynamics - Do agents change their answers during debate?
"""

import json
import sys
from pathlib import Path
from collections import Counter

def analyze_debate_results(results_path: Path):
    """Analyze how often agents change answers during debate."""

    with open(results_path) as f:
        results = json.load(f)

    # Track statistics
    initial_agreements = 0  # Both agents start with same answer
    initial_disagreements = 0  # Agents start with different answers

    agent_a_changes = 0  # Agent A changed answer during debate
    agent_b_changes = 0  # Agent B changed answer during debate

    final_agreements = 0  # Both agents end with same answer
    final_disagreements = 0  # Agents end with different answers

    # Track convergence patterns
    convergence_patterns = []  # "disagree->agree" or "agree->disagree" or "agree->agree" or "disagree->disagree"

    # Track detailed changes
    questions_with_changes = []

    for item in results:
        if "error" in item:
            continue

        full_result = item.get("full_result", {})
        debate_history = full_result.get("debate_history", [])

        if len(debate_history) < 4:
            continue  # Need at least round 1 A, round 1 B, round 2 A, round 2 B

        # Extract answers for each round
        round_1_a = None
        round_1_b = None
        round_2_a = None
        round_2_b = None

        for entry in debate_history:
            if entry["round"] == 1 and entry["agent"] == "A":
                round_1_a = entry.get("answer", "UNKNOWN")
            elif entry["round"] == 1 and entry["agent"] == "B":
                round_1_b = entry.get("answer", "UNKNOWN")
            elif entry["round"] == 2 and entry["agent"] == "A":
                round_2_a = entry.get("answer", "UNKNOWN")
            elif entry["round"] == 2 and entry["agent"] == "B":
                round_2_b = entry.get("answer", "UNKNOWN")

        if not all([round_1_a, round_1_b, round_2_a, round_2_b]):
            continue

        # Initial agreement/disagreement
        initially_agree = (round_1_a == round_1_b)
        if initially_agree:
            initial_agreements += 1
        else:
            initial_disagreements += 1

        # Final agreement/disagreement
        finally_agree = (round_2_a == round_2_b)
        if finally_agree:
            final_agreements += 1
        else:
            final_disagreements += 1

        # Did agents change?
        a_changed = (round_1_a != round_2_a)
        b_changed = (round_1_b != round_2_b)

        if a_changed:
            agent_a_changes += 1
        if b_changed:
            agent_b_changes += 1

        # Convergence pattern
        if initially_agree and finally_agree:
            pattern = "agree->agree"
        elif initially_agree and not finally_agree:
            pattern = "agree->disagree"
        elif not initially_agree and finally_agree:
            pattern = "disagree->agree (CONVERGENCE)"
        else:
            pattern = "disagree->disagree (PERSISTENT)"

        convergence_patterns.append(pattern)

        # Track detailed info if any changes occurred
        if a_changed or b_changed:
            questions_with_changes.append({
                "question_idx": item["question_idx"],
                "correct": item["correct"],
                "predicted": item["predicted"],
                "is_correct": item["is_correct"],
                "round_1_a": round_1_a,
                "round_1_b": round_1_b,
                "round_2_a": round_2_a,
                "round_2_b": round_2_b,
                "a_changed": a_changed,
                "b_changed": b_changed,
                "pattern": pattern
            })

    total = initial_agreements + initial_disagreements

    print("=" * 80)
    print("DEBATE DYNAMICS ANALYSIS")
    print("=" * 80)
    print(f"\nTotal questions analyzed: {total}")
    print()

    print("INITIAL STATE (Round 1):")
    print(f"  Both agents agree:    {initial_agreements:3d} ({initial_agreements/total*100:.1f}%)")
    print(f"  Agents disagree:      {initial_disagreements:3d} ({initial_disagreements/total*100:.1f}%)")
    print()

    print("FINAL STATE (Round 2):")
    print(f"  Both agents agree:    {final_agreements:3d} ({final_agreements/total*100:.1f}%)")
    print(f"  Agents disagree:      {final_disagreements:3d} ({final_disagreements/total*100:.1f}%)")
    print()

    print("AGENT POSITION CHANGES:")
    print(f"  Agent A changed answer: {agent_a_changes:3d} ({agent_a_changes/total*100:.1f}%)")
    print(f"  Agent B changed answer: {agent_b_changes:3d} ({agent_b_changes/total*100:.1f}%)")
    print(f"  Either agent changed:   {len(questions_with_changes):3d} ({len(questions_with_changes)/total*100:.1f}%)")
    print()

    print("CONVERGENCE PATTERNS:")
    pattern_counts = Counter(convergence_patterns)
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern:40s} {count:3d} ({count/total*100:.1f}%)")
    print()

    if questions_with_changes:
        print("\nQUESTIONS WHERE AGENTS CHANGED POSITIONS:")
        print("-" * 80)
        for q in questions_with_changes[:10]:  # Show first 10
            status = "[OK]" if q["is_correct"] else "[X]"
            print(f"\nQ{q['question_idx']:3d} {status} (Correct: {q['correct']}, Predicted: {q['predicted']})")
            print(f"  Agent A: {q['round_1_a']} -> {q['round_2_a']} {'(CHANGED)' if q['a_changed'] else ''}")
            print(f"  Agent B: {q['round_1_b']} -> {q['round_2_b']} {'(CHANGED)' if q['b_changed'] else ''}")
            print(f"  Pattern: {q['pattern']}")

        if len(questions_with_changes) > 10:
            print(f"\n  ... and {len(questions_with_changes) - 10} more questions with changes")

    print("\n" + "=" * 80)

    # Key insights
    print("\nKEY INSIGHTS:")
    print(f"1. Agents agree from the start {initial_agreements/total*100:.1f}% of the time")
    print(f"2. Only {len(questions_with_changes)/total*100:.1f}% of questions see any position changes")
    print(f"3. When agents disagree initially, convergence rate: {pattern_counts.get('disagree->agree (CONVERGENCE)', 0)/initial_disagreements*100 if initial_disagreements > 0 else 0:.1f}%")

    return {
        "total": total,
        "initial_agreements": initial_agreements,
        "initial_disagreements": initial_disagreements,
        "agent_a_changes": agent_a_changes,
        "agent_b_changes": agent_b_changes,
        "questions_with_changes": len(questions_with_changes),
        "convergence_patterns": dict(pattern_counts)
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        results_path = Path(sys.argv[1])
    else:
        # Default to most recent debate_plus test
        results_path = Path("runs/debate_plus_test/20251112_173518/results.json")

    if not results_path.exists():
        print(f"Error: {results_path} not found")
        sys.exit(1)

    analyze_debate_results(results_path)
