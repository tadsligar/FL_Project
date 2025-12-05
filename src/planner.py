"""
Planner agent: triage, enumerate, score, and select Top-K specialties.
"""

import json
from pathlib import Path
from typing import Optional

from .catalog import get_catalog, validate_specialty_ids, get_specialty_ids, Specialty
from .config import Config
from .llm_client import LLMClient, LLMResponse
from .schemas import PlannerResult


def load_planner_prompt() -> str:
    """Load the planner prompt template."""
    prompt_path = Path(__file__).parent / "prompts" / "planner.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def format_catalog_for_prompt(catalog: list[Specialty]) -> str:
    """Format the specialty catalog for inclusion in the prompt."""
    lines = []
    for spec in catalog:
        lines.append(f"- `{spec.id}`: {spec.display_name} ({spec.type})")
    return "\n".join(lines)


def run_planner(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config
) -> tuple[PlannerResult, LLMResponse]:
    """
    Run the planner agent to select Top-K specialties.

    Args:
        question: Clinical question or case
        options: Optional multiple choice options
        llm_client: LLM client instance
        config: Configuration

    Returns:
        (PlannerResult, LLMResponse) tuple
    """
    # Load catalog
    catalog = get_catalog()

    # Format prompt
    prompt_template = load_planner_prompt()
    prompt = prompt_template.format(
        question=question,
        options=options if options else "None",
        catalog=format_catalog_for_prompt(catalog),
        top_k=config.planner.top_k,
        red_flags=", ".join(config.planner.emergency_red_flags),
        pediatric_signals=", ".join(config.planner.pediatric_signals)
    )

    # Call LLM (planner needs more tokens to enumerate all specialties)
    # Use agent-specific temperature if configured, otherwise use default
    # Increased to 3500 for larger models (qwen2.5:32b) that generate verbose reasoning
    temp = config.agent_temperatures.planner if config.agent_temperatures.planner is not None else config.temperature
    response = llm_client.complete(prompt, max_tokens=3500, temperature=temp)

    # Parse JSON response
    try:
        result_dict = _extract_json(response.content)
        planner_result = PlannerResult(**result_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse planner response: {e}\n\nResponse: {response.content}")

    # Validate specialty IDs
    is_valid, invalid_ids = validate_specialty_ids(planner_result.selected_specialties)
    if not is_valid:
        if config.budgets.max_retries > 0:
            # Retry with correction prompt
            try:
                return _retry_planner_with_correction(
                    question=question,
                    options=options,
                    llm_client=llm_client,
                    config=config,
                    original_response=response.content,
                    invalid_ids=invalid_ids,
                    valid_ids=get_specialty_ids()
                )
            except ValueError as retry_error:
                # If retry also fails, fall back to filtering out invalid IDs
                print(f"WARNING: Retry failed, filtering out invalid specialty IDs: {invalid_ids}")
                valid_selections = [sid for sid in planner_result.selected_specialties if sid not in invalid_ids]

                # Ensure we have at least top_k valid specialties
                if len(valid_selections) < config.planner.top_k:
                    # Add top-scored valid specialties to reach top_k
                    all_valid_ids = set(get_specialty_ids())
                    available_ids = [s.specialty_id for s in planner_result.scored_catalog
                                    if s.specialty_id in all_valid_ids and s.specialty_id not in valid_selections]
                    # Sort by relevance score
                    available_sorted = sorted(
                        [s for s in planner_result.scored_catalog if s.specialty_id in available_ids],
                        key=lambda x: x.relevance,
                        reverse=True
                    )
                    needed = config.planner.top_k - len(valid_selections)
                    valid_selections.extend([s.specialty_id for s in available_sorted[:needed]])

                planner_result.selected_specialties = valid_selections[:config.planner.top_k]
                print(f"Filtered selections: {planner_result.selected_specialties}")
        else:
            raise ValueError(f"Planner selected invalid specialty IDs: {invalid_ids}")

    # Validate scored catalog
    scored_ids = [s.specialty_id for s in planner_result.scored_catalog]
    is_valid_scored, invalid_scored = validate_specialty_ids(scored_ids)
    if not is_valid_scored:
        # Filter out invalid entries (safety fallback)
        planner_result.scored_catalog = [
            s for s in planner_result.scored_catalog
            if s.specialty_id not in invalid_scored
        ]

    return planner_result, response


def _retry_planner_with_correction(
    question: str,
    options: Optional[list[str]],
    llm_client: LLMClient,
    config: Config,
    original_response: str,
    invalid_ids: list[str],
    valid_ids: list[str]
) -> tuple[PlannerResult, LLMResponse]:
    """Retry planner call with correction for invalid specialty IDs."""

    catalog = get_catalog()

    correction_prompt = f"""CRITICAL ERROR: Your previous response used INVALID specialty IDs.

[ERROR] INVALID IDs YOU USED: {', '.join(invalid_ids)}

These specialty IDs DO NOT EXIST in our catalog. They will cause the system to FAIL.

[VALID] COMPLETE LIST OF VALID SPECIALTY IDs (use ONLY these):
{chr(10).join(f"  - {sid}" for sid in valid_ids)}

INSTRUCTIONS:
1. Do NOT use "{', '.join(invalid_ids)}" - these are INVALID
2. ONLY use specialty IDs from the list above
3. Copy the specialty ID EXACTLY as shown (including underscores, lowercase)
4. If you want "{invalid_ids[0] if invalid_ids else 'a specialty'}", find the closest match from the valid list
5. Output ONLY valid JSON - no comments, no extra text

Provide a CORRECTED response now with ONLY valid specialty IDs from the list above:"""

    temp = config.agent_temperatures.planner if config.agent_temperatures.planner is not None else config.temperature
    response = llm_client.complete(correction_prompt, max_tokens=2500, temperature=temp)

    try:
        result_dict = _extract_json(response.content)
        planner_result = PlannerResult(**result_dict)

        # Validate again
        is_valid, still_invalid = validate_specialty_ids(planner_result.selected_specialties)
        if not is_valid:
            raise ValueError(
                f"Planner still selected invalid specialty IDs after retry: {still_invalid}\n\n"
                f"Response: {response.content}"
            )

        return planner_result, response
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"Failed to parse planner response after retry: {e}\n\n"
            f"Response: {response.content}"
        )


# Import shared JSON extraction utility
from .json_utils import extract_json_from_llm_response as _extract_json
