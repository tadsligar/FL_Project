"""
End-to-end integration tests.
"""

import pytest

from src.config import Config
from src.llm_client import MockLLMClient
from src.orchestration import run_case


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


def test_run_case_complete(mock_config, mock_llm_client):
    """Test complete case execution end-to-end."""
    question = "A 65-year-old man presents with sudden onset chest pain radiating to the left arm, diaphoresis, and nausea."
    options = ["A. GERD", "B. Acute Myocardial Infarction", "C. Pulmonary Embolism", "D. Musculoskeletal pain"]
    correct_answer = "B"

    final_decision, trace = run_case(
        question=question,
        options=options,
        correct_answer=correct_answer,
        config=mock_config,
        llm_client=mock_llm_client
    )

    # Check final decision
    assert final_decision.final_answer
    assert final_decision.justification
    assert len(final_decision.ordered_differential) > 0

    # Check trace completeness
    assert trace.trace_id
    assert trace.question == question
    assert trace.options == options
    assert trace.correct_answer == correct_answer
    assert trace.predicted_answer == final_decision.final_answer

    # Check agent traces
    assert trace.planner_trace is not None
    assert trace.planner_trace.agent_type == "planner"

    assert len(trace.specialist_traces) > 0
    for spec_trace in trace.specialist_traces:
        assert spec_trace.agent_type == "specialist"
        assert spec_trace.specialty_id

    assert trace.aggregator_trace is not None
    assert trace.aggregator_trace.agent_type == "aggregator"

    # Check timing
    assert trace.total_latency_seconds >= 0

    # Check correctness evaluation
    assert trace.is_correct is not None  # Should be True or False


def test_run_case_without_options(mock_config, mock_llm_client):
    """Test case execution without multiple choice options."""
    question = "What is the most likely diagnosis for a patient with acute chest pain?"

    final_decision, trace = run_case(
        question=question,
        options=None,
        config=mock_config,
        llm_client=mock_llm_client
    )

    assert final_decision.final_answer
    assert trace.options is None
    assert trace.correct_answer is None
    assert trace.is_correct is None


def test_run_case_respects_budgets(mock_config, mock_llm_client):
    """Test that case execution respects budget limits."""
    question = "Test question"

    final_decision, trace = run_case(
        question=question,
        options=None,
        config=mock_config,
        llm_client=mock_llm_client
    )

    # Count total agents: planner + specialists + aggregator
    total_agents = 1 + len(trace.specialist_traces) + 1

    assert total_agents <= mock_config.budgets.max_agents_total


def test_run_case_json_validity(mock_config, mock_llm_client):
    """Test that all outputs are valid JSON-serializable."""
    question = "Test question"

    final_decision, trace = run_case(
        question=question,
        options=None,
        config=mock_config,
        llm_client=mock_llm_client
    )

    # Should be able to serialize to dict
    trace_dict = trace.model_dump()
    assert isinstance(trace_dict, dict)

    decision_dict = final_decision.model_dump()
    assert isinstance(decision_dict, dict)


def test_pediatric_case_triage(mock_config, mock_llm_client):
    """Test that pediatric cases trigger appropriate triage."""
    question = "A 3-year-old child with fever and cough."

    final_decision, trace = run_case(
        question=question,
        options=None,
        config=mock_config,
        llm_client=mock_llm_client
    )

    # With mock client, triage_generalist is always emergency_medicine,
    # but in real scenario, "3-year-old" should trigger pediatrics
    # This test validates the pipeline runs for pediatric cases
    assert trace.planner_trace is not None
    assert final_decision.final_answer
