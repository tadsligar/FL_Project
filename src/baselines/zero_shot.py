"""
Zero-Shot Baseline

The ACTUAL baseline: just question + options, no prompting, no CoT, no debate.
This tells us the raw model capability on MedQA without any intervention.
"""

from typing import Optional
import re

from ..config import Config
from ..llm_client import LLMClient


def run_zero_shot(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Zero-shot baseline - just ask the question with no guidance.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, tokens, latency
    """

    options_str = "\n".join(options) if options else "No options"

    # Minimal prompt - just question and options
    prompt = f"""{question}

{options_str}

What is the answer?"""

    response = llm_client.complete(prompt)

    # Extract answer
    answer = _extract_answer(response.content, options)

    return {
        "method": "zero_shot",
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
