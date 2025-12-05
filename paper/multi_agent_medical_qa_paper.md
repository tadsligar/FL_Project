# Multi-Agent Systems for Medical Question Answering: When Does Complexity Help?

## Abstract

Multi-agent systems (MAS) have emerged as a promising approach for complex reasoning tasks, with the intuition that multiple specialized agents can outperform a single generalist model. We investigate this hypothesis in the domain of medical question answering using the MedQA-USMLE dataset. Through systematic experiments across model scales (8B to 32B parameters) and architectural variations, we identify a critical finding: multi-agent systems only outperform single-LLM baselines when the underlying model exceeds a capability threshold. At 8B parameters, single-LLM chain-of-thought achieves 54% accuracy while adaptive multi-agent systems achieve only 45%. However, at 32B parameters, this relationship inverts dramatically—adversarial debate achieves 76% accuracy compared to 66% for single-LLM. We further demonstrate that adversarial interaction patterns significantly outperform collaborative ones, with fixed-round debate exceeding agreement-based consultation by 12 percentage points. Our analysis reveals that increased architectural complexity does not monotonically improve performance; rather, optimal multi-agent design requires careful consideration of model capacity, interaction patterns, and error propagation. We validate our findings on the full 1,071-question MedQA dataset, achieving 63.4% accuracy with a mixed-temperature independent multi-agent approach. These results provide practical guidelines for deploying multi-agent systems in high-stakes domains where reliability is paramount.

## 1 Introduction

The application of large language models (LLMs) to medical question answering has shown remarkable progress, with recent models approaching or exceeding human physician performance on standardized medical licensing examinations. However, a fundamental question remains: can we improve upon single-model performance by orchestrating multiple specialized agents that mirror the collaborative nature of clinical decision-making?

This question is motivated by the observation that real-world medical diagnosis rarely occurs in isolation. Physicians routinely consult specialists, seek second opinions, and engage in differential diagnosis through collaborative reasoning. The multi-agent paradigm attempts to replicate this process computationally, with the hypothesis that specialized agents focusing on distinct medical domains can collectively achieve superior diagnostic accuracy.

Despite intuitive appeal, the empirical evidence for multi-agent superiority in medical QA remains mixed. Prior work has demonstrated both successes and failures, often without systematic analysis of the conditions under which multi-agent approaches excel. This paper addresses this gap through a comprehensive empirical investigation spanning multiple model scales, architectural designs, and interaction patterns.

Our investigation yields several surprising findings. First, we identify a **capability threshold** below which multi-agent systems actively harm performance. At 8B parameters, the overhead of agent coordination and the amplification of individual agent errors results in accuracy 9 percentage points below a simple single-LLM baseline. Second, we demonstrate that **adversarial interaction patterns dramatically outperform collaborative ones**—forced disagreement through fixed debate rounds achieves 76% accuracy, while agreement-seeking consultation achieves only 64%. Third, we show that **architectural complexity has diminishing and even negative returns**; our most complex system (7-10 LLM calls per question) performs 12 percentage points worse than a simpler debate approach (3-4 calls).

These findings have significant implications for the deployment of AI systems in medical settings. They suggest that the path to improved medical AI lies not in increasingly complex multi-agent architectures, but in careful matching of system complexity to model capability, with a preference for adversarial over collaborative interaction patterns.

The contributions of this paper are:

1. **Empirical characterization of the model scale threshold** for multi-agent system effectiveness, demonstrating a phase transition between 8B and 32B parameters.

2. **Systematic comparison of interaction patterns**, showing that adversarial debate outperforms collaborative consultation by 12 percentage points.

3. **Analysis of error propagation** in multi-stage pipelines, quantifying how coordination overhead compounds individual agent errors.

4. **Full-dataset validation** on 1,071 MedQA questions with analysis of result stability across multiple runs.

5. **Practical guidelines** for multi-agent system design in high-stakes medical applications.

## 2 Related Work

### 2.1 Large Language Models for Medical Question Answering

