"""
Tests for planner agent.
"""

import pytest

from src.config import Config
from src.llm_client import MockLLMClient
from src.planner import run_planner


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


def test_run_planner_basic(mock_llm_client, mock_config):
    """Test basic planner execution."""
    question = "A 65-year-old man with chest pain radiating to the left arm."
    options = ["A. GERD", "B. MI", "C. PE", "D. MSK pain"]

    planner_result, response = run_planner(
        question=question,
        options=options,
        llm_client=mock_llm_client,
        config=mock_config
    )

    # Check result structure
    assert planner_result.triage_generalist in ["emergency_medicine", "pediatrics", "family_internal_medicine"]
    assert len(planner_result.selected_specialties) <= mock_config.planner.top_k
    assert len(planner_result.selected_specialties) > 0
    assert len(planner_result.scored_catalog) > 0
    assert planner_result.rationale

    # Check response metadata
    assert response.model == "mock-model"
    assert response.latency_seconds >= 0


def test_planner_selects_valid_specialties(mock_llm_client, mock_config):
    """Test that planner only selects valid specialties."""
    from src.catalog import validate_specialty_ids

    question = "Test question"

    planner_result, _ = run_planner(
        question=question,
        options=None,
        llm_client=mock_llm_client,
        config=mock_config
    )

    is_valid, invalid_ids = validate_specialty_ids(planner_result.selected_specialties)
    assert is_valid, f"Planner selected invalid IDs: {invalid_ids}"


def test_planner_deterministic(mock_llm_client, mock_config):
    """Test that planner produces consistent results with same input."""
    question = "A 65-year-old man with chest pain."
    options = ["A. GERD", "B. MI"]

    result1, _ = run_planner(question, options, mock_llm_client, mock_config)
    result2, _ = run_planner(question, options, mock_llm_client, mock_config)

    # With mock client, should be identical
    assert result1.triage_generalist == result2.triage_generalist
    assert result1.selected_specialties == result2.selected_specialties


def test_planner_respects_top_k(mock_llm_client, mock_config):
    """Test that planner respects top_k limit."""
    question = "Complex multi-system case"

    planner_result, _ = run_planner(
        question=question,
        options=None,
        llm_client=mock_llm_client,
        config=mock_config
    )

    assert len(planner_result.selected_specialties) <= mock_config.planner.top_k
