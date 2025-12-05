# Forced Challenge Debate: Architectural Proposal

## Problem
Sequential Specialist Debate achieved only 64% accuracy because 100% of debates ended in 2 rounds with immediate agreement. No iterative refinement occurred.

## Root Cause
**Agreement-seeking behavior**: Generalist deferred to specialist authority and said "I AGREE" without challenge.

## Proposed Solution: Forced Challenge Mechanism

### Architecture: Generalist as Devil's Advocate

Instead of waiting for natural disagreement, **require** the generalist to challenge the specialist with counterpoints.

**Flow**:
1. **Specialist Initial Opinion** (Round 1)
   - Provides differential diagnosis
   - Recommends answer with confidence

2. **Generalist Challenges** (Round 2)
   - MUST generate 2-3 counterpoints/alternative considerations
   - Prompt: "I see your reasoning, but consider these alternatives..."
   - Forces critical evaluation even when initially agreeing

3. **Specialist Defends** (Round 3)
   - Must address each counterpoint
   - Can maintain position or revise

4. **Generalist Re-evaluates** (Round 4)
   - After hearing defense, decides if convinced or still has concerns
   - Can raise new counterpoints or accept specialist reasoning

5. **Continue** for 3 full cycles (minimum 6 exchanges)

### Key Design Changes

#### Change 1: Mandatory Challenge Prompts

**Current (Failed) Prompt**:
```
Review the specialist's opinion and respond:
1. Do you agree with their assessment?
...
If you agree, state: "I AGREE with the specialist's assessment."
```
→ Result: Immediate agreement

**New Prompt**:
```
You must critically evaluate the specialist's opinion by:
1. Identifying at least 2 alternative diagnoses not fully addressed
2. Raising concerns about their reasoning (e.g., "But what about...")
3. Challenging their confidence level
4. Proposing edge cases or contradictory findings

Do NOT immediately agree. Your role is to be skeptical and ensure
the specialist has considered all angles.

Format:
COUNTERPOINTS:
1. [Alternative diagnosis and why it fits]
2. [Contradictory finding or edge case]
3. [Question about their reasoning]

Based on these concerns, what is your current assessment?
```

#### Change 2: Fixed Round Count (No Early Termination)

- **Minimum 3 cycles** (6-8 exchanges) regardless of agreement
- Remove agreement detection entirely
- Force full debate even if agents seem to converge

#### Change 3: Prompt Engineering for Sustained Disagreement

**Specialist Prompt**:
```
The generalist has raised the following challenges to your assessment:
[counterpoints]

As a specialist, you must:
1. Directly address EACH counterpoint raised
2. Defend your original position OR revise it based on valid concerns
3. Provide additional evidence for your reasoning
4. Identify any weaknesses the generalist correctly identified

Do NOT simply agree with the generalist to end the debate quickly.
Your expertise is needed to evaluate these challenges thoroughly.
```

## Comparison: Three Debate Architectures

### Original Debate (76% accuracy) ✓
- 2 independent agents with opposing starting positions
- Fixed 3 rounds, 6 exchanges
- Adversarial by design (agents start with different answers)
- Moderator synthesizes at end

**Success factor**: Forced disagreement through opposing positions

### Sequential Specialist Debate (64% accuracy) ✗
- Generalist + Specialist (collaborative)
- Terminates on agreement (2 rounds average)
- Authority bias (generalist defers to specialist)
- No adversarial mechanism

**Failure factor**: Agreement-seeking eliminated refinement

