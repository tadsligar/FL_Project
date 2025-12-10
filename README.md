# Multi-Agent Medical QA Reasoning System

**Exploring Advanced Reasoning Architectures for Medical Question Answering**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **⚠️ EDUCATIONAL & RESEARCH USE ONLY**
> This is a research prototype for academic purposes only. **NOT** intended for clinical use, medical diagnosis, or patient care. Do not use this system to make medical decisions.

---

## Overview

This project systematically evaluates multiple reasoning architectures for medical question answering on the MedQA-USMLE dataset. Through extensive experimentation, we identified **Progressive Temperature with Parallel Exploration** as the highest-performing approach, achieving **73.6% accuracy** on the full MedQA US Test Set (1,071 questions).

### Research Highlights

- **Best Method**: Progressive Temperature Parallel V4 - **73.6% accuracy**
- **Dataset**: MedQA US Test Set (1,071 4-option multiple choice questions)
- **Model**: Qwen 2.5 32B (Q4_K_M quantization via Ollama)
- **Architectures Tested**: 8+ reasoning methods including multi-agent specialists, debate, self-consistency, and progressive temperature variants
- **Key Finding**: High-temperature parallel exploration + deterministic synthesis outperforms traditional multi-agent architectures

---

## Performance Summary

### Full Dataset Results (1,071 questions)

| Architecture | Accuracy | Tokens/Question | Cost vs Baseline |
|--------------|----------|-----------------|------------------|
| **Progressive Temp Parallel V4** | **73.6%** | 11,049 | 21.6x |
| Progressive Temperature (baseline) | 72.2% | 7,089 | 13.8x |
| Multi-Agent Specialist (temp=0.7) | 64.6% | 5,863 | 11.4x |
| Multi-Agent Specialist (Synthesis) | 63.8% | 5,966 | 11.6x |
| Multi-Agent Specialist (temp=0.3) | 63.4% | 6,154 | 12.0x |
| Debate (Standard) | 61.7% | 13,291 | 25.9x |
| Zero-Shot CoT | 57.8% | 513 | 1.0x |

See [ARCHITECTURE_PERFORMANCE_SUMMARY.md](ARCHITECTURE_PERFORMANCE_SUMMARY.md) for detailed analysis.

---

## Best Architecture: Progressive Temperature Parallel V4

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         STAGE 1: Parallel Exploration (N=5)             │
│              Temperature = 1.0 (High Diversity)         │
├─────────────────────────────────────────────────────────┤
│  Agent 1  │  Agent 2  │  Agent 3  │  Agent 4  │ Agent 5 │
│  Explore  │  Explore  │  Explore  │  Explore  │ Explore │
│  diverse  │  diverse  │  diverse  │  diverse  │ diverse │
│  hypotheses│ hypotheses│ hypotheses│ hypotheses│hypotheses│
└─────┬──────┴─────┬─────┴─────┬─────┴─────┬─────┴────┬──┘
      │            │           │           │          │
      └────────────┴───────────┴───────────┴──────────┘
                              │
                              ▼
            ┌─────────────────────────────────────┐
            │  STAGE 2: Deterministic Synthesis   │
            │        Temperature = 0.0            │
            │  • Merge all 5 explorations         │
            │  • Preserve all unique insights     │
            │  • Flag critical findings           │
            │  • Build comprehensive differential │
            └─────────────────┬───────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────┐
            │   STAGE 3: Deterministic Decision   │
            │        Temperature = 0.0            │
            │  • Review comprehensive differential│
            │  • Select best answer               │
            │  • Provide justification            │
            └─────────────────────────────────────┘
