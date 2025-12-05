# Mixed Temperature Multi-Agent Experiment Results

**Date**: November 2024
**Model**: qwen2.5:32b (Ollama)
**Dataset**: MedQA US Test (1,071 questions, 4-option multiple choice)

## Experiment Configuration

### Mixed Temperature Approach
- **Selector Agent**: temperature = 0.0 (deterministic specialist selection)
- **Specialist Agents**: temperature = 0.3 (diverse reasoning from 3 specialists)
- **Reviewer Agent**: temperature = 0.0 (deterministic final synthesis)

### Architecture
1. Selector picks top 3 specialists for each question (1 LLM call, temp=0.0)
2. Each specialist independently analyzes the question (3 LLM calls, temp=0.3)
3. Reviewer synthesizes specialist responses and selects final answer (1 LLM call, temp=0.0)

**Total**: 5 LLM calls per question

## Results Summary

### Accuracy Across 3 Runs

| Run | Correct | Total | Accuracy |
|-----|---------|-------|----------|
| Run 1 | 682 | 1071 | **63.68%** |
| Run 2 | 677 | 1071 | **63.21%** |
| Run 3 | 677 | 1071 | **63.21%** |

### Statistical Summary
- **Mean Accuracy**: 63.37%
- **Median Accuracy**: 63.21%
- **Standard Deviation**: 0.27%
- **Range**: 0.47 percentage points

### Comparison to Baseline

| Configuration | Accuracy | Difference |
|---------------|----------|------------|
| All temp=0.3 (baseline) | 62.56% | - |
| Mixed temp (selector=0, specialist=0.3, reviewer=0) | 63.37% | **+0.81%** |

The mixed temperature approach shows a modest improvement of ~0.8 percentage points over the uniform temperature baseline.

## Cross-Run Stability Analysis

Despite similar total accuracy, individual question outcomes vary significantly between runs:

### Question Classification by Consistency

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| **Reliably Correct** | 468 | 43.7% | Correct in ALL 3 runs |
| **Somewhat Stable** | 235 | 21.9% | Correct in exactly 2 runs |
| **Unstable** | 162 | 15.1% | Correct in exactly 1 run |
| **Reliably Wrong** | 206 | 19.2% | Wrong in ALL 3 runs |

### Run-to-Run Agreement

Comparing Run 2 vs Run 3 (both achieved 677/1071 = 63.21%):

| Metric | Value |
|--------|-------|
| Questions both got correct | 549 |
| Questions only Run 2 got correct | 128 |
| Questions only Run 3 got correct | 128 |
| **Agreement rate** | **68.2%** |
| Questions with different outcomes | 256 (23.9%) |

### Theoretical Ceiling

- **Unique questions answered correctly** (across any run): 865/1071 = **80.8%**
- This represents the maximum achievable if we could perfectly aggregate across runs
- Gap between actual (~63%) and ceiling (~81%) suggests ensemble methods could help

## Key Findings

### 1. Accuracy is Remarkably Stable
Despite temperature-induced randomness in specialist reasoning, total accuracy varies by only 0.47 percentage points across runs. The system achieves consistent ~63% accuracy.

### 2. Individual Question Outcomes Vary Significantly
24% of questions (256/1071) show different outcomes between runs. The temperature=0.3 on specialists creates meaningful diversity in reasoning paths.

### 3. Three Question Categories Emerge
- **Easy questions** (44%): Consistently correct regardless of specialist reasoning variations
- **Hard questions** (19%): Consistently wrong - likely beyond the model's capability
- **Borderline questions** (37%): Outcome depends on specific reasoning paths

### 4. Modest Improvement Over Baseline
Mixed temperature (+0.8%) suggests that deterministic selection and synthesis with diverse specialist reasoning is slightly better than uniform temperature.

## Implications for Future Work

1. **Ensemble Potential**: The 81% ceiling suggests that aggregating multiple runs (e.g., majority vote across 3-5 runs) could significantly boost accuracy.

2. **Question Difficulty Stratification**: The 468 "reliably correct" questions could inform a confidence-based routing strategy.

3. **Temperature Tuning**: Further experiments with specialist temperatures (0.2, 0.4, 0.5) could optimize the diversity-accuracy tradeoff.

4. **Selective Re-evaluation**: Questions where specialists disagree (no 3/3 consensus) might benefit from additional reasoning attempts.

## Raw Data Locations

- Run 1: `runs/independent_multi_agent_mixed_temp_full/20251119_040603/`
- Run 2: `runs/independent_multi_agent_mixed_temp_full_run2/20251119_211604/`
- Run 3: `runs/independent_multi_agent_mixed_temp_full_run3/[timestamp]/`
- Baseline: `runs/independent_multi_agent_synthesis_temp03_full/`
