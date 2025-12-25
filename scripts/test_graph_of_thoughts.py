"""
Test Graph of Thoughts on MedQA dataset
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.llm_client import create_llm_client
from src.medqa import load_medqa_subset
from src.baselines.graph_of_thoughts import run_graph_of_thoughts


def test_graph_of_thoughts(n_questions: int, config_path: str, output_dir: str = None, resume_from: str = None):
    """Test Graph of Thoughts on MedQA"""

    print("=" * 60)
    print("Graph of Thoughts - Medical QA Test")
    print("=" * 60)
    print()

    # Load config
    print("Loading configuration...")
    config = Config.from_yaml(config_path)
    print(f"  Model: {config.model}")
    print(f"  Provider: {config.provider}")
    print()

    # Load dataset
    print(f"Loading MedQA dataset ({n_questions} questions)...")
    questions = load_medqa_subset(path="data/medqa_us_test_4opt.json", n=n_questions)
    print(f"  Loaded {len(questions)} questions")
    print()

    # Initialize LLM
    print("Initializing LLM client...")
    llm_client = create_llm_client(config)
    print("  [OK] Client ready")
    print()

    # Setup output (or use resume path)
    if resume_from:
        output_path = Path(resume_from)
        if not output_path.exists():
            print(f"ERROR: Resume path not found: {resume_from}")
            return
        print(f"Resuming from: {output_path}")
    else:
        if output_dir is None:
            output_dir = f"runs/graph_of_thoughts/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_path}")
    print()

    # Results storage
    results = []
    correct_count = 0
    checkpoint_file = output_path / "checkpoint.json"

    # Try to load from checkpoint if it exists
    start_idx = 0
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r") as f:
                results = json.load(f)
                start_idx = len(results)
                correct_count = sum(1 for r in results if r.get('is_correct', False))
                print(f"Resuming from checkpoint: {start_idx}/{len(questions)} questions completed")
                print(f"Current accuracy: {correct_count}/{start_idx} = {correct_count/start_idx*100:.1f}%")
                print()
        except Exception as e:
            print(f"Could not load checkpoint: {e}. Starting fresh.")
            print()

    # Run evaluation
    print("Running Graph of Thoughts evaluation...")
    print()

    for i, q in enumerate(tqdm(questions, desc="Evaluating")):
        # Skip already processed questions
        if i < start_idx:
            continue

        question_text = q['question']
        options = q['options']
        correct_answer = q['answer']

        try:
            # Run Graph of Thoughts
            result = run_graph_of_thoughts(
                question=question_text,
                options=options,
                llm_client=llm_client,
                config=config
            )

            predicted = result['answer']
            is_correct = (predicted == correct_answer)
            if is_correct:
                correct_count += 1

            # Store result
            results.append({
                'question_idx': i,
                'question': question_text,
                'options': options,
                'correct': correct_answer,
                'predicted': predicted,
                'is_correct': is_correct,
                'reasoning': result['reasoning'],
                'tokens': result['tokens_used'],
                'latency': result['latency_seconds'],
                'graph': result['graph'],
                'graph_summary': result['graph_summary']
            })

            # Print progress
            status = "[OK]" if is_correct else "[X]"
            print(f"\nQuestion {i+1}/{len(questions)}")
            print(f"Correct Answer: {correct_answer}")
            print(f"  {status} Predicted: {predicted} ({result['latency_seconds']:.1f}s, {result['tokens_used']} tokens)")
            print(f"  Graph: {result['graph_summary']['num_nodes']} nodes, {result['graph_summary']['num_edges']} edges")

            # Save checkpoint every 10 questions
            if (i + 1) % 10 == 0:
                checkpoint_file = output_path / "checkpoint.json"
                with open(checkpoint_file, 'w') as f:
                    json.dump(results, f, indent=2)

        except Exception as e:
            print(f"\n  ERROR on question {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Calculate statistics
    accuracy = correct_count / len(results) if results else 0
    avg_tokens = sum(r['tokens'] for r in results) / len(results) if results else 0
    avg_latency = sum(r['latency'] for r in results) / len(results) if results else 0
    avg_nodes = sum(r['graph_summary']['num_nodes'] for r in results) / len(results) if results else 0
    avg_edges = sum(r['graph_summary']['num_edges'] for r in results) / len(results) if results else 0

    # Print summary
    print()
    print("=" * 60)
    print("Results Summary")
    print("=" * 60)
    print()
    print(f"Accuracy: {correct_count}/{len(results)} = {accuracy*100:.1f}%")
    print(f"Avg Latency: {avg_latency:.1f}s")
    print(f"Avg Tokens: {avg_tokens:.0f}")
    print(f"Avg Graph Size: {avg_nodes:.1f} nodes, {avg_edges:.1f} edges")
    print()

    # Save results
    results_file = output_path / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    summary_file = output_path / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'accuracy': accuracy,
            'correct': correct_count,
            'total': len(results),
            'avg_tokens': avg_tokens,
            'avg_latency': avg_latency,
            'avg_nodes': avg_nodes,
            'avg_edges': avg_edges
        }, f, indent=2)

    print(f"Results saved to: {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Test Graph of Thoughts on MedQA')
    parser.add_argument('--n', type=int, default=10,
                       help='Number of questions to evaluate')
    parser.add_argument('--config', type=str, default='configs/qwen25_32b.yaml',
                       help='Path to config file')
    parser.add_argument('--output', type=str, default=None,
                       help='Output directory')
    parser.add_argument('--resume', type=str, default=None,
                       help='Resume from checkpoint directory')

    args = parser.parse_args()

    test_graph_of_thoughts(
        n_questions=args.n,
        config_path=args.config,
        output_dir=args.output,
        resume_from=args.resume
    )


if __name__ == "__main__":
    main()
