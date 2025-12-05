"""
Logging utilities for trace storage.
Supports JSONL and SQLite backends.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config
from .schemas import CaseTrace


# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class TraceWriter:
    """Abstract base for trace writers."""

    def write_trace(self, trace: CaseTrace):
        """Write a case trace."""
        raise NotImplementedError


class JSONLTraceWriter(TraceWriter):
    """Write traces to JSONL files."""

    def __init__(self, config: Config):
        self.config = config
        self.traces_dir = Path(config.logging.traces_dir)
        self.traces_dir.mkdir(exist_ok=True, parents=True)

    def write_trace(self, trace: CaseTrace):
        """Write a trace to JSONL file."""
        # Create dated subdirectory
        date_str = datetime.now().strftime("%Y%m%d")
        output_dir = self.traces_dir / date_str
        output_dir.mkdir(exist_ok=True, parents=True)

        # Write trace
        output_file = output_dir / f"{trace.trace_id}.jsonl"

        with open(output_file, "w", encoding="utf-8") as f:
            # Write the full trace as a single JSON line
            f.write(json.dumps(trace.model_dump(), indent=None))
            f.write("\n")

        logger.info(f"Trace written to {output_file}")
        return str(output_file)


class SQLiteTraceWriter(TraceWriter):
    """Write traces to SQLite database using SQLModel."""

    def __init__(self, config: Config):
        self.config = config
        # TODO: Implement SQLite storage with SQLModel
        # This is left as a future enhancement
        logger.warning("SQLite backend not yet implemented, using JSONL fallback")
        self.jsonl_writer = JSONLTraceWriter(config)

    def write_trace(self, trace: CaseTrace):
        """Write trace to SQLite (fallback to JSONL for now)."""
        return self.jsonl_writer.write_trace(trace)


def create_trace_writer(config: Optional[Config] = None) -> TraceWriter:
    """
    Factory function to create a trace writer.

    Args:
        config: Configuration (uses default if not provided)

    Returns:
        TraceWriter instance
    """
    if config is None:
        from .config import get_config
        config = get_config()

    if config.logging.backend == "jsonl":
        return JSONLTraceWriter(config)
    elif config.logging.backend == "sqlite":
        return SQLiteTraceWriter(config)
    else:
        raise ValueError(f"Unknown logging backend: {config.logging.backend}")


def save_trace(trace: CaseTrace, config: Optional[Config] = None) -> str:
    """
    Convenience function to save a trace.

    Args:
        trace: CaseTrace to save
        config: Optional config

    Returns:
        Path to saved trace file
    """
    writer = create_trace_writer(config)
    return writer.write_trace(trace)
