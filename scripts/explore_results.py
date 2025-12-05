"""
Interactive script to explore evaluation results and examine reasoning traces.
"""

import json
import sys
from pathlib import Path
from typing import Optional


def load_results(results_dir: str) -> dict:
    """Load full results from a results directory."""
    results_path = Path(results_dir) / "full_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)


def show_question_summary(results: dict, question_idx: int):
    """Show summary for a specific question."""
    for method_name, method_results in results.items():
        print(f"\n{'='*60}")
        print(f"Method: {method_name}")
        print(f"{'='*60}")

        # Find the question
        question_result = None
        for result in method_results:
            if result.get("question_idx") == question_idx:
                question_result = result
                break

        if not question_result:
            print(f"  Question {question_idx} not found")
            continue

        # Check for errors
        if "error" in question_result:
            print(f"  ERROR: {question_result['error']}")
            continue

        # Show basic info
        print(f"  Question: {question_result['question'][:100]}...")
        print(f"  Correct Answer: {question_result['correct']}")
        print(f"  Predicted: {question_result['predicted']}")
        print(f"  Is Correct: {question_result['is_correct']}")
        print(f"  Latency: {question_result['latency']:.1f}s")
        print(f"  Tokens: {question_result['tokens']}")


def show_adaptive_mas_reasoning(results: dict, question_idx: int):
    """Show detailed reasoning trace for Adaptive MAS on a specific question."""
    adaptive_results = results.get("adaptive_mas", [])

    # Find the question
    question_result = None
    for result in adaptive_results:
        if result.get("question_idx") == question_idx:
            question_result = result
            break

    if not question_result:
        print(f"Question {question_idx} not found in Adaptive MAS results")
        return

    # Check for errors
    if "error" in question_result:
        print(f"\n{'='*60}")
        print(f"ERROR on Question {question_idx}")
        print(f"{'='*60}")
        print(f"Error: {question_result['error']}")
        return

    # Parse the trace string to extract structured data
    trace_str = question_result["full_result"]["trace"]

    # Extract basic info
    print(f"\n{'='*60}")
    print(f"ADAPTIVE MAS - Question {question_idx}")
    print(f"{'='*60}")

    print(f"\nQuestion: {question_result['question']}")
    print(f"Options: {question_result.get('options', 'N/A')}")
    print(f"Correct Answer: {question_result['correct']}")
    print(f"Predicted: {question_result['predicted']}")
    print(f"Is Correct: {question_result['is_correct']}")
    print(f"Tokens: {question_result['tokens']}")
    print(f"Latency: {question_result['latency']:.1f}s")
    print(f"Agents Used: {question_result['agents_used']}")

    # Try to extract planner info from trace
    if "planner_trace=" in trace_str:
        planner_start = trace_str.find("planner_trace=")
        planner_end = trace_str.find("specialist_traces=", planner_start)
        planner_section = trace_str[planner_start:planner_end]

        # Extract selected specialties
        if "selected_specialties" in planner_section:
            selected_start = planner_section.find("'selected_specialties': [")
            if selected_start != -1:
                selected_end = planner_section.find("]", selected_start)
                specialties_str = planner_section[selected_start:selected_end+1]
                print(f"\nPlanner Selected Specialties:")
                print(f"  {specialties_str}")

        # Extract rationale
        if "'rationale':" in planner_section:
            rationale_start = planner_section.find("'rationale': '") + len("'rationale': '")
            rationale_end = planner_section.find("'}", rationale_start)
            if rationale_end == -1:
                rationale_end = planner_section.find("'", rationale_start + 1)
            rationale = planner_section[rationale_start:rationale_end]
            print(f"\nPlanner Rationale:")
            print(f"  {rationale}")

    # Show final decision
    print(f"\n{'='*60}")
    print(f"FINAL DECISION")
    print(f"{'='*60}")
    print(f"Answer: {question_result['predicted']}")


def show_all_questions(results: dict):
    """Show summary of all questions."""
    print(f"\n{'='*60}")
    print(f"ALL QUESTIONS SUMMARY")
    print(f"{'='*60}")

    # Get adaptive_mas results
    adaptive_results = results.get("adaptive_mas", [])

    for result in adaptive_results:
        q_idx = result["question_idx"]

        if "error" in result:
            print(f"\nQ{q_idx}: ERROR - {result['error']}")
        else:
            correct = "[OK]" if result["is_correct"] else "[X]"
            print(f"\nQ{q_idx}: {correct}")
            print(f"  Predicted: {result['predicted']}")
            print(f"  Correct: {result['correct']}")
            print(f"  Latency: {result['latency']:.1f}s")
            print(f"  Agents: {result['agents_used']}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python explore_results.py <results_dir> [question_number]")
        print("")
        print("Examples:")
        print("  python explore_results.py runs/baseline_comparison/20251103_154723")
        print("  python explore_results.py runs/baseline_comparison/20251103_154723 2")
        return

    results_dir = sys.argv[1]
    results = load_results(results_dir)

    if len(sys.argv) >= 3:
        # Show specific question
        question_idx = int(sys.argv[2])
        show_question_summary(results, question_idx)
        print("\n")
        show_adaptive_mas_reasoning(results, question_idx)
    else:
        # Show all questions
        show_all_questions(results)


if __name__ == "__main__":
    main()
