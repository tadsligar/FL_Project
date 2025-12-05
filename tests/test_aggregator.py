"""
Tests for aggregator agent.
"""

import pytest

from src.aggregator import run_aggregator
from src.config import Config
from src.llm_client import MockLLMClient
from src.schemas import SpecialistReport, DifferentialItem


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
def mock_specialist_reports():
    """Create mock specialist reports."""
    return [
        SpecialistReport(
            specialty_id="cardiology",
            differential=[
                DifferentialItem(
                    dx="Acute Myocardial Infarction",
                    p=0.7,
                    evidence_for=["chest pain", "radiation to arm"],
                    evidence_against=[],
                    discriminators=["ECG", "troponin"]
                ),
                DifferentialItem(
                    dx="Unstable Angina",
                    p=0.2,
                    evidence_for=["chest pain"],
                    evidence_against=[],
                    discriminators=["negative troponin"]
                )
            ],
            notes="Consider immediate catheterization"
        ),
        SpecialistReport(
            specialty_id="pulmonology",
            differential=[
                DifferentialItem(
                    dx="Pulmonary Embolism",
                    p=0.3,
                    evidence_for=["chest pain"],
                    evidence_against=["no dyspnea mentioned"],
                    discriminators=["D-dimer", "CT angiography"]
                )
            ],
            notes="PE remains in differential"
        )
    ]


def test_run_aggregator_basic(mock_llm_client, mock_config, mock_specialist_reports):
    """Test basic aggregator execution."""
    question = "A 65-year-old man with chest pain."
    options = ["A. GERD", "B. MI", "C. PE", "D. MSK"]

    final_decision, response = run_aggregator(
        question=question,
        options=options,
        specialist_reports=mock_specialist_reports,
        llm_client=mock_llm_client,
        config=mock_config
    )

    # Check final decision structure
    assert final_decision.final_answer
    assert len(final_decision.ordered_differential) > 0
    assert final_decision.justification

    # Check differential items
    for item in final_decision.ordered_differential:
        assert item.dx
        assert 0.0 <= item.p <= 1.0

    # Warnings can be empty
    assert isinstance(final_decision.warnings, list)


def test_aggregator_merges_reports(mock_llm_client, mock_config, mock_specialist_reports):
    """Test that aggregator merges multiple specialist reports."""
    question = "Test case"

    final_decision, _ = run_aggregator(
        question=question,
        options=None,
        specialist_reports=mock_specialist_reports,
        llm_client=mock_llm_client,
        config=mock_config
    )

    # Should produce a single unified differential
    assert len(final_decision.ordered_differential) > 0
    assert final_decision.final_answer


def test_aggregator_with_single_report(mock_llm_client, mock_config, mock_specialist_reports):
    """Test aggregator with just one specialist report."""
    question = "Test case"

    final_decision, _ = run_aggregator(
        question=question,
        options=None,
        specialist_reports=[mock_specialist_reports[0]],
        llm_client=mock_llm_client,
        config=mock_config
    )

    assert final_decision.final_answer
    assert len(final_decision.ordered_differential) > 0


def test_aggregator_requires_reports(mock_llm_client, mock_config):
    """Test that aggregator requires at least one report."""
    question = "Test case"

    with pytest.raises(ValueError, match="No specialist reports"):
        run_aggregator(
            question=question,
            options=None,
            specialist_reports=[],
            llm_client=mock_llm_client,
            config=mock_config
        )
