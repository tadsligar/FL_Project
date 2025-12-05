#!/usr/bin/env python3
"""
Export traces to various formats for analysis.
"""

import argparse
import json
from pathlib import Path
from typing import Optional


def load_traces(traces_dir: Path) -> list[dict]:
    """Load all trace JSONL files from directory."""
    traces = []

    for trace_file in traces_dir.rglob("*.jsonl"):
        try:
            with open(trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        traces.append(json.loads(line))
        except Exception as e:
            print(f"Error loading {trace_file}: {e}")

    return traces


def export_to_csv(traces: list[dict], output_path: Path):
    """Export traces to CSV format."""
    import csv

    if not traces:
        print("No traces to export")
        return

    # Extract key fields
    rows = []
    for trace in traces:
        row = {
            "trace_id": trace.get("trace_id"),
            "question": trace.get("question", "")[:100],  # Truncate
            "predicted_answer": trace.get("predicted_answer"),
            "correct_answer": trace.get("correct_answer"),
            "is_correct": trace.get("is_correct"),
            "total_latency_seconds": trace.get("total_latency_seconds"),
            "total_tokens": trace.get("total_tokens"),
            "n_specialists": len(trace.get("specialist_traces", [])),
        }
        rows.append(row)

    # Write CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Exported {len(rows)} traces to {output_path}")


def export_summary(traces: list[dict], output_path: Path):
    """Export summary statistics."""
    if not traces:
        print("No traces to summarize")
        return

    total = len(traces)
    correct = sum(1 for t in traces if t.get("is_correct"))
    accuracy = correct / total if total > 0 else 0.0

    latencies = [t.get("total_latency_seconds", 0) for t in traces]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    tokens = [t.get("total_tokens", 0) for t in traces if t.get("total_tokens")]
    avg_tokens = sum(tokens) / len(tokens) if tokens else None

    summary = {
        "total_cases": total,
        "correct": correct,
        "accuracy": accuracy,
        "avg_latency_seconds": avg_latency,
        "avg_tokens": avg_tokens,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary exported to {output_path}")
    print(f"  Accuracy: {accuracy:.2%} ({correct}/{total})")
    print(f"  Avg Latency: {avg_latency:.2f}s")
    if avg_tokens:
        print(f"  Avg Tokens: {avg_tokens:.0f}")


def main():
    parser = argparse.ArgumentParser(description="Export trace files to various formats")
    parser.add_argument(
        "traces_dir",
        type=Path,
        help="Directory containing trace JSONL files"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Export to CSV file"
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Export summary JSON"
    )

    args = parser.parse_args()

    if not args.traces_dir.exists():
        print(f"Error: {args.traces_dir} does not exist")
        return

    print(f"Loading traces from {args.traces_dir}...")
    traces = load_traces(args.traces_dir)
    print(f"Loaded {len(traces)} traces")

    if args.csv:
        export_to_csv(traces, args.csv)

    if args.summary:
        export_summary(traces, args.summary)

    if not args.csv and not args.summary:
        print("No export format specified. Use --csv or --summary")


if __name__ == "__main__":
    main()
