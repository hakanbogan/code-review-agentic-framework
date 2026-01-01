"""Review PRs with OpenAI and extract ground truth.

Usage:
    poetry run python review_and_extract_gt.py \
        --pr-ids "14468,14,143" \
        --repo-url "https://github.com/fastapi/fastapi" \
        --language python
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.insert(0, str(Path(__file__).parent))

from app.config import Settings, get_settings
from app.logging import setup_logging
from app.review_storage import ReviewStorage
from domain import GroundTruthLabel, Language, LLMProvider, PRMetadata, PRReviewResult, Severity
from eval.run_eval import categorize_pr
from flows import ReviewFlow

console = Console()
app = typer.Typer()


def _fetch_pr_info_from_github(repo_url: str, pr_id: str, github_token: Optional[str]) -> Dict:
    """Fetch PR information from GitHub API."""
    import re
    import urllib.error
    import urllib.request

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
        else:
            raise ValueError(f"GitHub API error: {e.code} - {e.reason}")
    except Exception as e:
        raise ValueError(f"Failed to fetch PR info: {e}")


def _resolve_repo_path(repo_path_or_url: str) -> Path:
    """Resolve repository path (clone if GitHub URL)."""
    import tempfile
    from pathlib import Path

    if repo_path_or_url.startswith(("https://github.com/", "git@github.com:")):
        # Clone repository to temp directory
        import subprocess

        temp_dir = Path(tempfile.gettempdir()) / "code-review-repos"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract repo name from URL
        repo_name = repo_path_or_url.split("/")[-1].replace(".git", "")
        clone_path = temp_dir / repo_name

        if not clone_path.exists():
            console.print(f"[cyan]Cloning {repo_path_or_url} to {clone_path}...[/cyan]")
            subprocess.run(
                ["git", "clone", repo_path_or_url, str(clone_path)],
                check=True,
                capture_output=True,
            )
        else:
            console.print(f"[cyan]Repository already exists at {clone_path}[/cyan]")
            # Update repository
            subprocess.run(
                ["git", "-C", str(clone_path), "fetch"],
                check=False,
                capture_output=True,
            )

        return clone_path
    else:
        return Path(repo_path_or_url)


def _clean_text_for_terminal(text: str) -> str:
    """Remove emoji and non-ASCII characters for Windows terminal compatibility."""
    return text.encode('ascii', 'ignore').decode('ascii')


def _get_base_branch(repo_path: Path) -> str:
    """Get default branch name from repository."""
    import subprocess

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


def _checkout_pr_branch(repo_path: Path, pr_id: str) -> tuple[str, str]:
    """Checkout PR branch and return merge base."""
    import subprocess

    branch_name = f"pr-{pr_id}"

    console.print(f"[cyan]Fetching PR #{pr_id} branch...[/cyan]")

    # Get default branch name
    base_branch = _get_base_branch(repo_path).replace("origin/", "")

    # Checkout base branch first to allow branch deletion
    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", base_branch],
        capture_output=True,
    )

    # Delete PR branch if it exists
    subprocess.run(
        ["git", "-C", str(repo_path), "branch", "-D", branch_name],
        capture_output=True,
    )

    # Fetch PR branch
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

    console.print(f"[green]OK[/green] Checked out PR #{pr_id} branch")
    console.print(f"[green]OK[/green] Merge base: {merge_base[:8]}")

    return merge_base, branch_name


def extract_important_issues_from_review(review: PRReviewResult) -> List[str]:
    """Extract important issues from review findings."""
    important_issues = []

    for finding in review.findings:
        # Include critical and major findings
        if finding.severity in [Severity.CRITICAL, Severity.MAJOR]:
            issue_desc = finding.title
            if finding.description:
                issue_desc += f": {finding.description[:100]}"
            if finding.location:
                issue_desc += f" @ {finding.location}"
            important_issues.append(issue_desc)

        # Also include actionable findings (with patches)
        elif finding.has_patch and finding.severity == Severity.MINOR:
            issue_desc = finding.title
            if finding.description:
                issue_desc += f": {finding.description[:100]}"
            if finding.location:
                issue_desc += f" @ {finding.location}"
            important_issues.append(issue_desc)

    # Remove duplicates while preserving order
    seen = set()
    unique_issues = []
    for issue in important_issues:
        if issue not in seen:
            seen.add(issue)
            unique_issues.append(issue)

    return unique_issues


def save_ground_truth(gt_labels: List[Dict], settings: Settings):
    """Save ground truth to categorized directories."""
    from eval.run_eval import DatasetLoader

    categorized_path = settings.eval_dataset_path / "categorized"
    categorized_path.mkdir(parents=True, exist_ok=True)

    # Group by category
    by_category: Dict[str, List[Dict]] = {}
    for item in gt_labels:
        category = item["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(item)

    # Save each category
    for category, items in by_category.items():
        category_dir = categorized_path / category
        category_dir.mkdir(parents=True, exist_ok=True)

        gt_file = category_dir / "ground_truth.json"

        # Load existing ground truth
        existing_gt = []
        if gt_file.exists():
            with open(gt_file, "r", encoding="utf-8") as f:
                existing_gt = json.load(f)

        # Get existing PR IDs
        existing_pr_ids = {gt["pr_id"] for gt in existing_gt}

        # Add new ground truth (avoid duplicates)
        for item in items:
            if item["pr_id"] not in existing_pr_ids:
                gt_dict = item["gt"].model_dump(mode="json")
                # Convert datetime to ISO string
                if "labeled_at" in gt_dict and isinstance(gt_dict["labeled_at"], str):
                    pass  # Already string
                elif "labeled_at" in gt_dict:
                    gt_dict["labeled_at"] = gt_dict["labeled_at"].isoformat()
                existing_gt.append(gt_dict)
                existing_pr_ids.add(item["pr_id"])

        # Save updated ground truth
        with open(gt_file, "w", encoding="utf-8") as f:
            json.dump(existing_gt, f, indent=2, ensure_ascii=False)

        console.print(f"[green]OK[/green] Saved {len(items)} GT entries to {category}/ground_truth.json")


@app.command()
def main(
    pr_ids: str = typer.Option(..., "--pr-ids", help="Comma-separated PR IDs"),
    repo_url: str = typer.Option(..., "--repo-url", help="GitHub repository URL"),
    language: str = typer.Option("python", "--language", help="Primary language"),
    force_openai: bool = typer.Option(True, "--force-openai/--no-force-openai", help="Force OpenAI provider"),
):
    """Review PRs with OpenAI and extract ground truth."""
    setup_logging()

    # Parse PR IDs
    pr_id_list = [pid.strip() for pid in pr_ids.split(",")]
    console.print(f"[bold]Reviewing {len(pr_id_list)} PRs with OpenAI[/bold]")
    console.print(f"PR IDs: {', '.join(pr_id_list)}")
    console.print(f"Repository: {repo_url}")

    # Get settings and force OpenAI
    settings = get_settings()
    if force_openai:
        # Override provider to OpenAI
        settings.llm_provider = LLMProvider.OPENAI
        if not settings.openai_api_key:
            console.print("[red]Error: OPENAI_API_KEY not found in .env[/red]")
            raise typer.Exit(1)
        console.print(f"[green]OK[/green] Using OpenAI provider with model: {settings.openai_model}")

    # Convert language
    try:
        language_enum = Language(language.lower())
    except ValueError:
        language_map = {
            "js": Language.JAVASCRIPT,
            "ts": Language.TYPESCRIPT,
            "c++": Language.CPP,
            "c#": Language.CSHARP,
        }
        language_enum = language_map.get(language.lower(), Language.PYTHON)
        console.print(f"[yellow]Warning: Unknown language '{language}', defaulting to {language_enum.value}[/yellow]")

    # Resolve repository path
    repo_path = _resolve_repo_path(repo_url)

    # Initialize storage
    storage = ReviewStorage(settings)

    # Review each PR
    reviews: List[PRReviewResult] = []
    ground_truths: List[Dict] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for i, pr_id in enumerate(pr_id_list, 1):
            task = progress.add_task(f"[cyan]Processing PR {pr_id} ({i}/{len(pr_id_list)})...", total=None)

            try:
                # Fetch PR info
                console.print(f"\n[bold]PR {pr_id}[/bold]")
                console.print("[cyan]Fetching PR information from GitHub...[/cyan]")
                pr_info = _fetch_pr_info_from_github(repo_url, pr_id, settings.github_token)
                # Clean emoji and special characters for Windows terminal
                title_clean = _clean_text_for_terminal(pr_info['title'])[:60]
                console.print(f"[green]OK[/green] Fetched: {title_clean}...")

                # Checkout PR branch
                console.print("[cyan]Checking out PR branch...[/cyan]")
                merge_base, _ = _checkout_pr_branch(repo_path, pr_id)

                # Create PR metadata
                pr_metadata = PRMetadata(
                    pr_id=pr_id,
                    repository=repo_path.name,
                    branch_source=pr_info["branch_source"],
                    branch_target=pr_info["branch_target"],
                    title=pr_info["title"],
                    description=pr_info["description"],
                    author=pr_info["author"],
                    language=language_enum,
                )

                # Run review
                console.print("[cyan]Running multi-agent review with OpenAI...[/cyan]")
                flow = ReviewFlow(settings, language=language_enum)
                result = flow.run_multi_agent_review(pr_metadata, repo_path, base_branch=merge_base)

                # Add metadata
                result.metadata.update({
                    "repository": pr_metadata.repository,
                    "title": pr_metadata.title,
                    "author": pr_metadata.author,
                })

                # Save review
                saved_paths = storage.save_review(result)
                console.print(f"[green]OK[/green] Review saved: {len(result.findings)} findings")
                console.print(f"  Time: {result.review_time_s:.1f}s")
                console.print(f"  Cost: ${result.token_cost_estimate:.4f}")

                reviews.append(result)

                # Extract ground truth
                important_issues = extract_important_issues_from_review(result)
                if important_issues:
                    # Determine category
                    category = categorize_pr(pr_metadata)

                    # Calculate false positive tolerance
                    total_findings = len(result.findings)
                    false_positive_tolerance = min(5, max(1, total_findings // 10))

                    gt_label = GroundTruthLabel(
                        pr_id=pr_id,
                        important_issues=important_issues,
                        false_positive_tolerance=false_positive_tolerance,
                        labeler_id="openai_review_extraction",
                        labeled_at=datetime.now(timezone.utc),
                        notes=f"Extracted from OpenAI review. Total findings: {total_findings}, "
                              f"Critical: {sum(1 for f in result.findings if f.severity == Severity.CRITICAL)}, "
                              f"Major: {sum(1 for f in result.findings if f.severity == Severity.MAJOR)}"
                    )

                    ground_truths.append({
                        "pr_id": pr_id,
                        "category": category,
                        "gt": gt_label
                    })

                    console.print(f"[green]OK[/green] Extracted {len(important_issues)} important issues")
                    console.print(f"  Category: {category}")
                else:
                    console.print("[yellow]WARNING[/yellow] No important issues found (only minor/nit findings)")

            except Exception as e:
                error_msg = _clean_text_for_terminal(str(e))
                console.print(f"[red]Error processing PR {pr_id}: {error_msg}[/red]")
                import traceback
                # Print traceback to stderr instead of console to avoid encoding issues
                import sys
                traceback.print_exc(file=sys.stderr)
                continue

            finally:
                progress.remove_task(task)

    # Save ground truth
    if ground_truths:
        console.print(f"\n[bold]Saving Ground Truth[/bold]")
        save_ground_truth(ground_truths, settings)
        console.print(f"[green]OK[/green] Saved ground truth for {len(ground_truths)} PRs")
    else:
        console.print("[yellow]WARNING[/yellow] No ground truth to save")

    # Summary
    console.print(f"\n[bold]Summary[/bold]")
    console.print(f"PRs reviewed: {len(reviews)}/{len(pr_id_list)}")
    console.print(f"Ground truth extracted: {len(ground_truths)} PRs")
    console.print(f"Total findings: {sum(len(r.findings) for r in reviews)}")
    console.print(f"Total cost: ${sum(r.token_cost_estimate for r in reviews):.4f}")
    console.print(f"Total time: {sum(r.review_time_s for r in reviews):.1f}s")

    if len(reviews) < len(pr_id_list):
        console.print(f"[yellow]WARNING[/yellow] {len(pr_id_list) - len(reviews)} PRs failed")


if __name__ == "__main__":
    app()

