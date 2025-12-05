"""
Baseline 2: Fixed Four-Agent Pipeline
Fixed architecture: Planner → Specialist → Reviewer → Aggregator
No dynamic selection, always same 4 agents.
"""

import json
import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient


def run_fixed_pipeline(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Fixed 4-agent pipeline baseline.
    Always: Planner → Specialist → Reviewer → Aggregator
    No adaptive selection.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, reasoning, tokens, latency
    """

    options_str = "\n".join(options) if options else "No options"

    total_tokens = 0
    total_latency = 0.0
    traces = []

    # Agent 1: Planner (general assessment)
    planner_prompt = f"""You are a Clinical Planner. Provide an initial assessment of this case.

**Question:** {question}

**Options:** {options_str}

**Your Task:**
1. Identify key clinical features
2. List initial diagnostic hypotheses
3. Note critical information needed

Output your assessment in a structured format.
"""

    planner_response = llm_client.complete(planner_prompt)
    total_tokens += planner_response.tokens_used or 0
    total_latency += planner_response.latency_seconds
    traces.append({"agent": "planner", "output": planner_response.content})

    # Agent 2: Specialist (fixed to Internal Medicine)
    specialist_prompt = f"""You are an Internal Medicine Specialist. Review this case and provide your expert opinion.

**Question:** {question}

**Planner's Assessment:**
{planner_response.content}

**Your Task:**
Provide a differential diagnosis with:
- Top 3 most likely diagnoses
- Probability for each (0-1)
- Evidence supporting and against each

Format as a structured list.
"""

    specialist_response = llm_client.complete(specialist_prompt)
    total_tokens += specialist_response.tokens_used or 0
    total_latency += specialist_response.latency_seconds
    traces.append({"agent": "specialist", "output": specialist_response.content})

    # Agent 3: Reviewer (critique)
    reviewer_prompt = f"""You are a Clinical Reviewer. Critique the diagnostic reasoning provided.

**Question:** {question}

**Specialist's Analysis:**
{specialist_response.content}

**Your Task:**
Identify:
- Strengths of the analysis
- Weaknesses or gaps in reasoning
- Alternative considerations not mentioned
- Key tests or findings needed

Provide constructive critique.
"""

    reviewer_response = llm_client.complete(reviewer_prompt)
    total_tokens += reviewer_response.tokens_used or 0
    total_latency += reviewer_response.latency_seconds
    traces.append({"agent": "reviewer", "output": reviewer_response.content})

    # Agent 4: Aggregator (final decision)
    aggregator_prompt = f"""You are the Final Decision Maker. Synthesize all input and provide the final answer.

**Question:** {question}

**Options:** {options_str}

**Specialist Analysis:**
{specialist_response.content}

**Reviewer Critique:**
{reviewer_response.content}

**Your Task:**
Based on all the input, select the most likely answer and provide clear justification.

**Output Format:**
ANSWER: [A, B, C, or D]
JUSTIFICATION: [Your reasoning for this choice]
"""

    aggregator_response = llm_client.complete(aggregator_prompt)
    total_tokens += aggregator_response.tokens_used or 0
    total_latency += aggregator_response.latency_seconds
    traces.append({"agent": "aggregator", "output": aggregator_response.content})

    # Parse final answer
    answer = _extract_answer(aggregator_response.content, options)

    return {
        "method": "fixed_pipeline",
        "answer": answer,
        "agents_used": 4,
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "traces": traces,
        "full_response": aggregator_response.content
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract the final answer from aggregator response."""
    # Look for "ANSWER:" line
    lines = text.split('\n')
    for line in lines:
        if line.upper().startswith('ANSWER:'):
            answer = line.split(':', 1)[1].strip()
            answer = answer.strip('*').strip()
            match = re.search(r'\b([A-D])\b', answer)
            if match:
                return match.group(1)
            return answer

    # Fallback
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1)

    return "UNKNOWN"
