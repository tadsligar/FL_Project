"""
Safety guardrails and validation.
Ensures system operates within safe boundaries.
"""

import re
from typing import Optional

from .catalog import validate_specialty_ids, get_specialty_ids
from .config import Config
from .schemas import PlannerResult, SpecialistReport, FinalDecision


# Educational use disclaimer
DISCLAIMER = """
╔════════════════════════════════════════════════════════════════╗
║                    EDUCATIONAL USE ONLY                        ║
╠════════════════════════════════════════════════════════════════╣
║  This is a research prototype for academic purposes only.     ║
║  NOT intended for clinical use, medical diagnosis, or          ║
║  patient care. Do not use this system to make medical         ║
║  decisions.                                                     ║
╚════════════════════════════════════════════════════════════════╝
"""


def print_disclaimer():
    """Print the educational use disclaimer."""
    print(DISCLAIMER)


def validate_planner_output(result: PlannerResult, config: Config) -> tuple[bool, list[str]]:
    """
    Validate planner output for safety.

    Args:
        result: Planner result
        config: Configuration

    Returns:
        (is_valid, warnings) tuple
    """
    warnings = []

    # Check specialty IDs are from catalog
    is_valid, invalid_ids = validate_specialty_ids(result.selected_specialties)
    if not is_valid:
        warnings.append(f"Invalid specialty IDs selected: {invalid_ids}")

    # Check scored catalog contains valid IDs
    scored_ids = [s.specialty_id for s in result.scored_catalog]
    is_valid_scored, invalid_scored = validate_specialty_ids(scored_ids)
    if not is_valid_scored:
        warnings.append(f"Invalid specialty IDs in scored catalog: {invalid_scored}")

    # Check selection count
    if len(result.selected_specialties) > config.budgets.max_specialists:
        warnings.append(
            f"Too many specialties selected: {len(result.selected_specialties)} "
            f"> {config.budgets.max_specialists}"
        )

    # Check for score validity
    for scored in result.scored_catalog:
        if not (0.0 <= scored.relevance <= 1.0):
            warnings.append(f"Relevance score out of range for {scored.specialty_id}: {scored.relevance}")
        if not (0.0 <= scored.coverage_gain <= 1.0):
            warnings.append(f"Coverage gain out of range for {scored.specialty_id}: {scored.coverage_gain}")

    return len(warnings) == 0, warnings


def validate_specialist_output(report: SpecialistReport) -> tuple[bool, list[str]]:
    """
    Validate specialist output for safety.

    Args:
        report: Specialist report

    Returns:
        (is_valid, warnings) tuple
    """
    warnings = []

    # Check specialty ID is valid
    valid_ids = set(get_specialty_ids())
    if report.specialty_id not in valid_ids:
        warnings.append(f"Invalid specialty ID: {report.specialty_id}")

    # Check differential count
    if len(report.differential) > 3:
        warnings.append(f"Too many diagnoses in differential: {len(report.differential)} > 3")

    # Check probabilities
    total_p = sum(item.p for item in report.differential)
    if total_p > 1.01:  # Small tolerance
        warnings.append(f"Probabilities sum to {total_p:.2f} > 1.0")

    for item in report.differential:
        if not (0.0 <= item.p <= 1.0):
            warnings.append(f"Probability out of range for {item.dx}: {item.p}")

    return len(warnings) == 0, warnings


def validate_aggregator_output(decision: FinalDecision) -> tuple[bool, list[str]]:
    """
    Validate aggregator output for safety.

    Args:
        decision: Final decision

    Returns:
        (is_valid, warnings) tuple
    """
    warnings = []

    # Check that final answer is non-empty
    if not decision.final_answer or not decision.final_answer.strip():
        warnings.append("Final answer is empty")

    # Check differential probabilities
    for item in decision.ordered_differential:
        if not (0.0 <= item.p <= 1.0):
            warnings.append(f"Probability out of range for {item.dx}: {item.p}")

    return len(warnings) == 0, warnings


def check_for_phi(text: str) -> tuple[bool, list[str]]:
    """
    Check for potential PHI in text (basic heuristic).

    Args:
        text: Text to check

    Returns:
        (has_phi, warnings) tuple
    """
    warnings = []

    # Check for common PHI patterns (very basic)
    # SSN pattern
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
        warnings.append("Possible SSN detected")

    # MRN pattern (varies, but often numeric)
    if re.search(r'\b[Mm][Rr][Nn]\s*:?\s*\d+', text):
        warnings.append("Possible MRN detected")

    # Email addresses
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
        warnings.append("Email address detected")

    # Phone numbers
    if re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
        warnings.append("Possible phone number detected")

    # Dates in specific formats (MM/DD/YYYY, etc.)
    # Note: We allow "65-year-old" style mentions
    if re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b', text):
        warnings.append("Specific date detected (possible DOB)")

    return len(warnings) > 0, warnings


def sanitize_specialty_ids(specialty_ids: list[str]) -> list[str]:
    """
    Remove invalid specialty IDs from a list.

    Args:
        specialty_ids: List of specialty IDs

    Returns:
        Sanitized list with only valid IDs
    """
    valid_ids = set(get_specialty_ids())
    return [sid for sid in specialty_ids if sid in valid_ids]


def apply_safety_checks(
    question: str,
    planner_result: Optional[PlannerResult] = None,
    specialist_reports: Optional[list[SpecialistReport]] = None,
    final_decision: Optional[FinalDecision] = None,
    config: Optional[Config] = None
) -> list[str]:
    """
    Apply comprehensive safety checks.

    Args:
        question: Input question
        planner_result: Optional planner result
        specialist_reports: Optional specialist reports
        final_decision: Optional final decision
        config: Optional config

    Returns:
        List of warnings
    """
    all_warnings = []

    # Check for PHI in input
    has_phi, phi_warnings = check_for_phi(question)
    if has_phi:
        all_warnings.extend([f"[INPUT] {w}" for w in phi_warnings])

    # Validate planner
    if planner_result and config:
        is_valid, warnings = validate_planner_output(planner_result, config)
        if not is_valid:
            all_warnings.extend([f"[PLANNER] {w}" for w in warnings])

    # Validate specialists
    if specialist_reports:
        for report in specialist_reports:
            is_valid, warnings = validate_specialist_output(report)
            if not is_valid:
                all_warnings.extend([f"[SPECIALIST:{report.specialty_id}] {w}" for w in warnings])

    # Validate aggregator
    if final_decision:
        is_valid, warnings = validate_aggregator_output(final_decision)
        if not is_valid:
            all_warnings.extend([f"[AGGREGATOR] {w}" for w in warnings])

    return all_warnings
