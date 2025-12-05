"""
Baseline 3: Debate-Style Dual-Agent
Two agents debate and reach consensus.
"""

import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient


def run_debate(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config,
    rounds: int = 3
) -> dict:
    """
    Debate-style dual-agent baseline.
    Two agents debate for N rounds, then reach consensus.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration
        rounds: Number of debate rounds (default 3)

    Returns:
        Dict with answer, reasoning, tokens, latency
    """

    options_str = "\n".join(options) if options else "No options"

    total_tokens = 0
    total_latency = 0.0
    debate_history = []

    # Round 1: Agent A's initial position
    agent_a_prompt = f"""You are Clinical Reasoning Agent A. Analyze this case and propose your diagnosis.

**Question:** {question}

**Options:** {options_str}

**Your Task:**
1. Analyze the clinical presentation
2. Generate a differential diagnosis
3. Select your answer and explain your reasoning
4. Be prepared to defend your position

Provide your diagnostic reasoning and select an answer.
"""

    agent_a_response = llm_client.complete(agent_a_prompt)
    agent_a_position = agent_a_response.content
    total_tokens += agent_a_response.tokens_used or 0
    total_latency += agent_a_response.latency_seconds

    debate_history.append({
        "round": 1,
        "agent": "A",
        "position": agent_a_position
    })

    # Round 1: Agent B's counter-position
    agent_b_prompt = f"""You are Clinical Reasoning Agent B. Review Agent A's analysis and provide your perspective.

**Question:** {question}

**Options:** {options_str}

**Agent A's Position:**
{agent_a_position}

**Your Task:**
1. Critically evaluate Agent A's reasoning
2. Provide your own diagnostic analysis
3. Agree or disagree with Agent A
4. Explain your reasoning

If you disagree, explain why and provide your alternative answer.
"""

    agent_b_response = llm_client.complete(agent_b_prompt)
    agent_b_position = agent_b_response.content
    total_tokens += agent_b_response.tokens_used or 0
    total_latency += agent_b_response.latency_seconds

    debate_history.append({
        "round": 1,
        "agent": "B",
        "position": agent_b_position
    })

    # Subsequent debate rounds
    for round_num in range(2, rounds + 1):
        # Agent A responds to B
        agent_a_rebuttal_prompt = f"""You are Clinical Reasoning Agent A. This is Round {round_num} of the debate.

**Question:** {question}

**Your Previous Position:**
{agent_a_position}

**Agent B's Response:**
{agent_b_position}

**Your Task:**
- Consider Agent B's critique
- Respond to their points
- Refine or defend your position
- You may change your answer if Agent B's arguments are convincing

Provide your updated reasoning.
"""

        agent_a_response = llm_client.complete(agent_a_rebuttal_prompt)
        agent_a_position = agent_a_response.content
        total_tokens += agent_a_response.tokens_used or 0
        total_latency += agent_a_response.latency_seconds

        debate_history.append({
            "round": round_num,
            "agent": "A",
            "position": agent_a_position
        })

        # Agent B responds to A
        agent_b_rebuttal_prompt = f"""You are Clinical Reasoning Agent B. This is Round {round_num} of the debate.

**Question:** {question}

**Your Previous Position:**
{agent_b_position}

**Agent A's Response:**
{agent_a_position}

**Your Task:**
- Consider Agent A's rebuttal
- Respond to their updated points
- Refine or defend your position
- You may change your answer if Agent A's arguments are convincing

Provide your updated reasoning.
"""

        agent_b_response = llm_client.complete(agent_b_rebuttal_prompt)
        agent_b_position = agent_b_response.content
        total_tokens += agent_b_response.tokens_used or 0
        total_latency += agent_b_response.latency_seconds

        debate_history.append({
            "round": round_num,
            "agent": "B",
            "position": agent_b_position
        })

    # Final consensus
    consensus_prompt = f"""Based on the debate between Agent A and Agent B, provide the final consensus answer.

**Question:** {question}

**Options:** {options_str}

**Agent A's Final Position:**
{agent_a_position}

**Agent B's Final Position:**
{agent_b_position}

**Your Task:**
Synthesize both perspectives and provide:
1. The final answer (A, B, C, or D)
2. Justification that incorporates insights from both agents
3. Resolution of any disagreements

**Output Format:**
ANSWER: [A, B, C, or D]
JUSTIFICATION: [Synthesis of both agents' reasoning]
"""

    consensus_response = llm_client.complete(consensus_prompt)
    total_tokens += consensus_response.tokens_used or 0
    total_latency += consensus_response.latency_seconds

    debate_history.append({
        "round": "consensus",
        "agent": "Moderator",
        "position": consensus_response.content
    })

    # Parse final answer
    answer = _extract_answer(consensus_response.content, options)

    return {
        "method": "debate",
        "answer": answer,
        "debate_rounds": rounds,
        "agents_used": 2,
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "debate_history": debate_history,
        "full_response": consensus_response.content
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract the final answer from consensus response."""
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
