# Experimental Plan: Hyperparameter Optimization
## Multi-Agent System Performance Study

**Date**: November 4, 2024
**Goal**: Optimize Adaptive MAS performance through systematic hyperparameter tuning

---

## Motivation

Initial 100-question evaluation revealed:
1. **5% system failure rate** (JSON parsing + hallucination errors)
2. **44.2% accuracy** (lower than single-LLM baseline at 47%)
3. **16.5x token cost** vs single-LLM

**Research Questions**:
1. Do fixes eliminate all system failures?
2. Does temperature affect hallucination rate and accuracy?
3. Does reducing specialist count improve cost-efficiency without sacrificing accuracy?

---

## Experimental Design

### Independent Variables
1. **Temperature**: 0.1, 0.3, 0.5
2. **Number of Specialists (top_k)**: 2, 5

### Dependent Variables
1. **Accuracy** (primary metric)
2. **System Failure Rate** (reliability)
3. **Token Usage** (cost efficiency)
4. **Latency** (speed)
5. **Hallucination Rate** (instruction following)

### Controls
- **Model**: Llama 3 8B (constant)
- **Dataset**: Same 100 MedQA questions
- **Hardware**: RTX 4090 (constant)
- **Fixes**: All error handling fixes applied

---

## Experiments

### Phase 1: Baseline with Fixes ✓ (Running)
**Config**: `configs/llama3_8b.yaml`
- Temperature: **0.3**
- Specialists: **5**
- Purpose: Establish baseline with all fixes applied

**Expected Results**:
- 0% system failures (fixes eliminate all 5 errors)
- ~46-47% accuracy (errors becoming correct answers)
- Same token cost (~13,770 per question)

### Phase 2a: Low Temperature
**Config**: `configs/llama3_8b_temp01.yaml`
- Temperature: **0.1** (↓ from 0.3)
- Specialists: **5**
- Purpose: Test if stricter sampling reduces hallucination

**Hypothesis**:
- Lower hallucination attempts (fewer retry triggers)
- Slightly lower accuracy (less exploration)
- More deterministic outputs

### Phase 2b: High Temperature
**Config**: `configs/llama3_8b_temp05.yaml`
- Temperature: **0.5** (↑ from 0.3)
- Specialists: **5**
- Purpose: Test if more exploration improves reasoning

**Hypothesis**:
- Higher hallucination risk
- Potentially better accuracy (more creative reasoning)
- Less deterministic outputs

### Phase 3: Reduced Specialists
**Config**: `configs/llama3_8b_2spec.yaml`
- Temperature: **0.3**
- Specialists: **2** (↓ from 5)
- Purpose: Test cost-accuracy trade-off with fewer agents

**Expected Results**:
- ~60% token cost reduction (2 vs 5 specialists)
- Faster inference (~25s vs 37s per question)
- Possibly lower accuracy (less diverse perspectives)
- Fewer agents = less coordination overhead

---

## Cost Analysis

### Token Breakdown (5 Specialists)
- Planner: ~2,500 tokens
- 5 Specialists: ~8,000 tokens (5 × 1,600)
- Aggregator: ~3,000 tokens
- **Total**: ~13,770 tokens

### Token Breakdown (2 Specialists)
- Planner: ~2,500 tokens
- 2 Specialists: ~3,200 tokens (2 × 1,600)
- Aggregator: ~1,800 tokens (simpler synthesis)
- **Total**: ~7,500 tokens

### Cost Comparison
| Configuration | Tokens | Cost vs Baseline | Speedup |
|---------------|--------|------------------|---------|
| Single-LLM CoT | 832 | 1.0x | 1.0x |
| Adaptive MAS (5 spec) | 13,770 | 16.5x | 0.15x |
| **Adaptive MAS (2 spec)** | **~7,500** | **~9x** | **~0.25x** |

**Hypothesis**: 2 specialists may hit sweet spot of:
- Better accuracy than single-LLM (multi-perspective)
- Better cost than 5 specialists (fewer agents)
- Faster inference (less coordination)

---

## Execution Timeline

### Day 1 (Nov 4)
- ✅ Implement all fixes (JSON parsing, fallback filtering)
- 🔄 Phase 1: Baseline (temp=0.3, 5 spec) - **Running** (~1.5h)
- ⏳ Phase 2a: Low temp (temp=0.1, 5 spec) - Queued (~1.5h)
- ⏳ Phase 2b: High temp (temp=0.5, 5 spec) - Queued (~1.5h)
- ⏳ Phase 3: Reduced agents (temp=0.3, 2 spec) - Queued (~1.5h)

**Total Compute**: ~6 hours (all phases)

---

## Success Criteria

### Minimum Requirements
1. ✅ **0% system failures** across all experiments
2. ✅ **Accuracy ≥ 44%** (match or beat original)
3. ✅ **Complete all 100 questions** per experiment

### Stretch Goals
1. **Accuracy > 47%** (beat single-LLM baseline)
2. **Token cost < 10x** single-LLM (with 2 specialists)
3. **Hallucination rate < 1%** (with temp=0.1)

---

## Analysis Plan

### Primary Comparisons
1. **Temperature Effect** (holding specialists=5 constant)
   - Compare: temp 0.1 vs 0.3 vs 0.5
   - Metrics: Accuracy, hallucination rate, token variance

