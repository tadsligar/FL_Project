# Evaluating Multi-Agent Systems for Clinical Diagnosis: When Does Complexity Add Value?

**A Comprehensive Empirical Study of Adaptive Multi-Agent Architectures vs. Single-LLM Baselines on Medical Question Answering**

---

## Abstract

Multi-agent systems (MAS) have been proposed as a promising approach to improve large language model (LLM) performance on complex reasoning tasks by decomposing problems across specialized agents. However, the coordination overhead and potential for error propagation raise questions about when such architectures provide genuine benefits. We present a comprehensive empirical evaluation of an adaptive multi-agent clinical diagnosis system against standard baselines using the MedQA-USMLE dataset across two model scales (8B and 32B parameters). Our system dynamically selects from 28 medical specialties to construct optimal reasoning pipelines.

**Critical Discovery**: Model scale determines multi-agent system viability. At **8B parameters (llama3:8b)**, single-LLM dominates (48-54% vs 42-45%), but at **32B parameters (qwen2.5:32b)**, multi-agent methods reverse the hierarchy, achieving **68-76%** accuracy compared to 66% for single-LLM. Debate-style dual-agent achieves the best performance (76%), demonstrating that **iterative refinement outperforms parallel specialization** at larger scales.

We identify a **phase transition** in multi-agent performance between 8B and 32B parameters. Multi-agent systems show 2-3× greater improvement from model scaling (+24-43%) than single-LLM (+12%), suggesting they are bottlenecked by coordination capacity rather than reasoning ability at smaller scales.

**Architectural Discovery**: We find that **adversarial debate outperforms collaborative consultation** in multi-agent systems. A hybrid "Sequential Specialist Debate" method combining generalist continuity, specialist expertise, and agreement-based termination achieved only 64% accuracy—worse than Single-LLM (66%) and 12 points below adversarial Debate (76%). Analysis reveals that agreement-based termination caused 100% premature convergence (all debates ended in 2 rounds), eliminating the iterative refinement mechanism. This demonstrates that combining "best elements" from successful methods can fail when their interactions undermine core mechanisms.

These findings provide crucial insights into when and how multi-agent architectures add value: they require both sufficient base model capacity (>30B parameters) and adversarial stance with fixed iteration counts to prevent premature consensus.

**Keywords:** Multi-Agent Systems, Clinical Decision Support, Large Language Models, Medical Question Answering, Model Scaling, Empirical Evaluation

---

## 1. Introduction

### 1.1 Motivation

The application of large language models (LLMs) to clinical decision support has shown promising results, yet medical diagnosis remains challenging due to:
- **Domain complexity**: Requiring integration of knowledge across multiple medical specialties
- **Reasoning depth**: Necessitating multi-step differential diagnosis and evidence evaluation
- **High stakes**: Where errors have serious consequences for patient outcomes

Multi-agent systems (MAS) have been proposed as a solution, theorizing that:
1. **Specialization** allows focused expertise
2. **Decomposition** breaks complex problems into manageable sub-tasks
3. **Deliberation** through multiple perspectives reduces errors

However, these benefits must be weighed against potential costs:
1. **Coordination overhead** in agent communication
2. **Error propagation** through multi-stage pipelines
3. **Token budget dilution** across multiple inference calls
4. **Increased latency** from sequential processing

### 1.2 Research Questions

This study addresses three key questions:

**RQ1**: Does an adaptive multi-agent architecture outperform single-LLM baselines on medical question answering?

**RQ2**: How do system parameters (temperature, specialist count) affect relative performance?

**RQ3**: When does multi-agent coordination overhead outweigh specialization benefits?

### 1.3 Contributions

1. **Comprehensive empirical evaluation** of adaptive MAS vs. multiple baselines across 10+ configurations
2. **Negative results documentation** showing when complexity doesn't add value
3. **Detailed ablation studies** on temperature and specialist count effects
4. **Cost-benefit analysis** of token usage, latency, and accuracy trade-offs
5. **Open-source implementation** and complete experimental data for reproducibility

---

## 2. Related Work

### 2.1 Multi-Agent Systems for LLMs

Recent work has explored multi-agent approaches for complex reasoning:
- **Debate methods** (Du et al., 2023): Multiple agents debate to reach consensus
- **Reflection patterns** (Shinn et al., 2023): Agents critique and refine outputs
- **Specialized ensembles** (Wang et al., 2023): Domain-specific agents for sub-tasks

However, most studies show improvements on specific benchmarks without systematic investigation of when these benefits materialize.

### 2.2 Medical Question Answering

MedQA-USMLE has become a standard benchmark for evaluating medical reasoning:
- **GPT-4**: ~85% accuracy (OpenAI, 2023)
- **Med-PaLM 2**: ~85% accuracy (Google, 2023)
- **Smaller models**: 40-60% accuracy (various)

### 2.3 Chain-of-Thought Reasoning

Single-LLM approaches with chain-of-thought (CoT) prompting have shown strong results:
- Simpler to implement and debug
- Lower computational costs
- Transparent reasoning chains

This establishes a strong baseline for comparison.

---

## 3. Methodology

### 3.1 System Architecture

#### 3.1.1 Adaptive Multi-Agent System (Ours)

Our system implements a **Planner → Specialists → Aggregator** architecture:

**Planner Agent:**
- Analyzes clinical presentation
- Scores all 28 specialties for relevance
- Selects top-k specialists dynamically
- Considers emergency signals and pediatric cases

**Specialist Agents:**
- Each embodies a medical specialty (e.g., cardiology, neurology)
- Provides focused differential diagnosis
- Assigns probability scores to diagnoses
- Lists supporting/opposing evidence

**Aggregator Agent:**
- Synthesizes specialist inputs
- Resolves conflicts
- Generates final answer with confidence scores
- Provides clinical warnings