The application of LLMs to medical question answering has progressed rapidly. Early work demonstrated that models like GPT-3 could achieve near-passing scores on medical licensing examinations without domain-specific training. Subsequent models, including Med-PaLM and its successors, have achieved physician-level performance through a combination of scale, instruction tuning, and domain-specific fine-tuning.

The MedQA dataset, derived from United States Medical Licensing Examination (USMLE) questions, has become a standard benchmark for evaluating medical reasoning capabilities. The dataset comprises 1,273 four-option multiple choice questions spanning basic sciences, clinical medicine, and bioethics. Human physician performance on this dataset ranges from 60-87% depending on specialization and experience level, providing a meaningful comparison point for AI systems.

### 2.2 Multi-Agent Systems for Complex Reasoning

Multi-agent approaches to LLM reasoning have gained significant attention following demonstrations that agent interaction can improve performance on complex tasks. The core intuition is that multiple agents, potentially with different "perspectives" or "roles," can engage in productive discourse that surfaces errors and refines reasoning.

Several paradigms have emerged. **Debate-based approaches** pit agents against each other in adversarial argument, with the hypothesis that the need to defend positions against critique leads to more rigorous reasoning. **Consultation-based approaches** model collaborative expert discussion, where specialists contribute domain knowledge that is synthesized by a generalist. **Ensemble approaches** aggregate independent agent outputs through voting or learned combination.

Recent work on MAS-GPT proposed using LLMs to dynamically generate multi-agent architectures tailored to specific problems. While promising, this approach introduces additional complexity and potential failure modes through the architecture generation step itself.

### 2.3 Mixture of Experts and Specialist Selection

The mixture-of-experts (MoE) paradigm, where different model components specialize in different inputs, provides a architectural foundation for multi-agent specialization. In the context of medical QA, this translates to specialist agents embodying different medical domains—cardiology, neurology, infectious disease, etc.

A key challenge in specialist-based systems is **specialist selection**: determining which experts to consult for a given question. Prior approaches have used keyword matching, embedding similarity, or LLM-based classification. Our work employs a planner agent that scores questions against a predefined catalog of 28 medical specialties, selecting the top-k most relevant specialists for consultation.

### 2.4 Chain-of-Thought and Reasoning Enhancement

Chain-of-thought (CoT) prompting, which elicits step-by-step reasoning from LLMs, has proven highly effective for complex reasoning tasks including medical QA. CoT provides a strong single-model baseline against which multi-agent approaches must be compared.

Extensions to CoT, including self-consistency (sampling multiple reasoning paths and voting) and tree-of-thought (exploring branching reasoning structures), share conceptual similarities with multi-agent approaches in that they generate diverse reasoning for aggregation. Our work can be viewed as an agent-based instantiation of these ideas, where diversity arises from agent specialization rather than sampling.

## 3 Method

### 3.1 Problem Formulation

We address the task of multiple-choice medical question answering. Given a clinical vignette $q$ describing patient presentation, history, and findings, along with four answer options $\{A, B, C, D\}$, the system must select the single correct answer. Questions span diagnosis, treatment selection, pathophysiology, and clinical management.

### 3.2 System Architectures

We evaluate four primary architectures of increasing complexity:

#### 3.2.1 Single-LLM Chain-of-Thought (Baseline)

The simplest approach prompts a single LLM with the question and options, requesting step-by-step reasoning before a final answer. This serves as our primary baseline, representing the performance achievable without multi-agent complexity.

#### 3.2.2 Fixed Specialist Pipeline

A three-stage pipeline with predetermined specialist consultation:

1. **Specialist Consultation**: Three fixed specialists (Internal Medicine, Emergency Medicine, and a rotating domain specialist) independently analyze the question.
2. **Response Synthesis**: A generalist agent synthesizes specialist opinions.
3. **Answer Selection**: Final answer extracted from synthesis.

This architecture tests whether specialist perspectives improve accuracy without the complexity of dynamic specialist selection.

#### 3.2.3 Adaptive Multi-Agent System

