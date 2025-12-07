#!/usr/bin/env python3
"""Script to review open PRs from a GitHub repository."""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def get_open_prs(owner: str, repo: str, token: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get open PRs from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    params = {"state": "open", "per_page": limit, "sort": "updated", "direction": "desc"}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def clone_or_update_repo(repo_url: str, repo_path: Path) -> None:
    """Clone or update repository."""
    if repo_path.exists():
        console.print(f"[yellow]Repository exists, updating...[/yellow]")
        subprocess.run(["git", "fetch", "origin"], cwd=repo_path, check=True)
        subprocess.run(["git", "checkout", "master"], cwd=repo_path, check=True)
        subprocess.run(["git", "pull", "origin", "master"], cwd=repo_path, check=True)
    else:
        console.print(f"[cyan]Cloning repository...[/cyan]")
        subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)


def checkout_pr_branch(repo_path: Path, pr_number: int) -> None:
    """Checkout PR branch."""
    branch_name = f"pr-{pr_number}"

    # Fetch PR
    subprocess.run(
        ["git", "fetch", "origin", f"pull/{pr_number}/head:{branch_name}"],
        cwd=repo_path,
        check=True,
    )

    # Checkout branch
    subprocess.run(["git", "checkout", branch_name], cwd=repo_path, check=True)
    console.print(f"[green]Checked out PR #{pr_number}[/green]")


def review_pr(
    repo_path: Path,
    pr_number: int,
    title: str,
    description: str,
    language: str = "python",
) -> None:
    """Run review on a PR."""
    project_root = Path(__file__).parent.parent

    cmd = [
        sys.executable,
        "-m",
        "app.cli",
        "review",
        str(repo_path),
        "--pr-id",
        str(pr_number),
        "--title",
        title,
        "--description",
        description[:200],  # Limit description length
        "--language",
        language,
        "--multi-agent",
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            console.print(f"[green]✓ Review completed for PR #{pr_number}[/green]")
        else:
            console.print(f"[red]✗ Review failed for PR #{pr_number}[/red]")
            console.print(result.stderr)
    except subprocess.TimeoutExpired:
        console.print(f"[red]✗ Review timed out for PR #{pr_number}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error reviewing PR #{pr_number}: {e}[/red]")


def main():
    """Main function."""
    import argparse
    from app.config import get_settings
    from app.review_storage import ReviewStorage

    parser = argparse.ArgumentParser(description="Review open PRs from GitHub")
    parser.add_argument("owner", help="Repository owner")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument("--token", help="GitHub token (overrides settings)")
    parser.add_argument("--limit", type=int, default=5, help="Number of PRs to review")
    parser.add_argument("--repo-path", type=Path, default=Path("/tmp") / "Python", help="Local repo path")
    parser.add_argument("--language", default="python", help="Primary language")

    args = parser.parse_args()

    # Get token from args, settings, or environment
    token = args.token
    if not token:
        try:
            settings = get_settings()
            token = settings.github_token
        except Exception:
            pass
    if not token:
        token = os.getenv("GITHUB_TOKEN")

    if not token:
        console.print("[red]Error: GitHub token not configured[/red]")
        console.print("Set GITHUB_TOKEN in .env file, environment variable, or use --token flag")
        sys.exit(1)

    # Get open PRs
    console.print(f"[bold]Fetching open PRs from {args.owner}/{args.repo}...[/bold]")
    prs = get_open_prs(args.owner, args.repo, token, args.limit)

    if not prs:
        console.print("[yellow]No open PRs found[/yellow]")
        return

    console.print(f"[green]Found {len(prs)} open PR(s)[/green]")

    # Clone/update repository
    repo_url = f"https://github.com/{args.owner}/{args.repo}.git"
    clone_or_update_repo(repo_url, args.repo_path)

    # Review each PR
    for pr in prs:
        pr_number = pr["number"]
        title = pr["title"]
        description = pr.get("body", "") or ""

        console.print(f"\n[bold cyan]Reviewing PR #{pr_number}: {title}[/bold cyan]")

        try:
            checkout_pr_branch(args.repo_path, pr_number)
            review_pr(args.repo_path, pr_number, title, description, args.language)
        except Exception as e:
            console.print(f"[red]Error processing PR #{pr_number}: {e}[/red]")
            continue

    console.print("\n[bold green]All reviews completed![/bold green]")
    console.print(f"[cyan]Review files saved in: {Path.cwd()}/reviews/[/cyan]")

    # Show summary
    try:
        settings = get_settings()
        storage = ReviewStorage(settings)
        summary = storage.get_summary()

        console.print(f"\n[bold]Review Summary:[/bold]")
        console.print(f"Total reviews: {summary['total_reviews']}")
        console.print(f"Total findings: {summary['total_findings']}")
        console.print(f"Average review time: {summary['avg_review_time']:.2f}s")
    except Exception as e:
        console.print(f"[yellow]Could not load review summary: {e}[/yellow]")


if __name__ == "__main__":
    main()
