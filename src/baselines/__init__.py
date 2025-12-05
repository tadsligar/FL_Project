"""Baseline comparison methods for MAS evaluation."""

from .single_llm_cot import run_single_llm_cot
from .fixed_pipeline import run_fixed_pipeline
from .debate import run_debate

__all__ = [
    "run_single_llm_cot",
    "run_fixed_pipeline",
    "run_debate",
]