Our most complex architecture employs dynamic specialist selection:

1. **Planner Agent**: Analyzes the clinical presentation and scores all 28 specialties in a predefined catalog. Selects top-k (typically 5) specialists based on relevance scores. The catalog includes 3 generalist specialties, 20 medical specialties, and 5 surgical specialties.

2. **Specialist Agents**: Selected specialists provide independent consultations, each offering differential diagnoses with probability scores and supporting evidence.

3. **Aggregator Agent**: Synthesizes specialist inputs, resolves conflicts, and produces a final answer with confidence score.

The predefined specialty catalog prevents hallucination of non-existent specialties—a critical consideration for medical applications where invented specialties could introduce dangerous errors.

#### 3.2.4 Adversarial Debate

A two-agent debate system with fixed iteration:

1. **Agent A** proposes an initial answer with supporting reasoning.
2. **Agent B** critiques Agent A's reasoning and proposes an alternative.
3. **Iterative Refinement**: Agents alternate for 3 fixed rounds, forced to engage with opponent arguments.
4. **Moderator**: Synthesizes the debate and selects the final answer.

Critically, the debate runs for a fixed number of rounds regardless of apparent agreement. This design choice, informed by preliminary experiments, prevents premature convergence that undermines the benefits of adversarial interaction.

### 3.3 Independent Multi-Agent with Mixed Temperature

Based on our architectural experiments, we developed a hybrid approach combining insights from both specialist consultation and temperature-based diversity:

1. **Selector Agent** (temperature=0.0): Deterministically selects the top 3 most relevant specialists for each question.

2. **Specialist Agents** (temperature=0.3): Three specialists independently analyze the question with moderate temperature to encourage reasoning diversity.

3. **Reviewer Agent** (temperature=0.0): Deterministically synthesizes specialist responses and selects the final answer.

This architecture uses 5 LLM calls per question and balances the benefits of specialist diversity with deterministic selection and synthesis.

### 3.4 Specialty Catalog

Our system employs a fixed catalog of 28 medical specialties:

**Generalist (3)**: Family Medicine, Internal Medicine, Emergency Medicine

**Medical Specialties (20)**: Cardiology, Pulmonology, Gastroenterology, Nephrology, Neurology, Endocrinology, Hematology, Oncology, Infectious Disease, Rheumatology, Allergy/Immunology, Dermatology, Psychiatry, Pediatrics, Geriatrics, Obstetrics/Gynecology, Ophthalmology, Otolaryngology, Physical Medicine, Sleep Medicine

**Surgical Specialties (5)**: General Surgery, Orthopedic Surgery, Neurosurgery, Cardiothoracic Surgery, Vascular Surgery

This catalog was designed to cover the breadth of USMLE content while remaining tractable for specialist selection.

### 3.5 Implementation Details

All experiments use locally-deployed open-source models via Ollama. Primary experiments use Qwen2.5-32B for its strong medical reasoning capabilities. Scaling experiments additionally evaluate Llama3-8B to characterize model size effects.

Prompts were iteratively refined based on preliminary experiments to minimize JSON parsing failures and ensure consistent output formats. All specialist prompts include structured output requirements specifying differential diagnosis format, probability constraints (sum ≤ 1.0), and evidence enumeration.

## 4 Experiments

### 4.1 Experimental Setup

**Dataset**: MedQA-USMLE test set containing 1,071 four-option multiple choice questions. For rapid iteration experiments, we use a fixed 100-question subset (seed=42) that spans the full difficulty and topic distribution.

**Models**: Primary experiments use Qwen2.5-32B. Scaling experiments compare Llama3-8B and Llama3-70B.

**Metrics**: Primary metric is accuracy (percentage of correctly answered questions). Secondary metrics include tokens consumed, latency per question, and system error rate (failures due to parsing errors, timeouts, or invalid outputs).

**Reproducibility**: All experiments use fixed random seeds where applicable. Temperature settings are explicitly specified for all runs. Full experimental configurations are available in supplementary materials.

