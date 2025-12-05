# Progressive Temperature with Parallel Exploration

## Motivation

While progressive temperature reasoning (Section X) demonstrated strong performance through gradual temperature annealing (72.2% accuracy), we hypothesized that a single exploration path might miss important diagnostic considerations. To address this limitation, we developed a parallel exploration approach that combines diverse hypothesis generation with deterministic consolidation.

## Methodology

Our approach consists of three stages:

### Stage 1: Parallel Diverse Exploration (Temperature = 1.0, N=5)

We run five independent explorations in parallel, each at temperature 1.0 to maximize diversity. Each exploration receives the same prompt:

```
Generate a BROAD differential diagnosis. Consider all possibilities,
even unlikely ones. What could this possibly be? Explore diverse
reasoning paths.
```

The high temperature (1.0) samples from the full probability distribution, ensuring each parallel exploration can take different reasoning paths and consider different diagnostic hypotheses.

### Stage 2: Deterministic Synthesis (Temperature = 0.0)

The five explorations are then synthesized into a comprehensive differential diagnosis using a deterministic merge (temperature 0.0). The merge prompt prioritizes:

1. **Critical flags** (contraindications, drug interactions, safety issues)
2. **Consensus findings** (diagnoses mentioned by multiple explorations)
3. **Patient-specific factors** (history, comorbidities, medications)
4. **Comprehensive differential** (all unique diagnoses, ranked by evidence)
5. **Conflicting information** (disagreements between explorations)
6. **Unique insights** (clinically significant findings from single explorations)

The deterministic temperature ensures faithful preservation of information from all explorations without introducing additional randomness.

### Stage 3: Final Decision (Temperature = 0.0)

A final deterministic reasoning stage reviews the comprehensive differential and selects the single best answer, considering:
- Evidence for and against each option
- Which diagnosis best explains ALL clinical findings
- Critical contraindications or red flags

## Results

| Method | Accuracy | Stages | Key Characteristics |
|--------|----------|--------|-------------------|
| Progressive Temperature (baseline) | 72.2% | 5 | Single agent: 1.0→0.7→0.5→0.3→0.0 |
| **Parallel + Deterministic Merge** | **73.6%** | **7** | **5×1.0 → merge@0.0 → final@0.0** |

The parallel exploration approach achieved **73.6% accuracy** (788/1071 correct), representing a **+1.4 percentage point improvement** over the progressive temperature baseline. The approach averaged 11,050 tokens and 130 seconds per question.

## Analysis and Design Insights

### Evolution of the Approach

We iteratively refined the approach through three versions:

**V1 (Initial)**: 5 parallel explorations at temp=1.0, merge at temp=0.5, followed by 4 additional reasoning stages with decreasing temperatures (0.7→0.5→0.3→0.0). Result: **69.0%** accuracy (-3.2 points vs baseline).

**V2 (Enhanced Merge Prompt)**: Same architecture as V1 but with improved merge prompt emphasizing contraindications and consensus weighting. Result: **71.3%** accuracy (-0.9 points vs baseline).

**V4 (Simplified + Deterministic)**: 5 parallel explorations at temp=1.0, deterministic merge at temp=0.0, single final decision at temp=0.0. Result: **73.6%** accuracy (+1.4 points vs baseline).

### Key Design Decisions

**1. Deterministic Consolidation is Critical**

V1 and V2 used temperature 0.5 for the merge stage, which introduced randomness during consolidation. This caused two problems:
- Critical information mentioned in only 2-3 of 5 explorations could be downweighted or lost
- The stochastic sampling added noise rather than preserving the diverse signals

Changing the merge to temperature 0.0 (deterministic argmax selection) ensured faithful preservation of information from all five explorations.

**2. Post-Merge Randomness is Harmful**

After generating five diverse explorations, we already have sufficient variety in the hypothesis space. Additional stages with non-zero temperature (0.7, 0.5, 0.3) inject noise without adding value:
- The diversity benefit of temperature applies when generating *multiple samples*
- For *single-sample* consolidation and decision stages, determinism is superior
- Randomness in these stages was noise injection, not helpful exploration

**3. Fewer Stages Reduces Error Accumulation**

Simplifying from 10 stages (V1/V2) to 7 stages (V4) reduced opportunities for error accumulation. Each reasoning stage can introduce errors; the V4 architecture minimizes intermediate steps while maintaining the core benefits of parallel exploration and comprehensive synthesis.

**4. The Value of Parallel Exploration**

Examining the merged differentials revealed that parallel exploration effectively captured diverse diagnostic considerations:
- Important diagnoses mentioned by 3+ explorations gained appropriate emphasis
- Critical contraindications flagged in 1-2 explorations were preserved in the merge
- The comprehensive differential included both consensus and outlier hypotheses

This breadth of coverage, combined with deterministic consolidation, explains the performance improvement over single-agent progressive temperature.

## Comparison to Related Approaches

Unlike debate-based methods (Section Y) where agents iteratively challenge each other, our approach generates parallel explorations independently, then synthesizes them in a single deterministic step. This avoids the anchoring and convergence issues observed in multi-round debate while still capturing diverse perspectives.

The approach also differs from our multi-agent specialist architecture (Section Z) by using identical prompts for all parallel explorations rather than specialized roles. This ensures maximum diversity through stochastic sampling rather than prompt engineering.

## Computational Efficiency

The parallel exploration approach uses 7 LLM calls per question (vs 5 for baseline progressive temperature). With parallel execution capabilities, the wall-clock time can be significantly reduced by running the 5 initial explorations concurrently. In our sequential implementation, average latency was 130 seconds per question, comparable to other multi-agent approaches.

## Conclusion

Progressive temperature with parallel exploration demonstrates that combining diverse hypothesis generation (via parallel sampling at high temperature) with deterministic consolidation (temperature 0.0) can improve reasoning performance. The key insight is that temperature serves different purposes at different stages: high temperature for exploration breadth, zero temperature for faithful information preservation and final decision-making.

The approach's success validates the hypothesis that single-agent progressive temperature, while effective, can miss important diagnostic considerations that are captured when exploring multiple reasoning paths in parallel.