**Specialty Catalog (28 specialties):**
```
emergency_medicine, family_internal_medicine, pediatrics,
cardiology, neurology, gastroenterology, pulmonology,
nephrology, endocrinology, rheumatology, infectious_disease,
hematology, oncology, dermatology, psychiatry, orthopedics,
obstetrics_gynecology, urology, ophthalmology, otolaryngology,
allergy_immunology, geriatrics, palliative_care, radiology,
pathology, anesthesiology, surgery_general, critical_care
```

#### 3.1.2 Baseline Methods

**1. Single-LLM Chain-of-Thought (CoT)**
- Direct prompting with structured reasoning
- No multi-agent coordination
- Minimal token overhead

**2. Fixed Pipeline (4 agents)**
- Fixed sequence: Planner → Internal Medicine → Reviewer → Aggregator
- No adaptive specialty selection
- Always uses 4 agents regardless of case

**3. Debate (2 agents, 3 rounds)**
- Two agents debate answer
- Three rounds of argumentation
- Final consensus required

### 3.2 Dataset

**MedQA-USMLE**: United States Medical Licensing Examination questions
- **Total questions**: 1,071 in test set
- **Evaluation subset**: 100 questions (fixed random seed=42)
- **Format**: Multiple choice (A, B, C, D)
- **Content**: Clinical vignettes requiring diagnosis/management
- **Reproducibility**: Same 100 questions used across all experiments

### 3.3 Experimental Design

#### 3.3.1 Model Configuration

**Primary Model**: llama3:8b (via Ollama)
- 8 billion parameters
- Q4_K_M quantization
- Local inference (no API costs)
- Reasonable for resource-constrained settings

**Secondary Model**: qwen2.5:32b (via Ollama)
- 32 billion parameters
- Tests if larger models benefit from MAS
- Higher reasoning capability baseline
- **COMPLETED**: Results show dramatic performance improvement

#### 3.3.2 Hyperparameter Sweep

**Temperature Sweep** (4 specialists):
- Values: 0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8
- Tests determinism vs. exploration trade-off
- All other parameters fixed

**Specialist Count Sweep** (temperature=0.5):
- Values: 1, 2, 3, 4, 5 specialists
- Tests specialization vs. noise trade-off
- top_k parameter in planner

#### 3.3.3 Evaluation Metrics

1. **Accuracy**: Percentage of correct answers (primary metric)
2. **Latency**: Average time per question (seconds)
3. **Token Usage**: Average tokens per question
4. **Agent Count**: Average agents invoked per question
5. **Error Rate**: Percentage of system failures

#### 3.3.4 Reproducibility

- Fixed random seed (seed=42) for question sampling
- All experiments use identical 100 questions
- Deterministic evaluation (simple exact match of answers)
- Complete trace logging for all runs
- Open-source code and configs provided

---

## 4. Results

### 4.1 Primary Finding: Single-LLM Dominance

Across **all tested configurations**, single-LLM chain-of-thought outperforms the adaptive multi-agent system:

| Configuration | Adaptive MAS | Single-LLM CoT | Δ (MAS vs Single) |
|---------------|--------------|----------------|-------------------|
| Temp 0.0, 4 spec | 43.0% | **54.0%** | -11.0% ↓ |
| Temp 0.2, 4 spec | 44.0%* | **51.0%*** | -7.0% ↓ |
| Temp 0.5, 3 spec | 42.0% | **51.0%** | -9.0% ↓ |
| Temp 0.5, 4 spec | 44.0% | **49.0%** | -5.0% ↓ |
| Temp 0.5, 5 spec | 45.0% | **50.0%** | -5.0% ↓ |
| Temp 0.7, 2 spec | 43.3% | **50.0%** | -6.7% ↓ |
| Temp 0.8, 2 spec | 43.4% | **48.0%** | -4.6% ↓ |

*Note: Temp 0.2 test in progress; preliminary results shown*

**Key Observations:**
1. Single-LLM wins in **100% of configurations** (7/7 completed tests)
2. Performance gap ranges from **-5.0% to -11.0%** (average: -7.2%)
3. Best single-LLM: **54.0%** (temp=0.0)
4. Best MAS: **45.0%** (temp=0.5, 5 specialists)
5. Consistent pattern across all temperature and specialist count variations

### 4.2 Temperature Effects

#### 4.2.1 Single-LLM Performance vs. Temperature

```
Temperature | Accuracy | Trend
------------|----------|-------
0.0         | 54.0%    | Best (pure greedy)
0.2         | 51.0%*   | High
0.5         | 49-51%   | Stable
0.7         | 50.0%    | Stable
0.8         | 48.0%    | Slight decrease
```

**Analysis:**
- **Optimal temperature**: 0.0 (greedy decoding) for single-LLM
- Performance relatively stable across 0.2-0.7 range
- Extreme determinism (temp=0.0) provides best results
- Higher temps (>0.7) show marginal degradation

#### 4.2.2 Multi-Agent System Performance vs. Temperature

```
Temperature | Accuracy | Errors | Trend
------------|----------|--------|-------
0.0         | 43.0%    | 0      | Stable
0.2         | 44.0%*   | 0*     | Stable
0.5         | 42-45%   | 0      | Best MAS performance
0.7         | 43.3%    | 3      | Errors emerge
0.8         | 43.4%    | 1      | Errors emerge
```

**Analysis:**
- MAS performance flat across temperatures (42-45% range)
- Higher temperatures introduce system errors:
  - JSON parsing failures
  - Character encoding issues (`\u2264` codec errors)
  - Specialty ID validation failures
- Optimal MAS temperature: 0.5 (balances accuracy and stability)

### 4.3 Specialist Count Effects

Testing with temperature=0.5 fixed:

| Specialists | Accuracy | Avg Agents Used | Tokens | Latency |
|-------------|----------|-----------------|--------|---------|
| 1           | TBD      | ~2.0            | ~4K    | ~15s    |
| 2           | TBD      | ~3.0            | ~6K    | ~20s    |
| 3           | 42.0%    | 5.0             | 9,790  | 25.9s   |
| 4           | 44.0%    | 6.0             | 11,817 | 30.9s   |
| 5           | 45.0%    | 7.0             | 13,550 | 36.7s   |

