#!/usr/bin/env python3
"""Test Adaptive MAS system only"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.llm_client import create_llm_client
from src.orchestration import run_case

print("Testing Adaptive MAS System")
print("=" * 60)

# Load config
config = Config.from_yaml("configs/llama3_70b.yaml")
print(f"Config: {config.model} (timeout: {config.budgets.timeout_seconds}s)")

# Create client
client = create_llm_client(config)
print("Client created")

# Simple test question
question = "A 65-year-old man presents with chest pain radiating to left arm. What is the most likely diagnosis?"
options = ["A. GERD", "B. Acute MI", "C. PE", "D. MSK pain"]
correct = "B"

print()
print("Running Adaptive MAS...")
print(f"Question: {question}")
print()

try:
    final_decision, trace = run_case(
        question=question,
        options=options,
        correct_answer=correct,
        llm_client=client,
        config=config
    )

    print(f"[OK] Final answer: {final_decision.final_answer}")
    print(f"     Latency: {trace.total_latency_seconds:.1f}s")
    print(f"     Specialists: {len(trace.specialist_traces)}")
    print()
    print("SUCCESS!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
