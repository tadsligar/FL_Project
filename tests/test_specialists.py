"""
Tests for specialist agents.
"""

import pytest

from src.config import Config
from src.llm_client import MockLLMClient
from src.schemas import PlannerResult, ScoredSpecialty
from src.specialists import run_specialist, run_specialists


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return Config(
        provider="mock",
        model="mock-model",
        temperature=0.3,
        max_output_tokens=800,
    )


@pytest.fixture
def mock_llm_client(mock_config):
    """Create a mock LLM client."""
    return MockLLMClient(mock_config)


@pytest.fixture
def mock_planner_result():
    """Create a mock planner result."""
    return PlannerResult(
        triage_generalist="emergency_medicine",
        scored_catalog=[
            ScoredSpecialty(
                specialty_id="cardiology",
                relevance=0.9,
                coverage_gain=0.8,
                urgency_alignment=0.9,
                procedural_signal=0.3,
                reason="Cardiac symptoms"
            )
        ],
        selected_specialties=["cardiology", "pulmonology"],
        rationale="Test rationale"
    )


def test_run_specialist_basic(mock_llm_client, mock_config, mock_planner_result):
    """Test basic specialist execution."""
    question = "A 65-year-old man with chest pain."
    options = ["A. GERD", "B. MI"]

    report, response = run_specialist(
        specialty_id="cardiology",
        question=question,
        options=options,
        planner_result=mock_planner_result,
        llm_client=mock_llm_client,
        config=mock_config
    )

    # Check report structure
    assert report.specialty_id == "cardiology"
    assert len(report.differential) <= 3
    assert len(report.differential) > 0

    # Check differential items
    for item in report.differential:
        assert item.dx
        assert 0.0 <= item.p <= 1.0
        assert isinstance(item.evidence_for, list)
        assert isinstance(item.evidence_against, list)
        assert isinstance(item.discriminators, list)

    # Check probabilities sum to <= 1.0
    total_p = sum(item.p for item in report.differential)
    assert total_p <= 1.01  # Small tolerance for floating point


def test_run_specialists_multiple(mock_llm_client, mock_config, mock_planner_result):
    """Test running multiple specialists."""
    question = "Test question"

    results = run_specialists(
        selected_specialties=["cardiology", "pulmonology"],
        question=question,
        options=None,
        planner_result=mock_planner_result,
        llm_client=mock_llm_client,
        config=mock_config
    )

    assert len(results) == 2

    for report, response in results:
        assert report.specialty_id in ["cardiology", "pulmonology"]
        assert len(report.differential) > 0


def test_specialist_validates_schema(mock_llm_client, mock_config, mock_planner_result):
    """Test that specialist output validates against schema."""
    question = "Test case"

    report, _ = run_specialist(
        specialty_id="neurology",
        question=question,
        options=None,
        planner_result=mock_planner_result,
        llm_client=mock_llm_client,
        config=mock_config
    )

    # Should not raise validation errors
    assert report.specialty_id
    assert report.differential
