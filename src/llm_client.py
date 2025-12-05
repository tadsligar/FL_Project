"""
Abstract LLM client interface with pluggable providers.
Supports OpenAI, Anthropic, and mock clients for testing.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Optional

from openai import OpenAI
from anthropic import Anthropic

from .config import Config


class LLMResponse:
    """Standardized response from LLM."""

    def __init__(
        self,
        content: str,
        model: str,
        tokens_used: Optional[int] = None,
        latency_seconds: float = 0.0,
        raw_response: Optional[dict] = None
    ):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used
        self.latency_seconds = latency_seconds
        self.raw_response = raw_response


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: Config):
        self.config = config

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse object
        """
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, config: Config):
        super().__init__(config)
        api_key = config.ensure_api_key()
        self.client = OpenAI(api_key=api_key)

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using OpenAI API."""
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_output_tokens)
        model = kwargs.get("model", self.config.model)

        start = time.time()

        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        latency = time.time() - start

        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else None

        return LLMResponse(
            content=content,
            model=model,
            tokens_used=tokens_used,
            latency_seconds=latency,
            raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
        )


class AnthropicClient(LLMClient):
    """Anthropic API client."""

    def __init__(self, config: Config):
        super().__init__(config)
        api_key = config.ensure_api_key()
        self.client = Anthropic(api_key=api_key)

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Anthropic API."""
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_output_tokens)
        model = kwargs.get("model", self.config.model)

        # Map common model names to Anthropic format
        if model == "claude-3-5-sonnet":
            model = "claude-3-5-sonnet-20241022"
        elif model == "claude-3-opus":
            model = "claude-3-opus-20240229"

        start = time.time()

        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        latency = time.time() - start

        content = response.content[0].text if response.content else ""
        tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else None

        return LLMResponse(
            content=content,
            model=model,
            tokens_used=tokens_used,
            latency_seconds=latency,
            raw_response={"usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}} if response.usage else None
        )


class MockLLMClient(LLMClient):
    """Mock LLM client for testing (returns predefined responses)."""

    def __init__(self, config: Config, mock_responses: Optional[dict] = None):
        super().__init__(config)
        self.mock_responses = mock_responses or {}
        self.call_count = 0

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Return a mock response."""
        self.call_count += 1

        # Check if we have a specific mock for this prompt pattern
        for key, response in self.mock_responses.items():
            if key in prompt:
                content = response if isinstance(response, str) else json.dumps(response)
                return LLMResponse(
                    content=content,
                    model="mock-model",
                    tokens_used=100,
                    latency_seconds=0.1
                )

        # Default mock responses based on agent type (check multiple keywords for robustness)
        prompt_lower = prompt.lower()

        # Check for planner first (unique keywords)
        if "clinical generalist planner" in prompt_lower or "enumerate and score all specialties" in prompt_lower:
            return self._mock_planner_response()

        # Check for specialist (unique format with specialty name)
        elif "specialist**" in prompt_lower and "provide a focused differential diagnosis" in prompt_lower:
            return self._mock_specialist_response()

        # Check for aggregator
        elif "generalist aggregator" in prompt_lower or "synthesize their input" in prompt_lower:
            return self._mock_aggregator_response()

        # Fallback checks for main system
        elif "triage generalist selection" in prompt_lower or "fixed specialty catalog" in prompt_lower:
            return self._mock_planner_response()

        elif "specialist" in prompt_lower and '"specialty_id":' in prompt:
            return self._mock_specialist_response()

        # Baseline method support - simple text responses
        elif "clinical reasoning expert" in prompt_lower or "step-by-step reasoning" in prompt_lower:
            # Single-LLM CoT baseline
            return self._mock_cot_response()

        elif "clinical planner" in prompt_lower and "initial assessment" in prompt_lower:
            # Fixed pipeline baseline - planner
            return self._mock_cot_response()

        elif "internal medicine specialist" in prompt_lower or "clinical reviewer" in prompt_lower:
            # Fixed pipeline baseline - specialist or reviewer
            return self._mock_cot_response()

        elif "clinical reasoning agent" in prompt_lower or "debate" in prompt_lower:
            # Debate baseline
            return self._mock_cot_response()

        # Default fallback
        else:
            # Return a generic reasoning response
            return self._mock_cot_response()

    def _mock_planner_response(self) -> LLMResponse:
        """Generate a mock planner response."""
        response = {
            "triage_generalist": "emergency_medicine",
            "scored_catalog": [
                {
                    "specialty_id": "cardiology",
                    "relevance": 0.9,
                    "coverage_gain": 0.8,
                    "urgency_alignment": 0.9,
                    "procedural_signal": 0.3,
                    "reason": "Cardiac symptoms"
                },
                {
                    "specialty_id": "pulmonology",
                    "relevance": 0.6,
                    "coverage_gain": 0.5,
                    "urgency_alignment": 0.7,
                    "procedural_signal": 0.2,
                    "reason": "Respiratory differential"
                },
                {
                    "specialty_id": "gastroenterology",
                    "relevance": 0.4,
                    "coverage_gain": 0.4,
                    "urgency_alignment": 0.3,
                    "procedural_signal": 0.2,
                    "reason": "GI causes possible"
                },
                {
                    "specialty_id": "emergency_medicine",
                    "relevance": 1.0,
                    "coverage_gain": 0.9,
                    "urgency_alignment": 1.0,
                    "procedural_signal": 0.3,
                    "reason": "Acute presentation"
                },
                {
                    "specialty_id": "neurology",
                    "relevance": 0.3,
                    "coverage_gain": 0.3,
                    "urgency_alignment": 0.4,
                    "procedural_signal": 0.1,
                    "reason": "Low relevance"
                }
            ],
            "selected_specialties": ["cardiology", "pulmonology", "gastroenterology", "emergency_medicine", "neurology"],
            "rationale": "Mock planner rationale"
        }
        return LLMResponse(
            content=json.dumps(response),
            model="mock-model",
            tokens_used=200,
            latency_seconds=0.2
        )

    def _mock_specialist_response(self) -> LLMResponse:
        """Generate a mock specialist response."""
        response = {
            "specialty_id": "cardiology",
            "differential": [
                {
                    "dx": "Acute Myocardial Infarction",
                    "p": 0.7,
                    "evidence_for": ["chest pain", "radiation to arm"],
                    "evidence_against": [],
                    "discriminators": ["ECG", "troponin"]
                }
            ],
            "notes": "Mock specialist notes"
        }
        return LLMResponse(
            content=json.dumps(response),
            model="mock-model",
            tokens_used=150,
            latency_seconds=0.15
        )

    def _mock_aggregator_response(self) -> LLMResponse:
        """Generate a mock aggregator response."""
        response = {
            "final_answer": "B",
            "ordered_differential": [
                {
                    "dx": "Acute Myocardial Infarction",
                    "p": 0.75,
                    "evidence_for": ["chest pain", "radiation"],
                    "evidence_against": [],
                    "discriminators": ["ECG", "troponin"]
                }
            ],
            "justification": "Mock aggregator justification",
            "warnings": []
        }
        return LLMResponse(
            content=json.dumps(response),
            model="mock-model",
            tokens_used=180,
            latency_seconds=0.18
        )

    def _mock_cot_response(self) -> LLMResponse:
        """Generate a mock chain-of-thought response for baseline methods."""
        content = """REASONING:
Based on the clinical presentation of chest pain radiating to the left arm in a 65-year-old man, this is highly suggestive of acute coronary syndrome. The classic radiation pattern and age demographic are consistent with acute myocardial infarction.

Key clinical features:
- Chest pain radiating to left arm (classic ACS presentation)
- Age 65 (increased cardiovascular risk)
- Male gender (higher CAD risk)

Differential diagnosis:
1. Acute MI - Most likely given classic presentation
2. Unstable angina - Possible but pain radiation suggests infarction
3. GERD - Unlikely with this radiation pattern
4. PE - Possible but less likely with arm radiation
5. MSK pain - Unlikely given acute onset and radiation

ANSWER: B
"""
        return LLMResponse(
            content=content,
            model="mock-model",
            tokens_used=200,
            latency_seconds=0.2
        )


def create_llm_client(config: Config, mock_responses: Optional[dict] = None) -> LLMClient:
    """
    Factory function to create the appropriate LLM client.

    Args:
        config: Configuration object
        mock_responses: Optional dict of mock responses (for testing)

    Returns:
        LLMClient instance

    Supported providers:
    - openai: OpenAI API (GPT-4, GPT-3.5, etc.)
    - anthropic: Anthropic API (Claude)
    - mock: Mock client for testing
    - ollama: Local Ollama server
    - llamacpp: Local llama.cpp server
    - vllm: Local vLLM server
    """
    provider = config.provider.lower()

    if provider == "openai":
        return OpenAIClient(config)
    elif provider == "anthropic":
        return AnthropicClient(config)
    elif provider == "mock":
        return MockLLMClient(config, mock_responses)
    elif provider in ["ollama", "llamacpp", "vllm"]:
        # Import local clients dynamically to avoid dependency issues
        from .llm_client_local import create_local_llm_client
        return create_local_llm_client(config)
    else:
        raise ValueError(
            f"Unknown provider: {config.provider}. "
            f"Supported: openai, anthropic, mock, ollama, llamacpp, vllm"
        )
