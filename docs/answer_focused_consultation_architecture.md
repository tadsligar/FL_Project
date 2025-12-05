# Answer-Focused Specialist Consultation Architecture

## Overview
Instead of selecting specialists based on question content alone, analyze what each ANSWER CHOICE implies, then assign specialists to evaluate specific answers. The generalist challenges each specialist with counterpoints from alternative answers.

## Core Innovation
**Traditional**: "This question is about cardiology" → consult cardiologist
**New**: "Answer A suggests MI, Answer B suggests PE, Answer C suggests HF" → consult cardiology for A, pulmonology for B, cardiology for C

**Key Insight**: The answer choices contain information about which specialties are relevant.

---

## Architecture Flow

### Phase 1: Answer Analysis & Specialist Mapping

**Generalist analyzes answer choices**:
```
Question: 65yo with chest pain, elevated troponin, bilateral rales, O2 sat 89%

Answer A: Start aspirin and heparin
Answer B: Intubate immediately
Answer C: Start furosemide
Answer D: Perform pericardiocentesis

Analysis:
- Answer A (aspirin + heparin) → Suggests ACS/MI → Cardiology
- Answer B (intubate) → Suggests respiratory failure → Pulmonology or Critical Care
- Answer C (furosemide) → Suggests fluid overload/HF → Cardiology
- Answer D (pericardiocentesis) → Suggests tamponade → Cardiology

Specialists to consult:
1. Cardiology (covers A, C, D)
2. Pulmonology (covers B)
```

### Phase 2: Focused Consultation (Parallel)

For each specialist, run independent consultation:

#### Step 2.1: Specialist Briefing + Initial Assessment
```
Consultation with Cardiology:

"I'm consulting you because:
- Answer A (aspirin + heparin) suggests acute coronary syndrome
- Answer C (furosemide) suggests heart failure with fluid overload
- Answer D (pericardiocentesis) suggests cardiac tamponade

As a cardiologist, please evaluate these cardiac diagnoses:

Question: {question}
Options: {all_options}

Your assessment:
1. Which cardiac diagnosis best fits? (ACS, HF, tamponade, or none)
2. Which answer (A, C, or D) is most appropriate?
3. What key findings support your assessment?
4. Confidence level: HIGH / MEDIUM / LOW
"
```

**Cardiology Response Example**:
```
ASSESSMENT: This is acute MI with cardiogenic pulmonary edema

BEST ANSWER: A (aspirin + heparin)

KEY FINDINGS:
- Elevated troponin → confirms MI
- Bilateral rales → pulmonary edema (cardiogenic)
- Chest pain → ischemia

CONFIDENCE: HIGH

REASONING: The troponin elevation is diagnostic for MI. The rales are
likely secondary to left ventricular dysfunction causing pulmonary
congestion. Answer A (aspirin + heparin) is the correct immediate
treatment for acute MI.
```

#### Step 2.2: Generalist Challenges with Alternative Answers
```
GENERALIST CHALLENGES:

Thank you for your assessment. However, I need you to address these
counterpoints from the OTHER answer choices:

CHALLENGE 1 - Answer B (intubate immediately):
The patient has O2 sat 89% and bilateral rales. Could this be
primary respiratory failure requiring immediate intubation rather
than a cardiac issue? How do you rule out:
- Pulmonary embolism with respiratory failure
- ARDS
- Severe pneumonia

CHALLENGE 2 - Answer C (furosemide instead of aspirin):
If this is pulmonary edema as you suggest, why is Answer A (aspirin)
better than Answer C (furosemide)? Shouldn't we treat the fluid
overload first?

CHALLENGE 3 - Answer D (pericardiocentesis):
Could the elevated troponin be due to pericarditis/myocarditis with
tamponade? The bilateral findings could be from pericardial effusion
compressing the lungs.

YOUR TASK:
Address EACH challenge. For each, either:
1. DEFEND your original answer with specific evidence, OR
2. REVISE your assessment if the challenge is valid, OR
3. DEFER to another specialty if you realize this is outside cardiology

Format:
RESPONSE TO CHALLENGE 1: [defense/revision/defer]
RESPONSE TO CHALLENGE 2: [defense/revision/defer]
RESPONSE TO CHALLENGE 3: [defense/revision/defer]

FINAL STANCE:
Do you STAND FIRM on Answer A, or have these challenges changed your mind?
ANSWER: [A/B/C/D]
CONFIDENCE: [HIGH/MEDIUM/LOW]
```