2. **Specialist Count Effect** (holding temp=0.3 constant)
   - Compare: 2 spec vs 5 spec
   - Metrics: Accuracy, token cost, latency

3. **Best Configuration**
   - Identify optimal temperature and specialist count
   - Calculate cost-performance Pareto frontier

### Statistical Analysis
- Paired t-test for accuracy differences
- Chi-square for error rate differences
- Effect size (Cohen's d) for practical significance

---

## Expected Outcomes

### Scenario A: Temperature 0.1 Wins
- Lowest hallucination rate
- Most reliable
- Slightly lower accuracy
- **Recommendation**: Use 0.1 for production

### Scenario B: Temperature 0.3 Wins (Current)
- Balanced performance
- Current configuration is optimal
- No changes needed

### Scenario C: 2 Specialists Wins
- Much better cost-efficiency
- Competitive accuracy
- **Recommendation**: Always use 2 specialists

### Scenario D: Multi-Agent Still Loses
- Single-LLM remains best
- Multi-agent overhead not worth complexity
- **Conclusion**: Abandon MAS approach for 8B model

---

## Data Collection

### Per-Experiment Metrics
```json
{
  "experiment_name": "phase1_baseline_temp03_5spec",
  "config": "configs/llama3_8b.yaml",
  "temperature": 0.3,
  "top_k": 5,
  "results": {
    "adaptive_mas": {
      "n_samples": 100,
      "n_correct": 47,
      "accuracy": 0.47,
      "avg_latency": 37.4,
      "avg_tokens": 13770,
      "avg_agents": 7.0,
      "errors": 0,
      "hallucinations": 0
    },
    "single_cot": {...},
    "fixed_pipeline": {...},
    "debate": {...}
  }
}
```

### Aggregate Comparison Table
| Experiment | Temp | Spec | Accuracy | Error% | Tokens | Latency | Hallu% |
|------------|------|------|----------|--------|--------|---------|--------|
| Original (no fixes) | 0.3 | 5 | 44.2% | 5.0% | 13,770 | 37.4s | 1.0% |
| Phase 1 (baseline) | 0.3 | 5 | **?** | **0%** | ~13,770 | ~37s | **0%** |
| Phase 2a (low temp) | 0.1 | 5 | ? | 0% | ~13,770 | ~37s | ? |
| Phase 2b (high temp) | 0.5 | 5 | ? | 0% | ~13,770 | ~37s | ? |
| Phase 3 (2 spec) | 0.3 | 2 | ? | 0% | **~7,500** | **~25s** | 0% |

---

## Files Generated

### Config Files
```
configs/
├── llama3_8b.yaml           # Baseline (temp=0.3, 5 spec)
├── llama3_8b_temp01.yaml    # Low temp (temp=0.1, 5 spec)
├── llama3_8b_temp05.yaml    # High temp (temp=0.5, 5 spec)
└── llama3_8b_2spec.yaml     # Reduced agents (temp=0.3, 2 spec)
```

### Results Directories
```
runs/baseline_comparison/
├── 20251104_HHMMSS/  # Phase 1: baseline with fixes
├── 20251104_HHMMSS/  # Phase 2a: temp=0.1
├── 20251104_HHMMSS/  # Phase 2b: temp=0.5
└── 20251104_HHMMSS/  # Phase 3: 2 specialists
```

---

## Next Steps After Experiments

### If Results Show Improvement
1. Update RESULTS_SUMMARY.md with new findings
2. Re-run on full 1,071-question dataset
3. Test with 70B model for validation
4. Write ablation study section for paper

### If Results Show No Improvement
1. Document negative results (still valuable!)
2. Conclude that 8B model insufficient for MAS
3. Recommend single-LLM for 8B scale
4. Test 70B model as potential path forward

---

## Paper Contributions

### Key Findings to Report
1. **Error Handling is Critical**: 5% failure rate unacceptable, robust parsing essential
2. **Temperature Effect on Hallucination**: Quantify relationship
3. **Agent Count Trade-off**: Optimal number of specialists for cost-performance
4. **Model Scale Matters**: 8B may be too small for reliable multi-agent coordination

### Ablation Study Table (for paper)
| Configuration | Accuracy | Tokens | Latency | Error% |
|---------------|----------|--------|---------|--------|
| Single-LLM | 47.0% | 832 | 5.5s | 0% |
| MAS (temp=0.1, 5 spec) | ? | ~13,770 | ~37s | 0% |
| MAS (temp=0.3, 5 spec) | ? | ~13,770 | ~37s | 0% |
| MAS (temp=0.5, 5 spec) | ? | ~13,770 | ~37s | 0% |
| MAS (temp=0.3, 2 spec) | ? | **~7,500** | **~25s** | 0% |

---

## Notes

- All experiments use the SAME 100 questions for fair comparison
- Random seed fixed for reproducibility (where applicable)
- Baselines (Single-LLM, Fixed Pipeline, Debate) run once, reused for all comparisons
- Focus is on Adaptive MAS hyperparameter optimization
- All fixes (JSON parsing, fallback filtering) applied to ALL runs

---

## Contact

COMP 5970/6970 Course Project - Fall 2024
Multi-Agent Systems for Medical Diagnosis
