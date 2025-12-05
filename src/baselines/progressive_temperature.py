"""
Progressive Temperature Single-Agent Reasoning

Temperature annealing approach:
Stage 1 (temp=1.0): Broad exploration - generate diverse hypotheses
Stage 2 (temp=0.7): Evidence gathering - analyze each possibility
Stage 3 (temp=0.5): Prioritization - rank and narrow candidates
Stage 4 (temp=0.3): Deep analysis - detailed evaluation
Stage 5 (temp=0.0): Final decision - deterministic choice
"""

from typing import List, Dict, Any
from src.llm_client import LLMClient
from src.config import Config


def run_progressive_temperature(
    question: str,
    options: List[str],
    llm_client: LLMClient,
    config: Config
) -> Dict[str, Any]:
    """
    Progressive temperature reasoning with 5 stages.

    Returns dict with:
        - answer: final answer letter
        - reasoning: final reasoning
        - stage_outputs: list of outputs from each stage
        - tokens_used: total tokens
        - latency_seconds: total time
    """
    import time
    start_time = time.time()
    total_tokens = 0
    stage_outputs = []

    # Format options
    options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])

    # ========================
    # STAGE 1: BROAD EXPLORATION (temp=1.0)
    # ========================
    stage1_prompt = f"""You are a medical expert conducting initial diagnostic reasoning.

Question: {question}

Options:
{options_text}

TASK: Generate a BROAD differential diagnosis. Consider all possibilities, even unlikely ones. What could this possibly be? Explore diverse reasoning paths.

Provide your initial thoughts and multiple candidate answers with brief reasoning for each."""

    stage1_response = llm_client.complete(stage1_prompt, temperature=1.0)
    stage_outputs.append({
        "stage": 1,
        "temperature": 1.0,
        "purpose": "Broad exploration",
        "output": stage1_response.content
    })
    total_tokens += stage1_response.tokens_used

    # ========================
    # STAGE 2: EVIDENCE GATHERING (temp=0.7)
    # ========================
    stage2_prompt = f"""You are a medical expert analyzing diagnostic possibilities.

Question: {question}

Options:
{options_text}

PREVIOUS EXPLORATION:
{stage1_response.content}

TASK: For each possibility mentioned above, provide detailed clinical reasoning. What evidence SUPPORTS each diagnosis? What evidence REFUTES it? Consider pathophysiology, clinical presentation, and diagnostic criteria.

Provide thorough analysis for each candidate."""

    stage2_response = llm_client.complete(stage2_prompt, temperature=0.7)
    stage_outputs.append({
        "stage": 2,
        "temperature": 0.7,
        "purpose": "Evidence gathering",
        "output": stage2_response.content
    })
    total_tokens += stage2_response.tokens_used

    # ========================
    # STAGE 3: PRIORITIZATION (temp=0.5)
    # ========================
    stage3_prompt = f"""You are a medical expert prioritizing diagnoses.

Question: {question}

Options:
{options_text}

EVIDENCE ANALYSIS:
{stage2_response.content}

TASK: Based on the evidence above, RANK the answer options from most to least likely. Provide confidence levels and identify the top 2-3 most probable answers. Which diagnoses best fit the clinical picture?

Provide ranked list with brief justification."""

    stage3_response = llm_client.complete(stage3_prompt, temperature=0.5)
    stage_outputs.append({
        "stage": 3,
        "temperature": 0.5,
        "purpose": "Prioritization",
        "output": stage3_response.content
    })
    total_tokens += stage3_response.tokens_used

    # ========================
    # STAGE 4: DEEP ANALYSIS (temp=0.3)
    # ========================
    stage4_prompt = f"""You are a medical expert conducting detailed evaluation.

Question: {question}

Options:
{options_text}

PRIORITIZED CANDIDATES:
{stage3_response.content}

TASK: Perform DETAILED comparison of the top 2-3 diagnoses. Weigh all evidence carefully. Consider:
- How well does each explain ALL the clinical findings?
- Are there any inconsistencies or red flags?
- What is the most parsimonious explanation?

Provide rigorous comparative analysis."""

    stage4_response = llm_client.complete(stage4_prompt, temperature=0.3)
    stage_outputs.append({
        "stage": 4,
        "temperature": 0.3,
        "purpose": "Deep analysis",
        "output": stage4_response.content
    })
    total_tokens += stage4_response.tokens_used

    # ========================
    # STAGE 5: FINAL DECISION (temp=0.0)
    # ========================
    stage5_prompt = f"""You are a medical expert making a final diagnostic decision.

Question: {question}

Options:
{options_text}

COMPREHENSIVE ANALYSIS:
{stage4_response.content}

TASK: Based on all the reasoning above, select the SINGLE BEST answer. You must choose ONE option (A, B, C, or D).

Respond in this EXACT format:
ANSWER: [letter]
REASONING: [brief final justification]"""

    stage5_response = llm_client.complete(stage5_prompt, temperature=0.0)
    stage_outputs.append({
        "stage": 5,
        "temperature": 0.0,
        "purpose": "Final decision",
        "output": stage5_response.content
    })
    total_tokens += stage5_response.tokens_used

    # Extract answer
    answer_text = stage5_response.content
    answer = "UNKNOWN"

    # Try to parse answer
    import re
    answer_match = re.search(r'ANSWER:\s*([A-Da-d])', answer_text, re.IGNORECASE)
    if answer_match:
        answer = answer_match.group(1).upper()
    else:
        # Fallback: look for first letter
        for char in answer_text:
            if char.upper() in ['A', 'B', 'C', 'D']:
                answer = char.upper()
                break

    latency = time.time() - start_time

    return {
        "answer": answer,
        "reasoning": answer_text,
        "stage_outputs": stage_outputs,
        "tokens_used": total_tokens,
        "latency_seconds": latency,
        "method": "progressive_temperature",
        "temperature_schedule": [1.0, 0.7, 0.5, 0.3, 0.0]
    }
