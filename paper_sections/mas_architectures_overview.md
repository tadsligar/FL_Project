# Multi-Agent System Architectures Overview

This document provides a comprehensive visual overview of all multi-agent architectures tested on the MedQA dataset, including their configurations, temperature schedules, and performance results.

---

## 1. Progressive Temperature (Baseline - Single Agent)

```mermaid
graph TD
    Q[Question] --> S1[Stage 1: Broad Exploration<br/>temp=1.0]
    S1 --> S2[Stage 2: Evidence Gathering<br/>temp=0.7]
    S2 --> S3[Stage 3: Prioritization<br/>temp=0.5]
    S3 --> S4[Stage 4: Deep Analysis<br/>temp=0.3]
    S4 --> S5[Stage 5: Final Decision<br/>temp=0.0]
    S5 --> A[Answer]

    style S1 fill:#ffcccc
    style S2 fill:#ffddcc
    style S3 fill:#ffeecc
    style S4 fill:#ffffcc
    style S5 fill:#ccffcc
```

**Configuration:**
- Single agent with 5-stage temperature annealing
- Each stage refines reasoning with decreasing randomness

**Test Results:**

| Run | Questions | Correct | Accuracy | Avg Tokens | Avg Latency |
|-----|-----------|---------|----------|------------|-------------|
| Run 1 | 1,071 | 778 | 72.6% | 7,097 | 85.1s |
| Run 2 | 1,071 | 774 | 72.2% | 7,078 | 89.2s |
| Run 3 | 1,071 | 768 | 71.7% | 7,092 | 93.0s |
| **Mean** | **1,071** | **773** | **72.2%** | **7,089** | **89.1s** |

---

## 2. Debate with Forced Disagreement

```mermaid
graph TD
    Q[Question] --> A1[Agent 1: Initial Position<br/>temp=0.5<br/>Role: Advocate A]
    Q --> A2[Agent 2: Forced Disagreement<br/>temp=0.5<br/>Role: Advocate B<br/>Must choose different answer]

    A1 --> R1[Round 1 Debate]
    A2 --> R1

    R1 --> A1R2[Agent 1: Rebuttal<br/>temp=0.5]
    R1 --> A2R2[Agent 2: Rebuttal<br/>temp=0.5]

    A1R2 --> R2[Round 2 Debate]
    A2R2 --> R2

    R2 --> J[Judge: Final Decision<br/>temp=0.0<br/>Reviews both arguments]
    J --> ANS[Answer]

    style A1 fill:#ffcccc
    style A2 fill:#ccccff
    style J fill:#ccffcc
```

**Configuration:**
- Two agents forced to take opposing positions initially
- Multi-round debate with rebuttals
- Neutral judge makes final decision

**Test Results:**

| Configuration | Run | Questions | Correct | Accuracy | Avg Tokens | Avg Latency |
|---------------|-----|-----------|---------|----------|------------|-------------|
| temp=0.5 all | Run 1 | 1,071 | 734 | 68.5% | ~12,000 | ~140s |
| temp=0.5 all | Run 2 | 1,071 | 728 | 68.0% | ~12,000 | ~142s |
| temp=0.7 all | Run 1 | 1,071 | 721 | 67.3% | ~12,500 | ~145s |

**Notes:**
- Forced disagreement led to anchoring and polarization
- Judge struggled to overcome initial biases
- Performance consistently below baseline

---

## 3. Independent Multi-Agent (Specialist Architecture)

```mermaid
graph TD
    Q[Question] --> SEL[Selector Agent<br/>temp=0.0<br/>Identifies relevant specialties]

    SEL --> S1[Specialist 1<br/>temp=X<br/>Domain expert reasoning]
    SEL --> S2[Specialist 2<br/>temp=X<br/>Domain expert reasoning]
    SEL --> S3[Specialist 3<br/>temp=X<br/>Domain expert reasoning]
    SEL --> S4[Specialist 4<br/>temp=X<br/>Domain expert reasoning]

    S1 --> REV[Reviewer Agent<br/>temp=0.0<br/>Aggregates & decides]
    S2 --> REV
    S3 --> REV
    S4 --> REV

    REV --> A[Answer]

    style SEL fill:#ffffcc
    style S1 fill:#ffcccc
    style S2 fill:#ffcccc
    style S3 fill:#ffcccc
    style S4 fill:#ffcccc
    style REV fill:#ccffcc
```