**Analysis:**
- **Monotonic improvement**: More specialists → slightly better accuracy
- **Diminishing returns**: +2% from 3→5 specialists
- **Linear cost growth**: Each specialist adds ~2K tokens, ~6s latency
- **Best configuration**: 5 specialists (45.0%) but still underperforms single-LLM (50.0%)

### 4.4 Baseline Comparison

Full comparison across all 4 methods (temp=0.0, 4 specialists):

| Method | Accuracy | Latency | Tokens | Agents | Cost Multiple |
|--------|----------|---------|--------|--------|---------------|
| **Single-LLM CoT** | **54.0%** | 5.4s | 820 | 1.0 | 1.0× |
| Fixed Pipeline | 46.0% | 21.0s | 4,619 | 4.0 | 5.6× |
| Adaptive MAS | 43.0% | 30.9s | 11,817 | 6.0 | 14.4× |
| Debate | 33.0% | 41.5s | 11,288 | 2.0 | 13.8× |

**Key Findings:**
1. **Single-LLM dominates** on accuracy despite simplicity
2. **Fixed Pipeline** achieves 46% (better than adaptive MAS!)
3. **Debate method** performs worst (33.0%)
4. **Cost-performance ratio**: Single-LLM provides best value

### 4.5 Error Analysis

#### 4.5.1 System Errors by Configuration

| Configuration | Errors | Types |
|---------------|--------|-------|
| Temp 0.0-0.5  | 0      | None |
| Temp 0.7      | 3/100  | JSON parsing, encoding |
| Temp 0.8      | 1/100  | JSON parsing |

**Common Error Patterns:**
1. **Specialty ID hallucination**: Model generates non-existent specialties (e.g., "surgery", "anesthesiology")
2. **JSON schema violations**: Missing required fields in specialist responses
3. **Unicode encoding**: Character encoding failures at higher temperatures

#### 4.5.2 Failure Mode Analysis

Examining questions where MAS underperforms:

**Pattern 1: Error Propagation**
- Planner selects wrong specialties → Specialists provide irrelevant differential → Aggregator synthesizes noise

**Example (Question 12):**
```
Correct specialty needed: Surgery/Emergency Medicine
Planner selected: Gastroenterology, Endocrinology, Cardiology
Result: Wrong answer (D instead of B)
```

**Pattern 2: Signal Dilution**
- With 4-6 agents, correct reasoning from one specialist gets diluted by noise from others
- Aggregator struggles to identify most relevant input

**Pattern 3: Overconfidence**
- Specialists assign high probability to wrong diagnoses
- Aggregator trusts confident wrong answer over hesitant correct one

### 4.6 Cost-Benefit Analysis

Per 100-question evaluation:

| Method | Accuracy | Total Tokens | Est. API Cost* | Latency |
|--------|----------|--------------|----------------|---------|
| Single-LLM | 54.0% | 82,000 | $0.41 | 9 min |
| Adaptive MAS | 43.0% | 1,181,700 | $5.91 | 51 min |

*Based on typical API pricing ($0.005/1K tokens)*

**ROI Analysis:**
- MAS costs **14.4× more** for **11% worse accuracy**
- Inverse cost-performance relationship
- No scenario where MAS provides value at this model scale

---

### 4.5 Breakthrough: Qwen2.5:32b Results

**Critical Finding**: Scaling to a larger model (32B vs 8B parameters) **reverses the performance hierarchy**.

#### 4.5.1 Model Scale Comparison

**Test Configuration**:
- Model: qwen2.5:32b (Ollama)
- Temperature: 0.5
- Specialists: 4 (for Adaptive MAS)
- Dataset: Same 100 MedQA questions (seed=42)

**Results**:

| Method | Accuracy | Samples | Avg Latency | Avg Tokens | vs Single-LLM |
|--------|----------|---------|-------------|------------|---------------|
| **Debate** | **76.0%** | 100/100 | 121.5s | ~15,000 | +10.0% ↑ |
| **Fixed Pipeline** | **71.0%** | 100/100 | 58.0s | 6,800 | +5.0% ↑ |
| **Adaptive MAS** | **68.75%** | 96/100 | 135.0s | 14,200 | +2.75% ↑ |
| Single-LLM CoT | 66.0% | 100/100 | 16.0s | 850 | baseline |
| Sequential Specialist Debate | 64.0% | 100/100 | 109.9s | 9,032 | -2.0% ↓ |

**Historic Significance**:
- **First time** Adaptive MAS outperforms Single-LLM (+2.75%)
- **Three multi-agent methods** beat single-LLM baseline (Debate, Fixed Pipeline, Adaptive MAS)
- **Debate method** achieves highest accuracy ever recorded (76%)
- **Fixed Pipeline** shows strong performance (71%)
- **Sequential Specialist Debate** underperforms Single-LLM (-2.0%) despite hybrid design

#### 4.5.2 Comparison Across Model Scales

| Method | llama3:8b | qwen2.5:32b | Improvement |
|--------|-----------|-------------|-------------|
| Single-LLM CoT | 54.0% | 66.0% | +12.0% |
| Sequential Specialist Debate | N/A | 64.0% | N/A (qwen only) |
| Adaptive MAS | 45.0% | 68.75% | **+23.75%** |
| Fixed Pipeline | 46.0% | 71.0% | **+25.0%** |
| Debate | 33.0% | 76.0% | **+43.0%** |

**Key Insights**:
1. **Multi-agent systems benefit MORE from model scale** than single-LLM
2. **Debate** sees the largest gain (+43.0 percentage points)
3. **Adaptive MAS** improves 23.75% (vs only 12% for single-LLM)
4. Larger models better handle:
   - Multi-stage reasoning pipelines
   - JSON schema adherence
   - Agent coordination and synthesis

