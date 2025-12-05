"""
Baseline 1: Single-LLM Chain-of-Thought
Standard single-model reasoning with step-by-step thinking.
"""

import json
import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient, LLMResponse


def run_single_llm_cot(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Single-LLM Chain-of-Thought baseline.
    No agents, just one call with CoT prompting.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, reasoning, tokens, latency
    """

    # Format options
    options_str = ""
    if options:
        options_str = "\n".join(options)
    else:
        options_str = "No multiple choice options provided."

    # Chain-of-Thought prompt
    prompt = f"""You are a clinical reasoning expert. Analyze this medical case using step-by-step reasoning.

**Question:**
{question}

**Options:**
{options_str}

**Instructions:**
Think through this systematically:
1. Identify key clinical features (symptoms, signs, demographics)
2. Generate a differential diagnosis (list possible conditions)
3. Evaluate each diagnosis against the evidence (what supports it? what argues against it?)
4. Select the most likely answer based on your reasoning

Provide your reasoning step-by-step, then give your final answer.

**Format your response as:**

REASONING:
[Your detailed step-by-step clinical analysis]

ANSWER: [A, B, C, D, or the diagnosis name]
"""

    # Call LLM
    response = llm_client.complete(prompt)

    # Parse answer
    answer = _extract_answer(response.content, options)

    return {
        "method": "single_llm_cot",
        "answer": answer,
        "reasoning": response.content,
        "tokens_used": response.tokens_used,
        "latency_seconds": response.latency_seconds,
        "full_response": response.content
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract the final answer from LLM response."""
    # Look for "ANSWER:" line
    lines = text.split('\n')
    for line in lines:
        if line.upper().startswith('ANSWER:'):
            answer = line.split(':', 1)[1].strip()
            # Clean up answer
            answer = answer.strip('*').strip()
            # Extract just the letter if it's there
            match = re.search(r'\b([A-D])\b', answer)
            if match:
                return match.group(1)
            return answer

    # Fallback: search for A, B, C, D in the text
    if options:
        for letter in ['A', 'B', 'C', 'D']:
            if f'**{letter}' in text or f'Answer: {letter}' in text or f'answer is {letter}' in text.lower():
                return letter

    # Last resort: return first letter found
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1)

    return "UNKNOWN"
