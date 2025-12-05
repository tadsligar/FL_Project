# Prompt Analysis: Single-Shot CoT vs Debate

## Executive Summary

The **single-shot CoT prompt is significantly more thorough** than the debate prompts. The single-shot prompt explicitly requests step-by-step reasoning with detailed instructions, while the debate prompts are more minimal and don't explicitly invoke CoT reasoning.

**Potential Hypothesis**: Making debate prompts more thorough (adding explicit CoT instructions) could improve debate performance.

---

## Comparison

### Single-Shot CoT Prompt

**File**: `src/baselines/single_llm_cot.py:42-65`

```python
prompt = f"""You are a clinical reasoning expert. Analyze this medical case using step-by-step reasoning.

**Question:**
{question}

**Options:**
{options_str}

**Instructions:**
Think through this systematically:
1. Identify key clinical features (symptoms, signs, demographics)
2. Generate a differential diagnosis (list possible conditions)
3. Evaluate each diagnosis against the evidence (what supports it? what argues against it?)
4. Select the most likely answer based on your reasoning

Provide your reasoning step-by-step, then give your final answer.

**Format your response as:**

REASONING:
[Your detailed step-by-step clinical analysis]

ANSWER: [A, B, C, D, or the diagnosis name]
"""
```

**Characteristics:**
- ✓ Explicit CoT instruction: "using step-by-step reasoning"
- ✓ Meta-instruction: "Think through this systematically"
- ✓ Structured 4-step process with detailed sub-prompts
- ✓ Specific output format with labeled sections
- ✓ Asks for reasoning before answer

---

### Debate Agent A Prompt (Initial)

**File**: `src/baselines/debate.py:42-55`

```python
agent_a_prompt = f"""You are Clinical Reasoning Agent A. Analyze this case and propose your diagnosis.

**Question:** {question}

**Options:** {options_str}

**Your Task:**
1. Analyze the clinical presentation
2. Generate a differential diagnosis
3. Select your answer and explain your reasoning
4. Be prepared to defend your position

Provide your diagnostic reasoning and select an answer.
"""
```

**Characteristics:**
- ✗ No explicit CoT instruction
- ✗ No "step-by-step" or "systematic" guidance
- ✗ Less detailed task breakdown (no sub-questions)
- ✗ No structured output format
- ✗ Generic "explain your reasoning" without process guidance

---

### Debate Agent B Prompt (Initial)

**File**: `src/baselines/debate.py:69-85`

```python
agent_b_prompt = f"""You are Clinical Reasoning Agent B. Review Agent A's analysis and provide your perspective.

**Question:** {question}

**Options:** {options_str}

**Agent A's Position:**
{agent_a_position}

**Your Task:**
1. Critically evaluate Agent A's reasoning
2. Provide your own diagnostic analysis
3. Agree or disagree with Agent A
4. Explain your reasoning

If you disagree, explain why and provide your alternative answer.
"""
```

**Characteristics:**
- ✗ No explicit CoT instruction
- ✗ Focus on evaluation rather than reasoning process
- ✗ No guidance on systematic analysis
- ✗ No structured output format

---

## Key Differences

### 1. CoT Invocation

| Prompt | Explicit CoT? | Instruction |
|--------|---------------|-------------|
| Single-Shot | ✓ Yes | "using step-by-step reasoning" + "Think through this systematically" |
| Debate A | ✗ No | Generic "provide your diagnostic reasoning" |
| Debate B | ✗ No | Generic "explain your reasoning" |

### 2. Process Guidance

| Prompt | Process Detail | Sub-instructions |
|--------|----------------|------------------|
| Single-Shot | Very detailed | "what supports it? what argues against it?" |
| Debate A | Minimal | Just task names, no process detail |
| Debate B | Minimal | Evaluation-focused, not process-focused |

### 3. Output Structure

| Prompt | Structured Format? | Sections |
|--------|-------------------|----------|
| Single-Shot | ✓ Yes | REASONING: / ANSWER: |
| Debate A | ✗ No | Freeform |
| Debate B | ✗ No | Freeform |

### 4. Reasoning Emphasis

**Single-Shot**:
- "Think through this systematically"
- "Evaluate each diagnosis against the evidence"
- "Provide your reasoning step-by-step"

**Debate A/B**:
- "Provide your diagnostic reasoning" (generic)
- "Explain your reasoning" (generic)
- No emphasis on systematic thinking