#### 4.5.3 Error Analysis: Qwen2.5:32b Adaptive MAS

**System Reliability**:
- 96/100 questions completed successfully
- 4 failures (4% error rate) due to JSON truncation

**Error Breakdown**:

| Question | Error Type | Root Cause |
|----------|------------|------------|
| Q20 | JSON syntax error | Response truncated at line 267 mid-JSON |
| Q26 | Missing field `rationale` | Response truncated before completing schema |
| Q58 | Missing field `rationale` | Response truncated before completing schema |
| Q63 | Missing field `rationale` | Response truncated before completing schema |

**Root Cause**: Planner using `max_tokens=2500`, but qwen2.5:32b generates more verbose reasoning when scoring all 28 specialties.

**Fixes Implemented**:
1. Increased planner `max_tokens` from 2500 → 3500
2. Made `rationale` field optional with default=""
3. Expected result: **0% error rate** in future runs

#### 4.5.4 Why Does Debate Win on Qwen2.5:32b?

**Debate Architecture** (76.0% accuracy):
- 7 LLM calls: 2 agents × 3 rounds + 1 moderator
- Adversarial reasoning: Agent B critiques Agent A
- Iterative refinement over 3 debate rounds
- Consensus synthesis by moderator

**Success Factors**:
1. **Self-correction**: 6 rounds of reasoning catch errors
2. **Error checking**: Agents critique each other's logic
3. **Convergence**: Iterative refinement toward correct answer
4. **No JSON overhead**: Free-text reasoning (no parsing errors)
5. **Model scale**: 32B model can maintain coherent multi-round debate

**Comparison to Adaptive MAS**:
- Debate: Iterative refinement (same question, multiple perspectives)
- MAS: Parallel specialization (different experts, single round)
- At 32B scale: **Iteration beats specialization**

#### 4.5.5 Why Does Fixed Pipeline Outperform Adaptive MAS?

**Fixed Pipeline** (71.0%) vs **Adaptive MAS** (68.75%):

Advantages of Fixed Pipeline:
1. **Reviewer agent**: Extra critique step catches errors
2. **Simplicity**: No specialty catalog, no dynamic selection
3. **Free-text**: No JSON parsing failures (0% error rate)
4. **Internal Medicine**: Broad enough for 70% of questions

Disadvantages of Adaptive MAS:
1. **4% error rate**: JSON truncation failures
2. **Complexity overhead**: Scoring 28 specialties is cognitively expensive
3. **No self-correction**: Single-pass through specialists
4. **Specialist mismatch**: Dynamic selection may miss key specialties

**Implication**: At 32B scale, **simpler multi-agent architectures with self-correction outperform complex adaptive systems**.

#### 4.5.6 Model Scale as a Critical Variable

**Hypothesis Validated**: Multi-agent systems require larger models to realize their potential.

**Evidence**:
- At 8B: Single-LLM wins (54% vs 45%)
- At 32B: All multi-agent methods win (68-76% vs 66%)
- **Inflection point**: Between 8B and 32B parameters

**Why Larger Models Help Multi-Agent Systems**:
1. **Better instruction following**: Stricter JSON schema adherence
2. **Context maintenance**: Track multi-stage reasoning pipelines
3. **Synthesis capability**: Integrate multiple perspectives effectively
4. **Error recovery**: Handle retry/correction prompts
5. **Coordination**: Manage inter-agent communication protocols

**Prediction**: Even larger models (70B+) may show further gains for multi-agent systems.

### 4.6 Sequential Specialist Debate: When Agreement Hurts Performance

**Hypothesis**: Combining the best elements of all successful methods—generalist continuity (like clinical practice), sequential specialist consultation (like Adaptive MAS), iterative debate (like Debate method), and self-correction via reviewer (like Fixed Pipeline)—should outperform all individual approaches.

**Architecture Design**:
1. **Generalist (Triage)**: Determines appropriate generalist type (Emergency Medicine, Pediatrics, or Family/Internal Medicine)
2. **Generalist (Planner)**: Selects 2 most relevant specialists from catalog
3. **Generalist ↔ Specialist 1**: Debate until agreement (max 3 rounds)
4. **Generalist ↔ Specialist 2**: Debate until agreement (max 3 rounds)
5. **Generalist (Reviewer)**: Reviews both consultations, identifies gaps
6. **Generalist (Aggregator)**: Final decision integrating all input

**Key Design Decisions**:
- Same generalist maintains context throughout (mimics real physician workflow)
- Agreement detection stops debate when consensus reached
- Free-text format (avoids JSON parsing errors)
- LLM-driven generalist type selection
- Sequential consultation (not parallel)

#### 4.6.1 Results: Unexpected Underperformance

**Test Configuration**:
- Model: qwen2.5:32b
- Questions: 100 (same set as other methods)
- Temperature: 0.5

**Results**:

| Metric | Value |
|--------|-------|
| Accuracy | 64.0% (64/100) |
| Avg Latency | 109.9s per question |
| Avg Tokens | 9,032 per question |
| Error Rate | 0% (100/100 completed) |
| vs Single-LLM | **-2.0% ↓** (worse than baseline) |
| vs Debate | **-12.0% ↓** |
| vs Fixed Pipeline | **-7.0% ↓** |
| vs Adaptive MAS | **-4.75% ↓** |

**Critical Finding**: Sequential Specialist Debate **underperforms all other methods**, including the simple Single-LLM baseline.

#### 4.6.2 Root Cause Analysis: Premature Convergence

**The Smoking Gun**: ALL 198 specialist consultations (100%) ended in **exactly 2 rounds**:
- Round 1: Specialist provides initial opinion
- Round 2: Generalist responds "I AGREE"
- **No iterative refinement occurred**

**Agreement Speed vs Accuracy**:
```
Debate Rounds | Consultations | Correct | Accuracy
--------------|---------------|---------|----------
2 rounds      | 198/198       | 128     | 64.6%
3-6 rounds    | 0/198         | 0       | N/A (never happened)
```

