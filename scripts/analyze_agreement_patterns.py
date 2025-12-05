#!/usr/bin/env python3
"""
Deep dive into agreement patterns in Sequential Specialist Debate.
Investigates whether forcing agreement between generalist and specialists hurts performance.
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_agreement_patterns(results_path: str):
    """Analyze debate rounds and agreement patterns."""

    with open(results_path, 'r') as f:
        results = json.load(f)

    print("=" * 80)
    print("AGREEMENT PATTERN ANALYSIS")
    print("=" * 80)
    print()

    # Track agreement metrics
    consultation_data = []

    for r in results:
        if 'error' in r or 'full_result' not in r:
            continue

        question_idx = r['question_idx']
        is_correct = r.get('is_correct', False)
        consultation_history = r['full_result'].get('consultation_history', [])

        # Extract debate consultations
        for item in consultation_history:
            if item.get('stage', '').startswith('consultation_'):
                specialist = item.get('specialist', 'Unknown')
                specialist_id = item.get('specialist_id', 'unknown')
                debate_rounds = item.get('debate_rounds', [])
                total_rounds = item.get('total_rounds', 0)

                # Analyze the debate
                consultation_data.append({
                    'question_idx': question_idx,
                    'is_correct': is_correct,
                    'specialist': specialist,
                    'specialist_id': specialist_id,
                    'total_rounds': total_rounds,
                    'debate_rounds': debate_rounds
                })

    # Group by number of rounds
    print("AGREEMENT SPEED vs ACCURACY")
    print("=" * 80)

    rounds_to_accuracy = defaultdict(lambda: {'correct': 0, 'total': 0})

    for c in consultation_data:
        rounds = c['total_rounds']
        rounds_to_accuracy[rounds]['total'] += 1
        if c['is_correct']:
            rounds_to_accuracy[rounds]['correct'] += 1

    print(f"{'Rounds':>8} {'Consultations':>15} {'Correct':>10} {'Accuracy':>10}")
    print("-" * 50)

    for rounds in sorted(rounds_to_accuracy.keys()):
        data = rounds_to_accuracy[rounds]
        accuracy = data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"{rounds:>8} {data['total']:>15} {data['correct']:>10} {accuracy:>9.1f}%")

    print()

    # Analyze first specialist vs second specialist
    print("FIRST vs SECOND SPECIALIST CONSULTATION")
    print("=" * 80)

    first_specialist_data = [c for c in consultation_data if '_1' in c['debate_rounds'][0].get('speaker', '') or c['debate_rounds'][0].get('round') == 1]
    second_specialist_data = [c for c in consultation_data if c not in first_specialist_data]

    # Actually, let's group by consultation number differently
    # Each question should have 2 consultations
    consultations_by_question = defaultdict(list)
    for c in consultation_data:
        consultations_by_question[c['question_idx']].append(c)

    first_consultant_correct = 0
    first_consultant_total = 0
    second_consultant_correct = 0
    second_consultant_total = 0

    for q_idx, consultations in consultations_by_question.items():
        if len(consultations) >= 1:
            first_consultant_total += 1
            if consultations[0]['is_correct']:
                first_consultant_correct += 1

        if len(consultations) >= 2:
            second_consultant_total += 1
            if consultations[1]['is_correct']:
                second_consultant_correct += 1

    print(f"After 1st Specialist: {first_consultant_correct}/{first_consultant_total} = {first_consultant_correct/first_consultant_total*100 if first_consultant_total > 0 else 0:.1f}%")
    print(f"After 2nd Specialist: {second_consultant_correct}/{second_consultant_total} = {second_consultant_correct/second_consultant_total*100 if second_consultant_total > 0 else 0:.1f}%")
    print()

    # Look at specific cases where consultation was short (potential quick bad agreement)
    print("SHORT CONSULTATIONS (3 rounds or fewer)")
    print("=" * 80)

    short_consultations = [c for c in consultation_data if c['total_rounds'] <= 3]
    short_correct = sum(1 for c in short_consultations if c['is_correct'])
    short_total = len(short_consultations)

    print(f"Total: {short_correct}/{short_total} = {short_correct/short_total*100 if short_total > 0 else 0:.1f}%")
    print()

    # Sample a few debate transcripts
    print("SAMPLE DEBATE TRANSCRIPTS")
    print("=" * 80)
    print()

    # Find an incorrect case with quick agreement
    for r in results:
        if r.get('is_correct') or 'full_result' not in r:
            continue

        consultation_history = r['full_result'].get('consultation_history', [])

        for item in consultation_history:
            if item.get('stage', '').startswith('consultation_'):
                total_rounds = item.get('total_rounds', 0)
                if total_rounds <= 4:  # Quick agreement
                    print(f"Question {r['question_idx']} - INCORRECT with quick agreement")
                    print(f"Predicted: {r['predicted']}, Correct: {r['correct']}")
                    print(f"Specialist: {item.get('specialist', 'Unknown')}")
                    print(f"Total Rounds: {total_rounds}")
                    print()

                    debate_rounds = item.get('debate_rounds', [])
                    for round_info in debate_rounds[:4]:  # Show first 4 rounds
                        speaker = round_info.get('speaker', 'Unknown')
                        content = round_info.get('content', '')[:300]  # First 300 chars
                        print(f"[{speaker}]")
                        print(content)
                        print("...")
                        print()

                    print("-" * 80)
                    print()
                    break  # Only show one consultation per question

        if len([None for item in consultation_history if item.get('stage', '').startswith('consultation_') and item.get('total_rounds', 0) <= 4]) > 0:
            break  # Only show first matching question

    print()

    # Compare to a correct case with long debate
    print("COMPARISON: CORRECT CASE WITH LONGER DEBATE")
    print("=" * 80)
    print()

    for r in results:
        if not r.get('is_correct') or 'full_result' not in r:
            continue

        consultation_history = r['full_result'].get('consultation_history', [])

        for item in consultation_history:
            if item.get('stage', '').startswith('consultation_'):
                total_rounds = item.get('total_rounds', 0)
                if total_rounds >= 5:  # Longer debate
                    print(f"Question {r['question_idx']} - CORRECT with longer debate")
                    print(f"Predicted: {r['predicted']}, Correct: {r['correct']}")
                    print(f"Specialist: {item.get('specialist', 'Unknown')}")
                    print(f"Total Rounds: {total_rounds}")
                    print()

                    debate_rounds = item.get('debate_rounds', [])
                    for round_info in debate_rounds[:4]:  # Show first 4 rounds
                        speaker = round_info.get('speaker', 'Unknown')
                        content = round_info.get('content', '')[:300]  # First 300 chars
                        print(f"[{speaker}]")
                        print(content)
                        print("...")
                        print()

                    print("-" * 80)
                    print()
                    break

        if len([None for item in consultation_history if item.get('stage', '').startswith('consultation_') and item.get('total_rounds', 0) >= 5]) > 0:
            break

    print()


if __name__ == "__main__":
    results_path = Path("runs/sequential_debate/20251112_000220/results.json")
    analyze_agreement_patterns(results_path)
