# Multi-Agent Code Review Framework

A master's thesis project implementing a multi-agent system for automated code review using CrewAI.

## Quick Start

```bash
# Install dependencies
poetry install

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   - OPENAI_API_KEY (required)
#   - GITHUB_TOKEN (required for dataset collection)

# Run a review (local path)
poetry run python -m app.cli review \
  --pr-id "123" \
  --title "Your PR Title" \
  --language python \
  /path/to/repo

# Or use GitHub URL directly
poetry run python -m app.cli review \
  --pr-id "14468" \
  --title "Add upload file size limit" \
  --language python \
  "https://github.com/fastapi/fastapi"
```

## Features

- 🤖 **Multi-Agent System**: 7 specialized agents (context, security, style, logic, performance, docs, tests)
- 🔍 **Evidence-Based**: All findings require tool output or code references
- 📊 **Evaluation Framework**: Statistical analysis and thesis-ready LaTeX export
- ⚡ **Tool Integration**: Git, Ruff, ESLint, Semgrep, Bandit, Coverage.py
- 🎯 **Actionable**: Auto-patches for simple fixes, detailed guidance for complex issues

## System Architecture

```
┌─────────────┐
│   CLI       │  poetry run python -m app.cli review ...
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ReviewFlow  │  Orchestrates the entire process
└──────┬──────┘
       │
       ├─► 1️⃣ Context Builder (Git diff + Tools)
       │
       ├─► 2️⃣ Analysis Agents (Parallel)
       │    ├─ ChangeContextAnalyst (LLM)
       │    ├─ SecurityReviewer (Tool)
       │    ├─ StyleFormatReviewer (Tool)
       │    ├─ LogicBugReviewer (LLM)
       │    ├─ PerformanceReviewer (LLM)
       │    ├─ DocumentationReviewer (LLM)
       │    └─ TestCoverageReviewer (Hybrid)
       │
       ├─► 3️⃣ RevisionProposer (Patch generation)
       │
       ├─► 4️⃣ Supervisor (Consolidation)
       │
       └─► 5️⃣ PRReviewResult (Final output)
```

## System Flow

### Phase 1: Context Building
- Extract git diff between PR branch and base branch
- Run language-specific tools (Ruff, ESLint)
- Run security tools (Semgrep, Bandit)
- Build `PRContext` with all information

### Phase 2: Analysis Agents
7 specialized agents analyze the PR in parallel:
- **ChangeContextAnalyst**: Checks PR title/description consistency
- **SecurityReviewer**: Finds security vulnerabilities
- **StyleFormatReviewer**: Detects style/formatting issues
- **LogicBugReviewer**: Identifies logical errors
- **PerformanceReviewer**: Finds performance bottlenecks
- **DocumentationReviewer**: Checks documentation quality
- **TestCoverageReviewer**: Analyzes test coverage

### Phase 3: Revision Proposer
Generates patches for findings that need fixes.

### Phase 4: Supervisor
- Consolidates all findings
- Removes duplicates
- Prioritizes by severity
- Applies nit limits

### Phase 5: Result Synthesis
Creates final `PRReviewResult` with:
- Findings grouped by severity
- Markdown review comment
- JSON output for evaluation
- Metrics (time, cost, token usage)

## Project Structure

```
.
├── agents/              # Agent implementations
│   ├── base.py         # Base agent class
│   ├── change_context_analyst.py
│   ├── security_reviewer.py
│   ├── style_reviewer.py
│   ├── logic_reviewer.py
│   ├── performance_reviewer.py
│   ├── documentation_reviewer.py
│   ├── test_reviewer.py
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
│   └── dataset/
├── app/                # Application layer
│   ├── cli.py          # CLI interface
│   ├── config.py       # Settings
│   └── logging.py      # Structured logging
├── prompts/            # Versioned prompts
│   ├── cca/
│   ├── security/
│   ├── style/
│   └── ...
└── reviews/            # Review results storage
```

## Configuration

Key settings in `.env`:

```env
# Required
OPENAI_API_KEY=sk-proj-...
GITHUB_TOKEN=ghp_...

# LLM Settings
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

See `.env.example` for all available configuration options.

## Dataset Collection

Collect real PRs from GitHub for evaluation:

```bash
# Configure GitHub token in .env
# GITHUB_TOKEN=ghp_your_token_here

# Collect balanced dataset
poetry run python eval/dataset/collect_dataset.py collect \
  --repos 5 \
  --prs-per-repo 5 \
  --balanced
```

See [eval/dataset/README.md](eval/dataset/README.md) for detailed instructions.

## Evaluation

Run evaluation on collected dataset:

```bash
# Single-agent baseline
poetry run python -m app.cli evaluate \
  --system single_agent \
  /path/to/repo

# Multi-agent (proposed)
poetry run python -m app.cli evaluate \
  --system multi_agent \
  /path/to/repo

# Compare systems
poetry run python -m app.cli compare \
  ./eval/results/evaluation_single_agent.json \
  ./eval/results/evaluation_multi_agent.json \
  --latex thesis_results.tex
```

## Research Goals

Evaluate whether multi-agent code review with tool integration achieves:
- **Higher actionability** (more patches/clear fixes)
- **Lower noise** (fewer false positives)
- **Better coverage** (detect more critical issues)

Compared to single-agent LLM baselines.

## Design Principles

- **SOLID**: Single responsibility, dependency injection, clear abstractions
- **DRY**: Shared base classes, reusable components
- **Evidence-Based**: Every finding must cite tool output or code reference
- **Reproducible**: Deterministic settings, versioned prompts, pinned tools

## Development

```bash
# Run tests
poetry run pytest

# Lint
poetry run ruff check .

# Format
poetry run ruff format .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT
