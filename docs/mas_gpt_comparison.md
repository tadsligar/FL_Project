# MAS-GPT Comparison and Positioning

## MAS-GPT Overview (March 2025)

**Paper:** "MAS-GPT: Training LLMs to Build LLM-based Multi-Agent Systems"
**ArXiv:** https://arxiv.org/abs/2503.03686

### What MAS-GPT Does

**Core Innovation:**
- LLM generates entire multi-agent system as executable Python code in single inference
- Input: User query → Output: Complete MAS program that can be run to solve query

**Model:**
- Qwen2.5-Coder-32B-Instruct (same family as our Qwen2.5:32B-Instruct)
- Trained on 16 A100s for 3 epochs

**Benchmarks:**
- Math: MATH, GSM8K, GSM-Hard
- Coding: HumanEval, HumanEval+
- General: MMLU
- Science: GPQA, SciBench
- **NO medical benchmarks** (we are first to apply to MedQA-USMLE)

**Temperature:** Not specified in paper (common omission)

---

## How MAS-GPT Works (2-Phase Process)

### Phase 1: Generation (1 LLM call)
```python
Input: "Solve this math problem: ..."
Output: Complete Python code defining the MAS
# Specifies: agent roles, communication pattern, execution flow
```

### Phase 2: Execution (N LLM calls)
```python
# Generated code is executed
# Each agent makes its own LLM calls
Agent1.query_llm(prompt) → LLM call
Agent2.query_llm(prompt) → LLM call
Coordinator.query_llm(prompt) → LLM call
# Total cost = 1 (generation) + N (execution)
```

---

## MAS-GPT's Efficiency Claim

### Comparison to Other Adaptive Methods

| Method | Generation Phase | Execution Phase | Total |
|--------|------------------|-----------------|-------|
| **DyLAN, GPTSwarm** | 10+ LLM calls to design system | N agent calls | 10+ + N |
| **MAS-GPT** | 1 LLM call (generates code) | N agent calls | 1 + N |

**Key Insight:** Efficiency comes from GENERATION phase, not total execution.
- Other adaptive methods: 10+ calls just to DECIDE what agents to use
- MAS-GPT: One call generates complete system
- Both still execute N agent calls after that

**Their claim:** "Achieves best performance while requiring fewest inference calls" (compared to other adaptive methods)

---

## Our Approach vs MAS-GPT

### Efficiency Comparison

| Approach | Selection Overhead | Execution Calls | Total | Medical Validity |
|----------|-------------------|-----------------|-------|------------------|
| Fixed Architecture | 0 | 7 | 7 | ✓ |
| **Our System (Physician Role)** | **0** | **7** | **7** | **✓** |
| MAS-GPT Style | 1 | ~6-10 | ~7-11 | ? (could hallucinate) |
| Full Adaptive (DyLAN) | 10+ | ~5-10 | 15-20+ | ? |

### Our Key Advantages

1. **No generation overhead:**
   - MAS-GPT: 1 call to generate system
   - **Us: 0 calls** (deterministic specialist selection via clinical triage rules)

2. **Fixed execution cost:**
   - MAS-GPT: Variable (depends on generated architecture)
   - **Us: Always 7 calls** (predictable, budgetable)

3. **Medical safety:**
   - MAS-GPT: Could generate invalid/hallucinated specialties
   - **Us: Guaranteed valid medical specialties** from predefined catalog

4. **Interpretability:**
   - MAS-GPT: Generated Python code
   - **Us: Clinical reasoning traces** with clear specialist roles

---

## Similarities (Inspired By)

1. ✓ **Adaptive agent generation** - Agents selected based on task context
2. ✓ **Low overhead** - Efficient compared to fixed large teams
3. ✓ **Domain-specific expertise** - Agents have specialized roles
4. ✓ **Same model family** - Qwen2.5-Coder-32B vs Qwen2.5:32B-Instruct

---

## Key Differences (Our Contribution)

| Aspect | MAS-GPT | Our Work |
|--------|---------|-----------|
| **Domain** | Math, Coding, General QA | **Medical diagnosis** (MedQA-USMLE) |
| **Agent Generation** | Fully dynamic code generation | **Structured physician role selection** |
| **Interpretability** | Generated Python code | **Clinical reasoning traces** |
| **Agent Roles** | Generated on-the-fly | **Predefined medical specialties** (no hallucination) |
| **Selection Method** | 1 LLM call per query | **0 LLM calls** (rule-based triage) |
| **Temperature** | Not specified | **Systematic analysis (0.0-0.7)** |
| **Focus** | General task automation | **Clinical decision support** |
| **Execution Cost** | Variable | **Fixed (7 calls)** |

