# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- Poetry 1.7+
- Git
- OpenAI API key

## Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd code-review-agentic-framework
```

### 2. Install Dependencies

```bash
# Using Makefile
make install

# Or directly with Poetry
poetry install
```

### 3. Install Optional Analysis Tools

```bash
# For full functionality
make install-tools

# Or
poetry install --with tools
```

### 4. Setup Environment

```bash
# Copy example env file
make setup

# Or manually
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-key-here
```

## Basic Usage

### Run a Code Review

```bash
poetry run code-review review \
  --pr-id "123" \
  --title "Add authentication" \
  --language python \
  --multi-agent \
  /path/to/your/repo
```

Output:
- Console: Summary with findings by severity
- File: `review_123.md` (markdown review comment)
- JSON: Optional via `--output results.json`

### Collect Real Dataset from GitHub

```bash
# Set your GitHub token
export GITHUB_TOKEN=ghp_your_token_here

# Collect balanced dataset (5 repos, ~5 PRs each)
make collect-dataset

# List available repositories
make list-repos
```

This will:
- ✅ Collect real merged PRs from curated Python repos
- ✅ Filter for appropriate size (50-500 lines)
- ✅ Balance across categories (security, bugfix, feature, refactor)
- ✅ Extract ground truth from review comments

### Run Evaluation

```bash
# Run evaluation on collected dataset
poetry run code-review evaluate \
  --system multi_agent \
  /path/to/repo
```

### Compare Systems

```bash
poetry run code-review compare \
  ./eval/results/evaluation_single_agent.json \
  ./eval/results/evaluation_multi_agent.json \
  --latex thesis_results.tex
```

## Development

### Run Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
poetry run pytest tests/unit/test_models.py -v
```

### Code Quality

```bash
# Lint
make lint

# Format
make format

# All checks
make check
```

## Project Structure

```
.
├── agents/          # Agent implementations
├── domain/          # Data models
├── tools/           # Tool integrations
├── flows/           # Orchestration
├── eval/            # Evaluation framework
├── app/             # CLI & config
├── prompts/         # Versioned prompts
└── tests/           # Test suites
```

## Configuration

Key settings in `.env`:

```env
# Required
OPENAI_API_KEY=your-key

# Model settings (for reproducibility)
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.0
OPENAI_SEED=42

# Review constraints
MAX_NITS_PER_REVIEW=5
MAX_PATCH_LINES=10

# Evaluation
SEED_FOR_EXPERIMENTS=42
```

## Common Tasks

### Add a Ground Truth Label

Edit `eval/dataset/ground_truth.json`:

```json
[
  {
    "pr_id": "001",
    "important_issues": [
      "SQL injection in auth.py",
      "Missing input validation"
    ],
    "false_positive_tolerance": 3,
    "labeler_id": "expert_1"
  }
]
```

### View Results

```bash
# Review results stored in:
./eval/results/<system_type>/<pr_id>.json

# Evaluation summaries:
./eval/results/evaluation_<system_type>.json

# Review comments:
review_<pr_id>.md
```

### Debug Issues

Check logs:

```bash
# View logs
tail -f logs/app_*.json

# Search by correlation ID
grep "correlation_id" logs/app_*.json
```

## Next Steps

1. **Read Documentation**
   - [README_DETAILED.md](README_DETAILED.md) - Complete documentation
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
   - [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

2. **Try Demo**
   ```bash
   make run-demo
   ```

3. **Prepare Dataset**
   - Collect 20-30 PRs
   - Create ground truth labels (2+ experts)
   - Calculate Cohen's kappa for inter-rater reliability

4. **Run Experiments**
   - Run both single-agent and multi-agent reviews
   - Calculate metrics
   - Perform statistical tests
   - Export LaTeX tables for thesis

## Troubleshooting

### "Tool not available" Error

```bash
# Check which tools are installed
poetry run code-review review --help

# Install missing tools
pip install ruff semgrep bandit
npm install -g eslint
```

### "API Key not found"

Make sure `.env` exists and contains:
```env
OPENAI_API_KEY=sk-...
```

### Import Errors

```bash
# Reinstall dependencies
poetry install --no-cache
```

### Test Failures

```bash
# Run specific test with verbose output
poetry run pytest tests/unit/test_models.py -vv

# Check test dependencies
poetry install --with dev
```

## Support

- **Issues**: GitHub Issues
- **Questions**: Open issue with `question` label
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT - see [LICENSE](LICENSE)

