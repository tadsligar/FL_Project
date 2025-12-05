"""
Baseline 5: Answer Space Consultation with Generalist-Led Hypothesis Testing

Architecture:
1. Generalist analyzes ALL FOUR answer choices as a complete set
2. Identifies which medical domains/specialties the answer space represents
3. Selects 2-3 specialists to evaluate across the full answer space
4. Each specialist sees ALL options and must choose the best one
5. Generalist challenges each specialist with counterpoints from OTHER answers
6. Specialist must defend OR revise their choice
7. Aggregator synthesizes across all consultations
8. Optional reviewer checks the final decision

Key Innovation: Specialists evaluate the COMPLETE answer space, not individual answers.
"""

from typing import Optional
from ..config import Config
from ..llm_client import LLMClient
from ..catalog import get_specialty_by_id, get_catalog


def run_answer_space_consultation(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Run answer space consultation with generalist-led hypothesis testing.

    Args:
        question: Clinical question
        options: Multiple choice options (A, B, C, D)
        llm_client: LLM client
        config: Configuration

    Returns:
        Dict with answer, reasoning, tokens, latency
    """

    options_str = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)]) if options else "No options"

    total_tokens = 0
    total_latency = 0.0

    # Phase 1: Generalist analyzes the complete answer space
    answer_space_analysis = _analyze_answer_space(
        question, options_str, llm_client, config
    )
    total_tokens += answer_space_analysis["tokens"]
    total_latency += answer_space_analysis["latency"]

    selected_specialists = answer_space_analysis["specialists"]
    specialist_rationales = answer_space_analysis.get("specialist_rationales", {})

    # Phase 2: Parallel specialist consultations
    consultations = []
    for specialist_id in selected_specialists:
        specialty = get_specialty_by_id(specialist_id)

        # Handle hallucinated specialists (not in catalog)
        if not specialty:
            # Create a display name from the specialist_id
            specialist_name = specialist_id.replace('_', ' ').title()
            print(f"INFO: Using hallucinated specialist '{specialist_name}' for consultation")
        else:
            specialist_name = specialty.display_name

        # Get specialist-specific rationale
        selection_rationale = specialist_rationales.get(
            specialist_id,
            f"Selected to evaluate the answer space from {specialist_name} perspective."
        )

        consultation = _consult_specialist(
            question=question,
            options_str=options_str,
            specialist_name=specialist_name,
            specialist_id=specialist_id,
            answer_space_rationale=answer_space_analysis["rationale"],
            selection_rationale=selection_rationale,  # NEW: Pass specific rationale
            llm_client=llm_client,
            config=config
        )

        total_tokens += consultation["tokens"]
        total_latency += consultation["latency"]
        consultations.append(consultation)

    # Phase 3: Aggregation
    aggregation = _aggregate_consultations(
        question=question,
        options_str=options_str,
        consultations=consultations,
        llm_client=llm_client,
        config=config
    )

    total_tokens += aggregation["tokens"]
    total_latency += aggregation["latency"]

    # Phase 4: Review (optional)
    review = _review_decision(
        question=question,
        options_str=options_str,
        consultations=consultations,
        aggregation=aggregation,
        llm_client=llm_client,
        config=config
    )

    total_tokens += review["tokens"]
    total_latency += review["latency"]

    # Extract final answer
    final_answer = _extract_answer(review["final_decision"], options)

    return {
        "method": "answer_space_consultation",
        "answer": final_answer,
        "agents_used": 1 + len(consultations) + 1 + 1,  # generalist + specialists + aggregator + reviewer
        "tokens_used": total_tokens,
        "latency_seconds": total_latency,
        "answer_space_analysis": answer_space_analysis,
        "consultations": consultations,
        "aggregation": aggregation,
        "review": review
    }


def _analyze_answer_space(
    question: str,
    options_str: str,
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Generalist analyzes the complete answer space to identify relevant specialties.
    """

    # Get catalog for specialist selection
    catalog = get_catalog()
    catalog_list = "\n".join([f"- {s.id}: {s.display_name}" for s in catalog])

    prompt = f"""You are a generalist physician (Family Medicine/Internal Medicine) analyzing a clinical case.

**Question:** {question}

**Answer Choices:**
{options_str}

**Your Task - Analyze the Complete Answer Space:**

Look at ALL FOUR answer choices together. What do they collectively tell you about the differential diagnosis?

1. **Answer Space Analysis:**
   - Answer A suggests: [diagnosis/treatment approach and medical domain]
   - Answer B suggests: [diagnosis/treatment approach and medical domain]
   - Answer C suggests: [diagnosis/treatment approach and medical domain]
   - Answer D suggests: [diagnosis/treatment approach and medical domain]

2. **Medical Domains Represented:**
   Based on these four answers, which medical specialties are relevant?
   (e.g., if answers span cardiac vs respiratory, you need Cardiology and Pulmonology)

3. **Specialist Selection:**
   Select 2-3 specialists who can best evaluate this answer space.
   You may choose from the common specialists below, or suggest other specialties if needed.

**Common Specialists (examples):**
{catalog_list}

**Output Format:**
ANSWER SPACE ANALYSIS:
- Answer A: [implications]
- Answer B: [implications]
- Answer C: [implications]
- Answer D: [implications]

DOMAINS: [list of medical domains/organ systems involved]

SPECIALISTS TO CONSULT:
1. [specialty name or id] - [rationale for why this specialist is needed]
2. [specialty name or id] - [rationale]
3. [specialty name or id] - [rationale, if needed]

RATIONALE: [Overall explanation of specialist selection based on answer space]
"""

    response = llm_client.complete(prompt, max_tokens=2000)

    # Parse specialists
    import re
    specialists = []
    seen_specialists = set()  # Track to prevent duplicates
    lines = response.content.split('\n')

    # Get valid specialist IDs from catalog
    valid_ids = {s.id for s in catalog}
    valid_names = {s.display_name.lower(): s.id for s in catalog}

    # Find the section with specialist selections
    in_specialist_section = False
    for line in lines:
        # Detect start of specialist section
        if 'SPECIALISTS TO CONSULT' in line.upper():
            in_specialist_section = True
            continue

        # Stop at next major section
        if in_specialist_section and line.strip().startswith('**') and 'RATIONALE' in line.upper():
            break

        # Only parse within specialist section
        if in_specialist_section:
            # Pattern 1: "1. specialty_id" or "1. **specialty_id**" or "1. Specialty Name"
            match = re.search(r'^\d+\.\s+\*?\*?([A-Za-z\s]+?)\*?\*?\s*[-:]', line)
            if match:
                spec_text = match.group(1).strip().lower()

                # Try to match against catalog IDs first
                if spec_text in valid_ids and spec_text not in seen_specialists:
                    specialists.append(spec_text)
                    seen_specialists.add(spec_text)
                    if len(specialists) >= 3:
                        break
                    continue

                # Try to match against catalog display names
                if spec_text in valid_names and valid_names[spec_text] not in seen_specialists:
                    specialists.append(valid_names[spec_text])
                    seen_specialists.add(valid_names[spec_text])
                    if len(specialists) >= 3:
                        break
                    continue

                # Accept hallucinated specialist (not in catalog)
                if spec_text not in seen_specialists:
                    print(f"INFO: Using hallucinated specialist '{spec_text}' (not in catalog)")
                    specialists.append(spec_text)
                    seen_specialists.add(spec_text)
                    if len(specialists) >= 3:
                        break
                    continue

    # Fallback if parsing failed
    if not specialists:
        print(f"WARNING: Failed to parse specialists from response, using fallback")
        print(f"Response: {response.content[:500]}")
        specialists = ["cardiology", "pulmonology"]
        seen_specialists = set(specialists)

    # Ensure no duplicates in final list
    specialists = list(dict.fromkeys(specialists))  # Preserve order, remove duplicates

    # Limit to 3 specialists
    specialists = specialists[:3]

    # Extract individual specialist rationales
    specialist_rationales = {}
    in_specialist_section = False
    current_specialist = None
    current_rationale = []

    for line in lines:
        if 'SPECIALISTS TO CONSULT' in line.upper():
            in_specialist_section = True
            continue

        if in_specialist_section and ('RATIONALE' in line.upper() or '**RATIONALE' in line.upper()):
            # Save last specialist if exists
            if current_specialist and current_rationale:
                specialist_rationales[current_specialist] = ' '.join(current_rationale)
            break

        if in_specialist_section:
            # Check if this line starts a new specialist entry
            match = re.search(r'^\d+\.\s+\*?\*?([A-Za-z\s]+?)\*?\*?\s*[-:]\s*(.+)', line)
            if match:
                # Save previous specialist rationale
                if current_specialist and current_rationale:
                    specialist_rationales[current_specialist] = ' '.join(current_rationale)

                # Start new specialist
                spec_text = match.group(1).strip().lower()
                rationale_text = match.group(2).strip()
                if spec_text in specialists:  # Only track specialists we selected
                    current_specialist = spec_text
                    current_rationale = [rationale_text]
            elif current_specialist and line.strip() and not line.strip().startswith('**'):
                # Continue building current rationale
                current_rationale.append(line.strip())

    # Save last specialist if exists
    if current_specialist and current_rationale:
        specialist_rationales[current_specialist] = ' '.join(current_rationale)

    # Ensure all specialists have at least a default rationale
    for spec in specialists:
        if spec not in specialist_rationales:
            specialty = get_specialty_by_id(spec)
            if specialty:
                specialist_rationales[spec] = f"Selected to evaluate the answer space from {specialty.display_name} perspective."
            else:
                # Hallucinated specialist - use spec ID directly
                spec_name = spec.replace('_', ' ').title()
                specialist_rationales[spec] = f"Selected to evaluate the answer space from {spec_name} perspective."

    return {
        "analysis": response.content,
        "specialists": specialists,
        "specialist_rationales": specialist_rationales,  # NEW: Individual rationales
        "rationale": response.content,
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds
    }


def _consult_specialist(
    question: str,
    options_str: str,
    specialist_name: str,
    specialist_id: str,
    answer_space_rationale: str,
    selection_rationale: str,  # NEW: Specific reason for selecting this specialist
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Consult a specialist who evaluates the complete answer space.
    """

    # Step 1: Initial assessment across all options
    initial_prompt = f"""You are a {specialist_name} specialist consulted by a generalist physician.

**Question:** {question}

**Answer Choices:**
{options_str}

**Why You Were Selected:**
{selection_rationale}

**General Answer Space Context:**
{answer_space_rationale[:500]}...

**Your Task:**
Evaluate ALL FOUR answer choices from your specialty's perspective.

1. **For each answer, assess:**
   - Is it appropriate/correct from your specialty's viewpoint?
   - What diagnosis or condition does it imply?
   - What evidence supports or contradicts it?

2. **Select the BEST answer:**
   Which answer (A, B, C, or D) is most appropriate?

**Output Format:**

EVALUATION:
- Answer A: [appropriate/inappropriate] because [reasoning]
- Answer B: [appropriate/inappropriate] because [reasoning]
- Answer C: [appropriate/inappropriate] because [reasoning]
- Answer D: [appropriate/inappropriate] because [reasoning]

BEST ANSWER: [A/B/C/D]

KEY REASONING:
[2-3 sentences explaining why your chosen answer is best]

CONFIDENCE: [HIGH/MEDIUM/LOW]
"""

    initial_response = llm_client.complete(initial_prompt, max_tokens=1500)
    initial_answer = _extract_answer(initial_response.content, None)

    # Step 2: Generalist challenges with counterpoints from OTHER answers
    challenge_prompt = f"""You initially selected Answer {initial_answer}.

**Your Initial Assessment:**
{initial_response.content}

**Generalist Challenges:**

The generalist asks you to reconsider by addressing counterpoints from the OTHER answer choices:

"""

    # Generate challenges for each of the other 3 answers
    other_answers = ["A", "B", "C", "D"]
    other_answers.remove(initial_answer)

    for i, other_ans in enumerate(other_answers, 1):
        challenge_prompt += f"""
CHALLENGE {i} - Why not Answer {other_ans}?
Answer {other_ans} suggests a different approach. Specifically address:
- What evidence from the case supports Answer {other_ans}?
- Why is Answer {initial_answer} BETTER than Answer {other_ans}?
- Could Answer {other_ans} be correct instead?
"""

    challenge_prompt += f"""

**Your Task:**

Address EACH challenge. For each, either:
1. DEFEND your original answer with specific evidence, OR
2. REVISE your assessment if the challenge reveals you were wrong, OR
3. DEFER to another specialty if you realize this is outside your domain

**Format:**

RESPONSE TO CHALLENGE 1 (Answer {other_answers[0]}):
[Specific response with clinical reasoning]

RESPONSE TO CHALLENGE 2 (Answer {other_answers[1]}):
[Specific response with clinical reasoning]

RESPONSE TO CHALLENGE 3 (Answer {other_answers[2]}):
[Specific response with clinical reasoning]

FINAL STANCE:
ANSWER: [A/B/C/D]
CHANGED MIND: [YES/NO - if yes, explain what changed your mind]
CONFIDENCE: [HIGH/MEDIUM/LOW]

If you want to DEFER to another specialty:
DEFER TO: [specialty name]
REASON: [why they would be more appropriate]
"""

    challenge_response = llm_client.complete(challenge_prompt, max_tokens=1800)
    final_answer = _extract_answer(challenge_response.content, None)

    # Check if specialist changed their mind
    changed_mind = initial_answer != final_answer

    # Check for deferral
    deferred = "DEFER TO:" in challenge_response.content.upper()

    return {
        "specialist": specialist_name,
        "specialist_id": specialist_id,
        "initial_answer": initial_answer,
        "initial_reasoning": initial_response.content,
        "challenges": challenge_prompt,
        "final_response": challenge_response.content,
        "final_answer": final_answer,
        "changed_mind": changed_mind,
        "deferred": deferred,
        "tokens": (initial_response.tokens_used or 0) + (challenge_response.tokens_used or 0),
        "latency": initial_response.latency_seconds + challenge_response.latency_seconds
    }


def _aggregate_consultations(
    question: str,
    options_str: str,
    consultations: list[dict],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Aggregate specialist consultations into a final decision.
    """

    # Format consultation summary
    summary = "SPECIALIST CONSULTATIONS:\n\n"
    for i, consult in enumerate(consultations, 1):
        summary += f"[{consult['specialist']}]\n"
        summary += f"- Initial answer: {consult['initial_answer']}\n"
        summary += f"- Final answer: {consult['final_answer']}\n"
        summary += f"- Changed mind: {'Yes' if consult['changed_mind'] else 'No'}\n"
        summary += f"- Deferred: {'Yes' if consult['deferred'] else 'No'}\n"
        summary += f"\nKey reasoning:\n{consult['final_response'][:500]}...\n\n"

    # Check for consensus
    final_answers = [c["final_answer"] for c in consultations]
    from collections import Counter
    answer_counts = Counter(final_answers)
    consensus = len(answer_counts) == 1
    majority_answer = answer_counts.most_common(1)[0][0] if answer_counts else "UNKNOWN"

    prompt = f"""You are aggregating specialist consultations to make a final decision.

**Question:** {question}

**Answer Choices:**
{options_str}

{summary}

**Analysis:**
- Consensus: {"YES - all agree on " + majority_answer if consensus else "NO - disagreement"}
- Answer distribution: {dict(answer_counts)}
- Specialists who changed their mind: {sum(1 for c in consultations if c['changed_mind'])}

**Your Task:**

1. If there's consensus: Verify the reasoning is sound
2. If there's disagreement: Weigh the strength of evidence from each specialist
3. Consider: Which specialist is most relevant to this case?
4. Consider: Who provided the most convincing evidence?
5. Consider: Did any specialist identify a critical flaw in alternatives?

**Output Format:**

EVIDENCE ANALYSIS:
[Summarize the key evidence supporting each answer]

DECISION RATIONALE:
[2-3 sentences explaining your final decision]

FINAL ANSWER: [A/B/C/D]
"""

    response = llm_client.complete(prompt, max_tokens=1200)

    return {
        "summary": summary,
        "consensus": consensus,
        "answer_distribution": dict(answer_counts),
        "aggregation_reasoning": response.content,
        "aggregated_answer": _extract_answer(response.content, None),
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds
    }


def _review_decision(
    question: str,
    options_str: str,
    consultations: list[dict],
    aggregation: dict,
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Final review by generalist to check the aggregated decision.
    """

    prompt = f"""You are a generalist physician reviewing the final decision.

**Question:** {question}

**Answer Choices:**
{options_str}

**Specialist Consultations:**
{aggregation['summary'][:800]}

**Aggregator's Decision:**
{aggregation['aggregation_reasoning']}

**Aggregator chose: Answer {aggregation['aggregated_answer']}**

**Your Task as Reviewer:**

1. Is the aggregator's reasoning sound?
2. Did they properly weigh the specialist input?
3. Are there any critical findings overlooked?
4. Is there reason to doubt this decision?

If you find a problem, you can OVERRIDE the aggregator.

**Output Format:**

REVIEW:
[Your analysis of the aggregator's decision]

VERDICT: [APPROVE / OVERRIDE]

If OVERRIDE:
CORRECTED ANSWER: [A/B/C/D]
REASON: [Why you're overriding]

If APPROVE:
FINAL ANSWER: {aggregation['aggregated_answer']}
"""

    response = llm_client.complete(prompt, max_tokens=1000)

    # Check if reviewer overrode
    override = "OVERRIDE" in response.content and "VERDICT: OVERRIDE" in response.content

    if override:
        final_answer = _extract_answer(response.content, None)
    else:
        final_answer = aggregation['aggregated_answer']

    return {
        "review": response.content,
        "override": override,
        "final_decision": response.content,
        "final_answer": final_answer,
        "tokens": response.tokens_used or 0,
        "latency": response.latency_seconds
    }


def _extract_answer(text: str, options: Optional[list[str]]) -> str:
    """Extract the final answer from response text."""
    import re

    # Look for explicit answer statements
    patterns = [
        r'FINAL ANSWER:\s*([A-D])',
        r'ANSWER:\s*([A-D])',
        r'BEST ANSWER:\s*([A-D])',
        r'CORRECTED ANSWER:\s*([A-D])',
        r'\b([A-D])\b'  # Any single letter
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return "UNKNOWN"