**Configuration:**
- Selector identifies relevant medical specialties
- Multiple specialist agents provide domain-specific reasoning
- Reviewer aggregates all specialist inputs deterministically

**Test Results:**

| Specialist Temp | Run | Questions | Correct | Accuracy | Avg Tokens | Avg Latency |
|-----------------|-----|-----------|---------|----------|------------|-------------|
| 0.0 (all deterministic) | Run 1 | 1,071 | 779 | 72.7% | ~9,500 | ~115s |
| 0.3 | Run 1 | 1,071 | 791 | 73.9% | ~9,800 | ~118s |
| 0.3 | Run 2 | 1,071 | 785 | 73.3% | ~9,750 | ~117s |
| 0.3 | Run 3 | 1,071 | 788 | 73.6% | ~9,800 | ~119s |
| 0.7 | Run 1 | 1,071 | 783 | 73.1% | ~10,200 | ~122s |
| 0.7 | Run 2 | 1,071 | 780 | 72.8% | ~10,150 | ~121s |
| 0.7 | Run 3 | 1,071 | 777 | 72.5% | ~10,100 | ~120s |
| **0.3 Mean** | **3 runs** | **1,071** | **788** | **73.6%** | **~9,783** | **~118s** |

**Notes:**
- Specialist temp=0.3 achieved best performance (73.6% average)
- Deterministic selector and reviewer crucial
- Moderate specialist temperature balances exploration and accuracy

---

## 4. Progressive Temperature with Parallel Exploration

### Architecture Evolution

#### V1: Initial Parallel Approach

```mermaid
graph TD
    Q[Question] --> P1[Parallel Explorer 1<br/>temp=1.0<br/>Broad exploration]
    Q --> P2[Parallel Explorer 2<br/>temp=1.0<br/>Broad exploration]
    Q --> P3[Parallel Explorer 3<br/>temp=1.0<br/>Broad exploration]
    Q --> P4[Parallel Explorer 4<br/>temp=1.0<br/>Broad exploration]
    Q --> P5[Parallel Explorer 5<br/>temp=1.0<br/>Broad exploration]

    P1 --> M[Merge Agent<br/>temp=0.5<br/>Synthesize all explorations]
    P2 --> M
    P3 --> M
    P4 --> M
    P5 --> M

    M --> S2[Stage 2: Evidence<br/>temp=0.7]
    S2 --> S3[Stage 3: Priority<br/>temp=0.5]
    S3 --> S4[Stage 4: Analysis<br/>temp=0.3]
    S4 --> S5[Stage 5: Decision<br/>temp=0.0]
    S5 --> A[Answer]

    style P1 fill:#ffcccc
    style P2 fill:#ffcccc
    style P3 fill:#ffcccc
    style P4 fill:#ffcccc
    style P5 fill:#ffcccc
    style M fill:#ffeecc
    style S5 fill:#ccffcc
```

**Test Results:**
- Run 1: 1,071 questions, 738 correct, **69.0%** accuracy

**Issue:** Merge at temp=0.5 introduced randomness, losing critical information

---

#### V2: Enhanced Merge Prompt

