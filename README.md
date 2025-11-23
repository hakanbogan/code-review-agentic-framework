# Multi-Agent Code Review Framework

A master's thesis project implementing a multi-agent system for automated code review using CrewAI.

## Quick Start

```bash
# Install dependencies
poetry install

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run a review
poetry run code-review review \
  --pr-id "123" \
  --title "Your PR Title" \
  --language python \
  /path/to/repo
```

## Features

- 🤖 **Multi-Agent System**: Specialized agents for security, style, and consistency
- 🔍 **Evidence-Based**: All findings require tool output or code references
- 📊 **Evaluation Framework**: Statistical analysis and thesis-ready LaTeX export
- ⚡ **Tool Integration**: Git, Ruff, ESLint, Semgrep, Bandit
- 🎯 **Actionable**: Auto-patches for simple fixes, detailed guidance for complex issues

## Documentation

See [README_DETAILED.md](README_DETAILED.md) for complete documentation.

## Architecture

```
Context Builder → [CCA || SR || SFR] → Revision Proposer → Supervisor → Final Review
```

## Research Goals

Evaluate whether multi-agent code review with tool integration achieves:
- Higher actionability (more patches/clear fixes)
- Lower noise (fewer false positives)
- Better coverage (detect more critical issues)

Compared to single-agent LLM baselines.

## License

MIT
