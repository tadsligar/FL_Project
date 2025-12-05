"""
Independent Multi-Agent with Majority Voting

Architecture:
1. LLM selects 3 specialists for the question (1 LLM call)
2. Each of 3 specialists independently analyzes the question (3 LLM calls)
3. Majority voting determines final answer
   - If 2+ agents agree: use majority answer (0 additional LLM calls)
   - If no majority (1-1-1): use LLM synthesis (1 additional LLM call)

Total: 4-5 LLM calls per question (5 only when there's no majority)
Temperature: 0.0 for all agents
"""

from typing import Optional, List
from collections import Counter
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
    Does NOT answer the question, only selects specialists.

    Returns:
        List of 3 specialist names
    """

    # Get list of available specialists
    specialist_list = "\n".join([f"- {spec.display_name}"
                                 for spec in SPECIALTY_CATALOG])

    prompt = f"""You are a medical triage expert. Given a clinical question, identify the TOP 3 medical specialties most relevant to answering this question correctly.

Available specialties:
{specialist_list}

Question:
{question}

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


def agent_independent_analysis(
    specialist: str,
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Single agent independently analyzes the question.

    Args:
        specialist: Specialist role name
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with specialist name, analysis, answer
    """

    options_str = "\n".join(options) if options else "No options"

    prompt = f"""You are a board-certified {specialist}.

Please analyze this clinical question independently and provide your answer.

{question}

{options_str}

Provide your analysis and answer."""

    response = llm_client.complete(prompt)

    # Extract answer
    answer = _extract_answer(response.content, options)

    return {
        "specialist": specialist,
        "analysis": response.content,
        "answer": answer
    }


def final_decision_with_majority(
    question: str,
    options: Optional[list[str]],
    agent_responses: List[dict],
    llm_client: LLMClient,
    config: Config
) -> tuple:
    """
    Make final decision using majority voting with LLM synthesis fallback.

    Logic:
    1. Count votes from all agents
    2. If 2+ agents agree: return majority answer (no LLM call)
    3. If no majority (tie): use LLM synthesis (1 LLM call)

    Args:
        question: Clinical question
        options: Multiple choice options
        agent_responses: List of agent response dicts
        llm_client: LLM client
        config: Configuration

    Returns:
        Tuple of (final_answer, decision_method, synthesis_text_or_none)
        - decision_method: "majority" or "synthesis"
    """

    # Count votes
    answers = [resp['answer'] for resp in agent_responses]
    vote_counts = Counter(answers)

    # Check for majority (2+ votes)
    most_common = vote_counts.most_common(1)
    if most_common and most_common[0][1] >= 2:
        # Majority found!
        majority_answer = most_common[0][0]
        return majority_answer, "majority", None

    # No majority - fall back to LLM synthesis
    options_str = "\n".join(options) if options else "No options"

    # Format agent responses
    agent_analyses = []
    for i, resp in enumerate(agent_responses, 1):
        agent_analyses.append(f"""
Agent {i} ({resp['specialist']}):
Answer: {resp['answer']}
Analysis: {resp['analysis']}
""")

    agent_analyses_str = "\n".join(agent_analyses)

    prompt = f"""You are a senior medical reviewer. Three specialists have independently analyzed this clinical question, but they did not reach a consensus. Review their analyses and provide the final answer.

Question:
{question}

{options_str}

Specialist Analyses:
{agent_analyses_str}

Based on these analyses, what is the final answer? Provide your reasoning and the answer."""

    response = llm_client.complete(prompt)

    # Extract final answer
    answer = _extract_answer(response.content, options)

    return answer, "synthesis", response.content


def run_independent_multi_agent_majority(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Independent multi-agent with majority voting:
    1. Select top 3 specialists (1 LLM call)
    2. Each specialist analyzes independently (3 LLM calls)
    3. Majority voting (0 LLM calls if majority, 1 if synthesis needed)

    Total: 4-5 LLM calls (depends on whether majority exists)

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, specialists, agent responses, decision method, tokens, latency
    """

    import time
    start_time = time.time()
    total_tokens = 0

    # Step 1: Select specialists (1st LLM call)
    specialists = select_specialists(question, options, llm_client, config)

    # Step 2: Each agent analyzes independently (3 LLM calls)
    agent_responses = []
    for specialist in specialists:
        agent_response = agent_independent_analysis(
            specialist, question, options, llm_client, config
        )
        agent_responses.append(agent_response)

    # Step 3: Majority voting with synthesis fallback
    final_answer, decision_method, synthesis_text = final_decision_with_majority(
        question, options, agent_responses, llm_client, config
    )

    total_latency = time.time() - start_time

    # Calculate actual LLM calls
    num_llm_calls = 4  # 1 specialist selection + 3 agents
    if decision_method == "synthesis":
        num_llm_calls = 5  # +1 for synthesis

    # Estimate tokens
    if hasattr(llm_client, '_last_response_tokens'):
        total_tokens = llm_client._last_response_tokens * num_llm_calls

    return {
        "method": "independent_multi_agent_majority",
        "answer": final_answer,
        "specialists": specialists,
        "agent_responses": agent_responses,
        "decision_method": decision_method,  # "majority" or "synthesis"
        "synthesis_text": synthesis_text,  # None if majority was used
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "num_llm_calls": num_llm_calls
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract answer from response."""
    # Look for single letter
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1)

    return "UNKNOWN"