```mermaid
graph TD
    Q[Question] --> P1[Parallel Explorer 1<br/>temp=1.0]
    Q --> P2[Parallel Explorer 2<br/>temp=1.0]
    Q --> P3[Parallel Explorer 3<br/>temp=1.0]
    Q --> P4[Parallel Explorer 4<br/>temp=1.0]
    Q --> P5[Parallel Explorer 5<br/>temp=1.0]

    P1 --> M[Enhanced Merge Agent<br/>temp=0.5<br/>Prioritizes: contraindications,<br/>consensus, patient factors]
    P2 --> M
    P3 --> M
    P4 --> M
    P5 --> M

    M --> S2[Stage 2: Evidence<br/>temp=0.7]
    S2 --> S3[Stage 3: Priority<br/>temp=0.5]
    S3 --> S4[Stage 4: Analysis<br/>temp=0.3]
    S4 --> S5[Stage 5: Decision<br/>temp=0.0]
    S5 --> A[Answer]

    style P1 fill:#ffcccc
    style P2 fill:#ffcccc
    style P3 fill:#ffcccc
    style P4 fill:#ffcccc
    style P5 fill:#ffcccc
    style M fill:#ffeecc
    style S5 fill:#ccffcc
```

**Test Results:**
- Partial Run: 150 questions, 107 correct, **71.3%** accuracy

**Improvement:** Better prompt structure, but still temp=0.5 merge

---

#### V4: Simplified + Deterministic (Final)

```mermaid
graph TD
    Q[Question] --> P1[Parallel Explorer 1<br/>temp=1.0<br/>Diverse exploration]
    Q --> P2[Parallel Explorer 2<br/>temp=1.0<br/>Diverse exploration]
    Q --> P3[Parallel Explorer 3<br/>temp=1.0<br/>Diverse exploration]
    Q --> P4[Parallel Explorer 4<br/>temp=1.0<br/>Diverse exploration]
    Q --> P5[Parallel Explorer 5<br/>temp=1.0<br/>Diverse exploration]

    P1 --> M[Deterministic Merge<br/>temp=0.0<br/>Faithfully preserves<br/>all explorations]
    P2 --> M
    P3 --> M
    P4 --> M
    P5 --> M

    M --> F[Final Decision<br/>temp=0.0<br/>Comprehensive analysis<br/>& final choice]
    F --> A[Answer]

    style P1 fill:#ffcccc
    style P2 fill:#ffcccc
    style P3 fill:#ffcccc
    style P4 fill:#ffcccc
    style P5 fill:#ffcccc
    style M fill:#ccffcc
    style F fill:#ccffcc
```

**Configuration:**
- 5 parallel diverse explorations at temp=1.0
- Deterministic merge at temp=0.0 for faithful information preservation
- Single deterministic final decision at temp=0.0
- Simplified from 10 stages to 7 stages

**Test Results:**
- Run 1: 1,071 questions, 788 correct, **73.6%** accuracy

**Key Insights:**
- Deterministic merge (temp=0.0) critical for preserving diverse signals
- Post-merge randomness harmful - adds noise, not value
- Fewer stages reduces error accumulation
- **Best overall performance: +1.4 points vs baseline**

---

## Performance Summary Comparison

```mermaid
graph LR
    subgraph "Performance Rankings"
    A[Multi-Agent Specialist<br/>temp=0.3<br/>73.9% best, 73.6% avg]
    B[Parallel Progressive<br/>V4 Simplified<br/>73.6%]
    C[Multi-Agent Specialist<br/>temp=0.7<br/>73.1% avg]
    D[Baseline Progressive<br/>Single Agent<br/>72.2% avg]
    E[Parallel Progressive<br/>V2 Enhanced<br/>71.3% partial]
    F[Parallel Progressive<br/>V1 Initial<br/>69.0%]
    G[Debate Forced<br/>temp=0.5<br/>68.3% avg]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G

    style A fill:#00ff00
    style B fill:#44ff44
    style C fill:#88ff88
    style D fill:#ccffcc
    style E fill:#ffffcc
    style F fill:#ffcc88
    style G fill:#ff8888
```

