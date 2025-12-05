"""
MedQA dataset integration and evaluation harness.
Loads MedQA-USMLE questions and evaluates the system.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config, get_config
from .llm_client import create_llm_client
from .logging_utils import save_trace
from .orchestration import run_case
from .schemas import EvaluationResult, CaseTrace


# Mock MedQA sample for testing when real data not available
MOCK_MEDQA_SAMPLE = [
    {
        "question": "A 65-year-old man presents with sudden onset chest pain radiating to the left arm, diaphoresis, and nausea. Pain started 30 minutes ago. Which of the following is the most likely diagnosis?",
        "options": ["A. GERD", "B. Acute Myocardial Infarction", "C. Pulmonary Embolism", "D. Musculoskeletal pain"],
        "answer": "B"
    },
    {
        "question": "A 3-year-old boy is brought to the emergency department with a barking cough, stridor, and fever. His mother reports symptoms started 2 days ago. What is the most likely diagnosis?",
        "options": ["A. Epiglottitis", "B. Croup", "C. Asthma", "D. Foreign body aspiration"],
        "answer": "B"
    },
    {
        "question": "A 45-year-old woman presents with fatigue, weight gain, and cold intolerance over the past 6 months. Physical exam reveals dry skin and delayed relaxation phase of deep tendon reflexes. What is the most likely diagnosis?",
        "options": ["A. Hyperthyroidism", "B. Hypothyroidism", "C. Cushing syndrome", "D. Addison disease"],
        "answer": "B"
    },
]


def load_medqa_subset(
    path: Optional[str | Path] = None,
    n: int = 100,
    seed: int = 42,
    shuffle: bool = True
) -> list[dict]:
    """
    Load a subset of MedQA questions.

    Args:
        path: Path to MedQA JSON file (uses mock data if not provided)
        n: Number of samples to load
        seed: Random seed for reproducibility
        shuffle: Whether to shuffle before sampling

    Returns:
        List of question dicts with keys: question, options, answer
    """
    if path is None or not Path(path).exists():
        print(f"Warning: MedQA file not found at {path}, using mock data")
        data = MOCK_MEDQA_SAMPLE.copy()
    else:
        path_str = str(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()

                # Check if file contains error message
                if "404" in content or "Not Found" in content or len(content) < 100:
                    print(f"Warning: MedQA file appears invalid (contains error or too small), using mock data")
                    data = MOCK_MEDQA_SAMPLE.copy()
                # Try parsing as JSON array first
                elif content.startswith('['):
                    data = json.loads(content)
                # Try parsing as JSONL (one JSON per line)
                else:
                    lines = content.split('\n')
                    data = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                data.append(json.loads(line))
                            except json.JSONDecodeError:
                                # Skip invalid lines
                                continue

                    if not data:
                        print(f"Warning: No valid JSON found in {path}, using mock data")
                        data = MOCK_MEDQA_SAMPLE.copy()
        except Exception as e:
            print(f"Warning: Error loading MedQA file: {e}, using mock data")
            data = MOCK_MEDQA_SAMPLE.copy()

    if shuffle:
        random.seed(seed)
        random.shuffle(data)

    return data[:n]


def parse_medqa_item(item: dict) -> tuple[str, list[str], str]:
    """
    Parse a MedQA item into components.

    Args:
        item: MedQA dict

    Returns:
        (question, options, answer) tuple
    """
    question = item.get("question", "")
    options = item.get("options", [])
    answer = item.get("answer", "")

    return question, options, answer


def evaluate_on_subset(
    n: int = 100,
    config_path: Optional[str | Path] = None,
    dataset_path: Optional[str | Path] = None,
    seed: int = 42
) -> EvaluationResult:
    """
    Evaluate the system on a subset of MedQA.

    Args:
        n: Number of samples to evaluate
        config_path: Path to config YAML (optional)
        dataset_path: Path to MedQA dataset (optional)
        seed: Random seed

    Returns:
        EvaluationResult with metrics
    """
    # Load config
    if config_path:
        config = Config.from_yaml(config_path)
    else:
        config = get_config()

    # Load dataset
    dataset = load_medqa_subset(path=dataset_path, n=n, seed=seed)

    print(f"Evaluating on {len(dataset)} MedQA questions...")

    # Create output directory
    output_dir = Path(config.logging.traces_dir) / "medqa_eval" / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(exist_ok=True, parents=True)

    # Create LLM client
    llm_client = create_llm_client(config)

    # Run evaluation
    results = []
    correct_count = 0
    total_latency = 0.0
    total_tokens = 0

    for i, item in enumerate(dataset, 1):
        question, options, answer = parse_medqa_item(item)

        print(f"[{i}/{len(dataset)}] Processing question...")

        try:
            final_decision, trace = run_case(
                question=question,
                options=options,
                correct_answer=answer,
                config=config,
                llm_client=llm_client
            )

            # Save trace
            trace_path = output_dir / f"{trace.trace_id}.jsonl"
            with open(trace_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(trace.model_dump(), indent=2))

            # Track metrics
            is_correct = trace.is_correct
            if is_correct:
                correct_count += 1

            total_latency += trace.total_latency_seconds
            if trace.total_tokens:
                total_tokens += trace.total_tokens

            results.append({
                "question_idx": i,
                "trace_id": trace.trace_id,
                "predicted": trace.predicted_answer,
                "correct": trace.correct_answer,
                "is_correct": is_correct,
                "latency": trace.total_latency_seconds,
                "tokens": trace.total_tokens
            })

            print(f"  ✓ Predicted: {trace.predicted_answer}, Correct: {trace.correct_answer}, Match: {is_correct}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "question_idx": i,
                "error": str(e)
            })

    # Compute metrics
    n_samples = len(dataset)
    accuracy = correct_count / n_samples if n_samples > 0 else 0.0
    avg_latency = total_latency / n_samples if n_samples > 0 else 0.0
    avg_tokens = total_tokens / n_samples if n_samples > 0 and total_tokens > 0 else None

    # Save results summary
    summary_path = output_dir / "summary.json"
    summary_data = {
        "n_samples": n_samples,
        "n_correct": correct_count,
        "accuracy": accuracy,
        "avg_latency_seconds": avg_latency,
        "avg_tokens_used": avg_tokens,
        "results": results
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dumps(summary_data, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Evaluation Complete!")
    print(f"{'='*60}")
    print(f"Samples:       {n_samples}")
    print(f"Correct:       {correct_count}")
    print(f"Accuracy:      {accuracy:.2%}")
    print(f"Avg Latency:   {avg_latency:.2f}s")
    if avg_tokens:
        print(f"Avg Tokens:    {avg_tokens:.0f}")
    print(f"Traces saved:  {output_dir}")
    print(f"{'='*60}\n")

    return EvaluationResult(
        n_samples=n_samples,
        n_correct=correct_count,
        accuracy=accuracy,
        avg_latency_seconds=avg_latency,
        avg_tokens_used=avg_tokens,
        traces_path=str(output_dir),
        summary=f"Accuracy: {accuracy:.2%} ({correct_count}/{n_samples})"
    )