**Cardiology Response Example**:
```
RESPONSE TO CHALLENGE 1 (Intubation for respiratory failure):
DEFEND - While the O2 sat is low, this is likely cardiogenic pulmonary
edema, not primary respiratory failure. Key differences:
- Troponin elevation: Points to cardiac etiology, not pneumonia/ARDS
- Chest pain: Suggests ischemia, not isolated respiratory disease
- Treatment: MI requires aspirin/heparin FIRST. We can support O2 while
  treating the underlying cardiac issue. Intubation without treating MI
  would be dangerous.

RESPONSE TO CHALLENGE 2 (Furosemide vs Aspirin):
DEFEND - Both are needed, but sequence matters:
- In acute MI with pulmonary edema, the PRIMARY problem is myocardial
  ischemia causing pump failure
- Aspirin + heparin address the root cause (thrombosis)
- Furosemide treats the symptom (fluid) but doesn't stop ongoing infarction
- Standard STEMI protocol: antiplatelet/anticoagulation FIRST, then
  diuretics as adjunct

RESPONSE TO CHALLENGE 3 (Tamponade):
DEFEND - Tamponade is less likely:
- Tamponade causes HYPOTENSION and muffled heart sounds (not described)
- Tamponade causes elevated JVP and pulsus paradoxus (not mentioned)
- Troponin in tamponade is usually normal or mildly elevated, not high
- This patient's troponin + chest pain pattern is classic for MI, not
  pericardial disease

FINAL STANCE: STAND FIRM
ANSWER: A (aspirin + heparin)
CONFIDENCE: HIGH

These challenges have reinforced my assessment. The clinical picture is
most consistent with acute MI with secondary pulmonary edema. Answer A
addresses the root cause.
```

#### Step 2.3: Specialist Reconsideration (Optional)
If specialist revised or showed uncertainty:
```
You indicated [REVISION/UNCERTAINTY].

Would you like to DEFER this case to another specialist?
If so, which specialty would be more appropriate?

Options:
- STAND FIRM on your answer
- DEFER to [specify specialty]
```

**Example of Deferral**:
```
Cardiologist encounters a case:
"Actually, on reflection, the diffuse ST changes and lack of
reciprocal changes suggest this is more likely pericarditis
than MI. I would DEFER to Rheumatology or Infectious Disease
to evaluate for inflammatory causes of pericarditis."

→ System then consults Rheumatology with the same challenge framework
```

---

### Phase 3: Parallel Consultation with Other Specialists

**Simultaneously, consult Pulmonology**:

#### Step 3.1: Pulmonology Briefing
```
Consultation with Pulmonology:

"I'm consulting you because Answer B (intubate immediately) suggests
severe respiratory failure or compromise requiring airway management.

Question: {question}
Options: {all_options}

Your assessment:
1. Does this patient need immediate intubation?
2. Is Answer B the most appropriate?
3. What pulmonary diagnoses could explain these findings?
4. Confidence level
"
```

**Pulmonology Response Example**:
```
ASSESSMENT: Respiratory distress with hypoxemia

INITIAL ANSWER: B (intubate)

KEY FINDINGS:
- O2 sat 89% → significant hypoxemia
- Bilateral rales → likely pulmonary edema or ARDS
- Respiratory distress

REASONING: The low O2 saturation and bilateral lung findings suggest
respiratory failure. However, I'm uncertain whether intubation should
be FIRST intervention or if we should try CPAP/BiPAP first.

CONFIDENCE: MEDIUM
```

