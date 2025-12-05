# Temperature Effects and Progressive Reasoning Experiments

**Status**: In Progress (November 2024)
**Model**: qwen2.5:32b (Ollama)
**Dataset**: MedQA US Test (1,071 questions)

---

## Overview

This document captures findings and ongoing experiments exploring how temperature settings affect different reasoning architectures in multi-agent medical question answering systems.

---

## 4.3 The Role of Temperature in Adversarial vs Collaborative Reasoning

### Hypothesis

**Adversarial reasoning systems require higher temperatures than collaborative systems to function effectively.**

### Rationale

Temperature in LLM sampling controls the randomness/creativity of responses:
- **Low temperature (0.0-0.3)**: Deterministic, conservative, consistent
- **Medium temperature (0.4-0.7)**: Balanced creativity and coherence
- **High temperature (0.8-1.0)**: Diverse, exploratory, creative

#### Why Debate Needs Higher Temperature

In forced disagreement debate:
1. **Forced Opposition**: Agents must argue for different answers even when evidence is unclear
2. **Creative Counter-Arguments**: Need to generate novel perspectives and alternative interpretations
3. **Breaking Anchoring**: Must overcome the model's default/most-likely answer to provide genuine opposition

With low temperature, debate agents struggle to:
- Generate convincing arguments for non-preferred answers
- Avoid converging to the same conclusion despite forced disagreement
- Provide meaningful diversity in reasoning paths

#### Why Collaborative Systems Tolerate Lower Temperature

In independent multi-agent synthesis:
1. **No Forced Opposition**: Each specialist naturally focuses on their expertise
2. **Deterministic Selection**: Selector and reviewer benefit from consistent, reliable decisions
3. **Complementary Views**: Diversity comes from different specialist roles, not sampling randomness

### Comparison to Existing Results

| System | Temperature | Accuracy | Notes |
|--------|-------------|----------|-------|
| Multi-Agent (Mixed) | selector=0.0, specialist=0.3, reviewer=0.0 | 63.37% | Best collaborative performance |
| Debate | temp=0.5 | 61.44% | 2 percentage points below collaborative |
| Debate | temp=0.5 (run 1, completed) | 61.44% | Baseline adversarial performance |

**Initial Finding**: At temp=0.5, adversarial debate underperforms collaborative multi-agent by ~2 percentage points. This may indicate that temp=0.5 is still too low for effective adversarial reasoning.

---

## Ongoing Experiments (November 2024)

### 1. Debate Temperature Sensitivity Analysis

**Status**: Currently Running (~38% complete)

#### Motivation
Test whether increasing temperature improves debate performance by enabling more creative counter-arguments and genuine disagreement.

#### Tests Queued

1. **Debate temp=0.5 (run 2)** - Currently running for statistical validation
   - Progress: Question 411/1071 (38%)
   - Expected completion: ~23 hours
   - Purpose: Confirm stability of 61.4% accuracy

2. **Debate temp=0.7** - Queued to start after run 2
   - Higher temperature for more creative argumentation
   - Hypothesis: Will improve over temp=0.5 by enabling better counter-arguments

3. **Progressive Temperature** - Queued after debate temp=0.7
   - Novel approach combining exploration and exploitation
   - See Section 4.4 below

#### Expected Outcomes

**If temp=0.7 > temp=0.5:**
- Confirms that adversarial reasoning needs higher temperature
- Suggests debate may be viable with proper temperature tuning
- Opens question: Can debate match or exceed collaborative at optimal temperature?

**If temp=0.7 ≈ temp=0.5:**
- Temperature may not be the limiting factor
- Forced disagreement architecture may have fundamental limitations
- Collaborative approaches may be inherently more effective

**If temp=0.7 < temp=0.5:**
- Too much randomness hurts coherence
- Sweet spot exists between 0.5 and 0.7
- Suggests fine-grained temperature search needed

---

## 4.4 Progressive Temperature Reasoning (Simulated Annealing)

### Concept

**Progressive temperature scheduling**: Start with high temperature for exploration, gradually decrease to low temperature for exploitation.

Analogous to simulated annealing in optimization:
- High temp: Escape local optima, explore solution space
- Low temp: Converge to optimal solution

### Implementation

**5-Stage Temperature Schedule**: 1.0 → 0.7 → 0.5 → 0.3 → 0.0

Each stage maps to a clinical reasoning phase:

| Stage | Temp | Clinical Reasoning Phase | Purpose |
|-------|------|-------------------------|---------|
| 1 | 1.0 | Broad Differential Diagnosis | Generate diverse possibilities, even unlikely ones |
| 2 | 0.7 | Evidence Gathering | Analyze supporting/refuting evidence for each possibility |
| 3 | 0.5 | Prioritization | Rank candidates, narrow to top 2-3 diagnoses |
| 4 | 0.3 | Deep Analysis | Rigorous comparison of leading candidates |
| 5 | 0.0 | Final Decision | Deterministic selection of best answer |

### Advantages Over Fixed Temperature

