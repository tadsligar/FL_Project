"""
Configuration management using Pydantic Settings.
Loads from environment variables and YAML files.
"""

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BudgetConfig(BaseSettings):
    """Budget and limits configuration."""

    max_agents_total: int = Field(default=10, description="Maximum total agents per case")
    max_specialists: int = Field(default=5, description="Maximum specialist consultations")
    max_retries: int = Field(default=1, description="Max retries for failed API calls")
    timeout_seconds: int = Field(default=30, description="Timeout per API call")


class PlannerConfig(BaseSettings):
    """Planner-specific configuration."""

    top_k: int = Field(default=5, description="Number of specialties to select")
    allow_generalist: bool = Field(default=True, description="Allow generalist in selection")
    emergency_red_flags: list[str] = Field(
        default_factory=lambda: [
            "syncope", "unstable", "diaphoresis", "hemoptysis",
            "chest pain", "altered mental status", "severe bleeding",
            "respiratory distress", "shock"
        ]
    )
    pediatric_signals: list[str] = Field(
        default_factory=lambda: [
            "child", "infant", "pediatric", "newborn",
            "adolescent", "years old", "months old"
        ]
    )


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    traces_dir: str = Field(default="runs", description="Directory for trace files")
    backend: Literal["jsonl", "sqlite"] = Field(default="jsonl", description="Trace storage backend")
    level: str = Field(default="INFO", description="Log level")
    save_full_prompts: bool = Field(default=True, description="Save full prompts in traces")
    save_raw_responses: bool = Field(default=True, description="Save raw API responses")


class AgentTemperatureConfig(BaseSettings):
    """Agent-specific temperature configuration for differential sampling."""

    planner: Optional[float] = Field(default=None, description="Temperature for planner agent")
    specialist: Optional[float] = Field(default=None, description="Temperature for specialist agents")
    aggregator: Optional[float] = Field(default=None, description="Temperature for aggregator agent")


class SafetyConfig(BaseSettings):
    """Safety and guardrails configuration."""

    enable_guardrails: bool = Field(default=True, description="Enable safety checks")
    max_concurrent_calls: int = Field(default=5, description="Max concurrent API calls")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")


class VLLMConfig(BaseSettings):
    """vLLM-specific configuration."""

    base_url: str = Field(default="http://localhost:8000", description="vLLM server URL")
    use_chat_api: bool = Field(default=True, description="Use /v1/chat/completions instead of /v1/completions")
    timeout: int = Field(default=300, description="Request timeout in seconds")


class Config(BaseSettings):
    """Main configuration class."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Model configuration
    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    provider: Literal["openai", "anthropic", "mock", "ollama", "llamacpp", "vllm"] = Field(
        default="openai",
        description="LLM provider"
    )
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Sampling temperature")
    max_output_tokens: int = Field(default=800, description="Max tokens per response")

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")

    # Environment
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")

    # Sub-configurations
    budgets: BudgetConfig = Field(default_factory=BudgetConfig)
    planner: PlannerConfig = Field(default_factory=PlannerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    agent_temperatures: AgentTemperatureConfig = Field(default_factory=AgentTemperatureConfig)
    vllm: VLLMConfig = Field(default_factory=VLLMConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "Config":
        """Load configuration from a YAML file."""
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # Handle _base inheritance
        if "_base" in data:
            base_path = yaml_path.parent / data.pop("_base")
            base_config = cls.from_yaml(base_path)
            # Merge: data overrides base
            base_dict = base_config.model_dump()
            merged = {**base_dict, **data}
            return cls(**merged)

        return cls(**data)

    def ensure_api_key(self) -> str:
        """Get the API key for the current provider."""
        if self.provider == "openai":
            key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env")
            return key
        elif self.provider == "anthropic":
            key = self.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY in .env")
            return key
        elif self.provider in ["mock", "ollama", "llamacpp", "vllm"]:
            # Local providers don't need API keys
            return "local-no-key-required"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str | Path] = None) -> Config:
    """
    Get or initialize the global config.

    Args:
        config_path: Optional path to YAML config file. If not provided,
                     uses configs/default.yaml or creates from env vars.
    """
    global _config

    if _config is not None and config_path is None:
        return _config

    if config_path:
        _config = Config.from_yaml(config_path)
    else:
        # Try default config
        default_path = Path("configs/default.yaml")
        if default_path.exists():
            _config = Config.from_yaml(default_path)
        else:
            # Fallback to env vars only
            _config = Config()

    return _config


def reset_config():
    """Reset the global config (useful for testing)."""
    global _config
    _config = None