### **Forced Challenge Debate (Proposed)**
- Generalist + Specialist (collaborative BUT skeptical)
- Fixed 3 rounds minimum
- Generalist **must** challenge specialist (devil's advocate)
- Specialist **must** defend against challenges

**Design goal**: Combine specialist expertise with forced iterative refinement

## Implementation Details

### Prompt Structure

#### Round 1: Specialist Initial Assessment
```python
specialist_prompt = f"""You are a {specialist_name} specialist consulting on this case.

**Question:** {question}
**Options:** {options_str}

Provide your expert assessment:
1. Differential diagnosis (top 3 most likely)
2. Your recommended answer from the options
3. Key evidence supporting your answer
4. Confidence level (high/medium/low)

Be thorough but also consider what a generalist might challenge.
"""
```

#### Round 2: Generalist Forced Challenge
```python
challenge_prompt = f"""You are a {generalist_type} physician reviewing the specialist's opinion.

**Specialist's Assessment:**
{specialist_response}

YOUR TASK: You MUST challenge this assessment by raising counterpoints.
Do NOT immediately agree. Generate 2-3 specific challenges:

1. Alternative diagnosis: What other condition could explain these findings?
2. Contradictory evidence: What findings argue AGAINST their diagnosis?
3. Edge cases: What scenarios would change their recommendation?

Format your response as:
CHALLENGE 1: [specific alternative or concern]
CHALLENGE 2: [specific concern about their reasoning]
CHALLENGE 3: [edge case or contradictory finding]

QUESTION: Based on these concerns, do you still think the specialist's
answer is correct, or should they reconsider?
"""
```

#### Round 3: Specialist Defense
```python
defense_prompt = f"""The generalist has raised these challenges to your assessment:

{generalist_challenges}

As the specialist, you must:
1. Address EACH challenge point-by-point
2. Provide additional evidence if your position is correct
3. Acknowledge if any challenge reveals a weakness
4. Revise your recommendation if the challenges are valid

Do not dismiss concerns casually. Engage with the substance of each challenge.

RESPONSE:
[Point-by-point defense or revision]

UPDATED RECOMMENDATION: [A/B/C/D] with reasoning
"""
```

#### Rounds 4-6: Continue Pattern
- Generalist raises NEW challenges or acknowledges satisfaction
- Specialist continues to defend/refine
- Minimum 3 full cycles

### Final Synthesis: Generalist Review

After 3 cycles:
```python
final_prompt = f"""You have completed 3 rounds of consultation with the {specialist_name}.

**Consultation Summary:**
{all_debate_rounds}

Now make your final decision:
1. Review all arguments and counterarguments
2. Assess which reasoning was most convincing
3. Make your final answer selection

FINAL ANSWER: [A/B/C/D]
JUSTIFICATION: [Why this answer after considering all debate points]
"""
```

## Expected Outcomes

### Hypothesis
Forced Challenge Debate will:
- Achieve 70-75% accuracy (between current 64% and original Debate 76%)
- Generate 6-8 exchanges per question (vs 2 in failed version)
- Maintain specialist expertise while forcing refinement
- Cost similar to original Sequential Debate (~110s, ~9000 tokens)

### Success Metrics
- **Debate rounds**: Average 6+ exchanges (vs 2 in failed version)
- **Accuracy**: >70% (beat Single-LLM 66% baseline)
- **Challenge rate**: 100% of rounds include generalist counterpoints
- **Revision rate**: Specialists revise initial position in >30% of cases

### Risk Factors
1. **Forced challenges may be superficial**: Generalist generates weak counterpoints just to satisfy prompt
2. **Specialist may dismiss challenges**: Authority bias still present
3. **Longer debates may not improve accuracy**: Noise accumulation
4. **Cost**: Still 7× Single-LLM with uncertain benefit

## Alternative: Two-Specialist Adversarial Debate

Instead of Generalist vs Specialist, pit **two specialists against each other**:

### Architecture
1. Select 2 relevant specialists (e.g., Cardiology vs Pulmonology)
2. Each proposes initial diagnosis independently
3. Specialists debate each other for 3 rounds
4. Generalist moderator synthesizes at end

### Advantages
- Both agents have authority (no deference)
- Natural adversarial stance (different specialties emphasize different findings)
- Maintains specialist expertise
- Similar to original Debate but with domain knowledge

### Prompt Example
```
[Cardiologist]: "This is acute coronary syndrome (B). The chest pain
radiating to the jaw and elevated troponin are classic..."

[Pulmonologist]: "I disagree. The bilateral rales and oxygen
desaturation suggest pulmonary edema (C). The troponin could be
secondary to strain..."

[Continue for 3 rounds]

[Generalist Moderator]: "Both specialists raise valid points.
Considering the debate, the most likely answer is..."
```

## Recommendation

**Test both approaches**:

1. **Forced Challenge Debate**:
   - Generalist as devil's advocate
   - Fixed 3 rounds minimum
   - Tests if we can force iterative refinement in collaborative setting

2. **Two-Specialist Adversarial Debate**:
   - Two specialists with different perspectives
   - Natural disagreement from different specialty lenses
   - Tests if specialist expertise + adversarial stance beats original Debate

**Expected Results**:
- Forced Challenge: 68-72% (better than 64%, but forced challenges may feel artificial)
- Two-Specialist Adversarial: 73-77% (likely best - combines expertise with natural adversarial dynamic)

## Next Steps

1. Implement Forced Challenge Debate architecture
2. Test on same 100-question set
3. Analyze:
   - Did challenges force more debate rounds?
   - Were challenges substantive or superficial?
   - Did specialist revise positions?
4. If successful, implement Two-Specialist Adversarial variant
5. Compare all architectures head-to-head