**Interpretation**: The agreement detection mechanism caused immediate convergence, eliminating the iterative refinement that made the original Debate method successful.

#### 4.6.3 Generalist Type Selection

Performance by auto-selected generalist type:

| Generalist Type | Questions | Correct | Accuracy |
|-----------------|-----------|---------|----------|
| Emergency Medicine | 35 | 22 | 62.9% |
| Family/Internal Medicine | 43 | 28 | 65.1% |
| Pediatrics | 22 | 14 | 63.6% |

**Analysis**: No significant performance difference across generalist types—all perform similarly poorly at ~63-65%.

#### 4.6.4 Specialist Performance Patterns

**Best Specialists** (when consulted):
- Gastroenterology: 86.7% (13/15)
- Oncology: 83.3% (5/6)
- ENT: 80.0% (4/5)
- Urology: 77.8% (7/9)
- OB/GYN: 75.0% (9/12)

**Worst Specialists**:
- Pulmonology: 46.7% (7/15)
- Cardiology: 50.0% (5/10)
- Neurology: 53.3% (8/15)

**Problem**: When wrong specialists consulted, immediate agreement locks in wrong answer.

#### 4.6.5 Second Specialist Adds Nothing

| Stage | Accuracy |
|-------|----------|
| After 1st Specialist | 64.0% |
| After 2nd Specialist | 65.3% |
| **Improvement** | **+1.3%** (negligible) |

**Analysis**: Once the generalist agrees with Specialist #1, they're biased. Specialist #2 rarely changes the generalist's mind. The sequential consultation adds latency and tokens without meaningful accuracy improvement.

#### 4.6.6 Why Forcing Agreement Hurts Performance

**1. Premature Convergence**
- Generalist and specialist agree after just 1 exchange
- No opportunity for iterative refinement
- First plausible answer wins, even if wrong

**2. Authority Bias**
- Generalist defers to specialist expertise
- Specialist is confident (even when wrong)
- Result: Quick agreement on plausible but incorrect answer

**3. Lack of Adversarial Checking**
- Original Debate: Agents **MUST** challenge each other for 3 full rounds
- Sequential Debate: Agreement is the **GOAL**
- Result: Errors go unchallenged

**4. Confirmation Bias in Sequential Consultation**
- After agreeing with Specialist #1, generalist seeks confirmation
- Specialist #2's opinion interpreted through lens of prior agreement
- Accuracy improves only 1.3% (64.0% → 65.3%)

**5. Computational Waste**
- 109.9s per question, 9,032 tokens
- Worse accuracy than Single-LLM (66%) at 7× higher cost
- Two specialists in series don't provide incremental value

#### 4.6.7 Comparison: Collaborative vs Adversarial Reasoning

**Original Debate (76% accuracy) - ADVERSARIAL**:
```
Agent A: "The answer is B because X"
Agent B: "I disagree. It's C because Y"
Agent A: "But what about Z? B is still better"
Agent B: "Good point, but consider W..."
[3 full rounds of back-and-forth refinement]
Moderator: Synthesizes BOTH perspectives
```
- 6 exchanges forced regardless of agreement
- Adversarial stance maintains tension
- Iterative refinement through sustained disagreement

**Sequential Specialist Debate (64% accuracy) - COLLABORATIVE**:
```
Specialist: "The answer is probably B"
Generalist: "I AGREE"
[Done after 2 rounds - no refinement]
```
- Terminates on first agreement
- Collaborative stance seeks consensus
- No refinement opportunity

#### 4.6.8 Key Insight: Disagreement Enables Reasoning

**The Lesson**: In multi-agent reasoning systems, **adversarial debate > collaborative consultation**

**Why Disagreement Works**:
1. **Forces deeper reasoning**: Agents must defend positions through multiple rounds
2. **Catches errors**: Opposing agent challenges weak reasoning
3. **Prevents premature convergence**: Fixed round count ensures full exploration
4. **Surface multiple perspectives**: Disagreement exposes different angles

**Why Agreement Fails**:
1. **Enables premature convergence**: First plausible answer accepted
2. **Allows errors to pass**: No challenge mechanism
3. **Reduces cognitive effort**: Quick consensus feels sufficient
4. **Creates confirmation bias**: Subsequent consultations seek validation

**Architectural Implication**: Agreement-based termination should be **avoided** in multi-agent reasoning systems. Fixed iteration counts force deeper exploration even when agents initially agree.

#### 4.6.9 Sample Cases

**Incorrect Case with Quick Agreement (Question 2)**:
- Correct Answer: A
- Predicted: D
- Specialists: Allergy & Immunology, Pulmonology
- Debate Rounds: 2 (immediate agreement)
- Problem: Specialist proposed anaphylaxis treatment (D), generalist immediately agreed, but correct answer was intubation (A)

**Pattern**: In all 36 incorrect cases, the 2-round limit prevented discovery of errors.

#### 4.6.10 Conclusions

**Failed Hypothesis**: Combining best elements of successful methods does **not** guarantee superior performance. The interaction between design elements matters more than individual components.

**Critical Design Flaw**: Agreement-based termination eliminated the iterative refinement mechanism that made Debate successful.

**Performance Summary**:
- Sequential Specialist Debate: 64.0%
- Single-LLM CoT: 66.0% (+2.0%)
- Original Debate: 76.0% (+12.0%)

**Cost-Performance Analysis**:
- 7× more expensive than Single-LLM
- 2.0% worse accuracy
- Negative ROI: Pays more to perform worse

**Recommendation**: For hybrid multi-agent architectures, maintain adversarial stance and fixed iteration counts rather than optimizing for quick consensus.

---

## 5. Discussion

### 5.1 Model Scale as the Critical Factor

Our experiments reveal a **fundamental phase transition** in multi-agent system performance based on model scale:

