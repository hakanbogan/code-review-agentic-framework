"""Command-line interface for code review framework."""

import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.config import get_settings
from app.logging import setup_logging
from app.review_storage import ReviewStorage
from domain import Language, PRMetadata, SystemType
from eval import ComparisonAnalyzer, EvaluationRunner
from flows import ReviewFlow

app = typer.Typer(
    name="code-review",
    help="Multi-agent code review framework",
    add_completion=False,
)

console = Console()


def _resolve_repo_path(repo_path_or_url: str) -> Path:
    """Resolve repository path from local path or GitHub URL.

    Args:
        repo_path_or_url: Local path or GitHub URL (https://github.com/owner/repo)

    Returns:
        Path: Local repository path
    """
    # Check if it's a GitHub URL
    if repo_path_or_url.startswith(("https://github.com/", "git@github.com:")):
        # Extract repo name from URL
        if repo_path_or_url.startswith("https://"):
            repo_name = repo_path_or_url.rstrip("/").rstrip(".git").split("/")[-1]
        else:  # git@github.com:owner/repo.git
            repo_name = repo_path_or_url.split(":")[-1].rstrip(".git").split("/")[-1]

        # Clone to temp directory
        temp_dir = Path(tempfile.gettempdir()) / "code-review-repos" / repo_name

        if temp_dir.exists():
            console.print(f"[yellow]Repository exists at {temp_dir}, updating...[/yellow]")
            # Get current branch
            current_branch_result = subprocess.run(
                ["git", "-C", str(temp_dir), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = current_branch_result.stdout.strip()

            # Fetch updates
            subprocess.run(["git", "-C", str(temp_dir), "fetch", "origin"], check=True)

            # Only pull if on a tracking branch (not a PR branch)
            if not current_branch.startswith("pr-"):
                try:
                    subprocess.run(["git", "-C", str(temp_dir), "pull"], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    # If pull fails, try to checkout default branch and pull
                    default_branch = _get_base_branch(temp_dir).replace("origin/", "")
                    subprocess.run(["git", "-C", str(temp_dir), "checkout", default_branch],
                                   check=True, capture_output=True)
                    subprocess.run(["git", "-C", str(temp_dir), "pull"], check=True, capture_output=True)
        else:
            console.print(f"[cyan]Cloning {repo_path_or_url} to {temp_dir}...[/cyan]")
            temp_dir.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", repo_path_or_url, str(temp_dir)], check=True)

        console.print(f"[green]✓ Repository ready at {temp_dir}[/green]")
        return temp_dir

    # Local path
    return Path(repo_path_or_url)


def _checkout_pr_branch(repo_path: Path, pr_id: str) -> tuple[str, str]:
    """Checkout PR branch for review.

    Args:
        repo_path: Repository path
        pr_id: PR number

    Returns:
        Tuple of (merge_base_commit, pr_branch_name)
    """
    branch_name = f"pr-{pr_id}"

    console.print(f"[cyan]Fetching PR #{pr_id} branch...[/cyan]")

    # Get default branch name
    base_branch = _get_base_branch(repo_path).replace("origin/", "")

    # Checkout master first to allow branch deletion
    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", base_branch],
        capture_output=True,
    )

    # Delete PR branch if it exists
    subprocess.run(
        ["git", "-C", str(repo_path), "branch", "-D", branch_name],
        capture_output=True,
    )

    # Fetch PR branch (don't update base branch if currently checked out)
    subprocess.run(
        ["git", "-C", str(repo_path), "fetch", "origin", f"pull/{pr_id}/head:{branch_name}"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "fetch", "origin", base_branch],
        check=True,
    )

    # Checkout PR branch
    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", branch_name],
        check=True,
        capture_output=True,
    )

    # Get merge base (common ancestor of PR and base branch)
    merge_base_result = subprocess.run(
        ["git", "-C", str(repo_path), "merge-base", base_branch, branch_name],
        capture_output=True,
        text=True,
        check=True,
    )
    merge_base = merge_base_result.stdout.strip()

    console.print(f"[green]✓ Checked out PR #{pr_id} branch[/green]")
    console.print(f"[dim]Merge base: {merge_base[:8]}[/dim]")

    return merge_base, branch_name


def _get_base_branch(repo_path: Path) -> str:
    """Get default branch name (main or master).

    Args:
        repo_path: Repository path

    Returns:
        Default branch name
    """
    try:
        # Try to get default branch from remote
        result = subprocess.run(
            ["git", "-C", str(repo_path), "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Extract branch name (e.g., "refs/remotes/origin/main" -> "origin/main")
        ref = result.stdout.strip()
        return ref.replace("refs/remotes/", "")
    except subprocess.CalledProcessError:
        # Fallback: try common branch names
        for branch in ["origin/main", "origin/master"]:
            try:
                subprocess.run(
                    ["git", "-C", str(repo_path), "rev-parse", "--verify", branch],
                    capture_output=True,
                    check=True,
                )
                return branch
            except subprocess.CalledProcessError:
                continue
        # Last resort: use HEAD
        return "HEAD"


@app.callback()
def callback():
    """Initialize logging and configuration."""
    setup_logging()


def _fetch_pr_info_from_github(repo_url: str, pr_id: str, github_token: str | None) -> dict:
    """Fetch PR information from GitHub API.

    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        pr_id: PR number
        github_token: GitHub personal access token (optional)

    Returns:
        Dictionary with title, description, author, branch_source, branch_target
    """
    # Extract owner/repo from URL
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")

    owner, repo = match.groups()

    # Build API URL
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_id}"

    # Create request with optional authentication
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            return {
                "title": data.get("title", ""),
                "description": data.get("body") or "",
                "author": data.get("user", {}).get("login", "unknown"),
                "branch_source": data.get("head", {}).get("ref", "feature"),
                "branch_target": data.get("base", {}).get("ref", "main"),
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"PR #{pr_id} not found in {owner}/{repo}")
        elif e.code == 401:
            # Try without token for public repos
            if github_token:
                # Token might be invalid, try without it for public repos
                headers_no_auth = {"Accept": "application/vnd.github.v3+json"}
                req = urllib.request.Request(api_url, headers=headers_no_auth)
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())
                        return {
                            "title": data.get("title", ""),
                            "description": data.get("body") or "",
                            "author": data.get("user", {}).get("login", "unknown"),
                            "branch_source": data.get("head", {}).get("ref", "feature"),
                            "branch_target": data.get("base", {}).get("ref", "main"),
                        }
                except urllib.error.HTTPError:
                    raise ValueError(
                        "GitHub authentication failed. Check your GITHUB_TOKEN in .env or ensure repo is public")
            else:
                raise ValueError("GitHub authentication required. Set GITHUB_TOKEN in .env")
        else:
            raise ValueError(f"GitHub API error: {e.code} - {e.reason}")
    except Exception as e:
        raise ValueError(f"Failed to fetch PR info: {e}")


@app.command()
def review(
    repo_path_or_url: str = typer.Argument(..., help="Local path or GitHub URL (https://github.com/owner/repo)"),
    pr_id: str = typer.Option(..., "--pr-id", help="PR identifier"),
    title: Optional[str] = typer.Option(None, "--title", help="PR title (auto-fetched from GitHub if not provided)"),
    description: Optional[str] = typer.Option(
        None, "--description", help="PR description (auto-fetched from GitHub if not provided)"),
    language: str = typer.Option("python", "--language",
                                 help="Primary language (python, javascript, typescript, etc.)"),
    multi_agent: bool = typer.Option(True, "--multi-agent/--single-agent", help="Use multi-agent system"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    checkout_pr: bool = typer.Option(True, "--checkout-pr/--no-checkout-pr",
                                     help="Checkout PR branch if GitHub URL provided"),
):
    """Run code review on a repository.

    If GitHub URL is provided and title/description are not specified,
    they will be automatically fetched from GitHub API.
    """
    settings = get_settings()

    console.print(f"[bold]Starting review for PR {pr_id}[/bold]")

    # Resolve repository path (handle both local paths and GitHub URLs)
    repo_path = _resolve_repo_path(repo_path_or_url)

    # Auto-fetch PR info from GitHub if URL provided and title/description missing
    is_github_url = repo_path_or_url.startswith(("https://github.com/", "git@github.com:"))
    if is_github_url and (title is None or description is None):
        try:
            console.print("[cyan]Fetching PR information from GitHub...[/cyan]")
            pr_info = _fetch_pr_info_from_github(repo_path_or_url, pr_id, settings.github_token)
            title = title or pr_info["title"]
            description = description or pr_info["description"]
            author = pr_info["author"]
            branch_source = pr_info["branch_source"]
            branch_target = pr_info["branch_target"]
            console.print(f"[green]✓[/green] Fetched PR: {title[:60]}...")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch PR info from GitHub: {e}[/yellow]")
            if title is None:
                title = f"PR #{pr_id}"
            if description is None:
                description = ""
            author = "unknown"
            branch_source = "feature"
            branch_target = "main"
    else:
        # Use provided values or defaults
        title = title or f"PR #{pr_id}"
        description = description or ""
        author = "unknown"
        branch_source = "feature"
        branch_target = "main"

    # If GitHub URL and checkout_pr enabled, try to checkout PR branch
    base_ref = None
    if checkout_pr and is_github_url:
        try:
            merge_base, pr_branch = _checkout_pr_branch(repo_path, pr_id)
            # Use merge base as base_ref for accurate diff
            base_ref = merge_base
        except Exception as e:
            console.print(f"[yellow]Warning: Could not checkout PR branch: {e}[/yellow]")
            console.print("[yellow]Continuing with current branch...[/yellow]")

    # Convert language string to Language enum
    try:
        language_enum = Language(language.lower())
    except ValueError:
        # Try to map common aliases
        language_map = {
            "js": Language.JAVASCRIPT,
            "ts": Language.TYPESCRIPT,
            "c++": Language.CPP,
            "c#": Language.CSHARP,
        }
        language_enum = language_map.get(language.lower(), Language.PYTHON)
        console.print(f"[yellow]Warning: Unknown language '{language}', defaulting to {language_enum.value}[/yellow]")

    # Create PR metadata
    pr_metadata = PRMetadata(
        pr_id=pr_id,
        repository=repo_path.name,
        branch_source=branch_source,
        branch_target=branch_target,
        title=title,
        description=description,
        author=author,
        language=language_enum,
    )

    # Run review
    flow = ReviewFlow(settings, language=language_enum)

    try:
        if multi_agent:
            console.print("[cyan]Running multi-agent review...[/cyan]")
            result = flow.run_multi_agent_review(pr_metadata, repo_path, base_branch=base_ref)
        else:
            console.print("[cyan]Running single-agent review...[/cyan]")
            result = flow.run_single_agent_review(pr_metadata, repo_path, base_branch=base_ref)

        # Display results
        _display_review_result(result)

        # Save review using storage system
        storage = ReviewStorage(settings)

        # Add metadata for storage
        result.metadata.update({
            "repository": pr_metadata.repository,
            "title": pr_metadata.title,
            "author": pr_metadata.author,
        })

        saved_paths = storage.save_review(result)
        console.print(f"[green]Review saved to {saved_paths['directory']}[/green]")

        # Also save to custom output if requested
        if output:
            import json
            output.write_text(json.dumps(result.model_dump(mode="json"), indent=2))
            console.print(f"[green]Results also saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def evaluate(
    system: str = typer.Option("multi_agent", "--system", help="System to evaluate (single_agent or multi_agent)"),
    use_stored: bool = typer.Option(True, "--use-stored/--rerun", help="Use stored reviews or rerun"),
    pr_ids: Optional[str] = typer.Option(None, "--pr-ids", help="PR IDs to evaluate (comma-separated)"),
    all_reviews: bool = typer.Option(False, "--all-reviews", help="Evaluate all stored reviews"),
    aggregate: bool = typer.Option(False, "--aggregate", help="Save results in single aggregated file"),
    repo_path: Optional[Path] = typer.Option(None, "--repo-path", help="Repository path (required if --rerun)"),
):
    """Evaluate review system performance."""
    settings = get_settings()
    setup_logging()

    console.print(f"[bold]Evaluating {system} system[/bold]")

    if not use_stored and not repo_path:
        console.print("[red]Error: --repo-path required when using --rerun[/red]")
        raise typer.Exit(1)

    if all_reviews and pr_ids:
        console.print("[red]Error: Cannot use --all-reviews with --pr-ids[/red]")
        raise typer.Exit(1)

    # Parse PR IDs
    pr_id_list = None
    if all_reviews:
        console.print("[cyan]Evaluating all stored reviews...[/cyan]")
    elif pr_ids:
        pr_id_list = [pid.strip() for pid in pr_ids.split(",")]
        console.print(f"Filtering to PRs: {', '.join(pr_id_list)}")

    # Determine system type
    sys_type = SystemType.SINGLE_AGENT if system == "single_agent" else SystemType.MULTI_AGENT

    runner = EvaluationRunner(settings)

    try:
        if use_stored:
            console.print("[cyan]Loading stored review results...[/cyan]")
        else:
            console.print("[cyan]Running reviews (this may take a while)...[/cyan]")

        result = runner.run_evaluation(
            system_type=sys_type,
            repo_path=repo_path,
            use_stored_reviews=use_stored,
            pr_ids=pr_id_list,
            aggregate=aggregate,
        )

        # Display results
        _display_evaluation_result(result)

        if aggregate:
            console.print(f"[green]Evaluation complete. Aggregated results saved to {
                          settings.eval_results_path}[/green]")
        else:
            console.print(f"[green]Evaluation complete. Results saved to {settings.eval_results_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def compare(
    baseline_file: Path = typer.Argument(..., help="Baseline evaluation results (JSON)"),
    proposed_file: Path = typer.Argument(..., help="Proposed evaluation results (JSON)"),
    latex_output: Optional[Path] = typer.Option(None, "--latex", help="Output LaTeX table"),
):
    """Compare two evaluation results."""
    import json
    from domain import EvaluationResult

    settings = get_settings()

    # Load results
    with open(baseline_file) as f:
        baseline_data = json.load(f)
    baseline = EvaluationResult(**baseline_data)

    with open(proposed_file) as f:
        proposed_data = json.load(f)
    proposed = EvaluationResult(**proposed_data)

    # Compare
    analyzer = ComparisonAnalyzer(settings)
    comparison = analyzer.compare_systems(baseline, proposed)

    # Display comparison
    _display_comparison(comparison)

    # Export LaTeX if requested
    if latex_output:
        analyzer.export_latex_table([baseline, proposed], latex_output)
        console.print(f"[green]LaTeX table exported to {latex_output}[/green]")


@app.command()
def list_reviews(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of reviews to show"),
):
    """List recent reviews."""
    settings = get_settings()
    storage = ReviewStorage(settings)

    reviews = storage.list_reviews(limit=limit)

    if not reviews:
        console.print("[yellow]No reviews found[/yellow]")
        return

    table = Table(title=f"Recent Reviews (showing {len(reviews)})")
    table.add_column("PR ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Findings", justify="right", style="magenta")
    table.add_column("Time", justify="right", style="green")
    table.add_column("Cost", justify="right", style="yellow")

    for review in reviews:
        table.add_row(
            review["pr_id"],
            review.get("title", "")[:50] + ("..." if len(review.get("title", "")) > 50 else ""),
            str(review.get("findings_count", 0)),
            f"{review.get('review_time_s', 0):.1f}s",
            f"${review.get('token_cost', 0):.4f}",
        )

    console.print(table)

    # Show summary
    summary = storage.get_summary()
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Total reviews: {summary['total_reviews']}")
    console.print(f"Total findings: {summary['total_findings']}")
    console.print(f"Average review time: {summary['avg_review_time']:.2f}s")
    console.print(f"Total cost: ${summary['total_cost']:.4f}")


@app.command()
def show_review(
    pr_id: str = typer.Argument(..., help="PR ID to show"),
):
    """Show a specific review."""
    settings = get_settings()
    storage = ReviewStorage(settings)

    result = storage.get_review(pr_id)

    if not result:
        console.print(f"[red]Review not found: {pr_id}[/red]")
        raise typer.Exit(1)

    _display_review_result(result)

    # Show markdown
    md_path = storage.reviews_path / pr_id / "review.md"
    if md_path.exists():
        console.print(f"\n[bold]Review Comment:[/bold]")
        console.print(md_path.read_text())


@app.command()
def init_dataset(
    dataset_path: Path = typer.Argument(..., help="Path to dataset directory"),
):
    """Initialize evaluation dataset structure."""
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Create sample files
    pr_list_file = dataset_path / "pr_list.json"
    ground_truth_file = dataset_path / "ground_truth.json"

    if not pr_list_file.exists():
        import json
        pr_list_file.write_text(json.dumps([], indent=2))
        console.print(f"[green]Created {pr_list_file}[/green]")

    if not ground_truth_file.exists():
        import json
        ground_truth_file.write_text(json.dumps([], indent=2))
        console.print(f"[green]Created {ground_truth_file}[/green]")

    console.print(f"[bold green]Dataset structure initialized at {dataset_path}[/bold green]")


def _display_review_result(result):
    """Display review result in terminal."""
    from domain import Severity

    console.print("\n[bold]Review Summary[/bold]")
    console.print(f"PR ID: {result.pr_id}")
    console.print(f"System: {result.system_type.value}")
    console.print(f"Review time: {result.review_time_s:.2f}s")
    console.print(f"Estimated cost: ${result.token_cost_estimate:.4f}")

    # Findings table
    table = Table(title="Findings")
    table.add_column("Severity", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("With Patch", justify="right", style="green")

    by_severity = result.findings_by_severity
    for severity in [Severity.CRITICAL, Severity.MAJOR, Severity.MINOR, Severity.NIT]:
        findings = by_severity[severity]
        with_patch = sum(1 for f in findings if f.has_patch)
        table.add_row(
            severity.value,
            str(len(findings)),
            str(with_patch),
        )

    console.print(table)


def _display_evaluation_result(result):
    """Display evaluation result in terminal."""
    console.print("\n[bold]Evaluation Results[/bold]")
    console.print(f"System: {result.system_type.value}")
    console.print(f"Dataset size: {result.dataset_size} PRs")

    table = Table(title="Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")

    table.add_row("Actionability Rate", f"{result.actionability_rate:.2%}")
    table.add_row("Noise Rate", f"{result.noise_rate:.2%}")
    table.add_row("Important Issue Coverage", f"{result.important_issue_coverage:.2%}")
    table.add_row("Avg Findings per PR", f"{result.avg_findings_per_pr:.1f}")
    table.add_row("Avg Review Time", f"{result.avg_review_time_s:.1f}s")
    table.add_row("Avg Token Cost", f"${result.avg_token_cost:.4f}")

    console.print(table)


def _display_comparison(comparison):
    """Display comparison results."""
    console.print("\n[bold]System Comparison[/bold]")
    console.print(f"Baseline: {comparison['baseline']}")
    console.print(f"Proposed: {comparison['proposed']}")

    table = Table(title="Metric Improvements")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", justify="right", style="yellow")
    table.add_column("Proposed", justify="right", style="green")
    table.add_column("Improvement", justify="right", style="magenta")

    for metric_name, values in comparison["metrics"].items():
        improvement = values["improvement"]
        improvement_str = f"+{improvement:.2%}" if improvement > 0 else f"{improvement:.2%}"

        table.add_row(
            metric_name.capitalize(),
            f"{values['baseline']:.2%}",
            f"{values['proposed']:.2%}",
            improvement_str,
        )

    console.print(table)


if __name__ == "__main__":
    app()