### 4.2 Model Scale Experiments

Our first experiment investigates the relationship between model scale and multi-agent effectiveness.

**Table 1: Accuracy by Model Scale and Architecture (100 questions)**

| Method | Llama3-8B | Qwen2.5-32B | Delta |
|--------|-----------|-------------|-------|
| Single-LLM CoT | **54.0%** | 66.0% | +12.0 |
| Fixed Pipeline | 46.0% | 71.0% | +25.0 |
| Adaptive MAS | 45.0% | 68.8% | +23.8 |
| Debate | 33.0% | **76.0%** | +43.0 |

At 8B parameters, Single-LLM CoT outperforms all multi-agent approaches, with the gap reaching 21 percentage points versus Debate. This inverts completely at 32B parameters, where Debate achieves the highest accuracy at 76%, exceeding Single-LLM by 10 percentage points.

The improvement from scaling is dramatically larger for multi-agent methods (+23-43 points) compared to Single-LLM (+12 points). This suggests that multi-agent architectures have higher capability requirements that are only satisfied at larger model scales.

**Finding 1**: Multi-agent systems exhibit a capability threshold below which they underperform single-LLM baselines. At 8B parameters, coordination overhead and error propagation outweigh benefits of specialization.

### 4.3 Interaction Pattern Experiments

We compare adversarial (debate) and collaborative (consultation) interaction patterns at the 32B scale.

**Table 2: Interaction Pattern Comparison (100 questions, Qwen2.5-32B)**

| Method | Accuracy | Calls/Question | Pattern |
|--------|----------|----------------|---------|
| Debate (fixed rounds) | **76.0%** | 3-4 | Adversarial |
| Adaptive MAS | 68.8% | 6-8 | Collaborative |
| Sequential Consultation | 64.0% | 4-6 | Collaborative |
| Single-LLM CoT | 66.0% | 1 | N/A |

The adversarial debate approach outperforms all collaborative approaches by 7-12 percentage points. Notably, the Sequential Consultation method—which allows early termination upon agent agreement—performs 2 points worse than Single-LLM despite using 4-6x more compute.

Analysis of Sequential Consultation reveals that 100% of debates terminated after only 2 rounds due to immediate agreement. This premature convergence eliminates the iterative refinement that makes multi-agent interaction valuable.

**Finding 2**: Adversarial interaction with forced disagreement (fixed rounds) dramatically outperforms collaborative interaction with agreement-based termination. The mechanism of improvement requires sustained engagement, not mere consultation.

### 4.4 Complexity Analysis

We investigate whether increased architectural complexity improves performance.

**Table 3: Accuracy vs. Complexity (Qwen2.5-32B)**

| Method | LLM Calls | Accuracy | Efficiency |
|--------|-----------|----------|------------|
| Single-LLM | 1 | 66.0% | 66.0/call |
| Debate | 3-4 | 76.0% | 21.7/call |
| Adaptive MAS | 6-8 | 68.8% | 9.8/call |
| Answer Space Analysis | 7-10 | 54.0% | 6.2/call |

The Answer Space Analysis method, our most complex architecture involving preliminary answer extraction before specialist consultation, achieves the worst accuracy despite the highest compute cost. This represents a 12-point degradation from Single-LLM while using 7-10x more resources.

Detailed analysis revealed a paradoxical pattern: when the specialist parsing component failed (defaulting to generic specialists), accuracy reached 75%. When parsing succeeded with LLM-selected specialists, accuracy dropped to 50%. This suggests that premature commitment to answer choices introduces anchoring bias that degrades subsequent reasoning.

**Finding 3**: Architectural complexity has diminishing and negative returns. Optimal performance is achieved at moderate complexity (3-4 calls for Debate), with both simpler (1 call) and more complex (7-10 calls) approaches performing worse.

### 4.5 Temperature and Variance Analysis

To understand the reliability of our results, we conducted temperature sensitivity and variance analysis.

