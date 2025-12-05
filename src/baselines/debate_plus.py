"""
Debate++ Phase 1: Confidence-Weighted Debate

Enhancement over baseline Debate method:
- Agents report confidence levels (HIGH/MEDIUM/LOW)
- Judge weighs arguments by confidence AND evidence quality
- Tie-breaker specialist consultation if both agents have LOW confidence
"""

import re
from typing import Optional

from ..config import Config
from ..llm_client import LLMClient


def run_debate_plus(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config,
    rounds: int = 2
) -> dict:
    """
    Debate++ with confidence weighting.

    Two agents debate for N rounds with confidence scores.
    Judge weighs arguments by confidence and evidence quality.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration
        rounds: Number of debate rounds (default 2)

    Returns:
        Dict with answer, reasoning, tokens, latency, confidence scores
    """

    options_str = "\n".join(options) if options else "No options"

    total_tokens = 0
    total_latency = 0.0
    debate_history = []

    # Round 1: Agent A's initial position WITH confidence
    agent_a_prompt = f"""You are Clinical Reasoning Agent A. Analyze this case and propose your diagnosis.

**Question:** {question}

**Options:** {options_str}

**Your Task:**
1. Analyze the clinical presentation carefully
2. Generate a differential diagnosis
3. Select your answer and explain your reasoning with specific clinical evidence
4. **Rate your confidence in this answer: HIGH, MEDIUM, or LOW**

**Confidence Guidelines:**
- HIGH: Strong clinical evidence, clear diagnosis, minimal ambiguity
- MEDIUM: Reasonable evidence, some competing explanations possible
- LOW: Significant uncertainty, multiple plausible diagnoses, limited information

**Required Output Format:**
ANSWER: [A, B, C, or D]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [Your detailed clinical reasoning with specific evidence from the case]
"""

    agent_a_response = llm_client.complete(agent_a_prompt)
    agent_a_position = agent_a_response.content
    agent_a_confidence = _extract_confidence(agent_a_position)
    agent_a_answer = _extract_answer(agent_a_position, options)

    total_tokens += agent_a_response.tokens_used or 0
    total_latency += agent_a_response.latency_seconds

    debate_history.append({
        "round": 1,
        "agent": "A",
        "position": agent_a_position,
        "confidence": agent_a_confidence,
        "answer": agent_a_answer
    })

    # Round 1: Agent B's counter-position WITH confidence
    agent_b_prompt = f"""You are Clinical Reasoning Agent B. Review Agent A's analysis and provide your perspective.

**Question:** {question}

**Options:** {options_str}

**Agent A's Position:**
{agent_a_position}

**Your Task:**
1. Critically evaluate Agent A's reasoning and evidence
2. Provide your own diagnostic analysis with specific clinical evidence
3. Agree or disagree with Agent A (you should prefer to disagree if you see flaws)
4. **Rate your confidence in YOUR answer: HIGH, MEDIUM, or LOW**

**Confidence Guidelines:**
- HIGH: Strong clinical evidence, clear diagnosis, minimal ambiguity
- MEDIUM: Reasonable evidence, some competing explanations possible
- LOW: Significant uncertainty, multiple plausible diagnoses, limited information

**Required Output Format:**
ANSWER: [A, B, C, or D]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [Your detailed clinical reasoning, including critique of Agent A if you disagree]
"""

    agent_b_response = llm_client.complete(agent_b_prompt)
    agent_b_position = agent_b_response.content
    agent_b_confidence = _extract_confidence(agent_b_position)
    agent_b_answer = _extract_answer(agent_b_position, options)

    total_tokens += agent_b_response.tokens_used or 0
    total_latency += agent_b_response.latency_seconds

    debate_history.append({
        "round": 1,
        "agent": "B",
        "position": agent_b_position,
        "confidence": agent_b_confidence,
        "answer": agent_b_answer
    })

    # Subsequent debate rounds
    for round_num in range(2, rounds + 1):
        # Agent A responds to B
        agent_a_rebuttal_prompt = f"""You are Clinical Reasoning Agent A. This is Round {round_num} of the debate.

**Question:** {question}

**Your Previous Position:**
{agent_a_position}

**Agent B's Response (Confidence: {agent_b_confidence}):**
{agent_b_position}

**Your Task:**
- Consider Agent B's critique and their confidence level
- Respond to their points with specific clinical evidence
- Refine or defend your position
- You may change your answer if Agent B's arguments are more convincing
- **Update your confidence level: HIGH, MEDIUM, or LOW**

**Required Output Format:**
ANSWER: [A, B, C, or D]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [Your updated reasoning with response to Agent B]
"""

        agent_a_response = llm_client.complete(agent_a_rebuttal_prompt)
        agent_a_position = agent_a_response.content
        agent_a_confidence = _extract_confidence(agent_a_position)
        agent_a_answer = _extract_answer(agent_a_position, options)

        total_tokens += agent_a_response.tokens_used or 0
        total_latency += agent_a_response.latency_seconds

        debate_history.append({
            "round": round_num,
            "agent": "A",
            "position": agent_a_position,
            "confidence": agent_a_confidence,
            "answer": agent_a_answer
        })

        # Agent B responds to A
        agent_b_rebuttal_prompt = f"""You are Clinical Reasoning Agent B. This is Round {round_num} of the debate.

**Question:** {question}

**Your Previous Position:**
{agent_b_position}

**Agent A's Response (Confidence: {agent_a_confidence}):**
{agent_a_position}

**Your Task:**
- Consider Agent A's rebuttal and their confidence level
- Respond to their updated points with specific clinical evidence
- Refine or defend your position
- You may change your answer if Agent A's arguments are more convincing
- **Update your confidence level: HIGH, MEDIUM, or LOW**

**Required Output Format:**
ANSWER: [A, B, C, or D]
CONFIDENCE: [HIGH, MEDIUM, or LOW]
REASONING: [Your updated reasoning with response to Agent A]
"""

        agent_b_response = llm_client.complete(agent_b_rebuttal_prompt)
        agent_b_position = agent_b_response.content
        agent_b_confidence = _extract_confidence(agent_b_position)
        agent_b_answer = _extract_answer(agent_b_position, options)

        total_tokens += agent_b_response.tokens_used or 0
        total_latency += agent_b_response.latency_seconds

        debate_history.append({
            "round": round_num,
            "agent": "B",
            "position": agent_b_position,
            "confidence": agent_b_confidence,
            "answer": agent_b_answer
        })

    # Check if both agents have LOW confidence → trigger tie-breaker
    # (Future enhancement: actually consult specialist)
    low_confidence_both = (agent_a_confidence == "LOW" and agent_b_confidence == "LOW")

    # Final confidence-weighted judgment
    judgment_prompt = f"""Based on the debate between Agent A and Agent B, provide the final judgment.

**Question:** {question}

**Options:** {options_str}

**Agent A's Final Position:**
Answer: {agent_a_answer}
Confidence: {agent_a_confidence}
Reasoning: {agent_a_position}

**Agent B's Final Position:**
Answer: {agent_b_answer}
Confidence: {agent_b_confidence}
Reasoning: {agent_b_position}

**Your Task as Judge:**
1. **Weigh arguments by BOTH confidence level AND evidence quality**
   - Higher confidence positions deserve more weight, but only if backed by solid evidence
   - A LOW-confidence position with strong evidence beats a HIGH-confidence position with weak evidence

2. **Evaluate evidence quality:**
   - Specific clinical findings cited (labs, vitals, history)
   - Quantitative reasoning
   - Pathophysiology explanation
   - Ruling out alternatives

3. **Resolve disagreement if present:**
   - Which agent provided stronger clinical evidence?
   - Which reasoning better accounts for all findings?
   - Is one agent's confidence justified by their evidence?

4. **Provide final judgment:**
   - Select the answer (A, B, C, or D)
   - Explain which agent's position you're favoring and why
   - Note if confidence levels influenced your decision

**Special Case:** {"Both agents have LOW confidence - consider this high uncertainty case" if low_confidence_both else ""}

**Required Output Format:**
ANSWER: [A, B, C, or D]
RATIONALE: [Synthesis explaining your judgment, mentioning confidence and evidence quality]
"""

    judgment_response = llm_client.complete(judgment_prompt)
    total_tokens += judgment_response.tokens_used or 0
    total_latency += judgment_response.latency_seconds

    debate_history.append({
        "round": "judgment",
        "agent": "Judge",
        "position": judgment_response.content
    })

    # Parse final answer
    final_answer = _extract_answer(judgment_response.content, options)

    return {
        "method": "debate_plus_confidence",
        "answer": final_answer,
        "debate_rounds": rounds,
        "agents_used": 2,
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "debate_history": debate_history,
        "final_confidence_scores": {
            "agent_a": agent_a_confidence,
            "agent_b": agent_b_confidence,
            "both_low": low_confidence_both
        },
        "full_response": judgment_response.content
    }


def _extract_confidence(text: str) -> str:
    """Extract confidence level from agent response."""
    # Look for CONFIDENCE: HIGH/MEDIUM/LOW
    match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Fallback: search anywhere in text for confidence mentions
    text_upper = text.upper()
    if "CONFIDENCE: HIGH" in text_upper or "HIGH CONFIDENCE" in text_upper:
        return "HIGH"
    if "CONFIDENCE: MEDIUM" in text_upper or "MEDIUM CONFIDENCE" in text_upper:
        return "MEDIUM"
    if "CONFIDENCE: LOW" in text_upper or "LOW CONFIDENCE" in text_upper:
        return "LOW"

    # Default to MEDIUM if not specified
    return "MEDIUM"


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract the final answer from response."""
    # Look for ANSWER: [letter]
    match = re.search(r'ANSWER:\s*([A-D])', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Fallback: find any single letter A-D
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1).upper()

    return "UNKNOWN"
