#!/usr/bin/env python3
"""
Compare two methods to see which questions each gets right/wrong.
"""

import json
import sys
from pathlib import Path

def compare_methods(full_results_path: Path, method_a: str = "single_cot", method_b: str = "debate"):
    """Compare two methods to see performance differences."""

    with open(full_results_path) as f:
        data = json.load(f)

    # Get results for each method
    if method_a not in data:
        print(f"Error: Method '{method_a}' not found in results")
        print(f"Available methods: {list(data.keys())}")
        sys.exit(1)

    if method_b not in data:
        print(f"Error: Method '{method_b}' not found in results")
        print(f"Available methods: {list(data.keys())}")
        sys.exit(1)

    method_a_results = {}
    method_b_results = {}

    # Index results by question_idx
    for item in data[method_a]:
        q_idx = item["question_idx"]
        method_a_results[q_idx] = {
            "predicted": item.get("predicted", "UNKNOWN"),
            "correct_answer": item.get("correct"),
            "is_correct": item.get("is_correct", False),
            "question": item.get("question", "")[:100]
        }

    for item in data[method_b]:
        q_idx = item["question_idx"]
        method_b_results[q_idx] = {
            "predicted": item.get("predicted", "UNKNOWN"),
            "correct_answer": item.get("correct"),
            "is_correct": item.get("is_correct", False),
            "question": item.get("question", "")[:100]
        }

    # Find common questions
    common_questions = set(method_a_results.keys()) & set(method_b_results.keys())

    if not common_questions:
        print("Error: No common questions found between methods")
        sys.exit(1)

    # Categorize questions
    both_correct = []
    both_wrong = []
    only_a_correct = []
    only_b_correct = []

    for q_idx in sorted(common_questions):
        a_correct = method_a_results[q_idx]["is_correct"]
        b_correct = method_b_results[q_idx]["is_correct"]

        if a_correct and b_correct:
            both_correct.append(q_idx)
        elif a_correct and not b_correct:
            only_a_correct.append(q_idx)
        elif not a_correct and b_correct:
            only_b_correct.append(q_idx)
        else:
            both_wrong.append(q_idx)

    total = len(common_questions)

    print("=" * 80)
    print(f"METHOD COMPARISON: {method_a.upper()} vs {method_b.upper()}")
    print("=" * 80)
    print()

    print(f"Total questions: {total}")
    print()

    print("SUMMARY:")
    print(f"  Both methods correct:     {len(both_correct):3d} ({len(both_correct)/total*100:5.1f}%)")
    print(f"  Both methods wrong:       {len(both_wrong):3d} ({len(both_wrong)/total*100:5.1f}%)")
    print(f"  Only {method_a} correct:  {len(only_a_correct):3d} ({len(only_a_correct)/total*100:5.1f}%)")
    print(f"  Only {method_b} correct:  {len(only_b_correct):3d} ({len(only_b_correct)/total*100:5.1f}%)")
    print()

    # Calculate accuracy
    a_correct_total = len(both_correct) + len(only_a_correct)
    b_correct_total = len(both_correct) + len(only_b_correct)

    print(f"{method_a.upper()} accuracy: {a_correct_total}/{total} = {a_correct_total/total*100:.1f}%")
    print(f"{method_b.upper()} accuracy: {b_correct_total}/{total} = {b_correct_total/total*100:.1f}%")
    print(f"{method_b.upper()} advantage: +{len(only_b_correct) - len(only_a_correct)} questions ({(len(only_b_correct) - len(only_a_correct))/total*100:+.1f}%)")
    print()

    # Show questions where B beats A
    if only_b_correct:
        print("=" * 80)
        print(f"QUESTIONS WHERE {method_b.upper()} CORRECT BUT {method_a.upper()} WRONG:")
        print("=" * 80)
        for q_idx in sorted(only_b_correct)[:20]:  # Show first 20
            a_pred = method_a_results[q_idx]["predicted"]
            b_pred = method_b_results[q_idx]["predicted"]
            correct = method_a_results[q_idx]["correct_answer"]
            question = method_a_results[q_idx]["question"]

            print(f"\nQ{q_idx:3d}: {question}...")
            print(f"  Correct answer:     {correct}")
            print(f"  {method_a} predicted: {a_pred} [WRONG]")
            print(f"  {method_b} predicted: {b_pred} [CORRECT]")

        if len(only_b_correct) > 20:
            print(f"\n  ... and {len(only_b_correct) - 20} more")

    # Show questions where A beats B
    if only_a_correct:
        print()
        print("=" * 80)
        print(f"QUESTIONS WHERE {method_a.upper()} CORRECT BUT {method_b.upper()} WRONG:")
        print("=" * 80)
        for q_idx in sorted(only_a_correct)[:20]:  # Show first 20
            a_pred = method_a_results[q_idx]["predicted"]
            b_pred = method_b_results[q_idx]["predicted"]
            correct = method_a_results[q_idx]["correct_answer"]
            question = method_a_results[q_idx]["question"]

            print(f"\nQ{q_idx:3d}: {question}...")
            print(f"  Correct answer:     {correct}")
            print(f"  {method_a} predicted: {a_pred} [CORRECT]")
            print(f"  {method_b} predicted: {b_pred} [WRONG]")

        if len(only_a_correct) > 20:
            print(f"\n  ... and {len(only_a_correct) - 20} more")

    print()
    print("=" * 80)

    return {
        "both_correct": len(both_correct),
        "both_wrong": len(both_wrong),
        "only_a_correct": len(only_a_correct),
        "only_b_correct": len(only_b_correct),
        "advantage": len(only_b_correct) - len(only_a_correct)
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        results_path = Path(sys.argv[1])
    else:
        # Default to most recent baseline comparison
        results_path = Path("runs/baseline_comparison/20251111_072417/full_results.json")

    if not results_path.exists():
        print(f"Error: {results_path} not found")
        sys.exit(1)

    method_a = sys.argv[2] if len(sys.argv) > 2 else "single_cot"
    method_b = sys.argv[3] if len(sys.argv) > 3 else "debate"

    compare_methods(results_path, method_a, method_b)