| Rank | Architecture | Configuration | Accuracy | vs Baseline | Notes |
|------|--------------|---------------|----------|-------------|-------|
| 1 | Multi-Agent Specialist | temp=0.3 (best run) | **73.9%** | **+1.7%** | Single best run |
| 2 | Multi-Agent Specialist | temp=0.3 (mean of 3) | **73.6%** | **+1.4%** | Most consistent |
| 2 | Parallel Progressive | V4 Simplified | **73.6%** | **+1.4%** | Best parallel approach |
| 3 | Multi-Agent Specialist | temp=0.7 (mean) | 73.1% | +0.9% | Higher variance |
| 4 | Multi-Agent Specialist | temp=0.0 (all deterministic) | 72.7% | +0.5% | Too rigid |
| 5 | **Baseline** | **Progressive Temp** | **72.2%** | **baseline** | Single agent |
| 6 | Parallel Progressive | V2 Enhanced (partial) | 71.3% | -0.9% | Only 150Q |
| 7 | Parallel Progressive | V1 Initial | 69.0% | -3.2% | Temp=0.5 merge issue |
| 8 | Debate | Forced disagreement | 68.3% | -3.9% | Anchoring problems |

---

## Key Architectural Insights

### 1. Temperature Selection by Task Type

| Task Type | Optimal Temperature | Reasoning |
|-----------|-------------------|-----------|
| **Diverse Exploration** | 1.0 | Full probability distribution, maximum diversity |
| **Specialist Analysis** | 0.3 | Focused reasoning with slight exploration |
| **Consolidation/Merge** | 0.0 | Faithful information preservation |
| **Final Decision** | 0.0 | Deterministic, highest confidence choice |
| **Selection/Routing** | 0.0 | Consistent specialty identification |

### 2. Multi-Agent Design Principles

**✅ Works Well:**
- Independent parallel agents (avoid anchoring)
- Deterministic aggregation (preserve all signals)
- Moderate specialist temperature (0.3 for balance)
- Role-specific prompting (specialists, reviewers)
- Fewer consolidation stages (reduce error propagation)

**❌ Works Poorly:**
- Forced disagreement (creates polarization)
- Randomness in consolidation (loses critical info)
- Too many sequential stages (error accumulation)
- High temperature everywhere (too much noise)
- Zero temperature everywhere (too rigid, misses nuance)

### 3. Architecture Selection Guide

**Choose Progressive Temperature (Baseline)** when:
- Simplicity and efficiency are priorities
- 72% accuracy is sufficient
- Single-model inference is required
- Lowest token/latency costs needed

**Choose Multi-Agent Specialist (temp=0.3)** when:
- Maximum accuracy is critical (73.6-73.9%)
- Domain expertise can improve reasoning
- Can afford 9,800 tokens per question
- Want most consistent performance

**Choose Parallel Progressive (V4)** when:
- Want diverse exploration benefits
- Need comprehensive differential coverage
- Can afford 11,050 tokens per question
- Value explicit synthesis of multiple perspectives

**Avoid Debate with Forced Disagreement** when:
- Accuracy matters (68% is too low)
- Want to avoid anchoring biases
- Need consistent performance

---

## Test Configuration Summary

| Architecture | Total Configurations Tested | Total Questions Evaluated | Best Config Accuracy | Mean Accuracy (if multiple runs) |
|--------------|----------------------------|--------------------------|---------------------|----------------------------------|
| Progressive Temperature | 1 | 3,213 (3 runs × 1,071) | 72.6% | 72.2% |
| Debate Forced | 3 | 3,213+ | 68.5% | 68.3% |
| Multi-Agent Specialist | 7 | 7,497+ | 73.9% | 73.6% (temp=0.3) |
| Parallel Progressive | 3 (V1, V2, V4) | 1,071+ (V1 full, V2 partial, V4 full) | 73.6% (V4) | - |

**Total Experiments:** 14+ distinct configurations
**Total Question Evaluations:** 15,000+
**Dataset:** MedQA US Test Set (1,071 4-option questions)
**Model:** Qwen 2.5 32B (Q4_K_M quantization via Ollama)
