"""
Single-Shot Chain-of-Thought Baseline

Test if structured reasoning helps WITHOUT multi-agent debate.
This fills the gap between zero-shot (54%) and debate (71-75%).

If single-shot CoT performs well, it suggests the benefit comes from
structured reasoning rather than adversarial interaction.
"""

from typing import Optional
import re

from ..config import Config
from ..llm_client import LLMClient


def run_single_shot_cot(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Single-shot CoT - one agent with explicit step-by-step reasoning.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, tokens, latency
    """

    options_str = "\n".join(options) if options else "No options"

    # Structured CoT prompt - similar to what we use in debate Round 1
    prompt = f"""Analyze this medical case using step-by-step reasoning.

{question}

{options_str}

**Think through this systematically:**

1. **Identify Key Clinical Features**
   - What are the critical symptoms and signs?
   - What demographic factors are relevant?
   - What is the timeline of the presentation?

2. **Generate Differential Diagnosis**
   - List 2-3 possible conditions
   - For each, note what clinical features support it

3. **Evaluate Each Option**
   - What argues FOR each option?
   - What argues AGAINST each option?
   - What is the most likely diagnosis?

4. **Select Your Answer**
   - State your final answer clearly

Provide your analysis and final answer (A, B, C, or D)."""

    response = llm_client.complete(prompt)

    # Extract answer
    answer = _extract_answer(response.content, options)

    return {
        "method": "single_shot_cot",
        "answer": answer,
        "tokens_used": response.tokens_used or 0,
        "latency_seconds": response.latency_seconds,
        "full_response": response.content
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract answer from response."""
    # Look for explicit "Answer:" or "Final answer:" statements
    match = re.search(r'(?:answer|final answer)[:\s]+([A-D])', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Look for single letter near end of text (likely the final answer)
    last_500_chars = text[-500:]
    match = re.search(r'\b([A-D])\b', last_500_chars)
    if match:
        return match.group(1).upper()

    # Fallback: any letter A-D in the text
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1).upper()

    return "UNKNOWN"