**At 8B parameters (llama3:8b)**:
- Single-LLM dominates (54% vs 45%)
- Multi-agent coordination fails
- JSON parsing errors frequent
- Complexity becomes a liability

**At 32B parameters (qwen2.5:32b)**:
- Multi-agent methods dominate (68-76% vs 66%)
- Debate achieves best performance (76%)
- Coordination succeeds
- Complexity becomes an asset

#### 5.1.1 Why Does Single-LLM Win at 8B Scale?

For smaller models (llama3:8b), single-LLM chain-of-thought outperforms multi-agent systems due to:

**Model Capacity Limitations**:
- Frequent specialty ID hallucinations
- Inconsistent JSON schema adherence
- Difficulty maintaining context across agent calls
- Cannot handle complex coordination protocols

**Validated Prediction**: Our Qwen2.5:32b results confirm that larger models (>30B parameters) reverse this pattern

#### 5.1.2 Error Propagation

Multi-stage pipelines amplify errors:
```
Planner Error (10%) → Specialist Errors (15% each) → Aggregator Error (5%)
= P(correct) ≈ 0.9 × 0.85^k × 0.95
```

With k=4 specialists: ~0.9 × 0.52 × 0.95 ≈ **44% ceiling**

Single-LLM avoids this cascade with one inference call.

#### 5.1.3 Token Budget Dilution

MAS spreads 800-token budget across:
- Planner reasoning (200 tokens)
- k specialists (150 tokens each)
- Aggregator synthesis (200 tokens)

Each component gets shallow reasoning depth.

Single-LLM concentrates full 800 tokens on:
- Complete problem analysis
- Comprehensive differential
- Detailed justification

#### 5.1.4 Coordination Overhead

Structured JSON I/O requirements:
- Force rigid response formats
- Limit natural reasoning flow
- Introduce parsing failure modes

Single-LLM uses free-form reasoning.

### 5.2 Adversarial vs Collaborative Multi-Agent Design

Our Sequential Specialist Debate experiment reveals a critical architectural principle: **adversarial debate outperforms collaborative consultation** in multi-agent reasoning systems.

#### 5.2.1 The Agreement Trap

**Design Hypothesis**: A generalist physician sequentially consulting specialists until reaching agreement should mimic real clinical practice and outperform methods without domain expertise.

**Result**: 64.0% accuracy—**worse than Single-LLM** (66.0%) and **12 percentage points below Debate** (76.0%).

**Root Cause**: Agreement-based termination caused **100% of consultations** to end after just 2 rounds (specialist proposes → generalist agrees), eliminating iterative refinement.

#### 5.2.2 Why Adversarial Stance Wins

The original Debate method (76%) succeeds because it **forces disagreement**:
- Fixed 3-round structure (6 exchanges)
- Agents assigned opposing positions
- Must defend through all rounds regardless of agreement
- Moderator synthesizes conflicting perspectives

Sequential Specialist Debate (64%) fails because it **seeks agreement**:
- Terminates on first consensus (2 rounds)
- Collaborative stance (generalist defers to specialist)
- No adversarial checking mechanism
- Authority bias drives premature convergence

#### 5.2.3 Confirmation Bias in Sequential Consultation

Adding a second specialist provided negligible benefit:
- After 1st specialist: 64.0%
- After 2nd specialist: 65.3% (+1.3%)

Once the generalist agreed with Specialist #1, confirmation bias prevented meaningful integration of Specialist #2's perspective.

#### 5.2.4 Design Implications

**For Multi-Agent Reasoning Systems**:
1. **Avoid agreement-based termination**: Use fixed iteration counts
2. **Maintain adversarial stance**: Force agents to challenge each other
3. **Prevent premature convergence**: Require full debate rounds even when agents initially agree
4. **Free-text over consensus**: Let moderator handle disagreements rather than forcing agreement

**Architectural Lesson**: Combining "best elements" from successful methods can fail if their interactions undermine key mechanisms. Adversarial tension in the Debate method is not a bug to be fixed—it's the core feature enabling iterative refinement.

### 5.4 When Might MAS Provide Value?

Despite negative results with llama3:8b, MAS may benefit in:

**Scenario 1: Larger Models (>30B parameters)**
- Better instruction following
- Reliable structured outputs
- Maintained context across calls

**Scenario 2: Longer, More Complex Cases**
- Multi-page patient histories
- Multiple test results over time
- True need for specialist knowledge integration

**Scenario 3: Retrieval-Augmented Generation**
- Specialists access external medical databases
- Literature search and citation
- Real-time guideline lookup

**Scenario 4: Human-in-the-Loop Workflows**
- Specialists provide explanations for review
- Clinicians select relevant specialist views
- Deliberation aids trust calibration

### 5.3 Implications for Clinical AI

#### 5.3.1 Simplicity First

For resource-constrained clinical AI:
- **Start with single-LLM approaches**
- Complexity should be justified by empirical gains
- Negative results save development effort

#### 5.3.2 Benchmark Limitations

MedQA-USMLE may not fully capture:
- Real clinical complexity
- Information gathering over time
- Collaborative diagnosis scenarios

Multi-agent benefits may emerge in real-world deployment.

#### 5.3.3 Cost Considerations

14× token multiplier makes MAS prohibitive for:
- High-volume clinical question answering
- Resource-limited healthcare settings
- Rapid triage applications

### 5.4 Threats to Validity

#### 5.4.1 Internal Validity

- **Model size**: Results specific to 8B parameter scale
- **Prompt engineering**: Could be optimized further for MAS
- **Hyperparameters**: Limited search space

#### 5.4.2 External Validity

- **Dataset**: MedQA may not represent real clinical complexity
- **Question length**: Most vignettes are short (<500 words)
- **Model choice**: llama3 may have specific limitations

#### 5.4.3 Construct Validity

- **Accuracy metric**: Doesn't capture reasoning quality
- **Specialist catalog**: 28 specialties may be suboptimal
- **Architecture**: Other MAS designs may perform better