#### Step 3.2: Challenge Pulmonology
```
CHALLENGES:

CHALLENGE 1 - Answer A (aspirin + heparin):
Cardiology argues this is acute MI with CARDIOGENIC pulmonary edema.
If true, treating the MI first (Answer A) would improve oxygenation
without intubation. How do you respond?

CHALLENGE 2 - Could non-invasive ventilation work?
Intubation is invasive and has risks. Could CPAP or high-flow O2
stabilize this patient while treating the underlying cause?

CHALLENGE 3 - What if intubation delays definitive treatment?
If this IS a cardiac etiology, spending time on intubation could
delay urgent cardiac catheterization or thrombolytics.

Address each challenge.
```

**Pulmonology Response Example**:
```
RESPONSE TO CHALLENGE 1 (Cardiogenic pulmonary edema):
CONCEDE - Cardiology makes a strong point. The elevated troponin
strongly suggests MI as the primary issue. If this is cardiogenic
pulmonary edema:
- Treating the MI (Answer A) will reduce pulmonary congestion
- Intubation would be supportive, not curative
- Could try non-invasive ventilation first

RESPONSE TO CHALLENGE 2 (Non-invasive ventilation):
REVISE - Yes, CPAP or BiPAP would be appropriate before intubation:
- Less invasive
- Can be started immediately while treating MI
- O2 sat 89% is low but not critical (>85%)

RESPONSE TO CHALLENGE 3 (Delaying definitive treatment):
CONCEDE - Valid concern. If we intubate first:
- Sedation for intubation delays cath lab
- Mechanical ventilation may complicate coronary intervention
- Better to support oxygenation while treating MI

FINAL STANCE: REVISE
ANSWER: A (aspirin + heparin) - NOT B
CONFIDENCE: MEDIUM

After considering these challenges, I agree with Cardiology that the
primary issue is MI with cardiogenic pulmonary edema. Support oxygenation
non-invasively while treating the MI. Intubation is not the first-line
answer.
```

---

### Phase 4: Aggregation

**Aggregator receives all specialist consultations**:

```
CONSULTATION SUMMARY:

[Cardiology - Answer A]
- Initial assessment: Acute MI, Answer A (aspirin + heparin)
- After challenges: STOOD FIRM on Answer A
- Confidence: HIGH
- Key reasoning: Troponin + chest pain = MI; aspirin/heparin treat root cause

[Pulmonology - Answer B]
- Initial assessment: Respiratory failure, Answer B (intubate)
- After challenges: REVISED to Answer A
- Confidence: MEDIUM
- Key reasoning: Agreed with cardiogenic edema; non-invasive support
  better than intubation

AGGREGATOR TASK:
1. Which specialist's reasoning is strongest?
2. Do they agree or disagree on final answer?
3. What is the weight of evidence?

FINAL ANSWER: A
REASONING: Both specialists converged on Answer A. Cardiology had
strong conviction throughout. Pulmonology initially favored Answer B
but revised after considering cardiac etiology. The troponin elevation
is the most discriminating finding, supporting MI (Answer A).
```

---

### Phase 5: Reviewer (Optional)

```
REVIEWER CHECKS:

Review the aggregator's decision:

Consultations: [Cardiology, Pulmonology]
Aggregator chose: Answer A

REVIEWER QUESTIONS:
1. Did the aggregator properly weight the evidence?
2. Were any critical findings overlooked?
3. Did specialists adequately address challenges?
4. Is there reason to doubt the consensus?

VERDICT: APPROVE / REVISE
```

---

## Key Advantages

### 1. Answer-Driven Specialist Selection
**Traditional**: "This is a cardiology question" → may miss multi-system issues
**New**: "Answer A is cardio, Answer B is pulm" → comprehensive coverage

### 2. Structured Challenges
**Traditional**: "Generate counterpoints" → vague, generic
**New**: "Answer B suggests X. How do you respond?" → specific, focused

### 3. Delegation Mechanism
Specialists can self-correct:
- "This is actually more rheumatology than cardiology"
- Prevents specialists from overreaching beyond their domain

