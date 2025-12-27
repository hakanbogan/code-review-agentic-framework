# Multi-Agent Code Review Framework

A project implementing a multi-agent system for automated code review using CrewAI.

## Quick Start

```bash
# Install dependencies
poetry install

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   - LLM_PROVIDER (openai or anthropic)
#   - OPENAI_API_KEY (required if LLM_PROVIDER=openai)
#   - ANTHROPIC_API_KEY (required if LLM_PROVIDER=anthropic)
#   - GITHUB_TOKEN (required for dataset collection)

# Run a review (local path)
poetry run python -m app.cli review \
  --pr-id "123" \
  --title "Your PR Title" \
  --language python \
  /path/to/repo

# Or use GitHub URL directly (title/description auto-fetched)
poetry run python -m app.cli review \
  --pr-id "14468" \
  --language python \
  "https://github.com/fastapi/fastapi"

# Supported languages: python, javascript, typescript, java, go, rust, cpp, csharp, ruby, php
```

## Features

- 🤖 **Multi-Agent System**: 7 specialized agents (context, security, style, logic, performance, docs, tests)
- 🔍 **Evidence-Based**: All findings require tool output or code references
- 📊 **Evaluation Framework**: Statistical analysis and LaTeX export
- ⚡ **Tool Integration**: Git, Ruff (Python), ESLint (JS/TS), Semgrep, Bandit, Coverage.py
- 🎯 **Actionable**: Auto-patches for simple fixes, detailed guidance for complex issues
- 💰 **Cost Tracking**: Real-time token usage and cost estimation for OpenAI and Anthropic
- 🌐 **Multi-Provider**: Support for both OpenAI and Anthropic LLMs

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
- Run language-specific tools (automatically selected based on `--language` parameter):
  - **Python**: Ruff (linting), Bandit (security)
  - **JavaScript/TypeScript**: ESLint (linting)
  - **All languages**: Semgrep (security, language-agnostic)
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
- Real-time cost estimation based on provider and model

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
│   ├── models.py       # PRMetadata, Finding, Language enum, LLMProvider enum
│   └── __init__.py
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
# LLM Provider Selection
LLM_PROVIDER=anthropic  # or "openai"

# OpenAI Configuration (if LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.0
OPENAI_SEED=42

# Anthropic Configuration (if LLM_PROVIDER=anthropic)
# Recommended: claude-3-5-haiku-20241022 (best price-performance)
# Alternatives: claude-3-5-sonnet-20241022 (balanced), claude-3-opus-20240229 (highest quality)
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022

# GitHub (required for dataset collection and PR fetching)
GITHUB_TOKEN=ghp_...

# Review Configuration
MAX_NITS_PER_REVIEW=5
MAX_PATCH_LINES=10
ENABLE_PARALLEL_AGENTS=true

# Evaluation
EVAL_DATASET_PATH=./eval/dataset
EVAL_RESULTS_PATH=./eval/results
SEED_FOR_EXPERIMENTS=42
```

### LLM Provider Selection

The framework supports both **OpenAI** and **Anthropic** LLM providers:

- **OpenAI**: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
- **Anthropic**: 
  - **Claude 3.5 Haiku** (recommended): Best price-performance ratio ($0.80-1.00/1M input, $4-5/1M output)
  - **Claude 3.5 Sonnet**: Balanced performance ($3/1M input, $15/1M output)
  - **Claude 3 Opus**: Highest quality ($15/1M input, $75/1M output)

Set `LLM_PROVIDER=anthropic` or `LLM_PROVIDER=openai` in your `.env` file.

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
# Evaluate using stored reviews (recommended)
poetry run python -m app.cli evaluate \
  --system multi_agent \
  --use-stored

# Evaluate specific PRs
poetry run python -m app.cli evaluate \
  --system multi_agent \
  --pr-ids "14468,2779" \
  --use-stored

# Re-run reviews and evaluate
poetry run python -m app.cli evaluate \
  --system single_agent \
  --rerun \
  --repo-path /path/to/repo

# Compare systems
poetry run python -m app.cli compare \
  ./eval/results/evaluation_single_agent.json \
  ./eval/results/evaluation_multi_agent.json \
  --latex results.tex
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
- **Type-Safe**: Enum-based language and provider selection
- **Cost-Aware**: Real-time token tracking and cost estimation

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