```

### Key Design Insights

**Why This Works:**

1. **Parallel Exploration at High Temperature (1.0)**
   - Generates diverse diagnostic hypotheses across 5 independent reasoning paths
   - Captures rare diagnoses that might be missed by single-agent approaches
   - Avoids premature convergence

2. **Deterministic Synthesis (Temperature 0.0)**
   - Faithfully preserves information from all explorations
   - No information loss from stochastic sampling
   - Consensus findings get appropriate emphasis
   - Rare but critical flags are preserved

3. **Fewer Stages, Less Error Accumulation**
   - Only 7 LLM calls (vs 10 in earlier versions)
   - Each stage has clear purpose: explore → synthesize → decide
   - Minimal intermediate steps reduce compounding errors

### Evolution: V1 → V2 → V4

| Version | Architecture | Accuracy | Key Difference |
|---------|-------------|----------|----------------|
| V1 | 5×1.0 → merge@0.5 → 4-stage annealing | 69.0% | Stochastic merge lost information |
| V2 | 5×1.0 → merge@0.5 (improved prompt) → annealing | 71.3% | Better prompt, still lossy merge |
| **V4** | **5×1.0 → merge@0.0 → final@0.0** | **73.6%** | **Deterministic = faithful synthesis** |

**Key Breakthrough**: Moving from temperature 0.5 to 0.0 for synthesis was critical (+2.3 points from V2→V4)

See [paper_sections/progressive_temperature_parallel.md](paper_sections/progressive_temperature_parallel.md) for detailed analysis.

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) for local LLM inference
- 16GB+ RAM recommended for Qwen 2.5 32B

### Installation

```bash
# Clone repository
git clone https://github.com/tadsligar/FL_Project.git
cd FL_Project

# Install dependencies
pip install -r requirements.txt

# Pull Qwen 2.5 32B model
ollama pull qwen2.5:32b
```

### Run Evaluation

**Progressive Temperature Parallel V4** (best method):
```bash
python scripts/test_progressive_temperature_parallel.py \
  --n 1071 \
  --parallel 5 \
  --config configs/qwen25_32b.yaml
```

**Baseline comparison**:
```bash
python scripts/run_baseline_comparison.py --n 100
```

**Single question test**:
```bash
python scripts/test_progressive_temperature_parallel.py \
  --n 1 \
  --parallel 5 \
  --config configs/qwen25_32b.yaml