1. **Exploration without Sacrificing Precision**: High temp explores, low temp decides
2. **Mimics Human Clinical Reasoning**: Physicians naturally broaden then narrow differential
3. **Single-Agent Efficiency**: No debate coordination overhead, just 5 sequential LLM calls
4. **Theoretical Foundation**: Well-established in optimization literature

### Hypothesis

Progressive temperature will:
- **Outperform fixed temp=0.5**: Better exploration of hypothesis space
- **Potentially match multi-agent**: Systematic reasoning without coordination overhead
- **Show stage-specific benefits**: Early stages generate diverse hypotheses, late stages make reliable decisions

### Test Configuration

**Status**: Queued (will run after debate experiments)

- 5 LLM calls per question (1 per temperature stage)
- Full 1,071 question evaluation
- Checkpoint support for long-running test
- Temperature schedule: [1.0, 0.7, 0.5, 0.3, 0.0]

**Comparison points:**
- Debate temp=0.5: 61.4%
- Multi-agent temp=0.3: 63.4%
- Theoretical ceiling (if perfect aggregation): 80.8%

---

## 4.5 Hybrid Approach Experiments

### Motivation

After observing that:
- **Collaborative multi-agent** (63.4%) outperforms **adversarial debate** (61.4%)
- Both approaches have complementary strengths

We explored hybrid architectures attempting to combine the best aspects of both:
- **From debate**: Adversarial challenge, critical evaluation, forced disagreement
- **From specialists**: Domain expertise, focused knowledge, independent perspectives

### Approaches Explored

#### 1. Answer-Focused Specialist Consultation (Proposed, Not Tested)

**Core Innovation**: Analyze what each ANSWER CHOICE implies, then assign specialists accordingly.

**Architecture**:
1. **Answer Analysis Phase**: Generalist examines all 4 answer options
2. **Specialist Assignment**: For each answer, identify required expertise (e.g., Answer A implies cardiology, Answer B implies nephrology)
3. **Adversarial Consultation**: Generalist challenges each specialist with counterpoints from OTHER answers
4. **Synthesis**: Generalist weighs all specialist opinions

**Expected Performance**: 72-75% (not tested)

**Key Innovation**: Rather than analyzing the question, analyze the answer space to guide specialist selection.

**Status**: Proposed architecture documented in `docs/answer_focused_consultation_architecture.md`

---

#### 2. Forced Challenge Debate (Proposed, Not Tested)

**Core Innovation**: Generalist MUST act as devil's advocate and challenge specialist conclusions.

**Architecture**:
1. **Initial Analysis**: Specialist provides domain-specific diagnosis
2. **Mandatory Challenge**: Generalist is REQUIRED to argue against the specialist's conclusion
3. **Specialist Defense**: Specialist must defend or revise their position
4. **Final Decision**: Generalist synthesizes after adversarial exchange

**Expected Performance**: 68-72% (not tested)

**Key Difference from Standard Debate**:
- Debate: Two agents forced to disagree from the start
- Forced Challenge: Expert proposes, generalist MUST challenge (even if initially agreeing)

**Hypothesis**: Mandatory challenge prevents premature convergence while preserving specialist expertise.

**Status**: Proposed architecture documented in `docs/debate_refinement_proposal.md`

---

#### 3. Answer Space Consultation (Tested, Failed)

**Status**: COMPLETED - November 2024
**Result**: 54.2% accuracy (22 percentage points BELOW debate baseline)

**Architecture**:
1. **Answer Analysis**: LLM analyzes all 4 answer choices to infer medical domains
2. **Targeted Selection**: Dynamically selects 2 specialists based on answer space
3. **Synthesis**: Generalist combines specialist opinions

**The Parsing Failure Paradox**

This experiment revealed a critical failure mode:

| Approach | Accuracy | Notes |
|----------|----------|-------|
| **Generic specialists** (cardiology/pulmonology) | **75%** | Fixed, domain-general specialists |
| **LLM-selected specialists** (answer-guided) | **50%** | Dynamic, "targeted" selection |
| **Overall (Answer Space Consultation)** | **54%** | Weighted average |

**Key Finding**: LLM's attempt to "intelligently" select specialists based on answer choices was WORSE than random/generic selection by 25 percentage points.

**Possible Explanations**:
1. **Answer parsing errors**: LLM misidentified medical domains from answer text
2. **Over-specialization**: Highly specific specialists lack breadth needed for complex cases
3. **Selection bias**: LLM chose specialists based on superficial answer features, not true diagnostic requirements
4. **Added complexity**: Extra reasoning layer introduced more failure points

**Critical Lesson**: Sophisticated answer-space analysis can be actively harmful. Simpler architectures (fixed specialists, direct debate) may be more robust.

**Status**: Complete results documented in `docs/answer_space_consultation_results.md`

---

### Hybrid Approaches Summary

| Approach | Status | Expected/Actual Accuracy | Key Innovation |
|----------|--------|-------------------------|----------------|
| Answer-Focused Consultation | Proposed | 72-75% (not tested) | Analyze answer choices to guide specialist selection |
| Forced Challenge Debate | Proposed | 68-72% (not tested) | Mandatory adversarial challenge of specialist |
| Answer Space Consultation | **TESTED** | **54.2%** | Dynamic specialist selection based on answer parsing |

