# Dataset Collection Guide

## Overview

This directory contains tools for collecting real PR data from GitHub for evaluation purposes.

## Prerequisites

1. **GitHub Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Required scopes: `public_repo`
   - Copy the token

2. **Set Environment Variable**
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```

## Quick Start

### Collect Balanced Dataset (Recommended)

```bash
# Collect from 5 repos, ~5 PRs per repo, balanced across categories
poetry run python eval/dataset/collect_dataset.py \
  --repos 5 \
  --prs-per-repo 5 \
  --balanced
```

### Collect More PRs

```bash
# Collect from 10 repos, ~10 PRs per repo
poetry run python eval/dataset/collect_dataset.py \
  --repos 10 \
  --prs-per-repo 10
```

### List Available Repositories

```bash
poetry run python eval/dataset/collect_dataset.py list-repos
```

## Collection Criteria

### Repository Selection
- **Curated list** of high-quality Python projects
- Popular frameworks (Flask, Django, FastAPI)
- Data science tools (pandas, scikit-learn)
- Well-maintained with active reviews

### PR Filtering

**Must have:**
- ✅ Merged (not just closed)
- ✅ At least one Python file changed
- ✅ At least one review comment
- ✅ 50-500 lines changed (configurable)
- ✅ 1-15 files changed

**Excluded:**
- ❌ Draft PRs
- ❌ Too large (>500 lines)
- ❌ Too small (<50 lines)
- ❌ Only test files
- ❌ No reviews

### PR Categories

The collector categorizes PRs automatically:

1. **Security**: Fixes vulnerabilities, security issues
2. **Bugfix**: Bug fixes, error corrections
3. **Feature**: New features, enhancements
4. **Refactor**: Code restructuring, cleanup
5. **Test**: Test additions/modifications
6. **Other**: Everything else

## Output Files

### `pr_list.json`
Complete PR metadata in our format:

```json
[
  {
    "pr_id": "12345",
    "repository": "pallets/flask",
    "branch_source": "fix-security",
    "branch_target": "main",
    "title": "Fix XSS vulnerability in template rendering",
    "description": "...",
    "author": "contributor",
    "commit_messages": ["Fix XSS issue", "Add test"],
    "files_changed": 3,
    "lines_added": 45,
    "lines_deleted": 12,
    "language": "python"
  }
]
```

### `ground_truth.json`
Extracted important issues from reviews:

```json
[
  {
    "pr_id": "12345",
    "important_issues": [
      "XSS vulnerability in render_template @ templates.py:142",
      "Missing input validation @ utils.py:67"
    ],
    "false_positive_tolerance": 3,
    "labeler_id": "github_reviewers",
    "notes": "Extracted from 9 review comments"
  }
]
```

### `collection_summary.json`
Collection statistics:

```json
{
  "total_prs": 25,
  "total_ground_truth": 23,
  "repositories": ["pallets/flask", "django/django", ...],
  "filters": {
    "min_lines": 50,
    "max_lines": 500,
    "balanced": true
  }
}
```

## Manual Review & Refinement

After collection, manually review and refine:

### 1. Check PR Quality

```bash
# Review collected PRs
cat eval/dataset/pr_list.json | jq '.[] | {pr: .pr_id, title: .title, lines: (.lines_added + .lines_deleted)}'
```

### 2. Refine Ground Truth

Edit `ground_truth.json` to:
- ✅ Clarify important issues
- ✅ Remove false positives
- ✅ Add missing critical issues
- ✅ Update severity expectations

### 3. Add Expert Labels

For thesis validity, get 2+ experts to:
1. Review each PR independently
2. Mark important issues
3. Calculate Cohen's κ for inter-rater reliability

```python
from eval.metrics import cohens_kappa

# Compare two raters
kappa = cohens_kappa(rater_a, rater_b, num_categories=5)
print(f"Cohen's κ: {kappa:.3f}")  # Should be >0.6
```

## Rate Limits

GitHub API rate limits:
- **Authenticated**: 5,000 requests/hour
- **Per endpoint**: Various limits

The collector:
- ✅ Checks rate limit before starting
- ✅ Respects delays between requests
- ✅ Shows remaining calls

If you hit the limit:
```bash
# Check when limit resets
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
```

## Advanced Usage

### Custom Repository List

Edit `collect_dataset.py` and modify `CURATED_REPOS`:

```python
CURATED_REPOS = [
    ("your-org", "your-repo"),
    # Add more repos...
]
```

### Adjust Filters

```bash
poetry run python eval/dataset/collect_dataset.py \
  --min-lines 100 \        # Larger PRs
  --max-lines 1000 \       # Allow bigger changes
  --no-balanced            # Don't balance categories
```

## Troubleshooting

### "Rate limit exceeded"

Wait for limit to reset (shown in error message) or:
```bash
# Check current limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
```

### "No PRs found"

Try:
- Increase `max_lines` (some repos have larger PRs)
- Decrease `min_lines` (some repos have smaller PRs)
- Check if repo is active (recent PRs)

### "Token not found"

Make sure:
```bash
# Check token is set
echo $GITHUB_TOKEN

# Should output: ghp_...
```

## Best Practices

1. **Start small**: Collect 20-30 PRs first
2. **Manual review**: Check quality before evaluation
3. **Expert labeling**: Get 2+ independent reviewers
4. **Calculate κ**: Ensure inter-rater reliability >0.6
5. **Document**: Keep notes on selection criteria

## Example Workflow

```bash
# 1. Set token
export GITHUB_TOKEN=ghp_your_token

# 2. List available repos
poetry run python eval/dataset/collect_dataset.py list-repos

# 3. Collect dataset
poetry run python eval/dataset/collect_dataset.py --repos 5 --prs-per-repo 5

# 4. Review results
cat eval/dataset/collection_summary.json

# 5. Manual refinement
# Edit ground_truth.json as needed

# 6. Run evaluation
poetry run code-review evaluate --system multi_agent /path/to/repo
```

## Citation

If using this dataset collection methodology in research:

```bibtex
@misc{dataset-collection,
  title={Automated Dataset Collection for Code Review Evaluation},
  author={Your Name},
  year={2025},
  note={Part of Multi-Agent Code Review Framework}
}
```

