#!/usr/bin/env python3
"""Quick test of Ollama client"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.llm_client import create_llm_client

print("Testing Ollama Client...")
print("=" * 60)

# Load config
config = Config.from_yaml("configs/llama3_70b.yaml")
print(f"Config loaded: {config.model} ({config.provider})")
print(f"Timeout: {config.budgets.timeout_seconds}s")
print()

# Create client
client = create_llm_client(config)
print(f"Client created: {type(client).__name__}")
print()

# Test simple call
print("Testing simple completion...")
try:
    response = client.complete("What is 2+2? Answer in one word.")
    print(f"[OK] Response: {response.content}")
    print(f"     Latency: {response.latency_seconds:.2f}s")
    print(f"     Tokens: {response.tokens_used}")
    print()
    print("SUCCESS: Ollama client is working!")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
