"""
Independent Confidence-Based Agent Evaluation

Each agent rates their confidence (0-100%) that ONE option is correct.
Winner is highest confidence. Aggregator handles ties.

Similar to independent binary, but uses continuous confidence scores
instead of binary yes/no decisions.
"""

import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient


def run_independent_confidence_agents(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Independent confidence-based agent evaluation.

    Each agent rates confidence (0-100%) that their option is correct.
    Winner: Highest confidence
    Ties: Aggregator decides

    Args:
        question: Clinical question
        options: Multiple choice options (A, B, C, D)
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, reasoning, tokens, latency
    """

    if not options or len(options) != 4:
        raise ValueError("Expected exactly 4 options (A, B, C, D)")

    total_tokens = 0
    total_latency = 0.0
    agent_evaluations = []

    option_labels = ['A', 'B', 'C', 'D']

    # Each agent evaluates their assigned option in isolation
    for i, (label, option_text) in enumerate(zip(option_labels, options)):

        agent_prompt = f"""You are an experienced physician evaluating a clinical case.

**Your Task:**
Rate your confidence (0-100%) that the following option is the CORRECT answer.

**Question:** {question}

**Option to Evaluate:** {label}. {option_text}

**IMPORTANT:** You are ONLY evaluating this single option. Do NOT see or consider other options.

**Confidence Scale:**
- 90-100%: Very high confidence, strong evidence supports this answer
- 70-89%: High confidence, good evidence
- 50-69%: Moderate confidence, reasonable but some uncertainty
- 30-49%: Low confidence, weak evidence or alternatives likely
- 0-29%: Very low confidence, this is likely NOT the answer

**Your Response Must Include:**

1. **CONFIDENCE:** A number between 0-100
2. **REASONING:** Explain your clinical reasoning and what evidence supports/opposes this option

**Output Format:**
CONFIDENCE: [0-100]
REASONING: [Your detailed clinical reasoning]
"""

        response = llm_client.complete(agent_prompt)
        total_tokens += response.tokens_used or 0
        total_latency += response.latency_seconds

        # Parse response
        confidence = _extract_confidence(response.content)

        agent_evaluations.append({
            "option": label,
            "option_text": option_text,
            "confidence": confidence,
            "full_response": response.content
        })

    # Find maximum confidence
    max_confidence = max(eval["confidence"] for eval in agent_evaluations)
    top_candidates = [eval for eval in agent_evaluations if eval["confidence"] == max_confidence]

    if len(top_candidates) == 1:
        # Single winner
        final_answer = top_candidates[0]["option"]
        aggregation_needed = False
        aggregator_reasoning = f"Option {final_answer} has highest confidence: {max_confidence}%"

    else:
        # Tie - aggregator decides
        aggregation_needed = True
        tied_options = [eval["option"] for eval in top_candidates]

        aggregator_prompt = f"""You are an experienced physician making a final decision.

**Question:** {question}

**Multiple options tied with {max_confidence}% confidence:**

{_format_tied_evaluations(top_candidates)}

**Your Task:**
Select the BEST answer from the tied options: {', '.join(tied_options)}

**Output Format:**
ANSWER: [Single letter from {', '.join(tied_options)}]
JUSTIFICATION: [Brief explanation of why this is the best answer]
"""

        aggregator_response = llm_client.complete(aggregator_prompt)
        total_tokens += aggregator_response.tokens_used or 0
        total_latency += aggregator_response.latency_seconds

        final_answer = _extract_answer(aggregator_response.content, tied_options)
        aggregator_reasoning = aggregator_response.content

    return {
        "method": "independent_confidence_agents",
        "answer": final_answer,
        "agents_used": len(options) + (1 if aggregation_needed else 0),
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "agent_evaluations": agent_evaluations,
        "max_confidence": max_confidence,
        "aggregation_needed": aggregation_needed,
        "aggregator_reasoning": aggregator_reasoning if aggregation_needed else None
    }


def _extract_confidence(text: str) -> int:
    """Extract confidence score from agent response."""
    lines = text.split('\n')
    for line in lines:
        if line.upper().startswith('CONFIDENCE:'):
            confidence_str = line.split(':', 1)[1].strip()
            # Extract number
            match = re.search(r'(\d+)', confidence_str)
            if match:
                conf = int(match.group(1))
                # Clamp to 0-100
                return max(0, min(100, conf))

    # Fallback: search for percentage in entire text
    matches = re.findall(r'(\d+)%', text)
    if matches:
        conf = int(matches[0])
        return max(0, min(100, conf))

    # Default: 50% if unable to parse
    return 50


def _extract_answer(text: str, valid_options: list[str]) -> str:
    """Extract final answer from aggregator response."""
    lines = text.split('\n')
    for line in lines:
        if line.upper().startswith('ANSWER:'):
            answer = line.split(':', 1)[1].strip()
            answer = answer.strip('*').strip()
            # Try to find a valid option letter
            for opt in valid_options:
                if opt in answer.upper():
                    return opt

    # Fallback: search for any valid option
    for opt in valid_options:
        if re.search(rf'\b{opt}\b', text):
            return opt

    return "UNKNOWN"


def _format_tied_evaluations(evaluations: list[dict]) -> str:
    """Format tied evaluations for aggregator."""
    formatted = []
    for eval in evaluations:
        formatted.append(f"- Option {eval['option']}: {eval['option_text']}")
        formatted.append(f"  Confidence: {eval['confidence']}%")
        formatted.append(f"  Reasoning: {eval['full_response'][:200]}...")
    return '\n'.join(formatted)
