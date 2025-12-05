"""
CoT-Enhanced Debate

Same debate architecture as baseline, but with explicit Chain-of-Thought
instructions in the initial prompts (Round 1) to improve individual agent reasoning.

Hypothesis: Better individual reasoning + ensemble effect = higher accuracy
"""

import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient


def run_debate_cot_enhanced(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config,
    rounds: int = 3
) -> dict:
    """
    CoT-Enhanced debate-style dual-agent.

    Round 1: Detailed CoT prompts for both agents
    Rounds 2-3: Lighter critique/rebuttal prompts

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

    # Round 1: Agent A's initial position (ENHANCED COT)
    agent_a_prompt = f"""You are Clinical Reasoning Agent A. Analyze this case using step-by-step reasoning.

**Question:** {question}

**Options:** {options_str}

**Your Task - Think Through This Systematically:**

1. **Identify Key Clinical Features**
   - What are the critical symptoms and signs?
   - What demographic factors are relevant?
   - What is the clinical context?

2. **Generate Differential Diagnosis**
   - List 3-4 possible conditions that could explain this presentation
   - For each, note what clinical features support it

3. **Evaluate Each Option Against the Evidence**
   - Which option best matches the clinical evidence?
   - What argues FOR each option?
   - What argues AGAINST each option?

4. **Select Your Answer**
   - Based on your systematic analysis, which is most likely?
   - State your answer clearly

**Format:**
DIFFERENTIAL: [List possible diagnoses]
ANALYSIS: [Evaluate each option systematically]
ANSWER: [A, B, C, or D]
REASONING: [Why this answer is best]
"""

    agent_a_response = llm_client.complete(agent_a_prompt)
    agent_a_position = agent_a_response.content
    total_tokens += agent_a_response.tokens_used or 0
    total_latency += agent_a_response.latency_seconds

    debate_history.append({
        "round": 1,
        "agent": "A",
        "position": agent_a_position,
        "answer": _extract_answer(agent_a_position, options)
    })

    # Round 1: Agent B's counter-position (ENHANCED COT)
    agent_b_prompt = f"""You are Clinical Reasoning Agent B. Critically evaluate Agent A's analysis using step-by-step reasoning.

**Question:** {question}

**Options:** {options_str}

**Agent A's Position:**
{agent_a_position}

**Your Task - Systematic Critical Evaluation:**

1. **Assess Agent A's Clinical Feature Identification**
   - Did they identify the key features correctly?
   - Did they miss anything important?

2. **Review Their Differential Diagnosis**
   - Is their differential complete?
   - Are there other conditions to consider?

3. **Evaluate Their Analysis**
   - Are their arguments for/against each option sound?
   - What evidence did they overlook?
   - Where is their reasoning strongest/weakest?

4. **Provide Your Independent Analysis**
   - Think through the evidence systematically
   - Generate your own conclusion
   - Agree OR disagree with Agent A based on the evidence

**Format:**
CRITIQUE: [Evaluate Agent A's reasoning]
MY_ANALYSIS: [Your systematic evaluation]
ANSWER: [A, B, C, or D]
POSITION: [Agree/Disagree with Agent A and why]
"""

    agent_b_response = llm_client.complete(agent_b_prompt)
    agent_b_position = agent_b_response.content
    total_tokens += agent_b_response.tokens_used or 0
    total_latency += agent_b_response.latency_seconds

    debate_history.append({
        "round": 1,
        "agent": "B",
        "position": agent_b_position,
        "answer": _extract_answer(agent_b_position, options)
    })

    # Subsequent debate rounds (LIGHTER PROMPTS - CRITIQUE FOCUSED)
    for round_num in range(2, rounds + 1):
        # Agent A responds to B
        agent_a_rebuttal_prompt = f"""You are Clinical Reasoning Agent A. This is Round {round_num} of the debate.

**Question:** {question}

**Your Previous Position:**
{agent_a_position}

**Agent B's Response:**
{agent_b_position}

**Your Task:**
- Consider Agent B's critique and analysis
- Respond to their specific points
- Refine or defend your position with evidence
- You may change your answer if Agent B's arguments are more convincing

Provide your updated reasoning and answer.
"""

        agent_a_response = llm_client.complete(agent_a_rebuttal_prompt)
        agent_a_position = agent_a_response.content
        total_tokens += agent_a_response.tokens_used or 0
        total_latency += agent_a_response.latency_seconds

        debate_history.append({
            "round": round_num,
            "agent": "A",
            "position": agent_a_position,
            "answer": _extract_answer(agent_a_position, options)
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
- Respond to their updated points with evidence
- Refine or defend your position
- You may change your answer if Agent A's arguments are more convincing

Provide your updated reasoning and answer.
"""

        agent_b_response = llm_client.complete(agent_b_rebuttal_prompt)
        agent_b_position = agent_b_response.content
        total_tokens += agent_b_response.tokens_used or 0
        total_latency += agent_b_response.latency_seconds

        debate_history.append({
            "round": round_num,
            "agent": "B",
            "position": agent_b_position,
            "answer": _extract_answer(agent_b_position, options)
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
        "method": "debate_cot_enhanced",
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