### 4. Parallel Consultations
**Traditional Sequential**: Specialist 1 → Specialist 2 (sequential bias)
**New**: Independent assessments → avoid anchoring

### 5. Convergence Evidence
When multiple specialists independently converge on the same answer after
challenges, it's strong evidence:
- Cardiology: Answer A (stood firm)
- Pulmonology: Answer B → revised to Answer A
- Strong convergence signal

---

## Implementation Details

### Specialist Selection Algorithm

```python
def analyze_answers_and_select_specialists(question: str, options: list[str]) -> dict:
    """
    Analyze what each answer implies, then map to specialists.
    """

    prompt = f"""
    Question: {question}

    For each answer choice, identify:
    1. What diagnosis/condition it implies
    2. Which medical specialty is most relevant

    Answer A: {options[0]}
    → Implies: [diagnosis/treatment]
    → Specialty: [specialty_id]

    Answer B: {options[1]}
    → Implies: [diagnosis/treatment]
    → Specialty: [specialty_id]

    Answer C: {options[2]}
    → Implies: [diagnosis/treatment]
    → Specialty: [specialty_id]

    Answer D: {options[3]}
    → Implies: [diagnosis/treatment]
    → Specialty: [specialty_id]

    Based on this analysis:
    SELECT TOP 2-3 SPECIALTIES: [list specialties to consult]
    RATIONALE: [why these specialties cover the key answer options]
    """

    response = llm_client.complete(prompt)
    return parse_specialist_selection(response)
```

### Consultation Loop

```python
def run_answer_focused_consultation(
    question: str,
    options: list[str],
    specialist_id: str,
    specialist_name: str,
    relevant_answers: list[str],  # e.g., ["A", "C", "D"]
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Run focused consultation with one specialist about specific answers.
    """

    # Step 1: Brief specialist and get initial assessment
    briefing_prompt = f"""
    You are a {specialist_name} specialist. I'm consulting you because:

    {format_answer_rationale(relevant_answers, options)}

    Question: {question}
    Options:
    {format_options(options)}

    Your task:
    1. Which of the relevant answers ({', '.join(relevant_answers)}) is most appropriate?
    2. What diagnosis/treatment do you recommend?
    3. Key evidence supporting your assessment
    4. Confidence: HIGH / MEDIUM / LOW
    """

    initial_response = llm_client.complete(briefing_prompt)
    specialist_answer = extract_answer(initial_response)

    # Step 2: Generate challenges from OTHER answers
    other_answers = [ans for ans in ["A", "B", "C", "D"] if ans != specialist_answer]
    challenges = generate_challenges(other_answers, options, initial_response)

    challenge_prompt = f"""
    Your initial assessment: {initial_response}

    However, please address these counterpoints from OTHER answer choices:

    {format_challenges(challenges)}

    For each challenge, either:
    - DEFEND your original answer with specific evidence
    - REVISE your assessment if the challenge is valid
    - DEFER to another specialty if appropriate

    FINAL STANCE:
    ANSWER: [A/B/C/D]
    CONFIDENCE: [HIGH/MEDIUM/LOW]
    CHANGED MIND: [YES/NO]
    """

    final_response = llm_client.complete(challenge_prompt)

    # Step 3: Check for deferral
    if indicates_deferral(final_response):
        suggested_specialty = extract_suggested_specialty(final_response)
        return {
            "specialist": specialist_name,
            "status": "deferred",
            "deferred_to": suggested_specialty,
            "reasoning": final_response
        }

    return {
        "specialist": specialist_name,
        "initial_answer": specialist_answer,
        "final_answer": extract_answer(final_response),
        "changed_mind": extract_changed_mind(final_response),
        "confidence": extract_confidence(final_response),
        "reasoning": final_response,
        "status": "completed"
    }
```

### Aggregation