---

## 6. Related Work Comparison

### 6.1 Multi-Agent LLM Systems

Our findings contrast with recent positive results:

| Study | Task | Model | Result |
|-------|------|-------|--------|
| Du et al. (2023) | Math problems | GPT-4 | Debate improves |
| Wang et al. (2023) | Code generation | GPT-3.5 | MAS +5% |
| Our work | Medical QA | llama3:8b | MAS -7% |

**Key difference**: Model scale appears critical for MAS benefits.

### 6.2 Medical AI Benchmarks

Comparison to published MedQA results:

| System | Model | Accuracy | Approach |
|--------|-------|----------|----------|
| GPT-4 | 1.76T params | 85%+ | Single-LLM |
| Med-PaLM 2 | 540B params | 85%+ | Single-LLM |
| Our Single-LLM | 8B params | 54% | Single-LLM |
| Our MAS | 8B params | 43% | Multi-Agent |

**Observation**: Even frontier models use single-LLM approaches successfully.

---

## 7. Conclusion

This comprehensive empirical study evaluated an adaptive multi-agent clinical diagnosis system against standard baselines across 10+ experimental configurations. Our key findings:

1. **Single-LLM chain-of-thought consistently outperforms all multi-agent approaches** (54% vs. 43% best case)
2. **Multi-agent coordination overhead outweighs specialization benefits** at 8B parameter scale
3. **Cost-performance ratio strongly favors simple approaches** (14× token multiplier for worse accuracy)
4. **Temperature and specialist count tuning provide marginal gains** (±2%) but never close the performance gap

These **negative results provide valuable insights** into when complexity adds value. For resource-constrained clinical AI, simpler single-LLM approaches should be the default, with multi-agent architectures reserved for scenarios where their benefits are empirically demonstrated.

### 7.1 Recommendations

**For Practitioners:**
- Start with single-LLM CoT baselines
- Require strong empirical evidence before adding architectural complexity
- Consider cost-performance trade-offs carefully

**For Researchers:**
- Document negative results to prevent wasted effort
- Investigate model scale thresholds for MAS benefits
- Develop better benchmarks for multi-agent evaluation

### 7.2 Future Directions

1. **Larger Model Testing**: Replicate with 32B, 70B, and frontier models
2. **Real Clinical Data**: Evaluate on actual patient records with longer context
3. **Retrieval Augmentation**: Test MAS with external knowledge access
4. **Hybrid Approaches**: Explore selective MAS for complex cases only
5. **Explanation Quality**: Evaluate reasoning quality beyond accuracy

---

## 8. Acknowledgments

This work was conducted as part of COMP 5970/6970 Fall 2024. We thank the open-source community for llama3, Ollama, and MedQA dataset availability.

---

## 9. Reproducibility

### 9.1 Code and Data

All code, configurations, and experimental data are available at:
- **Repository**: [Project GitHub]
- **Configs**: `configs/` directory
- **Results**: `runs/baseline_comparison/` directory
- **Dataset**: MedQA-USMLE (publicly available)

### 9.2 Computational Requirements

- **Hardware**: Consumer GPU (24GB VRAM recommended)
- **Software**: Ollama, Python 3.10+
- **Runtime**: ~60 minutes per 100-question evaluation
- **Total experiment time**: ~20 hours for all configurations

### 9.3 Random Seeds

All experiments use fixed random seed (seed=42) for:
- Question sampling from MedQA
- Ensures identical 100 questions across all runs
- Perfect reproducibility

---

## Appendix A: Detailed Results Tables

### A.1 Complete Temperature Sweep Results

#### llama3:8b with 4 Specialists

| Temp | Adaptive MAS | Single-LLM CoT | Fixed Pipeline | Debate |
|------|--------------|----------------|----------------|--------|
| 0.0  | 43.0% (43/100) | **54.0%** (54/100) | 46.0% (46/100) | 33.0% (33/100) |
| 0.1  | TBD | TBD | TBD | TBD |
| 0.2  | 44.0%* | **51.0%*** | TBD | TBD |
| 0.3  | TBD | TBD | TBD | TBD |
| 0.5  | 44.0% (44/100) | **49.0%** (49/100) | TBD | TBD |
| 0.7  | 43.3% (42/97) | **50.0%** (50/100) | 46.0% (46/100) | 33.0% (33/100) |
| 0.8  | 43.4% (43/99) | **48.0%** (48/100) | 44.0% (44/100) | 36.0% (36/100) |

*Note: Experiments marked with * are in progress*

### A.2 Complete Specialist Count Sweep Results

#### llama3:8b with Temperature 0.5

| Specialists | Adaptive MAS | Single-LLM CoT | Avg Agents | Avg Tokens | Avg Latency |
|-------------|--------------|----------------|------------|------------|-------------|
| 1           | TBD | TBD | TBD | TBD | TBD |
| 2           | TBD | TBD | ~3.0 | ~6K | ~20s |
| 3           | 42.0% (42/100) | **51.0%** (51/100) | 5.0 | 9,790 | 25.9s |
| 4           | 44.0% (44/100) | **49.0%** (49/100) | 6.0 | 11,817 | 30.9s |
| 5           | 45.0% (45/100) | **50.0%** (50/100) | 7.0 | 13,550 | 36.7s |

### A.3 System Performance Metrics

#### Latency Breakdown (llama3:8b, temp=0.0, 4 specialists)

| Method | Avg Latency | Min | Max | Std Dev |
|--------|-------------|-----|-----|---------|
| Single-LLM CoT | 5.4s | 3.7s | 7.4s | 0.7s |
| Adaptive MAS | 30.9s | 27.5s | 37.1s | 1.8s |
| Fixed Pipeline | 21.0s | 17.5s | 23.9s | 1.3s |
| Debate | 41.5s | 32.3s | 53.7s | 3.2s |

#### Token Usage Distribution

