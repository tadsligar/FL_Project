"""
Pydantic schemas for the Clinical MAS Planner system.
Defines all data models and JSON schemas for agent inputs/outputs.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Planner Schemas
# ============================================================================

class ScoredSpecialty(BaseModel):
    """A specialty with relevance scores from the planner."""

    specialty_id: str = Field(..., description="ID from the fixed catalog")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Overall relevance to case")
    coverage_gain: float = Field(..., ge=0.0, le=1.0, description="Unique diagnostic coverage")
    urgency_alignment: float = Field(..., ge=0.0, le=1.0, description="Alignment with urgency")
    procedural_signal: float = Field(..., ge=0.0, le=1.0, description="Procedural/surgical signal")
    reason: str = Field(..., description="Brief justification for scores")


class PlannerResult(BaseModel):
    """Output from the Planner agent."""

    triage_generalist: Literal["emergency_medicine", "pediatrics", "family_internal_medicine"] = Field(
        ...,
        description="Selected generalist for triage"
    )
    scored_catalog: list[ScoredSpecialty] = Field(
        ...,
        description="All specialties scored"
    )
    selected_specialties: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Top-K specialty IDs selected for consultation"
    )
    rationale: str = Field(default="", description="Overall planning rationale")

    @field_validator('selected_specialties')
    @classmethod
    def validate_selected_count(cls, v):
        if len(v) > 5:
            raise ValueError("Cannot select more than 5 specialties")
        if len(v) == 0:
            raise ValueError("Must select at least 1 specialty")
        return v


# ============================================================================
# Specialist Schemas
# ============================================================================

class DifferentialItem(BaseModel):
    """A single differential diagnosis with evidence."""

    dx: str = Field(..., description="Diagnosis name")
    p: float = Field(..., ge=0.0, le=1.0, description="Probability/confidence")
    evidence_for: list[str] = Field(
        default_factory=list,
        description="Supporting evidence from the case"
    )
    evidence_against: list[str] = Field(
        default_factory=list,
        description="Evidence that argues against this diagnosis"
    )
    discriminators: list[str] = Field(
        default_factory=list,
        description="Key tests or findings that would distinguish this diagnosis"
    )


class SpecialistReport(BaseModel):
    """Output from a single Specialist agent."""

    specialty_id: str = Field(..., description="Specialty that generated this report")
    differential: list[DifferentialItem] = Field(
        ...,
        max_length=3,
        description="Top differential diagnoses (max 3)"
    )
    notes: str = Field(default="", description="Additional specialist notes")

    @field_validator('differential')
    @classmethod
    def validate_differential(cls, v):
        if len(v) == 0:
            raise ValueError("Differential must contain at least one diagnosis")
        if len(v) > 3:
            raise ValueError("Differential cannot contain more than 3 diagnoses")

        # Check that probabilities sum to <= 1.0
        total_p = sum(item.p for item in v)
        if total_p > 1.01:  # Small tolerance for floating point
            raise ValueError(f"Probabilities sum to {total_p:.2f}, must be <= 1.0")

        return v


# ============================================================================
# Aggregator Schemas
# ============================================================================

class FinalDecision(BaseModel):
    """Final output from the Aggregator agent."""

    final_answer: str = Field(..., description="Final diagnosis or answer (e.g., MedQA option)")
    ordered_differential: list[DifferentialItem] = Field(
        ...,
        description="Merged and ordered differential diagnoses"
    )
    justification: str = Field(..., description="Reasoning for final decision")
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings or caveats about the decision"
    )


# ============================================================================
# Request/Response Schemas for API
# ============================================================================

class CaseInput(BaseModel):
    """Input case for diagnosis."""

    question: str = Field(..., description="Clinical question or case presentation")
    options: Optional[list[str]] = Field(
        None,
        description="Multiple choice options (e.g., for MedQA)"
    )


class ConsultRequest(BaseModel):
    """Request for specialist consultation."""

    question: str
    options: Optional[list[str]] = None
    planner_result: PlannerResult


class AggregateRequest(BaseModel):
    """Request for final aggregation."""

    question: str
    options: Optional[list[str]] = None
    specialist_reports: list[SpecialistReport]


class EvaluationResult(BaseModel):
    """Results from MedQA evaluation."""

    n_samples: int
    n_correct: int
    accuracy: float
    avg_latency_seconds: float
    avg_tokens_used: Optional[float] = None
    traces_path: str
    summary: str


# ============================================================================
# Trace/Logging Schemas
# ============================================================================

class AgentTrace(BaseModel):
    """Trace of a single agent call."""

    trace_id: str
    agent_type: Literal["planner", "specialist", "aggregator"]
    specialty_id: Optional[str] = None
    input_prompt: str
    output_json: dict
    timestamp: str
    latency_seconds: float
    model: str
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class CaseTrace(BaseModel):
    """Complete trace for a case."""

    trace_id: str
    question: str
    options: Optional[list[str]]
    planner_trace: AgentTrace
    specialist_traces: list[AgentTrace]
    aggregator_trace: AgentTrace
    final_decision: FinalDecision
    total_latency_seconds: float
    total_tokens: Optional[int] = None
    timestamp: str
    correct_answer: Optional[str] = None
    predicted_answer: str
    is_correct: Optional[bool] = None
