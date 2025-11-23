# Multi-Agent Code Review Framework

[![CI](https://github.com/yourusername/code-review-agentic-framework/workflows/CI/badge.svg)](https://github.com/yourusername/code-review-agentic-framework/actions)
[![codecov](https://codecov.io/gh/yourusername/code-review-agentic-framework/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/code-review-agentic-framework)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **Master's Thesis Project**: A multi-agent code review framework using CrewAI that analyzes pull requests and generates actionable, evidence-based review comments.

## Overview

This framework implements a coordinated team of specialized AI agents to perform comprehensive code reviews:

- **Change & Context Analyst (CCA)**: Analyzes PR changes for consistency with stated intentions
- **Security Reviewer (SR)**: Identifies security vulnerabilities using static analysis tools
- **Style & Format Reviewer (SFR)**: Consolidates linting and formatting issues
- **Revision Proposer (RP)**: Generates patches and fix suggestions
- **Supervisor**: Consolidates findings, removes duplicates, and enforces evidence requirements

### Key Features

- ✅ **Evidence-based findings**: Every issue must cite a tool output or code reference
- ✅ **Tool integration**: Git diff, Ruff, ESLint, Semgrep, Bandit, coverage
- ✅ **Noise reduction**: Weighted voting, nit limits, deduplication
- ✅ **Actionable output**: Auto-patches for simple fixes, detailed guidance for complex issues
- ✅ **Reproducible**: Deterministic LLM settings, pinned tool versions, seed control
- ✅ **Evaluation framework**: Metrics, statistical tests, LaTeX export for thesis

## Architecture

```
┌─────────────────┐
│  PR + Repo Path │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Builder │ ◄── Tools: git diff, ruff, eslint, semgrep, bandit
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Parallel Agent Analysis             │
│  ┌───────┐  ┌─────────┐  ┌────────┐       │
│  │  CCA  │  │   SR    │  │  SFR   │       │
│  └───┬───┘  └────┬────┘  └───┬────┘       │
└──────┼───────────┼───────────┼─────────────┘
       │           │           │
       └───────────┴───────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Revision        │
         │ Proposer (RP)   │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   Supervisor    │
         │  (QA Checker)   │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Final Review   │
         │   (Markdown)    │
         └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Poetry 1.7+
- Git
- (Optional) Ruff, ESLint, Semgrep, Bandit for full functionality

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/code-review-agentic-framework.git
cd code-review-agentic-framework
```

2. Install dependencies:
```bash
poetry install
```

3. Install optional analysis tools:
```bash
poetry install --with tools
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Verify installation:
```bash
poetry run code-review --help
```

## Usage

### Command-Line Interface

#### Review a Pull Request

```bash
poetry run code-review review \
  --pr-id "123" \
  --title "Add authentication" \
  --description "Implements JWT auth" \
  --language python \
  --multi-agent \
  /path/to/repo
```

#### Run Evaluation

```bash
# Prepare dataset
poetry run code-review init-dataset ./eval/dataset

# Run evaluation
poetry run code-review evaluate \
  --system multi_agent \
  /path/to/repo

# Compare systems
poetry run code-review compare \
  ./eval/results/evaluation_single_agent.json \
  ./eval/results/evaluation_multi_agent.json \
  --latex results_table.tex
```

### Python API

```python
from pathlib import Path
from app.config import get_settings
from domain import PRMetadata
from flows import ReviewFlow

# Initialize
settings = get_settings()
flow = ReviewFlow(settings)

# Create PR metadata
pr_metadata = PRMetadata(
    pr_id="123",
    repository="my-repo",
    branch_source="feature/auth",
    branch_target="main",
    title="Add authentication",
    author="developer",
    language="python",
)

# Run review
result = flow.run_multi_agent_review(
    pr_metadata=pr_metadata,
    repo_path=Path("/path/to/repo"),
)

# Access results
print(f"Found {len(result.findings)} issues")
print(result.final_comment_md)
```

## Project Structure

```
.
├── agents/              # Agent implementations
│   ├── base.py         # Base agent class
│   ├── change_context_analyst.py
│   ├── security_reviewer.py
│   ├── style_reviewer.py
│   ├── revision_proposer.py
│   └── supervisor.py
├── domain/             # Domain models (Pydantic)
│   └── models.py
├── tools/              # Analysis tool integrations
│   ├── base.py         # Tool base class
│   ├── git_diff.py
│   ├── linters.py      # Ruff, ESLint
│   ├── security.py     # Semgrep, Bandit
│   └── coverage.py
├── flows/              # Orchestration
│   ├── context_builder.py
│   └── review_flow.py
├── eval/               # Evaluation framework
│   ├── metrics/
│   │   ├── base.py
│   │   ├── core_metrics.py
│   │   ├── performance_metrics.py
│   │   └── statistical.py
│   ├── run_eval.py
│   └── dataset/
├── app/                # Application layer
│   ├── cli.py          # CLI interface
│   ├── config.py       # Settings
│   └── logging.py      # Structured logging
├── prompts/            # Versioned prompts
│   ├── cca/
│   ├── security/
│   ├── style/
│   ├── revision/
│   └── supervisor/
└── tests/
    ├── unit/
    └── e2e/
```

## Configuration

Key settings in `.env`:

```env
# LLM
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.0
OPENAI_SEED=42

# Review Configuration
MAX_NITS_PER_REVIEW=5
MAX_PATCH_LINES=10
ENABLE_PARALLEL_AGENTS=true

# Evaluation
EVAL_DATASET_PATH=./eval/dataset
EVAL_RESULTS_PATH=./eval/results
SEED_FOR_EXPERIMENTS=42
```

## Evaluation Methodology

### Metrics

1. **Actionability Rate**: Ratio of findings with patches or clear action items
2. **Noise Rate**: False positives / total findings
3. **Important Issue Coverage**: Detected critical issues / total critical issues (from ground truth)
4. **CTR/CL/SI Scores**: Thesis-specific metrics for change understanding, location accuracy, solution quality

### Statistical Tests

- **Chi-square test**: Compare proportion differences (actionability rates)
- **Wilcoxon test**: Paired sample comparison
- **Mann-Whitney U**: Independent sample comparison
- **Cohen's κ**: Inter-rater reliability for manual labeling

### Dataset Collection

**Collect real PRs from GitHub:**

```bash
# Set GitHub token (required)
export GITHUB_TOKEN=ghp_your_token_here

# Collect balanced dataset (recommended)
make collect-dataset

# Or collect larger dataset
make collect-dataset-large

# List available repositories
make list-repos

# Or use script directly with custom options
poetry run python eval/dataset/collect_dataset.py \
  --repos 5 \
  --prs-per-repo 5 \
  --min-lines 50 \
  --max-lines 500 \
  --balanced
```

**What it collects:**
- ✅ Merged PRs with reviews
- ✅ 50-500 lines changed
- ✅ Python files only
- ✅ Balanced across categories (security, bugfix, feature, refactor)
- ✅ Extracts ground truth from review comments

See [eval/dataset/README.md](eval/dataset/README.md) for detailed instructions.

### Dataset Format

Ground truth labels (`eval/dataset/ground_truth.json`):

```json
[
  {
    "pr_id": "001",
    "important_issues": [
      "SQL injection in auth.py line 42",
      "Missing input validation on API endpoint"
    ],
    "false_positive_tolerance": 3,
    "labeler_id": "expert_1",
    "notes": "Security-critical PR"
  }
]
```

## Development

### Running Tests

```bash
# All tests
poetry run pytest

# Unit tests only
poetry run pytest tests/unit/

# With coverage
poetry run pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Lint
poetry run ruff check .

# Format
poetry run ruff format .

# Type check
poetry run mypy .
```

### Adding a New Agent

1. Create agent class in `agents/`:
```python
from agents.base import BaseAgent
from domain import AgentRole

class MyAgent(BaseAgent):
    def __init__(self, settings):
        super().__init__(AgentRole.MY_AGENT, settings)
    
    def analyze(self, context):
        # Implementation
        pass
```

2. Add prompt template in `prompts/my_agent/v1.md`
3. Register in `flows/review_flow.py`
4. Add tests in `tests/unit/`

## Research & Thesis Integration

### Hypothesis

Multi-agent code review with tool integration and evidence requirements achieves:
- **Higher actionability** (↑ patches and clear fixes)
- **Lower noise** (↓ false positives)
- **Better coverage** (↑ detection of critical issues)

Compared to single-agent LLM-only baselines.

### Experimental Design

- **Systems**: Single-agent, Multi-agent, (optional) Tools-only
- **Dataset**: 20-30 real PRs from OSS projects
- **Evaluation**: Blind labeling by ≥2 experts, Cohen's κ for agreement
- **Analysis**: Statistical significance tests, effect size calculations

### LaTeX Export

```bash
poetry run code-review compare \
  baseline.json proposed.json \
  --latex results.tex

# Include in thesis:
\input{results.tex}
```

## License

MIT License - see [LICENSE](LICENSE)

## Citation

If you use this framework in your research, please cite:

```bibtex
@mastersthesis{yourname2025multiagent,
  title={Multi-Agent Code Review Framework with Evidence-Based Findings},
  author={Your Name},
  year={2025},
  school={Your University},
  type={Master's Thesis}
}
```

## Contributing

This is a thesis project with specific research goals. Contributions are welcome but should align with the research methodology. Please open an issue first to discuss proposed changes.

## Acknowledgments

- Built with [CrewAI](https://www.crewai.com/)
- Uses OpenAI GPT-4 for LLM capabilities
- Integrates Ruff, ESLint, Semgrep, and Bandit for static analysis

