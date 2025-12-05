# Clinical MAS Planner

**Multi-Agent Diagnostic Reasoning System for Clinical Decision Support**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **⚠️ EDUCATIONAL USE ONLY**
> This is a research prototype for academic purposes only. **NOT** intended for clinical use, medical diagnosis, or patient care. Do not use this system to make medical decisions.

---

## 🚀 Quick Start

**System is ready to run!** See [`CURRENT_STATUS.md`](CURRENT_STATUS.md) for current setup status.

**Run evaluation now:**
```bash
python scripts/run_baseline_comparison.py --n 10
```

**Documentation:**
- 📋 [`CURRENT_STATUS.md`](CURRENT_STATUS.md) - What's ready and how to run
- 🔧 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) - Common issues and solutions
- 📖 [`READY_TO_RUN.md`](READY_TO_RUN.md) - Detailed setup guide
- 🪟 [`INSTALL_OLLAMA_WINDOWS.md`](INSTALL_OLLAMA_WINDOWS.md) - Ollama installation

---

## Overview

Clinical MAS Planner is an adaptive multi-agent diagnostic reasoning system inspired by [MAS-GPT](https://arxiv.org/abs/2305.15334). It orchestrates specialized AI agents to collaboratively analyze clinical cases and produce structured differential diagnoses.

### Key Features

- **Adaptive Specialist Selection**: Intelligently selects Top-K relevant medical specialties for each case
- **Fixed Specialty Catalog**: Prevents hallucination with a curated list of 30+ medical/surgical specialties
- **Structured Reasoning**: JSON-based agent outputs with explicit evidence, probabilities, and discriminators
- **Deterministic & Bounded**: Configurable budgets, temperature control, and reproducible execution
- **MedQA Evaluation**: Built-in evaluation harness for USMLE-style questions
- **Production-Ready**: FastAPI REST API, CLI, Docker support, and comprehensive logging

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Clinical Case Input                     │
│           (Question + Optional Multiple Choice)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    1. PLANNER AGENT                         │
│  • Triage (ER / Pediatrics / Family Medicine)               │
│  • Enumerate & Score ALL specialties from catalog           │
│  • Select Top-5 specialties (max coverage, min redundancy)  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                2. SPECIALIST AGENTS (Top-5)                 │
│  Each specialist produces:                                  │
│  • Differential diagnosis (up to 3 diagnoses)               │
│  • Probabilities (sum ≤ 1.0)                                │
│  • Evidence for/against each diagnosis                      │
│  • Discriminating tests/findings                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. AGGREGATOR AGENT                        │
│  • Merge specialist reports                                 │
│  • Resolve conflicts                                        │
│  • Produce final answer + ordered differential              │
│  • Flag warnings                                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Final Decision                           │
│           (Diagnosis + Justification + Traces)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip
- **Option A**: API key for OpenAI or Anthropic
- **Option B**: Local LLM setup (Ollama, llama.cpp, or vLLM) - **No API costs!**

> 📖 **Detailed Setup Guide**: See [SETUP_GUIDE.md](SETUP_GUIDE.md) for:
> - Downloading the full MedQA dataset (~12,000 questions)
> - Setting up local LLMs (Ollama recommended)
> - Model recommendations and cost comparison

### Setup

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/clinical-mas-planner.git
cd clinical-mas-planner
```

2. **Install dependencies**:

Using Poetry (recommended):
```bash
poetry install
```

Or using pip:
```bash
pip install -r requirements.txt  # (generate from poetry if needed)
```

3. **Configure environment**:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. **Verify installation**:

```bash
poetry run pytest -q
```

---

## Quick Start

### CLI Usage

**Run a single case**:

```bash
poetry run mas run \
  --question "A 65-year-old man presents with chest pain radiating to the left arm, diaphoresis, and nausea." \
  --options "A. GERD||B. Acute MI||C. PE||D. MSK pain"
```

**Run planner only**:

```bash
poetry run mas plan --question "Patient with acute chest pain"
```

**Evaluate on MedQA subset**:

```bash
poetry run mas eval --config configs/eval_medqa.yaml --n 100
```

### API Usage

**Start the server**:

```bash
poetry run mas serve --port 8000
```

**API Endpoints**:

- `POST /run` - Run complete case
- `POST /plan` - Run planner only
- `POST /consult` - Run specialist consultations
- `POST /aggregate` - Aggregate specialist reports
- `POST /eval/medqa` - Run MedQA evaluation

**Example API call**:

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "65yo man with chest pain radiating to arm",
    "options": ["A. GERD", "B. MI", "C. PE", "D. MSK"]
  }'
```

API documentation: `http://localhost:8000/docs`

### Docker Usage

**Build and run**:

```bash
cd docker
docker-compose up --build
```

Access API at `http://localhost:8000`

---

## Configuration

Configuration is managed via YAML files in `configs/`:

**`configs/default.yaml`**:

```yaml
model: "gpt-4o-mini"
provider: "openai"
temperature: 0.3
max_output_tokens: 800

planner:
  top_k: 5
  emergency_red_flags: ["syncope", "unstable", "chest pain"]

budgets:
  max_agents_total: 10
  max_specialists: 5
  max_retries: 1

logging:
  traces_dir: "runs"
  backend: "jsonl"
```

Override via environment variables or custom YAML files.

---

## Specialty Catalog

The system uses a **fixed catalog** of 30+ specialties to prevent hallucination:

### Generalists
- Emergency Medicine
- Pediatrics
- Family/Internal Medicine

### Medical Specialties
- Cardiology, Neurology, Psychiatry, Dermatology, Ophthalmology
- ENT, OB/GYN, Endocrinology, Gastroenterology, Hematology
- Infectious Disease, Nephrology, Oncology, Pulmonology, Rheumatology
- Geriatrics, Allergy/Immunology, Sleep Medicine, Urology, Sports Medicine

### Surgical Specialties
- General Surgery, Orthopedic Surgery, Vascular Surgery
- Plastic Surgery, Thoracic Surgery

Each specialty has metadata:
- `emergency_weight`, `pediatric_weight`, `adult_weight`
- `procedural_signal`
- `keywords`

See `src/catalog.py` for full definitions.

---

## Prompts

Agent prompts are stored in `src/prompts/`:

### Planner Prompt (`planner.txt`)

```
You are a Clinical Generalist Planner.

Tasks:
1. Choose triage generalist (ER / Pediatrics / Family Medicine)
2. Score ALL specialties from the fixed catalog
3. Select Top-5 specialties maximizing coverage

Output: JSON matching PlannerResult schema
```

### Specialist Prompt (`specialist.txt`)

```
You are a {specialty_display_name} Specialist.

Task: Produce up to 3 differential diagnoses with:
- Probability (0-1, sum ≤ 1)
- Evidence for/against
- Discriminating tests

Output: JSON matching SpecialistReport schema
```

### Aggregator Prompt (`aggregator.txt`)

```
You are a Generalist Aggregator.

Task: Merge specialist reports into:
- Final answer
- Ordered differential
- Justification
- Warnings

Output: JSON matching FinalDecision schema
```

See full prompts in `src/prompts/`.

---

## Evaluation

### MedQA Integration

Evaluate on MedQA-USMLE questions:

```bash
poetry run mas eval --config configs/eval_medqa.yaml --n 100
```

**Output**:
- Accuracy: % correct
- Avg latency per case
- Avg token usage
- Trace files for qualitative analysis

**Mock Data**: If MedQA dataset not available, uses built-in mock samples for testing.

### Traces

All executions are logged to `runs/` as JSONL files:

```json
{
  "trace_id": "uuid",
  "question": "...",
  "planner_trace": {...},
  "specialist_traces": [{...}, {...}],
  "aggregator_trace": {...},
  "final_decision": {...},
  "is_correct": true,
  "total_latency_seconds": 12.3
}
```

**Export traces**:

```bash
python scripts/export_traces.py runs/medqa_eval --csv results.csv --summary summary.json
```

---

## Development

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test file
poetry run pytest tests/test_planner.py -v

# With coverage
poetry run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type checking
poetry run mypy src/
```

### Adding a New Specialty

1. Edit `src/catalog.py`
2. Add to `SPECIALTY_CATALOG` with metadata
3. Run tests: `pytest tests/test_catalog.py`

---

## Safety & Ethics

### Guardrails

The system includes safety checks (see `src/safety.py`):

- **PHI Detection**: Basic heuristics for SSN, MRN, emails, phone numbers
- **Specialty Validation**: Rejects hallucinated specialties not in catalog
- **Probability Validation**: Ensures probabilities sum to ≤ 1.0
- **Disclaimer**: Displayed on all CLI/API interactions

### Limitations

- **Research Prototype**: Not validated for clinical use
- **No Real-Time Data**: Does not access patient records or real-time labs
- **No Retrieval**: Does not query PubMed or medical databases (future work)
- **Limited Scope**: Optimized for USMLE-style questions, not complex real-world cases

---

## Project Structure

```
clinical-mas-planner/
├── src/
│   ├── app.py                 # FastAPI + CLI entry point
│   ├── config.py              # Configuration management
│   ├── catalog.py             # Fixed specialty catalog
│   ├── schemas.py             # Pydantic models
│   ├── llm_client.py          # LLM abstraction (OpenAI/Anthropic/Mock)
│   ├── planner.py             # Planner agent
│   ├── specialists.py         # Specialist agents
│   ├── aggregator.py          # Aggregator agent
│   ├── orchestration.py       # Execution coordinator
│   ├── medqa.py               # MedQA evaluation harness
│   ├── logging_utils.py       # Trace storage
│   ├── safety.py              # Safety guardrails
│   └── prompts/               # Agent prompt templates
├── tests/                     # Pytest test suite
├── configs/                   # YAML configuration files
├── scripts/                   # Utility scripts
├── docker/                    # Dockerfile & docker-compose
├── runs/                      # Output traces (created at runtime)
├── pyproject.toml             # Poetry dependencies
├── README.md                  # This file
└── LICENSE                    # MIT License
```

---

## Future Work

### Near-Term Enhancements

- [ ] **Retrieval Augmentation**: Integrate PubMed abstracts or UpToDate snippets
- [ ] **Concurrency**: Run specialist agents in parallel (asyncio)
- [ ] **SQLite Backend**: Structured trace storage with query support
- [ ] **Streamlit Viewer**: Interactive trace exploration UI
- [ ] **Ablation Studies**: Compare enumerate+select vs direct Top-5 selection

### Research Directions

- [ ] **Multi-Turn Dialogue**: Iterative questioning and refinement
- [ ] **Uncertainty Quantification**: Confidence intervals on diagnoses
- [ ] **Explainability**: Natural language justifications for specialist selection
- [ ] **Human-in-the-Loop**: Interactive specialist selection and feedback
- [ ] **Multi-Modal Input**: Imaging, ECG, lab results

### Publication Targets

- Academic conferences: MLHC, AMIA, NeurIPS (Health)
- Journals: JAMIA, npj Digital Medicine, NEJM AI
- Focus: Novel multi-agent architecture, specialty selection strategies, ablation studies

---

## Troubleshooting

### Common Issues

**Import errors**:
```bash
# Ensure you're in the project root and using Poetry
poetry install
poetry shell
```

**API key errors**:
```bash
# Check .env file
cat .env | grep API_KEY

# Or set directly
export OPENAI_API_KEY="your-key"
```

**JSON parsing errors**:
- Check `runs/` for trace files with error details
- Enable `save_full_prompts: true` in config for debugging
- Use `provider: mock` for testing without API calls

**Tests failing**:
```bash
# Reset config between tests
poetry run pytest --cache-clear
```

---

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## Citation

If you use this work in your research, please cite:

```bibtex
@software{clinical_mas_planner,
  title = {Clinical MAS Planner: Multi-Agent Diagnostic Reasoning System},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/clinical-mas-planner}
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

For questions or collaboration:

- GitHub Issues: [https://github.com/yourusername/clinical-mas-planner/issues](https://github.com/yourusername/clinical-mas-planner/issues)
- Email: your.email@example.com

---

**Remember**: This is an educational tool. Always consult qualified healthcare professionals for medical advice.
