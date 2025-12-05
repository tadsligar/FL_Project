"""
Adaptive Triple Specialist Baseline

Two-step approach:
1. LLM selects top 3 specialists needed for the question
2. LLM answers as triple board-certified specialist in those areas

Efficiency: 2 LLM calls per question (vs 7 for physician role debate)
"""

from typing import Optional, List
import re

from ..config import Config
from ..llm_client import LLMClient
from ..catalog import SPECIALTY_CATALOG


def select_specialists(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> List[str]:
    """
    Use LLM to select top 3 specialists for this question.

    Returns:
        List of 3 specialist names
    """

    options_str = "\n".join(options) if options else "No options"

    # Get list of available specialists
    specialist_list = "\n".join([f"- {spec.display_name}"
                                 for spec in SPECIALTY_CATALOG])

    prompt = f"""You are a medical triage expert. Given a clinical question, identify the TOP 3 medical specialties most relevant to answering this question correctly.

Available specialties:
{specialist_list}

Question:
{question}

{options_str}

Respond with ONLY the 3 specialty names, one per line, in order of relevance. Use the exact names from the list above.

Example format:
Cardiology
Pulmonology
Emergency Medicine"""

    response = llm_client.complete(prompt)

    # Parse specialist names
    specialists = []
    lines = response.content.strip().split('\n')

    for line in lines[:3]:  # Take first 3 lines
        line = line.strip()
        # Remove numbers, dots, dashes at start
        line = re.sub(r'^\d+[\.\)\-]\s*', '', line)

        # Match against catalog (case insensitive)
        for spec in SPECIALTY_CATALOG:
            if spec.display_name.lower() in line.lower():
                specialists.append(spec.display_name)
                break

    # Fallback if parsing fails
    if len(specialists) < 3:
        # Use first 3 from catalog as fallback
        fallback = ["Emergency Medicine", "Internal Medicine", "Family Medicine"]
        specialists.extend(fallback[:3 - len(specialists)])

    return specialists[:3]


def run_adaptive_triple_specialist(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Adaptive triple specialist approach:
    1. Select top 3 specialists
    2. Answer as triple board-certified in those areas

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, specialists, tokens, latency
    """

    # Step 1: Select specialists (1st LLM call)
    specialists = select_specialists(question, options, llm_client, config)

    # Step 2: Answer as triple specialist (2nd LLM call)
    options_str = "\n".join(options) if options else "No options"

    specialist_str = ", ".join(specialists)

    prompt = f"""You are a (Triple) board certified {specialist_str}.

{question}

{options_str}

What is the answer?"""

    response = llm_client.complete(prompt)

    # Extract answer
    answer = _extract_answer(response.content, options)

    # Total tokens = selection call + answer call
    total_tokens = llm_client._last_response_tokens if hasattr(llm_client, '_last_response_tokens') else 0

    return {
        "method": "adaptive_triple_specialist",
        "answer": answer,
        "specialists": specialists,
        "tokens_used": total_tokens,
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
