"""
Baseline 4: Sequential Specialist Debate with Generalist Continuity
A single generalist MD selects specialists, debates with each sequentially,
reviews the consultations, and makes the final decision.

Architecture:
1. Generalist (Planner) → Selects Top-2 specialists
2. Generalist ↔ Specialist 1 → Debate until agreement (max 3 rounds)
3. Generalist ↔ Specialist 2 → Debate until agreement (max 3 rounds)
4. Generalist (Reviewer) → Reviews both consultations
5. Generalist (Aggregator) → Final decision

Key Features:
- Same generalist maintains context throughout (like a real physician)
- Iterative refinement via debate (what made Debate method win)
- Specialist expertise (what Adaptive MAS provides)
- Self-correction via Reviewer (what made Fixed Pipeline strong)
- Free-text format (avoids JSON parsing errors)
"""

import re
from typing import Optional

from ..catalog import get_specialty_by_id, get_catalog
from ..config import Config
from ..llm_client import LLMClient


def run_sequential_specialist_debate(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config,
    max_rounds_per_specialist: int = 3,
    num_specialists: int = 2
) -> dict:
    """
    Sequential specialist debate with generalist continuity.

    Args:
        question: Clinical question
        options: Multiple choice options
        llm_client: LLM client
        config: Configuration
        max_rounds_per_specialist: Maximum debate rounds per specialist (default 3)
        num_specialists: Number of specialists to consult (default 2)

    Returns:
        Dict with answer, reasoning, tokens, latency
    """

    options_str = "\n".join(options) if options else "No options"

    total_tokens = 0
    total_latency = 0.0
    consultation_history = []

    # Step 1: Generalist determines triage specialty and selects specialists
    generalist_type = _determine_generalist_type(question, options_str, llm_client, config)
    total_tokens += generalist_type["tokens"]
    total_latency += generalist_type["latency"]

    selected_specialists = _select_specialists(
        question, options_str, generalist_type["specialty"],
        llm_client, config, num_specialists
    )
    total_tokens += selected_specialists["tokens"]
    total_latency += selected_specialists["latency"]

    consultation_history.append({
        "stage": "triage_and_planning",
        "generalist_type": generalist_type["specialty"],
        "selected_specialists": selected_specialists["specialists"],
        "rationale": selected_specialists["rationale"]
    })

    # Step 2-3: Sequential debate with each specialist
    for i, specialist_id in enumerate(selected_specialists["specialists"], 1):
        specialty = get_specialty_by_id(specialist_id)
        if not specialty:
            continue

        debate_result = _debate_with_specialist(
            question=question,
            options_str=options_str,
            generalist_type=generalist_type["specialty"],
            specialist_name=specialty.display_name,
            specialist_id=specialist_id,
            llm_client=llm_client,
            config=config,
            max_rounds=max_rounds_per_specialist,
            consultation_number=i
        )

        total_tokens += debate_result["tokens"]
        total_latency += debate_result["latency"]
        consultation_history.append(debate_result)

    # Step 4: Generalist reviews all consultations
    review_result = _generalist_review(
        question=question,
        options_str=options_str,
        generalist_type=generalist_type["specialty"],
        consultation_history=consultation_history,
        llm_client=llm_client,
        config=config
    )

    total_tokens += review_result["tokens"]
    total_latency += review_result["latency"]
    consultation_history.append(review_result)

    # Step 5: Generalist makes final decision
    final_decision = _generalist_final_decision(
        question=question,
        options_str=options_str,
        generalist_type=generalist_type["specialty"],
        consultation_history=consultation_history,
        review_summary=review_result["review"],
        llm_client=llm_client,
        config=config
    )

    total_tokens += final_decision["tokens"]
    total_latency += final_decision["latency"]

    # Extract final answer
    answer = _extract_answer(final_decision["decision"], options)

    return {
        "method": "sequential_specialist_debate",
        "answer": answer,
        "agents_used": 1 + num_specialists,  # 1 generalist + N specialists
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "generalist_type": generalist_type["specialty"],
        "specialists_consulted": selected_specialists["specialists"],
        "consultation_history": consultation_history,
        "full_response": final_decision["decision"]
    }


