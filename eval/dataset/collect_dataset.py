"""Script to collect PR dataset from GitHub."""

import json
import os
from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from eval.dataset.collectors import DataTransformer, GitHubPRCollector, PRSelector
from app.logging import get_logger, setup_logging
from app.config import get_settings

app = typer.Typer()
console = Console()
logger = get_logger(__name__)

# Curated list of high-quality Python repositories
CURATED_REPOS = [
    # Web frameworks
    ("pallets", "flask"),
    ("django", "django"),
    ("fastapi", "fastapi"),
    ("tornadoweb", "tornado"),
    ("bottlepy", "bottle"),

    # Data science & ML
    ("pandas-dev", "pandas"),
    ("scikit-learn", "scikit-learn"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("scipy", "scipy"),
    ("pytorch", "pytorch"),
    ("tensorflow", "tensorflow"),

    # Tools & Libraries
    ("psf", "requests"),
    ("pytest-dev", "pytest"),
    ("python-poetry", "poetry"),
    ("python", "cpython"),
    ("python", "mypy"),
    ("python", "black"),

    # APIs & async
    ("encode", "httpx"),
    ("aio-libs", "aiohttp"),
    ("celery", "celery"),

    # CLI tools
    ("tiangolo", "typer"),
    ("tqdm", "tqdm"),
    ("click-contrib", "click"),

    # Database & ORM
    ("sqlalchemy", "sqlalchemy"),
    ("mongodb", "mongo-python-driver"),
    ("redis", "redis-py"),

    # Testing & Quality
    ("pytest-dev", "pytest"),
    ("coveragepy", "coverage"),
    ("PyCQA", "flake8"),
    ("PyCQA", "pylint"),

    # Configuration & Deployment
    ("ansible", "ansible"),
    ("saltstack", "salt"),

    # Scientific Computing
    ("sympy", "sympy"),
    ("statsmodels", "statsmodels"),
]


@app.command()
def collect(
    output_dir: Path = typer.Option(
        Path("eval/dataset"),
        "--output",
        "-o",
        help="Output directory",
    ),
    num_repos: int = typer.Option(
        15,  # More repos by default
        "--repos",
        "-r",
        help="Number of repositories to collect from",
    ),
    prs_per_repo: int = typer.Option(
        3,  # Fewer per repo but more repos
        "--prs-per-repo",
        "-p",
        help="Target PRs per repository",
    ),
    min_lines: int = typer.Option(
        0,  # No minimum (disabled)
        "--min-lines",
        help="Minimum lines changed (0 to disable)",
    ),
    max_lines: int = typer.Option(
        999999,  # Very high maximum (effectively disabled)
        "--max-lines",
        help="Maximum lines changed",
    ),
    balanced: bool = typer.Option(
        True,
        "--balanced/--no-balanced",
        help="Balance across PR categories",
    ),
):
    """Collect PR dataset from GitHub repositories.

    Requires GITHUB_TOKEN environment variable.

    Example:
        export GITHUB_TOKEN=ghp_...
        poetry run python eval/dataset/collect_dataset.py --repos 5 --prs-per-repo 5
    """
    # Setup logging and load settings
    try:
        setup_logging()
        settings = get_settings()
        token = settings.github_token
    except Exception as e:
        # Fallback to environment variable if settings not available
        console.print(f"[yellow]Warning: Could not load settings ({e}), using environment variable[/yellow]")
        import logging
        logging.basicConfig(level=logging.INFO)
        token = os.getenv("GITHUB_TOKEN")

    if not token:
        console.print("[red]Error: GitHub token not configured[/red]")
        console.print("Set GITHUB_TOKEN in .env file or as environment variable")
        console.print("Create token at: https://github.com/settings/tokens")
        console.print("Required scopes: public_repo")
        raise typer.Exit(1)

    # Initialize
    collector = GitHubPRCollector(token)
    # More lenient filters for better results
    selector = PRSelector(
        min_lines=min_lines,
        max_lines=max_lines,
        min_files=1,  # At least 1 file
        max_files=50,  # Allow many files (large PRs are OK)
        require_review=False,  # Make review optional
    )
    transformer = DataTransformer()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Check rate limit
    rate_limit = collector.get_rate_limit()
    remaining = rate_limit["resources"]["core"]["remaining"]
    console.print(f"[cyan]GitHub API rate limit remaining: {remaining}[/cyan]")

    if remaining < 100:
        console.print("[yellow]Warning: Low rate limit. Consider waiting.[/yellow]")

    # Collect PRs
    all_pr_metadata = []
    all_ground_truth = []

    repos_to_process = CURATED_REPOS[:num_repos]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        for owner, repo in repos_to_process:
            task = progress.add_task(f"Processing {owner}/{repo}...", total=None)

            try:
                # Get repository info
                repo_info = collector.get_repository_info(owner, repo)
                console.print(f"\n[bold]{repo_info['full_name']}[/bold]")
                console.print(f"  ⭐ Stars: {repo_info['stargazers_count']}")
                console.print(f"  🍴 Forks: {repo_info['forks_count']}")

                # List PRs
                prs = collector.list_pull_requests(owner, repo, max_pages=3)
                console.print(f"  Found {len(prs)} closed PRs")

                # Collect detailed data - process more PRs to find suitable ones
                files_data = {}
                reviews_data = {}
                commits_data = {}
                review_comments_data = {}

                # Process more PRs to increase chances of finding suitable ones
                prs_to_process = min(150, len(prs))  # Process more PRs
                console.print(f"  Processing {prs_to_process} PRs for detailed data...")

                for pr in prs[:prs_to_process]:
                    pr_number = pr["number"]

                    try:
                        files = collector.get_pr_files(owner, repo, pr_number)
                        reviews = collector.get_pr_review_comments(owner, repo, pr_number)
                        commits = collector.get_pr_commits(owner, repo, pr_number)

                        files_data[pr_number] = files
                        reviews_data[pr_number] = reviews
                        commits_data[pr_number] = commits
                        review_comments_data[pr_number] = reviews

                    except Exception as e:
                        logger.warning(f"Failed to fetch data for PR #{pr_number}: {e}")
                        continue

                # Filter PRs - only check PRs we have data for
                prs_with_data = [pr for pr in prs if pr["number"] in files_data]
                console.print(f"  Collected data for {len(prs_with_data)} PRs")
                filtered_prs = selector.filter_prs(prs_with_data, files_data, reviews_data)
                console.print(f"  ✓ Filtered to {len(filtered_prs)} suitable PRs")

                if not filtered_prs:
                    continue

                # Select balanced or top N
                if balanced:
                    selected_prs = selector.select_balanced_dataset(
                        filtered_prs,
                        files_data,
                        target_per_category=2,
                    )
                else:
                    selected_prs = filtered_prs[:prs_per_repo]

                console.print(f"  → Selected {len(selected_prs)} PRs")

                # Transform to our models
                for pr in selected_prs:
                    pr_number = pr["number"]

                    # Transform metadata
                    metadata = transformer.pr_to_metadata(
                        pr,
                        files_data[pr_number],
                        commits_data[pr_number],
                    )
                    all_pr_metadata.append(metadata)

                    # Extract ground truth
                    if review_comments_data[pr_number]:
                        gt = transformer.extract_ground_truth_from_reviews(
                            pr,
                            review_comments_data[pr_number],
                        )
                        all_ground_truth.append(gt)

                    # Show category
                    category = selector.categorize_pr(pr, files_data[pr_number])
                    complexity = selector.calculate_complexity_score(pr, files_data[pr_number])
                    console.print(
                        f"    • PR #{pr_number}: {pr['title'][:60]}... "
                        f"[{category}] [complexity: {complexity}]"
                    )

            except Exception as e:
                logger.error(f"Failed to process {owner}/{repo}: {e}")
                continue

            finally:
                progress.remove_task(task)

    # Save results
    console.print(f"\n[bold green]Collected {len(all_pr_metadata)} PRs total[/bold green]")

    # Save PR list
    pr_list_file = output_dir / "pr_list.json"
    with open(pr_list_file, "w") as f:
        json.dump(
            [pr.model_dump(mode="json") for pr in all_pr_metadata],
            f,
            indent=2,
        )
    console.print(f"✓ Saved PR list to {pr_list_file}")

    # Save ground truth
    if all_ground_truth:
        gt_file = output_dir / "ground_truth.json"
        with open(gt_file, "w") as f:
            json.dump(
                [gt.model_dump(mode="json") for gt in all_ground_truth],
                f,
                indent=2,
            )
        console.print(f"✓ Saved ground truth to {gt_file}")

    # Save summary
    summary = {
        "total_prs": len(all_pr_metadata),
        "total_ground_truth": len(all_ground_truth),
        "repositories": [f"{owner}/{repo}" for owner, repo in repos_to_process],
        "filters": {
            "min_lines": min_lines,
            "max_lines": max_lines,
            "balanced": balanced,
        },
    }

    summary_file = output_dir / "collection_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    console.print(f"✓ Saved summary to {summary_file}")

    # Check rate limit after
    rate_limit = collector.get_rate_limit()
    remaining = rate_limit["resources"]["core"]["remaining"]
    console.print(f"\n[cyan]API calls remaining: {remaining}[/cyan]")


@app.command()
def list_repos():
    """List curated repositories."""
    console.print("\n[bold]Curated Python Repositories:[/bold]\n")

    for i, (owner, repo) in enumerate(CURATED_REPOS, 1):
        console.print(f"{i:2d}. {owner}/{repo}")

    console.print(f"\n[cyan]Total: {len(CURATED_REPOS)} repositories[/cyan]")


if __name__ == "__main__":
    app()
