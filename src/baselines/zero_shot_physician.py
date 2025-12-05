"""
Zero-Shot Physician Baseline

Same as zero-shot, but with "You are an experienced physician." prefix.
This tests if simple role assignment improves performance.
"""

from typing import Optional
import re

from ..config import Config
from ..llm_client import LLMClient


def run_zero_shot_physician(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Zero-shot with physician role - minimal role prompting.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, tokens, latency
    """

    options_str = "\n".join(options) if options else "No options"

    # Add physician role prefix to zero-shot prompt
    prompt = f"""You are an experienced physician.

{question}

{options_str}

What is the answer?"""

    response = llm_client.complete(prompt)

    # Extract answer
    answer = _extract_answer(response.content, options)

    return {
        "method": "zero_shot_physician",
        "answer": answer,
        "tokens_used": response.tokens_used or 0,
        "latency_seconds": response.latency_seconds,
        "full_response": response.content
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract answer from response."""
    # Look for single letter
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1)

    return "UNKNOWN"
