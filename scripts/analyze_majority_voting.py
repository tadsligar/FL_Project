"""
Analyze majority voting across 3 runs of Progressive Temperature Parallel V4.

For each question, determine the majority vote from 3 runs and calculate
what the accuracy would be if we used majority voting.
"""

import json
import statistics
from pathlib import Path
from collections import Counter

def load_results(run_path):
    """Load results from a run."""
    results_file = Path(run_path)
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Handle both formats: list or dict with 'results' key
    if isinstance(data, list):
        return data
    else:
        return data['results']

def analyze_majority_voting():
    """Analyze majority voting across 3 runs."""

    # Load all 3 runs
    run_paths = [
        "runs/progressive_temperature_parallel_v4/20251203_214224/results.json",
        "runs/progressive_temperature_parallel_v4_run2/20251205_165007/results.json",
        "runs/progressive_temperature_parallel_v4_run3/20251208_103503/results.json"
    ]

    print("Loading results from 3 runs...")
    all_runs = []
    for i, path in enumerate(run_paths, 1):
        results = load_results(path)
        all_runs.append(results)
        correct = sum(1 for r in results if r.get('is_correct', r.get('correct', False)))
        print(f"  Run {i}: {correct}/{len(results)} = {correct/len(results)*100:.1f}%")

    # Verify all runs have same number of questions
    n_questions = len(all_runs[0])
    assert all(len(run) == n_questions for run in all_runs), "Runs have different lengths!"

    print(f"\nAnalyzing {n_questions} questions across 3 runs...\n")

    # Analyze agreement patterns
    unanimous_correct = 0  # All 3 agree and correct
    unanimous_wrong = 0    # All 3 agree but wrong
    majority_correct = 0   # 2/3 agree and correct
    majority_wrong = 0     # 2/3 agree but wrong
    no_majority = 0        # All 3 disagree

    majority_vote_correct = 0
    questions_by_agreement = {
        '3/3_correct': [],
        '3/3_wrong': [],
        '2/3_correct': [],
        '2/3_wrong': [],
        'no_majority': []
    }

    for i in range(n_questions):
        # Get answers from all 3 runs
        answers = [run[i]['predicted'] for run in all_runs]
        correct_answer = all_runs[0][i]['correct']
        question_id = all_runs[0][i].get('question_idx', i)

        # Count votes
        vote_counts = Counter(answers)
        most_common = vote_counts.most_common(1)[0]
        majority_answer = most_common[0]
        vote_count = most_common[1]

        # Check if majority vote is correct
        is_majority_correct = (majority_answer == correct_answer)
        if is_majority_correct:
            majority_vote_correct += 1

        # Categorize by agreement pattern
        if vote_count == 3:
            # Unanimous
            if is_majority_correct:
                unanimous_correct += 1
                questions_by_agreement['3/3_correct'].append({
                    'id': question_id,
                    'answer': majority_answer,
                    'correct': correct_answer
                })
            else:
                unanimous_wrong += 1
                questions_by_agreement['3/3_wrong'].append({
                    'id': question_id,
                    'answer': majority_answer,
                    'correct': correct_answer,
                    'votes': dict(vote_counts)
                })
        elif vote_count == 2:
            # 2/3 majority
            if is_majority_correct:
                majority_correct += 1
                questions_by_agreement['2/3_correct'].append({
                    'id': question_id,
                    'answer': majority_answer,
                    'correct': correct_answer,
                    'votes': dict(vote_counts)
                })
            else:
                majority_wrong += 1
                questions_by_agreement['2/3_wrong'].append({
                    'id': question_id,
                    'answer': majority_answer,
                    'correct': correct_answer,
                    'votes': dict(vote_counts)
                })
        else:
            # All 3 disagree
            no_majority += 1
            questions_by_agreement['no_majority'].append({
                'id': question_id,
                'votes': dict(vote_counts),
                'correct': correct_answer
            })

    # Calculate statistics
    individual_accuracies = []
    for run in all_runs:
        correct = sum(1 for r in run if r.get('is_correct', r.get('correct', False)))
        individual_accuracies.append(correct / n_questions * 100)

    majority_accuracy = majority_vote_correct / n_questions * 100
    mean_individual = statistics.mean(individual_accuracies)

    # Print results
    print("=" * 60)
    print("MAJORITY VOTING ANALYSIS")
    print("=" * 60)
    print()
    print("Individual Run Accuracies:")
    for i, acc in enumerate(individual_accuracies, 1):
        print(f"  Run {i}: {acc:.2f}%")
    print(f"  Mean:   {mean_individual:.2f}%")
    print()
    print("Majority Voting Performance:")
    print(f"  Accuracy: {majority_vote_correct}/{n_questions} = {majority_accuracy:.2f}%")
    print(f"  Improvement over mean: {majority_accuracy - mean_individual:+.2f} percentage points")
    print()
    print("Agreement Patterns:")
    print(f"  3/3 Agreement (Correct): {unanimous_correct} ({unanimous_correct/n_questions*100:.1f}%)")
    print(f"  3/3 Agreement (Wrong):   {unanimous_wrong} ({unanimous_wrong/n_questions*100:.1f}%)")
    print(f"  2/3 Agreement (Correct): {majority_correct} ({majority_correct/n_questions*100:.1f}%)")
    print(f"  2/3 Agreement (Wrong):   {majority_wrong} ({majority_wrong/n_questions*100:.1f}%)")
    print(f"  No Majority (All disagree): {no_majority} ({no_majority/n_questions*100:.1f}%)")
    print()
    print("Total Agreement:")
    total_agreement = unanimous_correct + unanimous_wrong
    print(f"  3/3 Agreement: {total_agreement} ({total_agreement/n_questions*100:.1f}%)")
    print()

    # Cost-benefit analysis
    print("=" * 60)
    print("COST-BENEFIT ANALYSIS")
    print("=" * 60)
    print()
    print(f"Running 3 instances costs 3x the computational resources.")
    print(f"  Single run: ~{mean_individual:.2f}% accuracy")
    print(f"  Majority voting (3 runs): {majority_accuracy:.2f}% accuracy")
    print(f"  Accuracy gain: {majority_accuracy - mean_individual:+.2f} percentage points")
    print(f"  Cost multiplier: 3x")
    print(f"  Questions improved: {majority_vote_correct - int(mean_individual * n_questions / 100)}")
    print()
    if majority_accuracy > mean_individual:
        print(f"Conclusion: Majority voting {'provides' if majority_accuracy - mean_individual > 0.5 else 'provides modest'} improvement.")
    else:
        print("Conclusion: Majority voting does not improve over single runs.")
    print()

    # Questions where majority helped
    print("=" * 60)
    print("QUESTIONS WHERE MAJORITY VOTING HELPED")
    print("=" * 60)
    print()
    print("2/3 Majority Correct (majority vote rescued the answer):")
    print(f"  Total: {len(questions_by_agreement['2/3_correct'])} questions")
    if questions_by_agreement['2/3_correct']:
        print("  Examples (first 10):")
        for q in questions_by_agreement['2/3_correct'][:10]:
            print(f"    Question {q['id']}: Majority voted {q['answer']} (correct: {q['correct']}), votes: {q['votes']}")
    print()

    # Questions where all 3 runs were wrong
    print("=" * 60)
    print("CHALLENGING QUESTIONS (All 3 Runs Wrong)")
    print("=" * 60)
    print()
    print(f"Questions where all 3 runs agreed but were wrong: {unanimous_wrong}")
    if questions_by_agreement['3/3_wrong']:
        print("  Examples (first 20):")
        for q in questions_by_agreement['3/3_wrong'][:20]:
            print(f"    Question {q['id']}: All voted {q['answer']}, correct: {q['correct']}")
    print()

    # Questions with no majority
    if no_majority > 0:
        print("=" * 60)
        print("QUESTIONS WITH NO MAJORITY (All 3 Disagree)")
        print("=" * 60)
        print()
        print(f"Total: {no_majority} questions")
        print("  Examples:")
        for q in questions_by_agreement['no_majority'][:10]:
            print(f"    Question {q['id']}: Votes {q['votes']}, correct: {q['correct']}")
        print()

    # Save detailed results
    output = {
        'summary': {
            'n_questions': n_questions,
            'individual_accuracies': individual_accuracies,
            'mean_individual_accuracy': mean_individual,
            'majority_voting_accuracy': majority_accuracy,
            'improvement': majority_accuracy - mean_individual,
            'unanimous_correct': unanimous_correct,
            'unanimous_wrong': unanimous_wrong,
            'majority_correct': majority_correct,
            'majority_wrong': majority_wrong,
            'no_majority': no_majority
        },
        'questions_by_agreement': questions_by_agreement
    }

    output_file = Path("runs/majority_voting_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"Detailed results saved to: {output_file}")

if __name__ == "__main__":
    analyze_majority_voting()
