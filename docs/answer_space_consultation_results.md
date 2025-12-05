# Answer Space Consultation - Experimental Results

**Date**: November 12, 2025
**Model**: Qwen2.5:32b via Ollama
**Dataset**: MedQA-USMLE (100 questions)

## Executive Summary

**Result: Failed Experiment**
- **Accuracy**: 54% (54/100 correct)
- **Performance**: 22 percentage points below Debate (76%), 12 points below Single-LLM (66%)
- **Critical Finding**: When specialist parsing failed, the system performed BETTER (75% vs 50%)
- **Conclusion**: Answer space analysis is actively harmful to diagnostic accuracy

## Performance Comparison

| Method | Accuracy | Rank |
|--------|----------|------|
| **Debate** | **76%** | 1st ⭐ |
| Single-LLM | 66% | 2nd |
| Sequential Specialist Debate | 64% | 3rd |
| **Answer Space Consultation** | **54%** | 4th ❌ |

## Architecture Overview

### Core Hypothesis
Analyzing all four answer choices together (the "answer space") would help the generalist select more appropriate specialists than looking at the question alone.

### Design Rationale
Instead of having the generalist pick specialists based only on the question, we wanted them to see what the answer choices suggest about the differential diagnosis:
- If answers span cardiac vs respiratory issues → consult Cardiology and Pulmonology
- If answers represent different psychiatric interventions → consult Psychiatry
- If answers involve endocrine + renal trade-offs → consult Endocrinology and Nephrology

### Implementation Phases

1. **Answer Space Analysis (Phase 1)**
   - Generalist analyzes ALL FOUR answer choices as a complete set
   - For each answer, identifies: diagnosis/treatment approach and medical domain
   - Determines which medical specialties the answer space collectively represents

2. **Specialist Selection (Phase 2)**
   - Selects 2-3 specialists based on answer space analysis
   - Documents specific rationale for each specialist selection
   - System allows LLM to "hallucinate" specialists outside the predefined catalog

3. **Specialist Consultation (Phase 3)**
   - Each specialist receives:
     - The question
     - ALL FOUR answer choices
     - Rationale for why they were selected
     - Answer space analysis context
   - Specialist evaluates ALL options and selects the best one

4. **Challenge-Response (Phase 4)**
   - Generalist challenges specialist with counterpoints from the OTHER 3 answers
   - Specialist must DEFEND, REVISE, or DEFER their choice
   - Tests if specialist can justify their answer against alternatives

5. **Aggregation (Phase 5)**
   - Aggregator synthesizes across all specialist consultations
   - Considers consensus, evidence strength, and changed minds
   - Makes final recommendation

6. **Review (Phase 6)**
   - Reviewer (generalist) checks aggregator's decision
   - Can APPROVE or OVERRIDE if serious flaws detected

### Technical Implementation

**File**: `src/baselines/answer_space_consultation.py`

**Key Functions**:
- `_analyze_answer_space()`: Generalist analyzes answer space and selects specialists
- `_consult_specialist()`: Two-step consultation with challenge-response
- `_aggregate_consultations()`: Synthesize specialist input
- `_review_decision()`: Final quality check

**Improvements Made**:
- ✅ Duplicate specialist prevention (set-based tracking)
- ✅ Scoped parsing (only in "SPECIALISTS TO CONSULT" section)
- ✅ Specialist selection rationale extraction and communication
- ✅ Hallucinated specialist support (handles non-catalog specialties)

## Results

### Overall Performance
- **Total Questions**: 100
- **Correct**: 54 (54.0%)
- **Incorrect**: 46 (46.0%)
- **Avg Latency**: 86.6 seconds per question
- **Avg Tokens**: 7,585 per question
- **Total Time**: ~2.4 hours

### Parsing Analysis

The system encountered specialist parsing failures in 16/100 questions (16%), where it fell back to default specialists (cardiology, pulmonology).

| Category | Accuracy | Count |
|----------|----------|-------|
| **Parsing FAILURES** (default cardiology/pulmonology) | **75.0%** | 12/16 ✓ |
| **Parsing SUCCESS** (LLM-selected specialists) | **50.0%** | 42/84 ✓ |
| **Overall** | **54.0%** | 54/100 ✓ |

### Technical Quality Metrics

✅ **Working Correctly**:
- Zero duplicate specialists across all 100 questions
- ENT over-selection eliminated (0 occurrences, was 90% in buggy version)
- Diverse specialist selection: 29+ different specialties used
- Hallucinated specialists handled successfully (4 cases)

