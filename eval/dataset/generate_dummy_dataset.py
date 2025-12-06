"""Generate professional dummy dataset for code review evaluation."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Realistic data templates
REPOSITORIES = [
    "django/django",
    "scikit-learn/scikit-learn",
    "pandas-dev/pandas",
    "fastapi/fastapi",
    "flask/flask",
    "requests/requests",
    "numpy/numpy",
    "tensorflow/tensorflow",
    "pytorch/pytorch",
    "scipy/scipy",
]

AUTHORS = [
    "johndoe", "janesmit", "alexchen", "mariaperez", "davidkim",
    "sarahjones", "michaelwu", "emilywhite", "robertbrown", "lisawang",
    "tomsmith", "annalee", "kevinpatel", "rachelchen", "briankim",
]

# Bug fix templates
BUGFIX_TEMPLATES = [
    {
        "title": "Fix {issue} in {component}",
        "description": "This PR fixes a {issue_type} that occurs when {condition}.\n\nThe root cause was {root_cause}.\n\nChanges:\n- Fixed {fix_action}\n- Added test coverage for edge case\n- Updated error messages",
        "files": ["src/{component}.py", "tests/test_{component}.py"],
        "commits": ["Fix {issue} in {component}", "Add test coverage"],
    },
    {
        "title": "Resolve {issue_type} when {action}",
        "description": "Fixes #{issue_number}\n\nWhen users {action}, a {issue_type} was raised due to {cause}.\n\nThis PR:\n- Adds proper {solution}\n- Updates documentation\n- Includes regression test",
        "files": ["src/core/{module}.py", "docs/{module}.md", "tests/test_{module}.py"],
        "commits": ["Resolve {issue_type} in {module}", "Update docs and tests"],
    },
]

# Feature templates
FEATURE_TEMPLATES = [
    {
        "title": "Add {feature} to {component}",
        "description": "This PR implements {feature} for {component}.\n\nFeatures:\n- {feature_detail_1}\n- {feature_detail_2}\n- {feature_detail_3}\n\nAPI Example:\n```python\n{code_example}\n```",
        "files": ["src/{component}.py", "src/utils/{helper}.py", "tests/test_{component}.py", "docs/api.md"],
        "commits": ["Implement {feature}", "Add tests and documentation"],
    },
    {
        "title": "Implement {feature_name} functionality",
        "description": "Closes #{issue_number}\n\n{feature_description}\n\nBreaking Changes: None\n\nBackward Compatible: Yes",
        "files": ["src/{module}.py", "src/interfaces/{interface}.py", "tests/integration/test_{module}.py"],
        "commits": ["Add {feature_name} interface", "Implement {feature_name}", "Add integration tests"],
    },
]

# Refactor templates
REFACTOR_TEMPLATES = [
    {
        "title": "Refactor {component} for better {quality}",
        "description": "This PR refactors {component} to improve {quality}.\n\nChanges:\n- Extract {extracted_item} into separate {target}\n- Reduce cyclomatic complexity from {old_val} to {new_val}\n- Improve code readability\n\nNo functional changes.",
        "files": ["src/{component}.py", "src/{extracted}.py", "tests/test_{component}.py"],
        "commits": ["Refactor {component}", "Extract {extracted_item}", "Update tests"],
    },
    {
        "title": "Optimize {component} performance",
        "description": "Performance optimization for {component}.\n\nImprovements:\n- {optimization_1}\n- {optimization_2}\n- Benchmark results: {benchmark}\n\nNo API changes.",
        "files": ["src/{component}.py", "benchmarks/bench_{component}.py"],
        "commits": ["Optimize {component}", "Add performance benchmarks"],
    },
]

# Content placeholders
ISSUES = ["null pointer exception", "validation error", "connection timeout", "memory leak", "race condition"]
COMPONENTS = ["authentication", "database", "cache", "parser", "validator", "serializer", "router", "middleware"]
ISSUE_TYPES = ["ValueError", "TypeError", "AttributeError", "KeyError", "IndexError"]
CONDITIONS = ["input is empty", "network fails", "timeout occurs", "data is invalid", "concurrent access happens"]
ROOT_CAUSES = ["missing null check", "incorrect type casting", "race condition", "buffer overflow", "improper locking"]
FIX_ACTIONS = ["null validation", "type checking", "proper synchronization", "buffer size validation", "mutex usage"]

FEATURES = ["async support", "batch processing", "caching mechanism", "retry logic", "validation schema"]
FEATURE_DETAILS = [
    "Supports both sync and async modes",
    "Configurable batch size",
    "Optional caching with TTL",
    "Exponential backoff retry",
    "JSON schema validation",
    "Rate limiting support",
    "Connection pooling",
    "Automatic failover",
]

QUALITIES = ["maintainability", "testability", "performance", "readability", "modularity"]
EXTRACTED_ITEMS = ["helper functions", "utility class", "configuration logic", "validation rules", "constants"]
TARGETS = ["module", "utility file", "separate class", "configuration file", "constants file"]
OPTIMIZATIONS = [
    "Replace O(n²) loop with hash map lookup",
    "Use lazy evaluation for expensive operations",
    "Cache frequently accessed data",
    "Reduce memory allocations",
    "Vectorize operations using numpy",
]


def generate_bugfix(pr_id: int) -> Dict:
    """Generate realistic bugfix PR."""
    template = random.choice(BUGFIX_TEMPLATES)
    component = random.choice(COMPONENTS)
    issue = random.choice(ISSUES)

    title = template["title"].format(
        issue=issue,
        component=component,
        issue_type=random.choice(ISSUE_TYPES),
        action=f"calling {component}",
    )

    description = template["description"].format(
        issue=issue,
        issue_type=random.choice(ISSUE_TYPES),
        component=component,
        condition=random.choice(CONDITIONS),
        root_cause=random.choice(ROOT_CAUSES),
        fix_action=random.choice(FIX_ACTIONS),
        issue_number=random.randint(1000, 9999),
        action=f"calling {component}",
        cause=random.choice(ROOT_CAUSES),
        solution=random.choice(FIX_ACTIONS),
        module=component,
    )

    files = [f.format(component=component, module=component) for f in template["files"]]
    commits = [c.format(issue=issue, component=component, issue_type=random.choice(ISSUE_TYPES), module=component)
               for c in template["commits"]]

    return {
        "pr_id": f"dummy-bugfix-{pr_id:04d}",
        "repository": random.choice(REPOSITORIES),
        "branch_source": f"fix/{component}-{pr_id}",
        "branch_target": "main",
        "title": title,
        "description": description,
        "author": random.choice(AUTHORS),
        "commit_messages": commits,
        "files_changed": len(files),
        "lines_added": random.randint(10, 150),
        "lines_deleted": random.randint(5, 100),
        "language": "python",
        "metrics": {
            "total_lines": random.randint(15, 250),
            "files_changed": len(files),
            "commits": len(commits),
            "complexity_score": random.randint(10, 40),
            "lines_added": random.randint(10, 150),
            "lines_deleted": random.randint(5, 100),
        },
        "has_ground_truth": random.random() < 0.3,
        "ground_truth_issues_count": random.randint(1, 4) if random.random() < 0.3 else 0,
    }


def generate_feature(pr_id: int) -> Dict:
    """Generate realistic feature PR."""
    template = random.choice(FEATURE_TEMPLATES)
    component = random.choice(COMPONENTS)
    feature = random.choice(FEATURES)

    details = random.sample(FEATURE_DETAILS, 3)

    title = template["title"].format(
        feature=feature,
        component=component,
        feature_name=f"{feature} for {component}",
    )

    code_example = f"result = {component}.{feature.replace(' ', '_')}(data, options={{'enabled': True}})"

    description = template["description"].format(
        feature=feature,
        component=component,
        feature_detail_1=details[0],
        feature_detail_2=details[1],
        feature_detail_3=details[2],
        code_example=code_example,
        feature_name=feature,
        feature_description=f"This adds {feature} support to improve {random.choice(QUALITIES)}.",
        issue_number=random.randint(1000, 9999),
        module=component,
        interface=f"{component}_interface",
        helper=f"{component}_helper",
    )

    files = [f.format(component=component, module=component, helper=f"{component}_helper", interface=f"{component}_interface")
             for f in template["files"]]
    commits = [c.format(feature=feature, feature_name=feature, module=component)
               for c in template["commits"]]

    return {
        "pr_id": f"dummy-feature-{pr_id:04d}",
        "repository": random.choice(REPOSITORIES),
        "branch_source": f"feature/{component}-{feature[:10].replace(' ', '-')}",
        "branch_target": "main",
        "title": title,
        "description": description,
        "author": random.choice(AUTHORS),
        "commit_messages": commits,
        "files_changed": len(files),
        "lines_added": random.randint(100, 500),
        "lines_deleted": random.randint(10, 150),
        "language": "python",
        "metrics": {
            "total_lines": random.randint(110, 650),
            "files_changed": len(files),
            "commits": len(commits),
            "complexity_score": random.randint(20, 60),
            "lines_added": random.randint(100, 500),
            "lines_deleted": random.randint(10, 150),
        },
        "has_ground_truth": random.random() < 0.25,
        "ground_truth_issues_count": random.randint(2, 6) if random.random() < 0.25 else 0,
    }


def generate_refactor(pr_id: int) -> Dict:
    """Generate realistic refactor PR."""
    template = random.choice(REFACTOR_TEMPLATES)
    component = random.choice(COMPONENTS)
    quality = random.choice(QUALITIES)

    title = template["title"].format(
        component=component,
        quality=quality,
    )

    description = template["description"].format(
        component=component,
        quality=quality,
        extracted_item=random.choice(EXTRACTED_ITEMS),
        target=random.choice(TARGETS),
        old_val=random.randint(15, 30),
        new_val=random.randint(5, 12),
        optimization_1=random.choice(OPTIMIZATIONS),
        optimization_2=random.choice(OPTIMIZATIONS),
        benchmark=f"{random.uniform(2.0, 5.0):.1f}x faster",
        extracted=f"{component}_utils",
    )

    files = [f.format(component=component, extracted=f"{component}_utils")
             for f in template["files"]]
    commits = [c.format(component=component, extracted_item=random.choice(EXTRACTED_ITEMS))
               for c in template["commits"]]

    return {
        "pr_id": f"dummy-refactor-{pr_id:04d}",
        "repository": random.choice(REPOSITORIES),
        "branch_source": f"refactor/{component}",
        "branch_target": "main",
        "title": title,
        "description": description,
        "author": random.choice(AUTHORS),
        "commit_messages": commits,
        "files_changed": len(files),
        "lines_added": random.randint(50, 300),
        "lines_deleted": random.randint(40, 280),
        "language": "python",
        "metrics": {
            "total_lines": random.randint(90, 580),
            "files_changed": len(files),
            "commits": len(commits),
            "complexity_score": random.randint(15, 45),
            "lines_added": random.randint(50, 300),
            "lines_deleted": random.randint(40, 280),
        },
        "has_ground_truth": random.random() < 0.15,
        "ground_truth_issues_count": random.randint(1, 3) if random.random() < 0.15 else 0,
    }


def generate_category(category: str, count: int) -> List[Dict]:
    """Generate PRs for a category."""
    generators = {
        "bugfix": generate_bugfix,
        "feature": generate_feature,
        "refactor": generate_refactor,
    }

    generator = generators[category]
    return [generator(i + 1) for i in range(count)]


def save_category(category: str, prs: List[Dict], output_dir: Path):
    """Save category data."""
    category_dir = output_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)

    # Save PRs
    prs_file = category_dir / "prs.json"
    with open(prs_file, "w") as f:
        json.dump(prs, f, indent=2)

    # Calculate metadata
    total_ground_truth = sum(1 for pr in prs if pr["has_ground_truth"])
    avg_lines = sum(pr["lines_added"] + pr["lines_deleted"] for pr in prs) / len(prs)
    avg_complexity = sum(pr["metrics"]["complexity_score"] for pr in prs) / len(prs)
    total_issues = sum(pr["ground_truth_issues_count"] for pr in prs)

    metadata = {
        "category": category,
        "pr_count": len(prs),
        "ground_truth_count": total_ground_truth,
        "statistics": {
            "avg_lines_changed": round(avg_lines, 1),
            "avg_complexity_score": round(avg_complexity, 1),
            "total_important_issues": total_issues,
            "avg_issues_per_pr": round(total_issues / total_ground_truth, 1) if total_ground_truth > 0 else 0,
        },
        "repositories": list(set(pr["repository"] for pr in prs)),
    }

    metadata_file = category_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Generated {len(prs)} {category} PRs")
    return metadata


def generate_index(categories: Dict, output_dir: Path):
    """Generate index file."""
    total_prs = sum(cat["pr_count"] for cat in categories.values())
    total_ground_truth = sum(cat["ground_truth_count"] for cat in categories.values())

    distribution = {
        cat: {
            "count": categories[cat]["pr_count"],
            "percentage": round(categories[cat]["pr_count"] / total_prs * 100, 1),
        }
        for cat in categories
    }

    index = {
        "total_prs": total_prs,
        "total_ground_truth": total_ground_truth,
        "categories": categories,
        "distribution": distribution,
        "generated_at": datetime.now().isoformat(),
    }

    index_file = output_dir / "index.json"
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n✓ Generated index with {total_prs} total PRs")


def main():
    """Generate complete dummy dataset."""
    random.seed(42)  # Reproducible results

    output_dir = Path("eval/dataset/categorized")

    print("Generating professional dummy dataset...\n")

    categories = {}

    # Generate each category
    for category, count in [("bugfix", 100), ("feature", 100), ("refactor", 100)]:
        print(f"Generating {count} {category} PRs...")
        prs = generate_category(category, count)
        metadata = save_category(category, prs, output_dir)
        categories[category] = metadata

    # Generate index
    generate_index(categories, output_dir)

    print("\n" + "="*60)
    print("✅ Dummy dataset generation complete!")
    print("="*60)
    print(f"\nTotal: {sum(cat['pr_count'] for cat in categories.values())} PRs")
    print(f"  - Bugfix:   {categories['bugfix']['pr_count']} PRs")
    print(f"  - Feature:  {categories['feature']['pr_count']} PRs")
    print(f"  - Refactor: {categories['refactor']['pr_count']} PRs")
    print(f"\nOutput: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
