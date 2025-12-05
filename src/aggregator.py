"""
Aggregator agent: merge specialist reports into final decision.
"""

import json
from pathlib import Path
from typing import Optional

from .config import Config
from .llm_client import LLMClient, LLMResponse
from .schemas import FinalDecision, SpecialistReport


def load_aggregator_prompt() -> str:
    """Load the aggregator prompt template."""
    prompt_path = Path(__file__).parent / "prompts" / "aggregator.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def format_specialist_reports(reports: list[SpecialistReport]) -> str:
    """Format specialist reports for inclusion in the prompt."""
    lines = []
    for i, report in enumerate(reports, 1):
        lines.append(f"\n### Specialist {i}: {report.specialty_id}")
        lines.append(f"**Differential:**")
        for dx_item in report.differential:
            lines.append(f"  - {dx_item.dx} (p={dx_item.p:.2f})")
            lines.append(f"    - Evidence for: {', '.join(dx_item.evidence_for)}")
            lines.append(f"    - Evidence against: {', '.join(dx_item.evidence_against)}")
            lines.append(f"    - Discriminators: {', '.join(dx_item.discriminators)}")
        if report.notes:
            lines.append(f"**Notes:** {report.notes}")

    return "\n".join(lines)


def run_aggregator(
    question: str,
    options: Optional[list[str]],
    specialist_reports: list[SpecialistReport],
    llm_client: LLMClient,
    config: Config,
    retry: bool = True
) -> tuple[FinalDecision, LLMResponse]:
    """
    Run the aggregator agent to produce final decision.

    Args:
        question: Clinical question or case
        options: Optional multiple choice options
        specialist_reports: List of specialist reports to merge
        llm_client: LLM client instance
        config: Configuration
        retry: Whether to retry on JSON parse failure

    Returns:
        (FinalDecision, LLMResponse) tuple
    """
    if not specialist_reports:
        raise ValueError("No specialist reports provided to aggregator")

    # Format prompt
    prompt_template = load_aggregator_prompt()
    prompt = prompt_template.format(
        question=question,
        options=options if options else "None",
        specialist_reports=format_specialist_reports(specialist_reports)
    )

    # Call LLM (aggregator needs more tokens to synthesize multiple reports)
    # Use agent-specific temperature if configured, otherwise use default
    temp = config.agent_temperatures.aggregator if config.agent_temperatures.aggregator is not None else config.temperature
    response = llm_client.complete(prompt, max_tokens=2000, temperature=temp)

    # Parse JSON response
    try:
        result_dict = _extract_json(response.content)
        final_decision = FinalDecision(**result_dict)
    except (json.JSONDecodeError, ValueError) as e:
        if retry and config.budgets.max_retries > 0:
            return _retry_aggregator_with_fix(
                question=question,
                options=options,
                specialist_reports=specialist_reports,
                llm_client=llm_client,
                config=config,
                original_response=response.content,
                error_msg=str(e)
            )
        else:
            raise ValueError(
                f"Failed to parse aggregator response: {e}\n\n"
                f"Response: {response.content}"
            )

    return final_decision, response


def _retry_aggregator_with_fix(
    question: str,
    options: Optional[list[str]],
    specialist_reports: list[SpecialistReport],
    llm_client: LLMClient,
    config: Config,
    original_response: str,
    error_msg: str
) -> tuple[FinalDecision, LLMResponse]:
    """Retry aggregator call with fix-JSON instruction."""

    fix_prompt = f"""The previous response had a JSON parsing error: {error_msg}

Original response:
{original_response}

Please provide a CORRECTED response with valid JSON only, matching the FinalDecision schema:
{{
  "final_answer": "A/B/C/D or diagnosis name",
  "ordered_differential": [
    {{
      "dx": "diagnosis",
      "p": 0.0-1.0,
      "evidence_for": ["..."],
      "evidence_against": ["..."],
      "discriminators": ["..."]
    }}
  ],
  "justification": "clear reasoning",
  "warnings": ["any warnings"]
}}

Ensure:
- Valid JSON syntax
- If options {options} are provided, final_answer should be the letter (A, B, C, D, etc.)
- No additional text outside the JSON
"""

    temp = config.agent_temperatures.aggregator if config.agent_temperatures.aggregator is not None else config.temperature
    response = llm_client.complete(fix_prompt, max_tokens=2000, temperature=temp)

    try:
        result_dict = _extract_json(response.content)
        final_decision = FinalDecision(**result_dict)
        return final_decision, response
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"Failed to parse aggregator response after retry: {e}\n\n"
            f"Response: {response.content}"
        )


# Import shared JSON extraction utility
from .json_utils import extract_json_from_llm_response as _extract_json