---

## Potential Impact

### Why This Might Matter

Research on CoT prompting shows that:
1. **Explicit instruction to think step-by-step improves performance**
2. **Structured prompts reduce reasoning errors**
3. **Process guidance helps models explore the problem space more thoroughly**

### Current Results

- Single-Shot CoT: 66% accuracy
- Debate (3 rounds): 70-76% accuracy

The debate wins, but it's using **7 API calls** vs **1 API call** for single-shot.

### Question

**What if we made debate prompts as thorough as single-shot CoT?**

Hypothesis:
- Each agent in debate would produce better reasoning
- The ensemble effect would compound with better individual performance
- Could potentially increase accuracy to 75-80%+

---

## Proposed Improvement: CoT-Enhanced Debate

### Enhanced Agent A Prompt

```python
agent_a_prompt = f"""You are Clinical Reasoning Agent A. Analyze this case using step-by-step reasoning.

**Question:** {question}

**Options:** {options_str}

**Your Task - Think Through This Systematically:**

1. **Identify Key Clinical Features**
   - What are the critical symptoms and signs?
   - What demographic factors are relevant?
   - What is the clinical context?

2. **Generate Differential Diagnosis**
   - List 3-4 possible conditions that could explain this presentation
   - For each, note what supports it

3. **Evaluate Each Diagnosis**
   - Which option best matches the clinical evidence?
   - What argues FOR each option?
   - What argues AGAINST each option?

4. **Select Your Answer**
   - Based on your systematic analysis, which is most likely?
   - Be prepared to defend this position with specific evidence

**Format:**
DIFFERENTIAL: [List possible diagnoses]
ANALYSIS: [Evaluate each option systematically]
ANSWER: [A, B, C, or D]
REASONING: [Why this answer is best]
"""
```

### Enhanced Agent B Prompt

```python
agent_b_prompt = f"""You are Clinical Reasoning Agent B. Critically evaluate Agent A's analysis using step-by-step reasoning.

**Question:** {question}

**Options:** {options_str}

**Agent A's Position:**
{agent_a_position}

**Your Task - Systematic Critical Evaluation:**

1. **Assess Agent A's Clinical Feature Identification**
   - Did they identify the key features correctly?
   - Did they miss anything important?

2. **Review Their Differential Diagnosis**
   - Is their differential complete?
   - Are there other conditions to consider?

3. **Evaluate Their Analysis**
   - Are their arguments for/against each option sound?
   - What evidence did they overlook?
   - Where is their reasoning strongest/weakest?

4. **Provide Your Independent Analysis**
   - Think through the evidence systematically
   - Generate your own diagnosis
   - Agree OR disagree with Agent A based on the evidence

**Format:**
CRITIQUE: [Evaluate Agent A's reasoning]
MY_DIFFERENTIAL: [Your diagnostic considerations]
MY_ANALYSIS: [Your systematic evaluation]
ANSWER: [A, B, C, or D]
POSITION: [Agree/Disagree with Agent A and why]
"""
```

---

## Testing Recommendations

### Experiment: CoT-Enhanced Debate

**Hypothesis**: Adding explicit CoT instructions to debate prompts will improve performance by >5%

**Method**:
1. Create `debate_cot_enhanced.py` with the enhanced prompts above
2. Run on same 100 questions as baseline debate
3. Compare:
   - Accuracy (expect 75-80% vs 70-76% baseline)
   - Reasoning quality (manual review of 10 questions)
   - Convergence rate (do agents agree more/less?)

**Expected Results**:
- Better individual agent reasoning
- Potentially better ensemble effect
- More structured debate history for analysis

**Cost/Benefit**:
- Cost: Same 7 API calls, slightly longer prompts
- Benefit: If +5-10% accuracy, significant improvement with no architectural change

---

## Conclusion

The single-shot CoT prompt is significantly more thorough than the debate prompts. The debate prompts lack:

1. Explicit CoT invocation ("step-by-step reasoning")
2. Detailed process guidance (sub-questions for each step)
3. Structured output format
4. Emphasis on systematic thinking

This represents a potential **low-hanging fruit optimization**: Keep the debate architecture, but improve individual agent reasoning quality through better prompting.

**Recommendation**: Test CoT-enhanced debate prompts as the next experiment. This could bridge the gap between the simplicity of single-shot CoT and the complexity of multi-agent systems, potentially achieving better results with the same architectural pattern.
