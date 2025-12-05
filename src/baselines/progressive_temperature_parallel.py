"""
Progressive Temperature with Parallel Exploration

Enhanced temperature annealing with diverse hypothesis generation:
Stage 1a-e (temp=1.0 x5): Parallel broad exploration - 5 diverse hypothesis sets
Stage 1-merge (temp=0.5): Synthesize all explorations into unified hypothesis set
Stage 2 (temp=0.7): Evidence gathering - analyze merged possibilities
Stage 3 (temp=0.5): Prioritization - rank and narrow candidates
Stage 4 (temp=0.3): Deep analysis - detailed evaluation
Stage 5 (temp=0.0): Final decision - deterministic choice
"""

from typing import List, Dict, Any
from src.llm_client import LLMClient
from src.config import Config


def run_progressive_temperature_parallel(
    question: str,
    options: List[str],
    llm_client: LLMClient,
    config: Config,
    n_parallel: int = 5
) -> Dict[str, Any]:
    """
    Progressive temperature reasoning with parallel exploration.

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
    # STAGE 1: PARALLEL BROAD EXPLORATION (temp=1.0 x N)
    # ========================
    stage1_prompt = f"""You are a medical expert conducting initial diagnostic reasoning.

Question: {question}

Options:
{options_text}

TASK: Generate a BROAD differential diagnosis. Consider all possibilities, even unlikely ones. What could this possibly be? Explore diverse reasoning paths.

Provide your initial thoughts and multiple candidate answers with brief reasoning for each."""

    # Run N parallel explorations
    stage1_responses = []
    for i in range(n_parallel):
        response = llm_client.complete(stage1_prompt, temperature=1.0)
        stage_outputs.append({
            "stage": f"1{chr(97+i)}",  # 1a, 1b, 1c, etc.
            "temperature": 1.0,
            "purpose": f"Parallel exploration {i+1}/{n_parallel}",
            "output": response.content
        })
        stage1_responses.append(response.content)
        total_tokens += response.tokens_used

    # ========================
    # STAGE 1-MERGE: SYNTHESIZE EXPLORATIONS (temp=0.5)
    # ========================
    # Format all explorations for merging
    explorations_text = "\n\n".join([
        f"=== EXPLORATION {i+1} ===\n{content}"
        for i, content in enumerate(stage1_responses)
    ])

    merge_prompt = f"""You are a medical expert synthesizing multiple diagnostic explorations.

Question: {question}

Options:
{options_text}

MULTIPLE EXPLORATIONS FROM DIFFERENT PERSPECTIVES:

{explorations_text}

TASK: Synthesize ALL the hypotheses and reasoning from the {n_parallel} explorations above into a comprehensive, unified differential diagnosis.

CRITICAL SYNTHESIS PRIORITIES (in order):
1. **CONTRAINDICATIONS & RED FLAGS**: Identify and PROMINENTLY FLAG any contraindications, drug interactions, or critical safety considerations mentioned in ANY exploration. These are HIGHEST priority.

2. **CONSENSUS FINDINGS**: Identify diagnoses or reasoning mentioned by MULTIPLE explorations ({n_parallel} explorations total). Give these HIGH weight - if 3+ explorations agree, this is a strong signal.

3. **PATIENT-SPECIFIC FACTORS**: Preserve all details about the patient's history, comorbidities, current medications, and special circumstances. These may be critical for treatment decisions.

4. **COMPREHENSIVE DIFFERENTIAL**: Include all unique diagnoses mentioned across all explorations, but RANK them by:
   - Number of explorations that mentioned it
   - Strength of supporting evidence
   - Clinical plausibility

5. **CONFLICTING INFORMATION**: When explorations disagree, explicitly note the disagreement and the reasoning from each side.

6. **UNIQUE INSIGHTS**: Include insights mentioned by only one exploration IF they are clinically significant (contraindications, rare but dangerous diagnoses, etc.).

FORMAT YOUR SYNTHESIS:
- Start with CRITICAL FLAGS (contraindications, safety issues)
- Then CONSENSUS diagnoses (mentioned by multiple explorations)
- Then other possibilities ranked by likelihood
- Preserve key clinical reasoning from each perspective

Create a thorough, merged analysis that emphasizes clinical safety and diagnostic accuracy."""

    merge_response = llm_client.complete(merge_prompt, temperature=0.0)
    stage_outputs.append({
        "stage": "1-merge",
        "temperature": 0.0,
        "purpose": f"Synthesis of {n_parallel} parallel explorations",
        "output": merge_response.content
    })
    total_tokens += merge_response.tokens_used

    # ========================
    # STAGE 2: FINAL DECISION (temp=0.0)
    # ========================
    final_prompt = f"""You are a medical expert making a final diagnostic decision based on a comprehensive differential diagnosis.

Question: {question}

Options:
{options_text}

COMPREHENSIVE DIFFERENTIAL DIAGNOSIS (synthesized from {n_parallel} diverse explorations):
{merge_response.content}

TASK: Based on the comprehensive analysis above, which includes:
- Flagged contraindications and safety concerns
- Consensus findings across multiple explorations
- Patient-specific factors and clinical context
- Ranked differential diagnoses

Perform systematic final analysis:
1. Review the evidence for and against each option
2. Consider which diagnosis best explains ALL clinical findings
3. Identify any critical contraindications or red flags
4. Select the SINGLE BEST answer

You must choose ONE option (A, B, C, or D).

Respond in this EXACT format:
ANSWER: [letter]
REASONING: [comprehensive justification including key evidence and why other options were ruled out]"""

    stage5_response = llm_client.complete(final_prompt, temperature=0.0)
    stage_outputs.append({
        "stage": 2,
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
        "method": "progressive_temperature_parallel_simple",
        "n_parallel": n_parallel,
        "temperature_schedule": [1.0] * n_parallel + [0.0, 0.0]  # 5x exploration + merge + final
    }