❌ **Issues**:
- Parsing failures: 16/100 (16%)
- Accuracy degradation: 70% (10 questions) → 54% (100 questions)

### Specialist Selection Distribution

**Most Frequently Selected Specialists** (parsing success only):
1. Pediatrics: 14 times
2. Cardiology: 11 times
3. Neurology: 10 times
4. Gastroenterology: 9 times
5. Nephrology: 9 times
6. Pulmonology: 9 times
7. Hematology: 8 times

**Hallucinated Specialists** (not in catalog):
- Anesthesiology (Q41)
- Genetics (Q80, Q84)
- Epidemiology (Q99)

## Critical Finding: The Parsing Failure Paradox

### Discovery
**Questions with parsing failures (defaulting to generic cardiology/pulmonology) achieved 75% accuracy, while questions with successful specialist selection achieved only 50% accuracy.**

This is a 25 percentage point difference in favor of the "failure" mode.

### Parsing Failure Examples (75% accuracy)

**Successful Cases** (12/16):
- Q10: [OK] Chlorine dioxide disinfection → A (correct)
- Q13: [OK] Antigenic variation infection → B (correct)
- Q31: [OK] Drug side effects → A (correct)
- Q47: [OK] Drug interaction contraception → A (correct)
- Q50: [OK] Cardiac physiology → B (correct)
- Q52: [OK] Disinfection method → C (correct)
- Q65: [OK] Medical ethics DNR → B (correct)
- Q68: [OK] Surgical anatomy → D (correct)
- Q83: [OK] Reproductive counseling → A (correct)
- Q90: [OK] IBD histology → C (correct)
- Q92: [OK] Stress fracture diagnosis → A (correct)
- Q100: [OK] Pediatric diagnosis → D (correct)

**Failed Cases** (4/16):
- Q26: [X] Acetaminophen overdose → B (wrong, correct: A)
- Q58: [X] Bleeding disorder workup → A (wrong, correct: D)
- Q79: [X] Diabetes management → A (wrong, correct: C)
- Q91: [X] Bladder cancer risk factors → A (wrong, correct: B)

### Parsing Success Examples (50% accuracy)

Many questions with perfectly parsed, contextually appropriate specialists still failed:
- Q2: Pediatrics selected → D (wrong, correct: A)
- Q3: Pulmonology, Emergency Medicine, Cardiology → A (wrong, correct: B)
- Q4: Dermatology → A (wrong, correct: C)
- Q8: Gastroenterology → A (wrong, correct: C)
- Q9: Pulmonology, Rheumatology, Nephrology → B (wrong, correct: D)

## Analysis: Why Did This Fail?

### 1. Answer Space Analysis Is Actively Harmful

The fundamental hypothesis - that analyzing answer choices helps select better specialists - appears to be **contradicted by the data**.

**Evidence**:
- Default specialists (cardiology/pulmonology): 75% accuracy
- LLM-selected specialists: 50% accuracy
- Difference: -25 percentage points

**Possible Mechanisms**:
1. **Anchoring Bias**: Seeing answer choices may anchor the specialist toward certain diagnoses
2. **Premature Commitment**: Generalist forms opinion during answer space analysis, biasing specialist selection
3. **Over-Specialization**: Highly specialized consultants may miss broader context
4. **Information Leakage**: Answer space analysis reveals too much, reducing independent reasoning

### 2. Generic Specialists Provide Better General Reasoning

Cardiology and pulmonology represent broad internal medicine domains with overlap in:
- Cardiovascular physiology
- Respiratory physiology
- Systemic disease manifestations
- Pharmacology
- Critical care

These generalist-specialist hybrids may provide better balanced reasoning than narrow specialists.

### 3. The Challenge-Response Pattern May Be Insufficient

While the generalist challenges specialists with counterpoints, this may not overcome the damage from the initial answer space analysis. The specialist has already been primed with:
- Which answers the generalist thinks map to which specialties
- The generalist's interpretation of each answer's implications
- Expectations about what the "correct" answer space should look like

### 4. Increased Cognitive Load

The answer space consultation process involves:
- 1 answer space analysis step
- 2-3 specialist consultations (each with 2 LLM calls)
- 1 aggregation step
- 1 review step

Total: **7-10 LLM calls per question**

Compare to:
- Single-LLM: 1 call (66% accuracy)
- Debate: 3-4 calls (76% accuracy)

More complexity ≠ better performance. Each step may introduce noise and drift.

### 5. Multi-Agent Coordination Failure