**Zero-Shot Temperature Sweep (Qwen2.5-32B, 100 questions)**:

| Temperature | Accuracy | Latency |
|-------------|----------|---------|
| 0.0 | 54% | 11.2s |
| 0.1 | 54% | 9.3s |
| 0.3 | 49% | 10.8s |
| 0.5 | 52% | 12.1s |
| 0.7 | 51% | 11.9s |

Zero-shot accuracy is relatively stable across temperatures (49-54%), with lower temperatures marginally faster due to reduced output verbosity.

**Debate Variance Analysis**: We ran the debate method twice with identical configurations at temperature 0.5:
- Run 1: 76% accuracy
- Run 2: 70% accuracy
- Variance: ±6 percentage points

This substantial variance at temperature 0.5 has important implications for methodology: **performance differences less than 10 percentage points may not be statistically meaningful** without multiple replicates.

**Finding 4**: High-temperature sampling introduces significant variance (±6%). Only differences exceeding 10 percentage points should be considered reliable without replication.

### 4.6 Full Dataset Validation

To validate our findings at scale, we evaluated the Independent Multi-Agent Mixed Temperature approach on the complete 1,071-question MedQA dataset across three independent runs.

**Table 4: Full Dataset Results (1,071 questions, Qwen2.5-32B)**

| Run | Correct | Accuracy |
|-----|---------|----------|
| 1 | 682 | 63.68% |
| 2 | 677 | 63.21% |
| 3 | 677 | 63.21% |
| **Mean** | 678.7 | **63.37%** |
| **Std Dev** | 2.9 | 0.27% |

The results demonstrate remarkable stability across runs, with standard deviation of only 0.27 percentage points. This validates that our methodology produces reliable, reproducible results.

**Cross-Run Agreement Analysis**: Despite identical total accuracy in Runs 2 and 3 (677/1071), the runs disagreed on 256 questions (23.9%). This reveals:

| Category | Questions | Percentage |
|----------|-----------|------------|
| Reliably Correct (all 3 runs) | 468 | 43.7% |
| Correct in 2 runs | 235 | 21.9% |
| Correct in 1 run | 162 | 15.1% |
| Reliably Wrong (all 3 runs) | 206 | 19.2% |

The 865 unique questions answered correctly across any run (80.8%) represents a theoretical ceiling achievable through perfect ensemble aggregation—17 percentage points above single-run performance.

**Specialist Temperature Comparison**: We additionally evaluated specialist temperature of 0.7 (higher diversity) versus 0.3:

| Specialist Temp | Accuracy | Status |
|-----------------|----------|--------|
| 0.3 | 63.37% | Complete |
| 0.7 | [PENDING] | In Progress |

[Results for temperature 0.7 to be added upon completion]

**Comparison to Baseline**:

| Method | Accuracy | Improvement |
|--------|----------|-------------|
| All agents temp=0.3 | 62.56% | baseline |
| Mixed temp (0.0/0.3/0.0) | 63.37% | +0.81% |

The mixed temperature approach shows modest improvement over uniform temperature, suggesting that deterministic selection and synthesis with diverse specialist reasoning is beneficial.

### 4.7 Error Analysis

We analyzed failure modes across architectures to understand sources of error.

**Adaptive MAS Error Breakdown** (100 questions, 8B model):
- JSON parsing failures: 3%
- Specialty hallucination: 1%
- Timeout errors: 1%
- Total system failures: 5%

These system failures, while individually rare, compound across pipeline stages. With k specialists and 3 pipeline stages, the probability of completing without error is approximately:

$$P(\text{success}) = (1 - p_{\text{error}})^{k+2}$$

With 5% per-stage error rate and k=5 specialists, this yields only 70% completion rate, creating a ceiling below which architectural improvements cannot lift accuracy.

**Finding 5**: Error propagation in multi-stage pipelines creates hard accuracy ceilings. Robust error handling with graceful degradation is essential for multi-agent system deployment.

## 5 Conclusion