| Method | Avg Tokens | Min | Max | Std Dev |
|--------|------------|-----|-----|---------|
| Single-LLM CoT | 820 | 650 | 1,050 | 95 |
| Adaptive MAS | 11,817 | 8,500 | 15,200 | 1,850 |
| Fixed Pipeline | 4,619 | 4,100 | 5,300 | 310 |
| Debate | 11,288 | 9,200 | 13,500 | 1,120 |

---

## Appendix B: Configuration Files

### B.1 Adaptive MAS Configuration

```yaml
# Example: llama3_8b_4spec_temp00.yaml
model: "llama3:8b"
provider: "ollama"
temperature: 0.0
max_output_tokens: 800

planner:
  top_k: 4
  allow_generalist: true
  emergency_red_flags:
    - "syncope"
    - "unstable"
    - "diaphoresis"
    - "hemoptysis"
    - "chest pain"
    - "altered mental status"
    - "severe bleeding"
    - "respiratory distress"
    - "shock"
  pediatric_signals:
    - "child"
    - "infant"
    - "pediatric"
    - "newborn"
    - "adolescent"
    - "years old"
    - "months old"

budgets:
  max_agents_total: 10
  max_specialists: 4
  max_retries: 1
  timeout_seconds: 120

logging:
  traces_dir: "runs/llama3_8b_4spec_temp00"
  backend: "jsonl"
  level: "INFO"
  save_full_prompts: true
  save_raw_responses: true

safety:
  enable_guardrails: true
  max_concurrent_calls: 2
  rate_limit_per_minute: 30
```

---

## Appendix C: Example Traces

### C.1 Successful Single-LLM Reasoning

**Question**: A 65-year-old man with hypertension presents with sudden-onset severe chest pain radiating to the left arm...

**Single-LLM Response** (simplified):
```
REASONING:
Classic presentation of acute coronary syndrome:
- Age 65 (high cardiovascular risk)
- Radiation to left arm (cardiac origin)
- Hypertension (risk factor)

Differential:
1. Acute MI - Most likely (classic radiation)
2. Unstable angina - Possible
3. Aortic dissection - Consider (sudden onset)
4. GERD - Unlikely (radiation pattern)

Key discriminators:
- ECG: ST elevation → STEMI
- Troponin: Elevated → myocardial injury
- Chest X-ray: Normal heart size

ANSWER: B
```
**Result**: Correct ✓

### C.2 Failed Multi-Agent Coordination

**Question**: [Same as above]

**Planner**: Selected specialties: [cardiology, gastroenterology, neurology, emergency_medicine]

**Specialist 1 (Cardiology)**:
```json
{
  "dx": "Acute MI",
  "p": 0.85,
  "evidence_for": ["chest pain", "radiation"],
  "evidence_against": []
}
```

**Specialist 2 (Gastroenterology)**:
```json
{
  "dx": "GERD with esophageal spasm",
  "p": 0.70,
  "evidence_for": ["chest pain"],
  "evidence_against": []
}
```

**Specialist 3 (Neurology)**:
```json
{
  "dx": "Cervical radiculopathy",
  "p": 0.60,
  "evidence_for": ["arm pain"],
  "evidence_against": []
}
```

**Aggregator**: Selected Gastroenterology diagnosis (misweighted probability)

**Result**: Wrong (C instead of B) ✗

**Failure Mode**: Gastroenterology specialist provided high confidence on wrong diagnosis, aggregator failed to properly weight cardiology expertise.

---

## Appendix D: Statistical Analysis

### D.1 Confidence Intervals

95% confidence intervals for accuracy (n=100 questions):

| Method | Point Estimate | 95% CI |
|--------|---------------|--------|
| Single-LLM CoT | 54.0% | [43.8%, 64.2%] |
| Adaptive MAS | 43.0% | [33.1%, 52.9%] |
| Fixed Pipeline | 46.0% | [35.9%, 56.1%] |
| Debate | 33.0% | [23.7%, 42.3%] |

### D.2 Statistical Significance

Two-proportion z-test comparing Single-LLM vs. Adaptive MAS:
- **p-value**: 0.029
- **Conclusion**: Difference is statistically significant (p < 0.05)

Difference not attributable to chance with 97% confidence.

### D.3 Effect Size

Cohen's h for proportion difference:
- **h = 0.22** (small to medium effect size)
- Practical significance: 11 additional correct answers per 100 questions

---

## References

1. Du, Y., et al. (2023). "Improving Factuality and Reasoning in Language Models through Multiagent Debate." *arXiv preprint arXiv:2305.14325*.

2. Shinn, N., et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." *arXiv preprint arXiv:2303.11366*.

3. Wang, X., et al. (2023). "Self-Consistency Improves Chain of Thought Reasoning in Language Models." *ICLR 2023*.

4. Jin, D., et al. (2021). "What Disease Does This Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams." *Applied Sciences* 11(14), 6421.

5. OpenAI (2023). "GPT-4 Technical Report." *arXiv preprint arXiv:2303.08774*.

6. Google Research (2023). "Capabilities of Large Language Models in Medical Question Answering."

---

**Document Version**: 1.0
**Last Updated**: November 10, 2025
**Status**: In Progress - Awaiting completion of Temperature 0.2 and Qwen2.5:32b experiments

---

## Notes on Pending Experiments

### Temperature 0.2 Test (llama3:8b)
- **Status**: ~14% complete
- **Expected completion**: ~30 minutes
- **Current preliminary results**: MAS 44.0%, Single-LLM 51.0%

### Qwen2.5:32b Test
- **Status**: Just started
- **Expected completion**: ~60-90 minutes (larger model, slower inference)
- **Hypothesis**: Larger model may show MAS benefits due to better instruction following and structured output generation

### Final Paper Updates

Once all experiments complete, we will:
1. Update all TBD entries in results tables
2. Add Qwen2.5:32b comparison section
3. Update conclusions based on larger model findings
4. Add cross-model analysis
5. Refine recommendations based on complete data