```

---

## Architectures Tested

### 1. Progressive Temperature (Single-Agent Baseline)

**Temperature schedule**: 1.0 → 0.7 → 0.5 → 0.3 → 0.0

**Result**: 72.2% accuracy (773/1071), 7,089 tokens/question

Single agent reasons through 5 stages with decreasing temperature for gradual exploration→exploitation.

### 2. Progressive Temperature Parallel (Multi-Path)

**Best variant**: V4 with 5×1.0 parallel → merge@0.0 → final@0.0

**Result**: 73.6% accuracy (788/1071), 11,049 tokens/question

Five parallel explorations at high temperature, deterministic synthesis.

### 3. Multi-Agent Specialist Architecture

**Architecture**: Planner → 5 Specialists → Aggregator

**Best variant**: Temperature 0.7

**Result**: 64.6% accuracy (692/1071), 5,863 tokens/question

Inspired by MAS-GPT, selects specialized medical experts for each case.

### 4. Debate Methods

**Architecture**: Two agents debate iteratively

**Result**: 61.7% accuracy (660/1071), 13,291 tokens/question

Adversarial reasoning with iterative refinement. Poor cost-effectiveness.

### 5. Zero-Shot Chain-of-Thought

**Result**: 57.8% accuracy, 513 tokens/question

Baseline single-shot reasoning.

---

## Repository Structure

```
FL_Project/
├── src/
│   ├── baselines/
│   │   ├── progressive_temperature.py         # Single-agent baseline
│   │   ├── progressive_temperature_parallel.py # Parallel exploration
│   │   ├── multi_agent.py                     # MAS-GPT-style specialists
│   │   └── debate.py                          # Two-agent debate
│   ├── llm_client.py                          # Ollama client
│   ├── config.py                              # Configuration management
│   └── medqa.py                               # MedQA dataset loader
├── scripts/
│   ├── test_progressive_temperature_parallel.py # Run parallel experiments
│   ├── test_progressive_temperature.py          # Run baseline
│   ├── run_baseline_comparison.py               # Compare all methods
│   ├── analyze_progressive_temp_v4.py           # V4 analysis
│   └── summarize_all_architectures.py           # Performance summary
├── configs/
│   └── qwen25_32b.yaml                        # Qwen 2.5 32B config
├── paper_sections/
│   ├── progressive_temperature_parallel.md    # V4 detailed writeup
│   └── mas_architectures_overview.md          # Architecture comparison
├── runs/                                      # Experiment results
│   ├── progressive_temperature_parallel_v4/   # Best method runs
│   ├── progressive_temperature_full/          # Baseline runs
│   └── multi_agent_specialist_*/              # Specialist architecture runs
├── ARCHITECTURE_PERFORMANCE_SUMMARY.md        # All results table
├── TOKEN_USAGE_SUMMARY.md                     # Cost analysis
└── README.md                                  # This file
```

---

## Analysis & Results Documents

- **[ARCHITECTURE_PERFORMANCE_SUMMARY.md](ARCHITECTURE_PERFORMANCE_SUMMARY.md)** - Complete performance table for all architectures
- **[TOKEN_USAGE_SUMMARY.md](TOKEN_USAGE_SUMMARY.md)** - Token usage and cost-effectiveness analysis
- **[PROGRESSIVE_TEMP_V4_ANALYSIS.md](PROGRESSIVE_TEMP_V4_ANALYSIS.md)** - V4 stability analysis across multiple runs
- **[paper_sections/progressive_temperature_parallel.md](paper_sections/progressive_temperature_parallel.md)** - Detailed V4 methodology and evolution
- **[paper_sections/mas_architectures_overview.md](paper_sections/mas_architectures_overview.md)** - MAS-GPT architecture comparison

---

## Configuration

**Model Configuration** (`configs/qwen25_32b.yaml`):

```yaml
model: "qwen2.5:32b"
provider: "ollama"
base_url: "http://localhost:11434"
temperature: 1.0  # Overridden per stage
max_output_tokens: 2048
timeout: 300
```

**Progressive Temperature Parallel Settings**:
- Parallel explorations: 5
- Exploration temperature: 1.0
- Merge temperature: 0.0 (deterministic)
- Final decision temperature: 0.0 (deterministic)

---

## Key Research Findings

### 1. Deterministic Synthesis is Critical

Early versions (V1, V2) used temperature 0.5 for merging parallel explorations, which caused information loss. Moving to temperature 0.0 (deterministic argmax) improved accuracy by 2.3 percentage points.

### 2. Temperature Serves Different Purposes

- **High temp (1.0) for exploration**: Generate diverse hypotheses
- **Zero temp (0.0) for consolidation**: Preserve all signals without noise

### 3. Parallel > Sequential for Medical Reasoning

Parallel exploration at high temperature captured diagnostic considerations that single-agent progressive temperature missed, despite the baseline being strong (72.2%).

### 4. Multi-Agent Specialists Underperformed Expectations

Despite intuitive appeal, specialist-aggregator architecture (inspired by MAS-GPT) achieved only 64.6% accuracy. Hypothesis: Fixed role assignments limit flexibility compared to parallel exploration.

### 5. Debate Methods Have Poor ROI

Debate achieved 61.7% accuracy at 25.9x baseline cost - worse performance than progressive temperature at higher computational cost.

---

## Dataset

**MedQA-USMLE US Test Set**

- 1,071 4-option multiple choice questions
- USMLE-style clinical vignettes
- Located at: `data/medqa_us_test_4opt.json`

Questions test clinical reasoning across medical specialties, requiring integration of patient history, physical findings, and diagnostic workup.

---

## Future Work

### Near-Term

- [ ] Majority voting analysis across 3 runs of V4
- [ ] Ablation studies: impact of number of parallel agents (3, 5, 7, 10)
- [ ] Temperature sweep for merge stage
- [ ] Hybrid: V4 parallel exploration + specialist consultation

### Research Directions

- [ ] Retrieval augmentation (PubMed, UpToDate)
- [ ] Multi-turn reasoning with intermediate questions
- [ ] Uncertainty quantification
- [ ] Analysis of disagreement patterns
- [ ] Generalization to other medical QA datasets (MedMCQA, PubMedQA)

---

## Citation

If you use this work, please cite:

```bibtex
@misc{fl_project_2025,
  title={Progressive Temperature with Parallel Exploration for Medical Question Answering},
  author={Sligar, Tad},
  year={2025},
  url={https://github.com/tadsligar/FL_Project}
}
```

Inspired by:
```bibtex
@article{zhou2023masgpt,
  title={MAS-GPT: Multi-Agent Systems with Generative Pre-trained Transformers},
  author={Zhou, Kexin and others},
  journal={arXiv preprint arXiv:2305.15334},
  year={2023}
}
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Contact

- GitHub: [@tadsligar](https://github.com/tadsligar)
- Repository: [https://github.com/tadsligar/FL_Project](https://github.com/tadsligar/FL_Project)

---

**Disclaimer**: This is an educational research tool. Always consult qualified healthcare professionals for medical advice and diagnosis.