def _determine_generalist_type(
    question: str,
    options_str: str,
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Determine which type of generalist is most appropriate for this case.
    """

    prompt = f"""You are a medical triage coordinator. Determine which type of generalist physician is most appropriate for this case.

**Question:** {question}

**Options:** {options_str}

**Available Generalist Types:**
1. **Emergency Medicine** - For acute, unstable, or emergency presentations (e.g., trauma, shock, acute chest pain, altered mental status)
2. **Pediatrics** - For patients age 18 or under (infants, children, adolescents)
3. **Family/Internal Medicine** - Default for stable adult general medicine cases

**Your Task:**
Based on the clinical presentation, select the most appropriate generalist physician type.

**Output Format:**
GENERALIST TYPE: [Emergency Medicine | Pediatrics | Family/Internal Medicine]
REASON: [Brief 1-2 sentence explanation]
"""

    response = llm_client.complete(prompt)

    # Parse response
    specialty = "Family/Internal Medicine"  # Default
    if "Emergency Medicine" in response.content:
        specialty = "Emergency Medicine"
    elif "Pediatrics" in response.content:
        specialty = "Pediatrics"

    return {
        "specialty": specialty,
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds,
        "full_response": response.content
    }


def _select_specialists(
    question: str,
    options_str: str,
    generalist_type: str,
    llm_client: LLMClient,
    config: Config,
    num_specialists: int
) -> dict:
    """
    Generalist selects which specialists to consult.
    """

    # Get catalog
    catalog = get_catalog()
    catalog_list = "\n".join([f"- {s.id}: {s.display_name}" for s in catalog])

    prompt = f"""You are a {generalist_type} physician. You need to select {num_specialists} medical specialists to consult for this case.

**Question:** {question}

**Available Specialists:**
{catalog_list}

**Your Task:**
1. Analyze the clinical presentation
2. Select the {num_specialists} most relevant specialists from the list above
3. Explain your reasoning

**Output Format:**
SPECIALIST 1: [specialty_id]
SPECIALIST 2: [specialty_id]
RATIONALE: [Explain why these specialists are most relevant for this case]
"""

    response = llm_client.complete(prompt)

    # Parse specialists
    specialists = []
    lines = response.content.split('\n')
    for line in lines:
        if line.strip().startswith('SPECIALIST'):
            # Extract specialty_id
            match = re.search(r':\s*(\w+)', line)
            if match:
                specialists.append(match.group(1))

    # Validate and limit
    valid_ids = {s.id for s in catalog}
    specialists = [s for s in specialists if s in valid_ids][:num_specialists]

    # If parsing failed, use defaults
    if not specialists:
        specialists = ["cardiology", "pulmonology"][:num_specialists]

    return {
        "specialists": specialists,
        "rationale": response.content,
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds
    }


def _debate_with_specialist(
    question: str,
    options_str: str,
    generalist_type: str,
    specialist_name: str,
    specialist_id: str,
    llm_client: LLMClient,
    config: Config,
    max_rounds: int,
    consultation_number: int
) -> dict:
    """
    Conduct debate between generalist and one specialist until agreement.
    """

    debate_rounds = []
    tokens_used = 0
    latency_used = 0.0

    # Round 1: Specialist's initial consultation
    specialist_prompt = f"""You are a {specialist_name} specialist. You have been consulted by a {generalist_type} physician for this case.

**Question:** {question}

**Options:** {options_str}

**Your Task:**
Provide your expert opinion as a {specialist_name} specialist:
1. Differential diagnosis (list 2-3 most likely diagnoses from your specialty's perspective)
2. Probability/confidence for each diagnosis
3. Evidence supporting each diagnosis
4. Key discriminating tests or findings
5. Your recommended answer from the options

Provide your consultation note.
"""

    specialist_response = llm_client.complete(specialist_prompt)
    specialist_position = specialist_response.content
    tokens_used += specialist_response.tokens_used or 0
    latency_used += specialist_response.latency_seconds

    debate_rounds.append({
        "round": 1,
        "speaker": f"{specialist_name} Specialist",
        "content": specialist_position
    })

    # Round 2+: Generalist responds and iterates
    for round_num in range(2, max_rounds + 1):
        # Generalist responds
        generalist_prompt = f"""You are a {generalist_type} physician consulting with a {specialist_name} specialist.

**Question:** {question}

**Options:** {options_str}

**{specialist_name} Specialist's Opinion:**
{specialist_position}

**Your Task:**
Review the specialist's opinion and respond:
1. Do you agree with their differential diagnosis and recommended answer?
2. Are there any gaps or alternative considerations?
3. What is your current assessment?
4. If you disagree, explain why
5. If you agree, confirm the consensus

**Important:** If you have reached agreement with the specialist, clearly state: "I AGREE with the specialist's assessment."
"""

        generalist_response = llm_client.complete(generalist_prompt)
        generalist_position = generalist_response.content
        tokens_used += generalist_response.tokens_used or 0
        latency_used += generalist_response.latency_seconds

        debate_rounds.append({
            "round": round_num,
            "speaker": f"{generalist_type} Physician",
            "content": generalist_position
        })

        # Check for agreement
        if _check_agreement(generalist_position):
            break

        # If not last round, get specialist's rebuttal
        if round_num < max_rounds:
            specialist_rebuttal_prompt = f"""You are a {specialist_name} specialist continuing consultation with a {generalist_type} physician.

**Question:** {question}

**Your Previous Opinion:**
{specialist_position}

**{generalist_type} Physician's Response:**
{generalist_position}

**Your Task:**
Respond to the generalist's points:
1. Address any concerns or questions they raised
2. Refine your differential diagnosis if needed
3. Clarify your reasoning
4. If you agree with the generalist's assessment, state: "I AGREE with the generalist's assessment."

Continue the professional consultation.
"""

            specialist_rebuttal = llm_client.complete(specialist_rebuttal_prompt)
            specialist_position = specialist_rebuttal.content
            tokens_used += specialist_rebuttal.tokens_used or 0
            latency_used += specialist_rebuttal.latency_seconds

            debate_rounds.append({
                "round": round_num,
                "speaker": f"{specialist_name} Specialist",
                "content": specialist_position
            })

            # Check specialist agreement
            if _check_agreement(specialist_position):
                break

    return {
        "stage": f"consultation_{consultation_number}",
        "specialist": specialist_name,
        "specialist_id": specialist_id,
        "debate_rounds": debate_rounds,
        "total_rounds": len(debate_rounds),
        "tokens": tokens_used,
        "latency": latency_used
    }


def _check_agreement(text: str) -> bool:
    """
    Check if the text indicates agreement.
    """
    agreement_phrases = [
        "I AGREE",
        "I agree",
        "we agree",
        "reached agreement",
        "in agreement",
        "consensus"
    ]
    return any(phrase in text for phrase in agreement_phrases)


def _generalist_review(
    question: str,
    options_str: str,
    generalist_type: str,
    consultation_history: list,
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Generalist reviews all specialist consultations.
    """

    # Format consultation summaries
    consultations_summary = ""
    for item in consultation_history:
        if item["stage"].startswith("consultation_"):
            consultations_summary += f"\n\n**{item['specialist']} Consultation:**\n"
            consultations_summary += f"- Total rounds: {item['total_rounds']}\n"
            for round_info in item["debate_rounds"]:
                consultations_summary += f"\n[Round {round_info['round']} - {round_info['speaker']}]\n"
                consultations_summary += round_info['content'][:500] + "...\n"

    prompt = f"""You are a {generalist_type} physician reviewing specialist consultations for this case.

**Question:** {question}

**Options:** {options_str}

**Specialist Consultations Summary:**
{consultations_summary}

**Your Task as Reviewer:**
1. Identify areas of agreement between specialists
2. Identify any disagreements or gaps in the consultations
3. Note any key points that emerged from the debates
4. Assess the strength of evidence for different diagnoses
5. Identify any additional considerations not covered by specialists

Provide your comprehensive review.
"""

    response = llm_client.complete(prompt)

    return {
        "stage": "review",
        "review": response.content,
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds
    }


def _generalist_final_decision(
    question: str,
    options_str: str,
    generalist_type: str,
    consultation_history: list,
    review_summary: str,
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Generalist makes final decision integrating all input.
    """

    prompt = f"""You are a {generalist_type} physician making the final clinical decision for this case.

**Question:** {question}

**Options:** {options_str}

**Your Review Summary:**
{review_summary}

**Your Task - Final Decision:**
Based on all the specialist consultations and your review:
1. Provide a final differential diagnosis
2. Select the best answer from the options
3. Justify your decision with clear reasoning
4. Reference key insights from specialist consultations

**Output Format:**
FINAL ANSWER: [A, B, C, or D]
DIFFERENTIAL DIAGNOSIS:
1. [Most likely diagnosis and probability]
2. [Second most likely diagnosis and probability]
3. [Third most likely diagnosis and probability]

JUSTIFICATION: [Comprehensive reasoning for your final answer, incorporating specialist input]
"""

    response = llm_client.complete(prompt)

    return {
        "stage": "final_decision",
        "decision": response.content,
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract the final answer from decision text."""
    lines = text.split('\n')
    for line in lines:
        if line.upper().startswith('FINAL ANSWER:'):
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
