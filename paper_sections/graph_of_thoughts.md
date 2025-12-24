# Graph of Thoughts for Medical Reasoning

## Overview

Graph of Thoughts (GoT) is a neurosymbolic reasoning framework that extends Chain-of-Thought and Tree-of-Thoughts by representing reasoning as a **directed graph** rather than a linear chain or tree structure. This enables more sophisticated reasoning patterns including feedback loops, iterative refinement, and complex aggregation.

## Motivation

Medical diagnostic reasoning is inherently **non-linear** and **iterative**:

1. **Feedback loops:** New evidence can revise earlier hypotheses
2. **Cross-pollination:** Competing diagnoses inform each other
3. **Iterative refinement:** Diagnostic confidence evolves through multiple passes
4. **Complex aggregation:** Multiple reasoning paths must be reconciled

Traditional approaches (Chain-of-Thought, Tree-of-Thoughts) force reasoning into rigid structures that don't capture this complexity. Graph of Thoughts allows the reasoning process to mirror actual clinical decision-making.

## Architecture

### Graph Structure

**Nodes:** Represent distinct reasoning states

| Node Type | Purpose | Temperature |
|-----------|---------|-------------|
| INITIAL | Problem understanding | 0.3 (factual) |
| HYPOTHESIS | Diagnostic hypotheses (one per option) | 0.8 (diverse) |
| EVIDENCE | Evidence for/against each hypothesis | 0.5 (balanced) |
| REFINEMENT | Updated hypotheses after evidence | 0.4 (focused) |
| AGGREGATION | Synthesis of all reasoning | 0.0 (deterministic) |
| DECISION | Final answer selection | 0.0 (deterministic) |

**Edges:** Represent transformations and dependencies

| Edge Type | Meaning |
|-----------|---------|
| generates | Initial → Hypotheses |
| supports | Hypotheses → Evidence |
| informs | Evidence → Refinement |
| refines | Original Hypothesis → Refined Hypothesis |
| aggregates | Refinements → Aggregation |
| concludes | Aggregation → Decision |

### Reasoning Flow

```
                    ┌─────────────┐
                    │  INITIALIZE │  (temp=0.3)
                    │ Understand  │
                    │   Problem   │
                    └──────┬──────┘
                           │ generates
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐        ┌─────────┐       ┌─────────┐
   │HYPOTHESIS│        │HYPOTHESIS│       │HYPOTHESIS│  (temp=0.8)
   │    A    │        │    B    │       │  C & D  │
   └────┬────┘        └────┬────┘       └────┬────┘
        │ supports         │ supports        │ supports
        ▼                  ▼                 ▼
   ┌─────────┐        ┌─────────┐       ┌─────────┐
   │EVIDENCE │        │EVIDENCE │       │EVIDENCE │  (temp=0.5)
   │  for A  │        │  for B  │       │ for C&D │
   └────┬────┘        └────┬────┘       └────┬────┘
        │ informs          │ informs         │ informs
        │    ┌─────────────┴─────┬───────────┘
        │    │  (cross-pollination)│
        ▼    ▼                    ▼
   ┌──────────┐          ┌──────────┐          (temp=0.4)
   │ REFINE A │◄────────►│ REFINE B │  ← feedback
   └────┬─────┘          └────┬─────┘
        │ aggregates          │ aggregates
        └──────────┬──────────┘
                   ▼
            ┌─────────────┐
            │ AGGREGATION │  (temp=0.0)
            │  Synthesis  │
            └──────┬──────┘
                   │ concludes
                   ▼
            ┌─────────────┐
            │  DECISION   │  (temp=0.0)
            │Final Answer │
            └─────────────┘
```

## Key Innovations

### 1. Feedback Loops in Refinement

Unlike linear approaches, the **refinement stage** receives:
- Original hypothesis
- Evidence for/against that hypothesis
- **All competing hypotheses and their evidence**

This cross-pollination allows each hypothesis to be refined in the context of alternatives, mimicking how physicians compare differential diagnoses.

### 2. Temperature Scheduling Per Node Type

Different reasoning stages require different exploration/exploitation trade-offs:

- **High temperature (0.8)** for hypothesis generation → diverse options
- **Medium temperature (0.4-0.5)** for evidence and refinement → balanced
- **Zero temperature (0.0)** for aggregation and decision → deterministic

This is more sophisticated than progressive temperature's linear schedule.

### 3. Explicit Graph Structure

The graph itself is a **symbolic artifact** that can be:
- Visualized for interpretability
- Analyzed for patterns (e.g., which hypotheses get most evidence)
- Used for ablation studies (remove nodes/edges)

### 4. Iterative Refinement (Optional)

The refinement stage can be repeated multiple times, creating deeper graphs:

```
Hypothesis → Evidence → Refine₁ → Refine₂ → ... → Refineₙ → Aggregate
```

Each iteration allows further cross-pollination and convergence.

## Implementation Details

### Node Operations

**Generate (1 → N):**
- Input: Single parent node
- Output: Multiple child nodes
- Example: Initial analysis → 4 hypotheses (one per option)

**Transform (1 → 1):**
- Input: Single parent node
- Output: Single transformed node
- Example: Hypothesis → Evidence analysis

**Aggregate (N → 1):**
- Input: Multiple parent nodes
- Output: Single synthesized node
- Example: All refined hypotheses → Comprehensive analysis

### Deterministic Aggregation

Critical design choice: Final aggregation and decision use **temperature 0.0**

**Why?** After generating diverse hypotheses and evidence at higher temperatures, we want:
- Faithful preservation of all information
- Reproducible final decisions
- No additional randomness in synthesis

This mirrors Progressive Temperature Parallel V4's key insight.

## Expected Performance

### Advantages Over Prior Approaches

| Method | Structure | Feedback | Cross-Pollination |
|--------|-----------|----------|-------------------|
| Chain-of-Thought | Linear | ❌ No | ❌ No |
| Tree-of-Thoughts | Tree | ❌ No | ❌ No |
| Progressive Temp | Linear pipeline | ❌ No | ❌ No |
| Progressive Temp Parallel | Parallel → Merge | ❌ No | ✅ Yes (in merge) |
| **Graph of Thoughts** | **Graph** | **✅ Yes** | **✅ Yes (in refine)** |

### Potential Weaknesses

1. **Higher token cost:** More LLM calls than simpler methods
2. **Increased latency:** Sequential dependencies limit parallelization
3. **Complexity:** More moving parts = more potential failure modes

### Hypothesis

We hypothesize that **explicit feedback and cross-pollination** will improve accuracy on challenging cases where:
- Multiple diagnoses are plausible
- Evidence is ambiguous or contradictory
- Iterative refinement is needed

## Evaluation Plan

### Metrics

1. **Accuracy:** Correct answers / Total questions
2. **Token efficiency:** Accuracy per 1K tokens
3. **Graph complexity:** Average nodes/edges per question
4. **Refinement impact:** Accuracy with vs without refinement iteration

### Ablation Studies

1. **Remove feedback:** Run refinement without seeing competing hypotheses
2. **Remove refinement:** Skip directly from evidence to aggregation
3. **Temperature variations:** Test different temperature schedules
4. **Iteration depth:** 0, 1, 2, 3 refinement iterations

### Comparison Baselines

- Progressive Temperature (single-agent baseline): 72.2%
- Progressive Temperature Parallel V4: **73.6%** (current best)
- Multi-Agent Specialist: 64.6%
- Debate: 61.7%

**Target:** Beat 73.6% by leveraging feedback and refinement

## Computational Cost

**Estimated LLM calls per question:**
- 1 initialization
- 4 hypothesis generation
- 4 evidence gathering
- 4 refinement (×N iterations)
- 1 aggregation
- 1 decision

**Total:** 15 calls (single iteration) or 15 + 4N (multiple iterations)

**Comparison:**
- Progressive Temp: 5 calls
- Progressive Temp Parallel V4: 7 calls
- Graph of Thoughts: 15+ calls (2-3x cost)

Cost is justified if accuracy improvement exceeds 2-3 percentage points.

## Extensions

### Multi-Iteration Refinement

```python
for iteration in range(num_iterations):
    refined_ids = refine_hypotheses(
        hypothesis_ids,
        evidence_map,
        previous_refinements=refined_ids  # Feedback from last iteration
    )
```

### Confidence-Based Pruning

```python
# After evidence gathering, prune low-confidence hypotheses
high_conf_ids = [h_id for h_id in hypothesis_ids
                 if get_node(h_id).score > 0.3]
# Only refine high-confidence hypotheses (reduce cost)
```

### Dynamic Graph Construction

```python
# Let LLM decide graph structure
graph_plan = llm.generate("Design reasoning graph for this case")
# Execute generated plan
```

## Conclusion

Graph of Thoughts brings neurosymbolic reasoning to medical QA by:
1. **Symbolic:** Explicit graph structure with typed nodes/edges
2. **Neural:** LLM-generated content at each node
3. **Feedback:** Iterative refinement with cross-pollination
4. **Deterministic:** Final synthesis at temperature 0.0

This approach is theoretically well-motivated for medical reasoning and offers a rich framework for ablation studies and analysis. The key question is whether the added complexity and cost justify accuracy improvements over simpler approaches like Progressive Temperature Parallel V4.