---

## Paper Positioning Statements

### On MAS-GPT Inspiration
> "Inspired by MAS-GPT's efficiency principle of adaptive agent selection with low overhead, we extend multi-agent reasoning to the medical domain. However, rather than using an LLM to dynamically generate agent architectures (requiring additional inference calls), we employ **domain-specific structural constraints**—clinical triage rules and a predefined specialty catalog—to achieve adaptive behavior with **zero generation overhead** while ensuring medical validity and interpretability."

### On Efficiency
> "Our approach achieves **superior efficiency** compared to adaptive multi-agent methods. While MAS-GPT reduces generation overhead from 10+ calls to 1 call, our system eliminates it entirely through rule-based specialist selection, resulting in a **fixed cost of 7 LLM calls per query**—predictable, interpretable, and safe for medical applications."

### On Temperature Analysis (Our Contribution)
> "Unlike prior multi-agent work which typically does not report temperature settings, we systematically analyze temperature sensitivity across the range [0.0, 0.7] and find **temperature 0.3 optimal** for balancing consistency and diversity in medical reasoning, achieving 76% accuracy on MedQA-USMLE."

### On Medical Domain Extension
> "We are the first to apply adaptive multi-agent reasoning to medical diagnosis at scale. Our physician role debate framework achieves **76% accuracy** on the complete MedQA-USMLE test set (1,071 questions) compared to **55% zero-shot baseline**—a **+38% relative improvement**—while maintaining clinical interpretability through structured specialist consultation."

### On Safety vs Adaptivity Trade-off
> "While fully adaptive agent generation (e.g., MAS-GPT) offers maximum flexibility, medical applications require **guaranteed validity** of agent roles and reasoning patterns. Our predefined specialty catalog prevents hallucinated medical specialties while still enabling adaptive selection based on case context, striking an optimal balance between flexibility and safety."

---

## Experimental Comparison

### What We Test (vs MAS-GPT)

| MAS-GPT | Our Work |
|---------|----------|
| 9 benchmarks (no medical) | MedQA-USMLE (medical-specific) |
| 10+ baseline methods | 3+ baselines + 5 debate variants |
| Temperature: Not reported | Temperature: 0.0, 0.1, 0.3, 0.5, 0.7 |
| Dataset: Various (MATH, MMLU, etc.) | Dataset: 1,071 medical licensing questions |
| Model size: 32B | Model size: 32B (comparable) |

---

## Key Claims for Our Paper

### Claim 1: Multi-agent > Single-agent
- Zero-shot: 55%
- Debate (generic): 68%
- **Evidence:** +24% relative improvement from collaboration

### Claim 2: Role specialization > Generic debate
- Debate (generic): 68%
- Physician role: 76%
- **Evidence:** +12% from domain expertise roles

### Claim 3: Efficiency with medical safety
- Overhead: **0 generation calls** + 7 fixed execution calls
- Gain: +38% over zero-shot baseline
- Safety: Predefined specialty catalog prevents hallucination
- **Evidence:** Efficient AND safe multi-agent reasoning

### Claim 4: Temperature matters (novel contribution)
- Tested: 0.0, 0.1, 0.3, 0.5, 0.7
- Optimal: **0.3**
- Range: 66% (temp 0.0) to 76% (temp 0.3) to 73% (temp 0.5)
- **Evidence:** Systematic temperature analysis for multi-agent medical reasoning

---

## One-Sentence Positioning

**MAS-GPT:** Generates adaptive multi-agent systems as code for general problem-solving.

**Our Work:** Structured physician role debate with predefined specialties for safe, interpretable, and efficient medical diagnosis.

---

## Future Work Connections

Could extend our approach by:
1. Testing MAS-GPT-style dynamic generation on medical tasks (benchmark comparison)
2. Hybrid approach: MAS-GPT generates consultation strategy, executes with our specialist catalog
3. Expanding specialty catalog while maintaining safety constraints
4. Testing on other medical reasoning tasks (diagnosis, treatment planning, etc.)

---

## References

**MAS-GPT Paper:**
- Rui Ye et al., "MAS-GPT: Training LLMs to Build LLM-based Multi-Agent Systems"
- arXiv:2503.03686, March 2025
- https://arxiv.org/abs/2503.03686
- GitHub: https://github.com/MASWorks/MAS-GPT

**Related Work:**
- DyLAN (other adaptive method - 10+ generation calls)
- GPTSwarm (other adaptive method - 10+ generation calls)
- AgentVerse (fixed architecture)
- AutoGen (fixed architecture)
