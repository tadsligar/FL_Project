"""
Local LLM client implementations.
Supports Ollama and other local inference backends.
"""

import json
import time
from typing import Optional

import requests

from .config import Config
from .llm_client import LLMClient, LLMResponse


class OllamaClient(LLMClient):
    """
    Client for locally-hosted Ollama models.

    Install Ollama: https://ollama.ai/

    Example usage:
        # Pull a model
        ollama pull llama3:8b

        # Or a medical model
        ollama pull meditron

        # Configure in configs/default.yaml
        provider: "ollama"
        model: "llama3:8b"
    """

    def __init__(self, config: Config, base_url: str = "http://localhost:11434"):
        super().__init__(config)
        self.base_url = base_url.rstrip("/")

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Ollama API."""
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_output_tokens)
        model = kwargs.get("model", self.config.model)

        # Ollama API endpoint
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        start = time.time()

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=kwargs.get("timeout", self.config.budgets.timeout_seconds)
            )
            response.raise_for_status()

            result = response.json()

            latency = time.time() - start

            content = result.get("response", "")

            # Ollama returns token counts in different format
            tokens_used = (
                result.get("prompt_eval_count", 0) +
                result.get("eval_count", 0)
            )

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used if tokens_used > 0 else None,
                latency_seconds=latency,
                raw_response=result
            )

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama. "
                "Make sure Ollama is running: 'ollama serve'"
            )
        except requests.exceptions.Timeout:
            actual_timeout = kwargs.get("timeout", self.config.budgets.timeout_seconds)
            raise RuntimeError(
                f"Ollama request timed out after {actual_timeout}s"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")


class LlamaCppClient(LLMClient):
    """
    Client for llama.cpp server.

    Setup:
        1. Build llama.cpp: https://github.com/ggerganov/llama.cpp
        2. Download a GGUF model (e.g., Llama-3, Mistral)
        3. Start server:
           ./server -m models/llama-3-8b.gguf --port 8080

    Configure:
        provider: "llamacpp"
        model: "llama-3-8b"
    """

    def __init__(self, config: Config, base_url: str = "http://localhost:8080"):
        super().__init__(config)
        self.base_url = base_url.rstrip("/")

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using llama.cpp server."""
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_output_tokens)
        model = kwargs.get("model", self.config.model)

        url = f"{self.base_url}/completion"

        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": max_tokens,
            "stop": kwargs.get("stop", []),
        }

        start = time.time()

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=kwargs.get("timeout", self.config.budgets.timeout_seconds)
            )
            response.raise_for_status()

            result = response.json()
            latency = time.time() - start

            content = result.get("content", "")
            tokens_used = result.get("tokens_predicted", None)

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                latency_seconds=latency,
                raw_response=result
            )

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to llama.cpp server. "
                "Make sure server is running on port 8080"
            )
        except Exception as e:
            raise RuntimeError(f"llama.cpp API error: {e}")


class VLLMClient(LLMClient):
    """
    Client for vLLM server (high-performance inference).

    Setup (Local):
        pip install vllm

        vllm serve meta-llama/Llama-3-8B-Instruct \
            --port 8000 \
            --gpu-memory-utilization 0.9

    Setup (RunPod):
        1. Deploy a vLLM pod with your model
        2. Get the endpoint URL (e.g., https://xxx-8000.proxy.runpod.net)
        3. Set in config: vllm.base_url

    Configure:
        provider: "vllm"
        model: "Qwen/Qwen2.5-32B-Instruct"
        vllm:
          base_url: "https://your-pod-id.proxy.runpod.net"
          use_chat_api: true  # Use /v1/chat/completions (better for instruct models)
    """

    def __init__(self, config: Config, base_url: Optional[str] = None):
        super().__init__(config)
        # Get base_url from config or parameter
        if base_url is None:
            base_url = getattr(config, 'vllm', {}).get('base_url', 'http://localhost:8000')
        self.base_url = base_url.rstrip("/")

        # Check if we should use chat API (better for instruct models)
        self.use_chat_api = getattr(config, 'vllm', {}).get('use_chat_api', False)

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using vLLM OpenAI-compatible API."""
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_output_tokens)
        model = kwargs.get("model", self.config.model)

        if self.use_chat_api:
            # Use chat completions API (better for instruct models)
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        else:
            # Use completions API (classic)
            url = f"{self.base_url}/v1/completions"
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

        start = time.time()

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=kwargs.get("timeout", self.config.budgets.timeout_seconds)
            )
            response.raise_for_status()

            result = response.json()
            latency = time.time() - start

            # Extract content based on API type
            if self.use_chat_api:
                content = result["choices"][0]["message"]["content"]
            else:
                content = result["choices"][0]["text"]

            tokens_used = result.get("usage", {}).get("total_tokens")

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                latency_seconds=latency,
                raw_response=result
            )

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to vLLM server at {self.base_url}. "
                "Make sure vLLM is running or RunPod endpoint is correct"
            )
        except requests.exceptions.Timeout:
            actual_timeout = kwargs.get("timeout", self.config.budgets.timeout_seconds)
            raise RuntimeError(
                f"vLLM request timed out after {actual_timeout}s"
            )
        except Exception as e:
            raise RuntimeError(f"vLLM API error: {e}")


def create_local_llm_client(config: Config) -> LLMClient:
    """
    Factory function for local LLM clients.

    Supported providers:
    - ollama: Easiest to set up, good for development
    - llamacpp: Lightweight, runs on CPU
    - vllm: High-performance, requires GPU
    """
    provider = config.provider.lower()

    if provider == "ollama":
        return OllamaClient(config)
    elif provider == "llamacpp":
        return LlamaCppClient(config)
    elif provider == "vllm":
        return VLLMClient(config)
    else:
        raise ValueError(f"Unknown local provider: {provider}")
