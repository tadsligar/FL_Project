"""
Clinical MAS Planner: Multi-Agent Diagnostic Reasoning System
"""

__version__ = "0.1.0"

from .aggregator import run_aggregator
from .catalog import get_catalog, get_specialty_by_id
from .config import Config, get_config
from .llm_client import create_llm_client, LLMClient
from .orchestration import run_case
from .planner import run_planner
from .specialists import run_specialist, run_specialists

__all__ = [
    "run_case",
    "run_planner",
    "run_specialist",
    "run_specialists",
    "run_aggregator",
    "get_catalog",
    "get_specialty_by_id",
    "Config",
    "get_config",
    "create_llm_client",
    "LLMClient",
]