```python
def aggregate_consultations(
    question: str,
    options: list[str],
    consultations: list[dict],
    llm_client: LLMClient,
    config: Config
) -> dict:
    """
    Aggregate multiple specialist consultations.
    """

    # Format consultation summary
    summary = format_consultation_summary(consultations)

    # Check for consensus
    final_answers = [c["final_answer"] for c in consultations if c["status"] == "completed"]
    consensus = all(ans == final_answers[0] for ans in final_answers)

    aggregation_prompt = f"""
    You are aggregating specialist consultations for this case.

    Question: {question}
    Options: {format_options(options)}

    CONSULTATION SUMMARY:
    {summary}

    ANALYSIS:
    1. Consensus: {"YES - all agree on " + final_answers[0] if consensus else "NO - disagreement"}
    2. Confidence levels: {[c["confidence"] for c in consultations]}
    3. Mind changes: {[c["changed_mind"] for c in consultations]}

    YOUR TASK:
    - If consensus: Verify the reasoning is sound
    - If disagreement: Weigh the strength of evidence from each specialist
    - Consider: Which specialist is most relevant to this case?
    - Consider: Who provided the strongest evidence?

    FINAL ANSWER: [A/B/C/D]
    JUSTIFICATION: [2-3 sentences explaining your decision]
    """

    response = llm_client.complete(aggregation_prompt)

    return {
        "final_answer": extract_answer(response),
        "justification": response,
        "consensus": consensus,
        "consultations": consultations
    }
```

---

## Expected Performance

### Hypothesis
This architecture should achieve **72-75% accuracy** because:

1. **Better specialist selection**: Answer-driven selection is more precise
2. **Structured challenges**: Specific counterpoints from alternative answers
3. **Self-correction**: Specialists can defer when appropriate
4. **Convergence signal**: Multiple independent consultations → strong evidence
5. **No premature agreement**: Challenges force critical evaluation

### Comparison to Previous Methods

| Method | Accuracy | Key Feature | Weakness |
|--------|----------|-------------|----------|
| Sequential Specialist Debate | 64% | Specialist expertise | Premature agreement |
| Original Debate | 76% | Adversarial refinement | No specialist knowledge |
| **Answer-Focused (Proposed)** | **72-75%** | Specialist expertise + structured challenges | More complex |

### Cost Analysis

**Per question**:
- Answer analysis: 1 LLM call (~500 tokens)
- 2 specialists × 2 rounds each: 4 LLM calls (~7000 tokens)
- Aggregation: 1 LLM call (~1000 tokens)
- Review: 1 LLM call (~800 tokens)
- **Total: ~9300 tokens, ~100s latency**

Similar to Sequential Specialist Debate, but better performance expected.

---

## Advantages Over Alternatives

### vs Sequential Specialist Debate (64%)
- **Structured challenges**: Not generic, tied to specific alternative answers
- **Parallel consultations**: No sequential bias
- **Delegation**: Specialists can self-correct

### vs Original Debate (76%)
- **Specialist expertise**: Domain knowledge guides reasoning
- **Answer-focused**: More targeted than topic-focused selection

### vs Forced Challenge Debate
- **Natural challenges**: Counterpoints come from actual alternative answers, not forced
- **Clear specialist brief**: "Evaluate THIS answer because..." vs vague challenge

---

## Implementation Priority

**Phase 1**: Core architecture
1. Answer analysis → specialist selection
2. Specialist briefing with answer focus
3. Challenge generation from alternative answers
4. Specialist reconsideration

**Phase 2**: Enhancements
1. Delegation mechanism
2. Parallel consultation handling
3. Aggregation with consensus detection
4. Reviewer layer

**Phase 3**: Optimizations
1. Confidence-based routing (only use for uncertain questions)
2. Adaptive specialist count (2-3 based on answer diversity)
3. Early termination (if high-confidence consensus)

---

## Next Steps

1. **Implement** core architecture (Phase 1)
2. **Test** on same 100 questions
3. **Analyze**:
   - Did challenges improve over generic "forced challenge"?
   - How often did specialists defer?
   - Convergence rate across specialists?
4. **Compare** to Sequential Specialist Debate (64%) and Original Debate (76%)

Expected timeline: ~2-3 days implementation, 3-4 hours testing
Expected result: **72-75% accuracy**
