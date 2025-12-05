"""
Specialist agents: produce differential diagnoses from specific specialty perspectives.
"""

import json
from pathlib import Path
from typing import Optional

from .catalog import get_specialty_by_id
from .config import Config
from .llm_client import LLMClient, LLMResponse
from .schemas import SpecialistReport, PlannerResult


def load_specialist_prompt() -> str:
    """Load the specialist prompt template."""
    prompt_path = Path(__file__).parent / "prompts" / "specialist.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def run_specialist(
    specialty_id: str,
    question: str,
    options: Optional[list[str]],
    planner_result: PlannerResult,
    llm_client: LLMClient,
    config: Config,
    retry: bool = True
) -> tuple[SpecialistReport, LLMResponse]:
    """
    Run a single specialist consultation.

    Args:
        specialty_id: ID of the specialty to consult
        question: Clinical question or case
        options: Optional multiple choice options
        planner_result: Output from the planner
        llm_client: LLM client instance
        config: Configuration
        retry: Whether to retry on JSON parse failure

    Returns:
        (SpecialistReport, LLMResponse) tuple
    """
    # Get specialty metadata
    specialty = get_specialty_by_id(specialty_id)
    if not specialty:
        raise ValueError(f"Invalid specialty ID: {specialty_id}")

    # Format prompt
    prompt_template = load_specialist_prompt()
    prompt = prompt_template.format(
        specialty_display_name=specialty.display_name,
        specialty_id=specialty_id,
        question=question,
        options=options if options else "None",
        planner_rationale=planner_result.rationale
    )

    # Call LLM
    # Use agent-specific temperature if configured, otherwise use default
    temp = config.agent_temperatures.specialist if config.agent_temperatures.specialist is not None else config.temperature
    response = llm_client.complete(prompt, temperature=temp)

    # Parse JSON response
    try:
        result_dict = _extract_json(response.content)
        specialist_report = SpecialistReport(**result_dict)
    except (json.JSONDecodeError, ValueError) as e:
        if retry and config.budgets.max_retries > 0:
            # Retry with fix-JSON instruction
            return _retry_specialist_with_fix(
                specialty_id=specialty_id,
                question=question,
                options=options,
                planner_result=planner_result,
                llm_client=llm_client,
                config=config,
                original_response=response.content,
                error_msg=str(e)
            )
        else:
            raise ValueError(
                f"Failed to parse specialist ({specialty_id}) response: {e}\n\n"
                f"Response: {response.content}"
            )

    # Validate specialty_id matches
    if specialist_report.specialty_id != specialty_id:
        specialist_report.specialty_id = specialty_id  # Force correction

    return specialist_report, response


def run_specialists(
    selected_specialties: list[str],
    question: str,
    options: Optional[list[str]],
    planner_result: PlannerResult,
    llm_client: LLMClient,
    config: Config
) -> list[tuple[SpecialistReport, LLMResponse]]:
    """
    Run multiple specialist consultations.

    Args:
        selected_specialties: List of specialty IDs
        question: Clinical question
        options: Optional multiple choice options
        planner_result: Planner output
        llm_client: LLM client
        config: Configuration

    Returns:
        List of (SpecialistReport, LLMResponse) tuples
    """
    results = []

    for specialty_id in selected_specialties:
        try:
            report, response = run_specialist(
                specialty_id=specialty_id,
                question=question,
                options=options,
                planner_result=planner_result,
                llm_client=llm_client,
                config=config
            )
            results.append((report, response))
        except Exception as e:
            # Log error but continue with other specialists
            print(f"Error running specialist {specialty_id}: {e}")
            # TODO: use proper logging
            continue

    if not results:
        raise ValueError("All specialist consultations failed")

    return results


def _retry_specialist_with_fix(
    specialty_id: str,
    question: str,
    options: Optional[list[str]],
    planner_result: PlannerResult,
    llm_client: LLMClient,
    config: Config,
    original_response: str,
    error_msg: str
) -> tuple[SpecialistReport, LLMResponse]:
    """Retry specialist call with fix-JSON instruction."""
    specialty = get_specialty_by_id(specialty_id)

    fix_prompt = f"""The previous response had a JSON parsing error: {error_msg}

Original response:
{original_response}

Please provide a CORRECTED response with valid JSON only, matching the SpecialistReport schema:
{{
  "specialty_id": "{specialty_id}",
  "differential": [
    {{
      "dx": "diagnosis name",
      "p": 0.0-1.0,
      "evidence_for": ["..."],
      "evidence_against": ["..."],
      "discriminators": ["..."]
    }}
  ],
  "notes": "..."
}}

Ensure:
- Valid JSON syntax
- Probabilities sum to ≤ 1.0
- Max 3 diagnoses
- No additional text outside the JSON
"""

    temp = config.agent_temperatures.specialist if config.agent_temperatures.specialist is not None else config.temperature
    response = llm_client.complete(fix_prompt, temperature=temp)

    try:
        result_dict = _extract_json(response.content)
        specialist_report = SpecialistReport(**result_dict)
        specialist_report.specialty_id = specialty_id  # Ensure correct ID
        return specialist_report, response
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"Failed to parse specialist ({specialty_id}) response after retry: {e}\n\n"
            f"Response: {response.content}"
        )


# Import shared JSON extraction utility
from .json_utils import extract_json_from_llm_response as _extract_json
