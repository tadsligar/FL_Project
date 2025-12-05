#!/usr/bin/env python3
"""Quick test to verify installation works."""

print("Testing Clinical MAS Planner installation...")
print("=" * 60)

# Test 1: Import modules
print("\n1. Testing imports...")
try:
    from src.config import Config, get_config
    from src.llm_client import create_llm_client, MockLLMClient
    from src.orchestration import run_case
    from src.baselines import run_single_llm_cot, run_fixed_pipeline, run_debate
    print("   [OK] All imports successful")
except Exception as e:
    print(f"   [FAIL] Import failed: {e}")
    exit(1)

# Test 2: Load config
print("\n2. Testing configuration...")
try:
    config = get_config()
    print(f"   [OK] Config loaded: {config.model} ({config.provider})")
except Exception as e:
    print(f"   [FAIL] Config failed: {e}")
    exit(1)

# Test 3: Create mock LLM client
print("\n3. Testing LLM client (mock)...")
try:
    config.provider = "mock"
    llm_client = create_llm_client(config)
    print(f"   [OK] Mock LLM client created: {type(llm_client).__name__}")
except Exception as e:
    print(f"   [FAIL] LLM client failed: {e}")
    exit(1)

# Test 4: Run a test case with mock provider
print("\n4. Testing full case execution (mock)...")
try:
    question = "A 65-year-old man with chest pain radiating to left arm."
    options = ["A. GERD", "B. Acute MI", "C. PE", "D. MSK pain"]

    final_decision, trace = run_case(
        question=question,
        options=options,
        correct_answer="B",
        config=config,
        llm_client=llm_client
    )

    print(f"   [OK] Case executed successfully")
    print(f"   [OK] Final answer: {final_decision.final_answer}")
    print(f"   [OK] Specialists consulted: {len(trace.specialist_traces)}")
    print(f"   [OK] Total latency: {trace.total_latency_seconds:.2f}s")

except Exception as e:
    print(f"   [FAIL] Case execution failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Test baseline methods
print("\n5. Testing baseline methods (mock)...")
try:
    # Single CoT
    result = run_single_llm_cot(question, options, llm_client, config)
    print(f"   [OK] Single-LLM CoT: {result['answer']}")

    # Fixed pipeline
    result = run_fixed_pipeline(question, options, llm_client, config)
    print(f"   [OK] Fixed Pipeline: {result['answer']}")

    # Debate
    result = run_debate(question, options, llm_client, config, rounds=2)
    print(f"   [OK] Debate: {result['answer']}")

except Exception as e:
    print(f"   [FAIL] Baseline test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Success!
print("\n" + "=" * 60)
print("[SUCCESS] ALL TESTS PASSED!")
print("=" * 60)
print("\nYour installation is working correctly!")
print("\nNext steps:")
print("1. Install Ollama: https://ollama.com/download/windows")
print("2. Pull a model: ollama pull llama3:70b")
print("3. Download MedQA: python scripts/download_medqa.py --split test --options 4")
print("4. Run comparison: python scripts/run_baseline_comparison.py --n 10")
print()