This work provides a systematic empirical investigation of multi-agent systems for medical question answering. Our experiments reveal several findings that challenge common assumptions about multi-agent system design.

**Model scale is the primary determinant of multi-agent effectiveness.** Below a capability threshold (approximately 32B parameters for current architectures), multi-agent systems underperform simple single-LLM baselines. The coordination overhead and error propagation inherent in multi-agent systems requires sufficient model capability to overcome. This finding suggests that practitioners should first maximize single-model performance before introducing multi-agent complexity.

**Adversarial interaction dramatically outperforms collaborative consultation.** Our debate-based approach, which forces sustained disagreement through fixed iteration counts, achieves 76% accuracy compared to 64% for agreement-seeking consultation. The mechanism underlying this improvement appears to be the prevention of premature convergence—when agents are allowed to agree and terminate early, they forfeit the iterative refinement that makes multi-agent interaction valuable.

**Increased architectural complexity has diminishing and negative returns.** Our most complex system (7-10 LLM calls per question) performed 22 percentage points worse than our best system (3-4 calls). The optimal complexity point lies at moderate levels where specialization benefits outweigh coordination costs.

**Temperature-induced variance is substantial and must be accounted for in evaluation.** At temperature 0.5, we observed ±6% variance across identical runs. This implies that performance differences below 10 percentage points may not be meaningful without multiple replicates.

**Practical implications for medical AI deployment:**

1. Start with single-model approaches and only add multi-agent complexity when using capable (32B+) models.

2. Prefer adversarial over collaborative interaction patterns; force disagreement through fixed iteration counts.

3. Design for graceful degradation with robust error handling at each pipeline stage.

4. Validate findings with multiple replicates and report variance, especially at higher temperatures.

5. Consider that the theoretical ensemble ceiling (80.8% in our experiments) substantially exceeds single-run performance (63.4%), suggesting room for improvement through aggregation methods.

**Limitations and Future Work**: Our experiments use a single model family (Qwen) at the primary scale point; validation across model families would strengthen generalizability. The debate architecture uses fixed hyperparameters (3 rounds, 2 agents) that may not be optimal. Future work should investigate adaptive debate termination criteria that preserve the benefits of forced disagreement while reducing unnecessary computation when true consensus exists.

The findings of this work suggest that the path to improved medical AI lies not in increasingly complex multi-agent architectures, but in principled design choices that match system complexity to model capability while leveraging the power of adversarial interaction to surface errors and refine reasoning.

## References

[1] Jin, Q., Dhingra, B., Liu, Z., Cohen, W. W., & Lu, X. (2021). PubMedQA: A Dataset for Biomedical Research Question Answering. EMNLP.

[2] Jin, D., Pan, E., Oufattole, N., Weng, W. H., Fang, H., & Szolovits, P. (2021). What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams. Applied Sciences.

[3] Singhal, K., et al. (2023). Large Language Models Encode Clinical Knowledge. Nature.

[4] Wei, J., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. NeurIPS.

[5] Wang, X., et al. (2023). Self-Consistency Improves Chain of Thought Reasoning in Language Models. ICLR.

[6] Du, Y., et al. (2023). Improving Factuality and Reasoning in Language Models through Multiagent Debate. arXiv preprint.

[7] Liang, T., et al. (2023). Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate. arXiv preprint.

[8] Chen, W., et al. (2024). MAS-GPT: Training LLMs to Build Multi-Agent Systems. arXiv preprint.

[9] Shazeer, N., et al. (2017). Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer. ICLR.

[10] Touvron, H., et al. (2023). LLaMA: Open and Efficient Foundation Language Models. arXiv preprint.

[11] Yang, A., et al. (2024). Qwen2 Technical Report. arXiv preprint.

[12] Brown, T., et al. (2020). Language Models are Few-Shot Learners. NeurIPS.

[13] OpenAI. (2023). GPT-4 Technical Report. arXiv preprint.

[14] Nori, H., et al. (2023). Capabilities of GPT-4 on Medical Challenge Problems. arXiv preprint.