The system suffers from classic multi-agent problems:
- **Information Fragmentation**: Each specialist sees a slice, aggregator tries to reconstruct whole
- **Byzantine Disagreement**: Specialists may contradict each other without clear resolution
- **Responsibility Diffusion**: No single agent "owns" the decision
- **Compound Errors**: Errors propagate and amplify through the pipeline

## Comparison to Successful Approaches

### Why Debate (76%) Works Better

**Debate Architecture**:
1. Two adversarial agents each pick an answer
2. They argue directly with each other
3. Judge synthesizes the debate

**Key Differences**:
- **Adversarial**: Agents have opposing positions from the start
- **Direct Engagement**: Agents address each other's arguments directly
- **Simple**: Only 3-4 agents total
- **No Answer Space Analysis**: Agents see question naturally, not through "answer space" lens

### Why Single-LLM (66%) Works Better

Even a single LLM with no specialization outperforms Answer Space Consultation by 12 percentage points.

**Possible Reasons**:
- No coordination overhead
- No information fragmentation
- Direct question-to-answer reasoning
- No anchoring from answer space analysis

## Lessons Learned

### What We Learned

1. **Answer space analysis is not a useful signal for specialist selection** - It may actively harm performance by introducing bias

2. **Generic specialists > Narrow specialists** (in this task) - Broad medical knowledge domains (cardiology, pulmonology) provide better balanced reasoning than highly specialized consultants

3. **Parsing "failures" can reveal ground truth** - When your bug fixes make things worse, the bug was actually a feature

4. **Simpler architectures often win** - Debate's simple adversarial structure beats complex multi-agent coordination

5. **Increased agent count ≠ better performance** - Answer Space Consultation uses 7-10 LLM calls per question vs Debate's 3-4, yet performs 22 points worse

### What Failed

1. **Core Hypothesis**: Answer space analysis guiding specialist selection
2. **Architectural Complexity**: 6-phase pipeline with 7-10 LLM calls
3. **Specialist Selection Strategy**: LLM-driven selection performed worse than random fallback
4. **Information Flow**: Answer space analysis may leak too much information too early

### What Worked (Technically)

1. Duplicate prevention system
2. Scoped parsing to specific sections
3. Hallucinated specialist handling
4. Specialist rationale extraction and communication
5. Challenge-response dialogue pattern

These technical implementations worked correctly, but they were solving the wrong problem.

## Implications for Future Work

### Do NOT Pursue

1. **Answer space analysis for specialist selection** - Data shows it's harmful
2. **Complex multi-agent pipelines** - Coordination overhead outweighs benefits
3. **Over-specialization** - Narrow specialists may lack necessary context

### Worth Exploring

1. **Generic specialist consultation** - Test cardiology/pulmonology (or other broad specialties) on all questions
2. **Simplified consultation** - Single specialist consultation without answer space analysis
3. **Hybrid approaches** - Combine Debate's adversarial structure with specialist consultation
4. **Pre-question specialist selection** - Choose specialists based on question domain, NOT answer choices

### Open Questions

1. **Why does Debate work so well (76%)?** - Need deeper analysis of what makes adversarial structure effective
2. **Can we beat Debate?** - Or is 76% close to the ceiling for this model on MedQA?
3. **Does answer space analysis help in other domains?** - Or is it specifically harmful for medical diagnosis?
4. **What's the optimal number of agents?** - Is there a sweet spot between 1 (Single-LLM) and 7-10 (Answer Space)?

## Conclusion

Answer Space Consultation represents a failed but informative experiment. The core innovation - using answer choices to guide specialist selection - proved to be actively harmful, achieving 54% accuracy vs. 75% when the system "accidentally" used generic specialists.

The paradox of parsing failures outperforming successful parsing reveals a fundamental flaw in the architectural hypothesis. This experiment demonstrates that:

1. **Increased complexity ≠ increased accuracy**
2. **More agents ≠ better decisions**
3. **Domain-specific selection can backfire**
4. **Sometimes bugs hide the truth**

The Debate method remains the strongest performer at 76% accuracy, likely due to its simplicity, adversarial structure, and lack of premature commitment to specific medical specialties.

## Files and Data

**Implementation**: `src/baselines/answer_space_consultation.py`
**Test Script**: `scripts/test_answer_space_consultation.py`
**Results**: `runs/answer_space_consultation_test/20251112_140301/`
  - `results.json`: Full per-question results
  - `summary.json`: Aggregate statistics

**Related Documentation**:
- `docs/answer_focused_consultation_architecture.md`: Original architecture proposal
- `docs/debate_architecture_weaknesses.md`: Analysis of debate method weaknesses
- `docs/debate_refinement_proposal.md`: Forced challenge debate proposal