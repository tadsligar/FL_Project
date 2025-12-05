"""
Orchestration logic: coordinate planner, specialists, and aggregator.
Manages budgets, retries, and execution flow.
"""

import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .aggregator import run_aggregator
from .config import Config
from .llm_client import LLMClient, create_llm_client
from .planner import run_planner
from .specialists import run_specialists
from .schemas import (
    AgentTrace,
    CaseTrace,
    FinalDecision,
    PlannerResult,
    SpecialistReport,
)


class OrchestratedCase:
    """Container for a complete case execution."""

    def __init__(
        self,
        question: str,
        options: Optional[list[str]] = None,
        correct_answer: Optional[str] = None,
    ):
        self.trace_id = str(uuid4())
        self.question = question
        self.options = options
        self.correct_answer = correct_answer

        self.planner_result: Optional[PlannerResult] = None
        self.specialist_reports: list[SpecialistReport] = []
        self.final_decision: Optional[FinalDecision] = None

        self.planner_trace: Optional[AgentTrace] = None
        self.specialist_traces: list[AgentTrace] = []
        self.aggregator_trace: Optional[AgentTrace] = None

        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_tokens: int = 0

    def to_trace(self) -> CaseTrace:
        """Convert to CaseTrace schema."""
        if not all([self.planner_trace, self.aggregator_trace, self.final_decision]):
            raise ValueError("Case execution incomplete")

        total_latency = (
            (self.end_time - self.start_time).total_seconds()
            if self.start_time and self.end_time
            else 0.0
        )

        is_correct = None
        if self.correct_answer and self.final_decision:
            is_correct = self.final_decision.final_answer == self.correct_answer

        return CaseTrace(
            trace_id=self.trace_id,
            question=self.question,
            options=self.options,
            planner_trace=self.planner_trace,
            specialist_traces=self.specialist_traces,
            aggregator_trace=self.aggregator_trace,
            final_decision=self.final_decision,
            total_latency_seconds=total_latency,
            total_tokens=self.total_tokens if self.total_tokens > 0 else None,
            timestamp=self.start_time.isoformat() if self.start_time else datetime.now().isoformat(),
            correct_answer=self.correct_answer,
            predicted_answer=self.final_decision.final_answer,
            is_correct=is_correct,
        )


def run_case(
    question: str,
    options: Optional[list[str]] = None,
    correct_answer: Optional[str] = None,
    config: Optional[Config] = None,
    llm_client: Optional[LLMClient] = None,
) -> tuple[FinalDecision, CaseTrace]:
    """
    Run a complete case through the multi-agent system.

    Args:
        question: Clinical question or case presentation
        options: Optional multiple choice options
        correct_answer: Optional ground truth (for evaluation)
        config: Configuration (uses default if not provided)
        llm_client: LLM client (creates one if not provided)

    Returns:
        (FinalDecision, CaseTrace) tuple
    """
    # Initialize
    if config is None:
        from .config import get_config
        config = get_config()

    if llm_client is None:
        llm_client = create_llm_client(config)

    case = OrchestratedCase(question, options, correct_answer)
    case.start_time = datetime.now()

    try:
        # Step 1: Planner
        planner_start = time.time()
        planner_result, planner_response = run_planner(
            question=question,
            options=options,
            llm_client=llm_client,
            config=config
        )
        planner_latency = time.time() - planner_start

        case.planner_result = planner_result
        case.planner_trace = AgentTrace(
            trace_id=case.trace_id,
            agent_type="planner",
            specialty_id=None,
            input_prompt="[Planner prompt]",  # Simplified; can save full prompt if needed
            output_json=planner_result.model_dump(),
            timestamp=datetime.now().isoformat(),
            latency_seconds=planner_latency,
            model=planner_response.model,
            tokens_used=planner_response.tokens_used,
        )

        if planner_response.tokens_used:
            case.total_tokens += planner_response.tokens_used

        # Step 2: Specialists
        selected_specialties = planner_result.selected_specialties[:config.budgets.max_specialists]

        specialist_results = run_specialists(
            selected_specialties=selected_specialties,
            question=question,
            options=options,
            planner_result=planner_result,
            llm_client=llm_client,
            config=config
        )

        for report, response in specialist_results:
            case.specialist_reports.append(report)

            specialist_trace = AgentTrace(
                trace_id=case.trace_id,
                agent_type="specialist",
                specialty_id=report.specialty_id,
                input_prompt="[Specialist prompt]",
                output_json=report.model_dump(),
                timestamp=datetime.now().isoformat(),
                latency_seconds=response.latency_seconds,
                model=response.model,
                tokens_used=response.tokens_used,
            )
            case.specialist_traces.append(specialist_trace)

            if response.tokens_used:
                case.total_tokens += response.tokens_used

        # Step 3: Aggregator
        aggregator_start = time.time()
        final_decision, aggregator_response = run_aggregator(
            question=question,
            options=options,
            specialist_reports=case.specialist_reports,
            llm_client=llm_client,
            config=config
        )
        aggregator_latency = time.time() - aggregator_start

        case.final_decision = final_decision
        case.aggregator_trace = AgentTrace(
            trace_id=case.trace_id,
            agent_type="aggregator",
            specialty_id=None,
            input_prompt="[Aggregator prompt]",
            output_json=final_decision.model_dump(),
            timestamp=datetime.now().isoformat(),
            latency_seconds=aggregator_latency,
            model=aggregator_response.model,
            tokens_used=aggregator_response.tokens_used,
        )

        if aggregator_response.tokens_used:
            case.total_tokens += aggregator_response.tokens_used

        case.end_time = datetime.now()

        # Check budgets
        total_agents = 1 + len(case.specialist_reports) + 1  # planner + specialists + aggregator
        if total_agents > config.budgets.max_agents_total:
            print(f"Warning: Total agents ({total_agents}) exceeded budget ({config.budgets.max_agents_total})")

        return final_decision, case.to_trace()

    except Exception as e:
        case.end_time = datetime.now()
        raise RuntimeError(f"Case execution failed: {e}") from e
