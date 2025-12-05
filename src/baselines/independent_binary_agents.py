"""
Independent Binary Agent Evaluation

Each agent evaluates ONE option in isolation (yes/no).
Aggregator handles ties or all-no scenarios.

Key differences from debate:
- No anchoring: agents don't see other options
- Independent evaluation: no cross-contamination
- Simple voting: no complex synthesis needed
"""

import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient


def run_independent_binary_agents(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Independent binary agent evaluation.

    Each agent evaluates one option independently:
    - "Is option X the correct answer? YES or NO"
    - If NO, agent must propose an alternative

    Aggregator handles:
    - Exactly 1 YES → that's the answer
    - Multiple YES → aggregator picks best
    - All NO → aggregator picks from proposed alternates

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
Evaluate whether the following option is the CORRECT answer to this clinical question.

**Question:** {question}

**Option to Evaluate:** {label}. {option_text}

**IMPORTANT:** You are ONLY evaluating this single option. Do NOT see or consider other options.

**Your Response Must Include:**

1. **DECISION:** Answer YES or NO
   - YES if this option is the correct answer
   - NO if this option is NOT the correct answer

2. **REASONING:** Explain your clinical reasoning (2-3 sentences)

3. **ALTERNATIVE:** If you answered NO, what do you think the correct answer is?
   - Provide your best diagnosis/answer
   - Explain why (1-2 sentences)

**Output Format:**
DECISION: [YES or NO]
REASONING: [Your clinical reasoning for the decision]
ALTERNATIVE: [If NO, state your proposed answer and brief justification. If YES, write "N/A"]
"""

        response = llm_client.complete(agent_prompt)
        total_tokens += response.tokens_used or 0
        total_latency += response.latency_seconds

        # Parse response
        decision = _extract_decision(response.content)
        alternative = _extract_alternative(response.content)

        agent_evaluations.append({
            "option": label,
            "option_text": option_text,
            "decision": decision,
            "alternative": alternative if decision == "NO" else None,
            "full_response": response.content
        })

    # Count YES votes
    yes_votes = [eval for eval in agent_evaluations if eval["decision"] == "YES"]

    # Determine final answer
    if len(yes_votes) == 1:
        # Exactly one YES - that's the answer
        final_answer = yes_votes[0]["option"]
        aggregation_needed = False
        aggregator_reasoning = f"Single YES vote for option {final_answer}"

    elif len(yes_votes) > 1:
        # Multiple YES - aggregator decides
        aggregation_needed = True
        yes_options = [eval["option"] for eval in yes_votes]

        aggregator_prompt = f"""You are an experienced physician making a final decision.

**Question:** {question}

**Multiple agents voted YES for different options:**

{_format_yes_votes(yes_votes)}

**Your Task:**
Select the BEST answer from the options that received YES votes.

**Output Format:**
ANSWER: [Single letter: {', '.join(yes_options)}]
JUSTIFICATION: [Brief explanation of why this is the best answer]
"""

        aggregator_response = llm_client.complete(aggregator_prompt)
        total_tokens += aggregator_response.tokens_used or 0
        total_latency += aggregator_response.latency_seconds

        final_answer = _extract_answer(aggregator_response.content, yes_options)
        aggregator_reasoning = aggregator_response.content

    else:
        # All NO - aggregator picks from alternatives
        aggregation_needed = True
        alternatives = [eval["alternative"] for eval in agent_evaluations if eval["alternative"]]

        aggregator_prompt = f"""You are an experienced physician making a final decision.

**Question:** {question}

**Original Options:**
{_format_options(options)}

**All agents voted NO to their assigned options. Their proposed alternatives:**

{_format_alternatives(agent_evaluations)}

**Your Task:**
Based on the agents' alternative suggestions, provide the final answer.
- If an alternative matches one of the original options (A/B/C/D), select that
- Otherwise, explain what the correct approach should be

**Output Format:**
ANSWER: [Single letter A/B/C/D, or "UNKNOWN" if none fit]
JUSTIFICATION: [Brief explanation]
"""

        aggregator_response = llm_client.complete(aggregator_prompt)
        total_tokens += aggregator_response.tokens_used or 0
        total_latency += aggregator_response.latency_seconds

        final_answer = _extract_answer(aggregator_response.content, option_labels)
        aggregator_reasoning = aggregator_response.content

    return {
        "method": "independent_binary_agents",
        "answer": final_answer,
        "agents_used": len(options) + (1 if aggregation_needed else 0),
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "agent_evaluations": agent_evaluations,
        "yes_count": len(yes_votes),
        "aggregation_needed": aggregation_needed,
        "aggregator_reasoning": aggregator_reasoning if aggregation_needed else None
    }


def _extract_decision(text: str) -> str:
    """Extract YES/NO decision from agent response."""
    lines = text.split('\n')
    for line in lines:
        if line.upper().startswith('DECISION:'):
            decision = line.split(':', 1)[1].strip()
            if 'YES' in decision.upper():
                return "YES"
            elif 'NO' in decision.upper():
                return "NO"

    # Fallback: search entire text
    if re.search(r'\bYES\b', text, re.IGNORECASE):
        return "YES"
    if re.search(r'\bNO\b', text, re.IGNORECASE):
        return "NO"

    return "UNKNOWN"


def _extract_alternative(text: str) -> Optional[str]:
    """Extract alternative answer if agent said NO."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.upper().startswith('ALTERNATIVE:'):
            alternative = line.split(':', 1)[1].strip()
            if alternative.upper() in ['N/A', 'NONE', '']:
                return None
            return alternative

    return None


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


def _format_yes_votes(yes_votes: list[dict]) -> str:
    """Format YES votes for aggregator."""
    formatted = []
    for vote in yes_votes:
        formatted.append(f"- Option {vote['option']}: {vote['option_text']}")
        formatted.append(f"  Agent reasoning: {vote['full_response'][:200]}...")
    return '\n'.join(formatted)


def _format_alternatives(evaluations: list[dict]) -> str:
    """Format alternative suggestions for aggregator."""
    formatted = []
    for eval in evaluations:
        formatted.append(f"- Agent {eval['option']} (voted NO) suggests: {eval['alternative']}")
    return '\n'.join(formatted)


def _format_options(options: list[str]) -> str:
    """Format options list."""
    return '\n'.join(f"{chr(65+i)}. {opt}" for i, opt in enumerate(options))