### Key Lessons Learned

1. **Complexity ≠ Performance**: The most sophisticated approach (Answer Space Consultation) performed worst
2. **Parsing Failure Risk**: LLM-driven meta-reasoning (selecting specialists) can fail catastrophically
3. **Generic > Targeted**: Fixed, broad specialists outperformed dynamic, targeted selection by 25 points
4. **Simplicity Advantage**: Simpler architectures (debate, independent multi-agent) are more robust

### Implications for Future Work

**What NOT to do**:
- Dynamic specialist selection based on LLM analysis of answer text
- Adding meta-reasoning layers that can introduce additional failure modes
- Over-engineering specialist targeting

**What MIGHT work**:
- Forced Challenge Debate: Leverages specialist expertise while forcing adversarial evaluation
- Fixed specialist pools: Robust, predictable, avoid parsing errors
- Post-hoc validation: Use adversarial challenge AFTER specialist consensus (not during selection)

**Untested hypotheses**:
- Would Forced Challenge Debate achieve expected 68-72% performance?
- Would Answer-Focused Consultation succeed if using FIXED specialist mapping (not LLM-driven selection)?
- Can any hybrid approach exceed the 63.4% multi-agent baseline?

---

## Related Work

### Temperature in Multi-Agent Systems

The mixed temperature results (Section 4.2) showed:
- Specialists benefit from moderate diversity (temp=0.3)
- Selector and reviewer benefit from determinism (temp=0.0)
- Mixed approach: 63.37% accuracy

### Why Progressive Temperature is Different

Unlike mixed temperature multi-agent:
1. **Single agent**: No coordination overhead
2. **Temporal structure**: Temperature changes over time, not across agents
3. **Explicit stages**: Each temperature serves a specific reasoning purpose

---

## Future Experiments

### Short-term (Ongoing)
1. Complete debate temp=0.5 run 2 for statistical validation
2. Test debate temp=0.7 to validate temperature sensitivity hypothesis
3. Evaluate progressive temperature approach

### Medium-term (Proposed)
1. **Fine-grained temperature search**: Test debate at 0.6, 0.8 to find optimal setting
2. **Alternative schedules**: Test different temperature progressions (e.g., 1.0→0.0 in 3 stages vs 5)
3. **Reverse annealing**: Start low, go high (0.0→1.0) to test if order matters
4. **Adaptive temperature**: Let model confidence determine temperature adjustments

### Long-term (Speculative)
1. **Hybrid approaches**: Combine progressive temperature with multi-agent
2. **Per-question temperature**: Adjust schedule based on question difficulty
3. **Stage-specific specialist selection**: Use high-temp stage to pick specialists, low-temp for synthesis

---

## Implementation Notes

### Checkpointing
All long-running tests include checkpoint support:
- Save progress every 50 questions
- Resume capability using `--resume` flag
- Prevents data loss from crashes or interruptions

### Test Isolation
Tests are queued sequentially using `&&` operators to:
- Prevent resource competition
- Ensure clean results
- Enable automatic progression through test suite

### Data Locations

**Completed Tests:**
- Debate temp=0.5 (run 1): `runs/debate_full_dataset/20251124_214202/`
- Multi-agent mixed temp: `docs/experiments/mixed_temperature_results.md`

**Ongoing Tests:**
- Debate temp=0.5 (run 2): `runs/debate_temp05_run2/20251126_133617/` (in progress)
- Debate temp=0.7: Queued
- Progressive temperature: Queued

---

## Key Questions

1. **Does higher temperature improve adversarial debate?**
   - Testing: temp=0.5 vs temp=0.7
   - Hypothesis: Yes, creative counter-arguments need randomness

2. **Can progressive temperature match multi-agent performance?**
   - Testing: Progressive (1.0→0.0) vs multi-agent (63.4%)
   - Hypothesis: Systematic exploration can rival multiple perspectives

3. **What is the optimal temperature for each architecture?**
   - Collaborative: Appears to be ~0.3 (63.4%)
   - Adversarial: Unknown, testing 0.5 and 0.7
   - Progressive: By definition uses all temperatures

4. **Is temperature the limiting factor for debate?**
   - If temp=0.7 ≈ temp=0.5, the architecture itself may be the issue
   - If temp=0.7 > temp=0.5, suggests temperature tuning is crucial

---

## Preliminary Conclusions

Based on completed experiments:

1. **Multi-agent collaborative reasoning outperforms debate by ~2 percentage points** (63.4% vs 61.4%)
2. **Mixed temperature improves multi-agent performance** (+0.8% over uniform temp=0.3)
3. **Temperature likely matters more for adversarial than collaborative systems**

Final conclusions await completion of ongoing experiments.

---

**Last Updated**: November 27, 2024
**Experiments Running**: Yes (debate temp=0.5 run 2 at 38% complete)
