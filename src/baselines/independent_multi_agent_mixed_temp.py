"""
Independent Multi-Agent with Mixed Temperature

Architecture:
1. LLM selects 3 specialists for the question (1 LLM call, temp=0.0)
2. Each of 3 specialists independently analyzes the question (3 LLM calls, temp=0.3)
3. Final reviewer agent synthesizes responses and makes choice (1 LLM call, temp=0.0)

Total: 5 LLM calls per question
Temperature: 0.0 for selector and reviewer, 0.3 for specialists
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
    config: Config,
    temperature: float = 0.0
) -> List[str]:
    """
    Use LLM to select top 3 specialists for this question.
    Does NOT answer the question, only selects specialists.

    Args:
        temperature: Temperature override for this call

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

    response = llm_client.complete(prompt, temperature=temperature)

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
    config: Config,
    temperature: float = 0.3
) -> dict:
    """
    Single agent independently analyzes the question.

    Args:
        specialist: Specialist role name
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration
        temperature: Temperature override for this call

    Returns:
        Dict with specialist name, analysis, answer
    """

    options_str = "\n".join(options) if options else "No options"

    prompt = f"""You are a board-certified {specialist}.

Please analyze this clinical question independently and provide your answer.

{question}

{options_str}

Provide your analysis and answer."""

    response = llm_client.complete(prompt, temperature=temperature)

    # Extract answer
    answer = _extract_answer(response.content, options)

    return {
        "specialist": specialist,
        "analysis": response.content,
        "answer": answer
    }


def final_reviewer(
    question: str,
    options: Optional[list[str]],
    agent_responses: List[dict],
    llm_client: LLMClient,
    config: Config,
    temperature: float = 0.0
) -> str:
    """
    Final reviewer synthesizes all agent responses and makes final choice.

    Args:
        question: Clinical question
        options: Multiple choice options
        agent_responses: List of agent response dicts
        llm_client: LLM client
        config: Configuration
        temperature: Temperature override for this call

    Returns:
        Final answer
    """

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

    prompt = f"""You are a senior medical reviewer. Three specialists have independently analyzed this clinical question. Review their analyses and provide the final answer.

Question:
{question}

{options_str}

Specialist Analyses:
{agent_analyses_str}

Based on these analyses, what is the final answer? Provide your reasoning and the answer."""

    response = llm_client.complete(prompt, temperature=temperature)

    # Extract final answer
    answer = _extract_answer(response.content, options)

    return answer, response.content


def run_independent_multi_agent_mixed_temp(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config,
    selector_temp: float = 0.0,
    specialist_temp: float = 0.3,
    reviewer_temp: float = 0.0
) -> dict:
    """
    Independent multi-agent with mixed temperatures:
    1. Select top 3 specialists (1 LLM call, temp=selector_temp)
    2. Each specialist analyzes independently (3 LLM calls, temp=specialist_temp)
    3. Final reviewer makes choice (1 LLM call, temp=reviewer_temp)

    Total: 5 LLM calls

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration
        selector_temp: Temperature for specialist selection
        specialist_temp: Temperature for specialist analysis
        reviewer_temp: Temperature for final reviewer

    Returns:
        Dict with answer, specialists, agent responses, tokens, latency
    """

    import time
    start_time = time.time()
    total_tokens = 0

    # Step 1: Select specialists (1st LLM call, temp=0.0)
    specialists = select_specialists(
        question, options, llm_client, config, temperature=selector_temp
    )

    # Step 2: Each agent analyzes independently (3 LLM calls, temp=0.3)
    agent_responses = []
    for specialist in specialists:
        agent_response = agent_independent_analysis(
            specialist, question, options, llm_client, config,
            temperature=specialist_temp
        )
        agent_responses.append(agent_response)

    # Step 3: Final reviewer (5th LLM call, temp=0.0)
    final_answer, reviewer_analysis = final_reviewer(
        question, options, agent_responses, llm_client, config,
        temperature=reviewer_temp
    )

    total_latency = time.time() - start_time

    # Estimate tokens (5 calls total)
    # This is rough - actual tracking would require summing all response tokens
    if hasattr(llm_client, '_last_response_tokens'):
        total_tokens = llm_client._last_response_tokens * 5

    return {
        "method": "independent_multi_agent_mixed_temp",
        "answer": final_answer,
        "specialists": specialists,
        "agent_responses": agent_responses,
        "reviewer_analysis": reviewer_analysis,
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "num_llm_calls": 5,
        "temperatures": {
            "selector": selector_temp,
            "specialist": specialist_temp,
            "reviewer": reviewer_temp
        }
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract answer from response."""
    # Look for single letter
    match = re.search(r'\b([A-D])\b', text)
    if match:
        return match.group(1)

    return "UNKNOWN"
