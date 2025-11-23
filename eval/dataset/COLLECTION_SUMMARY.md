# Dataset Collection System - Summary

## 🎯 Purpose

Automated collection of real PR data from GitHub for evaluation of the multi-agent code review framework.

## 🏗️ Architecture

### Components

1. **GitHubPRCollector** (`github_collector.py`)
   - GitHub API client with rate limiting
   - Fetches PRs, files, commits, reviews
   - Handles authentication and errors

2. **PRSelector** (`pr_selector.py`)
   - Filters PRs by criteria (size, reviews, language)
   - Categorizes PRs (security, bugfix, feature, refactor)
   - Balances dataset across categories
   - Calculates complexity scores

3. **DataTransformer** (`data_transformer.py`)
   - Transforms GitHub API responses to our domain models
   - Extracts ground truth from review comments
   - Calculates file statistics

4. **Collection Script** (`collect_dataset.py`)
   - CLI interface with Typer + Rich
   - Orchestrates collection process
   - Saves results in our format

## 📊 Collection Criteria

### Repository Selection
- **Curated list**: 12 high-quality Python projects
- Popular frameworks: Flask, Django, FastAPI
- Data science: pandas, scikit-learn, numpy
- Tools: pytest, poetry, requests

### PR Filtering

**Must have:**
- ✅ Merged (not just closed)
- ✅ ≥1 Python file changed
- ✅ ≥1 review comment
- ✅ 50-500 lines changed (default)
- ✅ 1-15 files changed

**Excluded:**
- ❌ Draft/unmerged PRs
- ❌ Too large (>500 lines)
- ❌ Too small (<50 lines)
- ❌ Only test files
- ❌ No reviews

### Categorization Logic

```python
# Security: keywords in title/labels
"security", "vulnerability", "cve" → security

# Bugfix: fix-related keywords
"fix", "bug", "issue", "error" → bugfix

# Feature: new functionality
"add", "implement", "feature", "new" → feature

# Refactor: restructuring
"refactor", "cleanup", "reorganize" → refactor

# Test: only test files changed
all files in test/ → test
```

### Balanced Selection

Collects equal numbers from each category:
- 🔴 Security (highest priority)
- 🟠 Bugfix
- 🟢 Feature
- 🔵 Refactor

## 🚀 Usage

### Quick Start

```bash
# 1. Get GitHub token
# https://github.com/settings/tokens
# Scope: public_repo

# 2. Set token
export GITHUB_TOKEN=ghp_...

# 3. Collect
make collect-dataset
```

### Custom Collection

```bash
poetry run python eval/dataset/collect_dataset.py \
  --repos 10 \              # Number of repos
  --prs-per-repo 5 \        # PRs per repo
  --min-lines 100 \         # Min lines changed
  --max-lines 1000 \        # Max lines changed
  --balanced                # Balance categories
```

## 📁 Output Format

### pr_list.json
```json
[
  {
    "pr_id": "12345",
    "repository": "pallets/flask",
    "title": "Fix XSS vulnerability",
    "files_changed": 3,
    "lines_added": 45,
    "lines_deleted": 12,
    ...
  }
]
```

### ground_truth.json
```json
[
  {
    "pr_id": "12345",
    "important_issues": [
      "XSS vulnerability @ templates.py:142",
      "Missing validation @ utils.py:67"
    ],
    "labeler_id": "github_reviewers",
    ...
  }
]
```

## 🔬 Ground Truth Extraction

Automatically extracts from review comments:

**Heuristics for important issues:**
- Security keywords: "security", "vulnerability", "injection", "xss", "sql"
- Bug keywords: "bug", "error", "crash", "fail"
- Severity markers: "breaking", "critical", "must fix"

**Format:**
```
<comment_snippet>... @ <file>:<line>
```

## 📈 Quality Metrics

### Complexity Score (0-100)

```python
score = 0
score += min(40, total_lines / 10)          # Lines changed
score += min(30, files_changed * 5)         # Files
score += min(20, commits * 2)               # Commits
score += python_percentage * 10             # Python %
```

### Statistics Tracked

- Total PRs collected
- PRs per category
- Lines changed distribution
- Files changed distribution
- Complexity distribution

## ⚡ Rate Limiting

GitHub API limits:
- **5,000 requests/hour** (authenticated)
- **60 requests/hour** (unauthenticated)

Mitigation:
- ✅ Check rate limit before start
- ✅ 1 second delay between requests
- ✅ Show remaining calls
- ✅ Graceful failure with reset time

## 🎓 Academic Rigor

### Reproducibility
- **Deterministic**: Same repos, same criteria
- **Versioned**: Collection config saved
- **Traceable**: Full metadata preserved

### Validity
- **Representative**: Diverse real-world PRs
- **Balanced**: Multiple categories
- **Sized appropriately**: Not too large/small
- **Reviewed**: Real expert feedback

### Post-Collection Steps

1. **Manual Review**: Check PR quality
2. **Expert Labeling**: 2+ independent reviewers
3. **Inter-rater Reliability**: Calculate Cohen's κ (target >0.6)
4. **Refinement**: Update ground truth based on expert input

## 📝 Example Workflow

```bash
# 1. Collect
export GITHUB_TOKEN=ghp_...
make collect-dataset

# 2. Review summary
cat eval/dataset/collection_summary.json

# 3. Inspect PRs
cat eval/dataset/pr_list.json | jq '.[] | {id: .pr_id, title: .title, category: .category}'

# 4. Check ground truth
cat eval/dataset/ground_truth.json | jq '.[] | {pr: .pr_id, issues: .important_issues | length}'

# 5. Manual refinement
# Edit ground_truth.json as needed

# 6. Run evaluation
poetry run code-review evaluate --system multi_agent /path/to/repo
```

## 🛠️ Extending

### Add New Repositories

Edit `collect_dataset.py`:

```python
CURATED_REPOS = [
    # Add your repos
    ("your-org", "your-repo"),
    ...
]
```

### Custom Filtering

Modify `PRSelector` in `pr_selector.py`:

```python
def custom_filter(self, pr, files):
    # Your custom logic
    return meets_criteria
```

### Enhanced Ground Truth

Modify `DataTransformer.extract_ground_truth_from_reviews()`:

```python
# Add custom extraction logic
if your_condition:
    important_issues.append(issue)
```

## ⚠️ Limitations

1. **API-based**: Limited to public repos
2. **Heuristic GT**: Ground truth extraction is automated (needs manual validation)
3. **Language-specific**: Only Python PRs
4. **Size bias**: Excludes very large/small PRs
5. **Review bias**: Only PRs with review comments

## 🎯 Best Practices

1. ✅ **Start small**: 20-30 PRs first
2. ✅ **Check quality**: Manual review before evaluation
3. ✅ **Expert validation**: Get 2+ reviewers
4. ✅ **Calculate κ**: Ensure agreement >0.6
5. ✅ **Document**: Keep selection notes
6. ✅ **Version control**: Track collection config

## 📊 Expected Results

From 5 repos × 5 PRs each:
- **Total**: ~25 PRs
- **Security**: 3-5 PRs
- **Bugfix**: 5-8 PRs
- **Feature**: 5-8 PRs
- **Refactor**: 3-5 PRs
- **Ground Truth**: ~23 PRs (some may have no review comments)

## 🏆 Advantages Over Manual Collection

1. **Faster**: Automated vs manual search
2. **Consistent**: Same criteria applied
3. **Traceable**: Full provenance
4. **Scalable**: Easy to collect more
5. **Reproducible**: Others can replicate
6. **Balanced**: Automatic category distribution

---

**Status**: ✅ Production-ready, academically rigorous, extensible

