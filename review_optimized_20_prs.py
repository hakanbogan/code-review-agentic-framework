"""Review 20 PRs with optimized system."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from app.config import get_settings
from flows.review_flow import ReviewFlow
from domain import PRMetadata, Language
from tools.github import fetch_pr_info
from tools.git_utils import checkout_pr_branch

app = typer.Typer()
console = Console()

@app.command()
def main(
    repo_path: Path = typer.Option(..., "--repo-path", help="Repository path"),
    repo_url: str = typer.Option(..., "--repo-url", help="GitHub repository URL"),
    pr_ids: str = typer.Option(..., "--pr-ids", help="Comma-separated PR IDs"),
    language: str = typer.Option("python", "--language", help="Primary language"),
):
    """Review 20 PRs with optimized multi-agent system."""
    settings = get_settings()
    
    pr_id_list = [pid.strip() for pid in pr_ids.split(",")]
    language_enum = Language.PYTHON if language == "python" else Language.JAVASCRIPT
    
    console.print(f"[bold]Reviewing {len(pr_id_list)} PRs with optimized system[/bold]")
    
    flow = ReviewFlow(settings, language=language_enum)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for i, pr_id in enumerate(pr_id_list, 1):
            task = progress.add_task(f"[cyan]Reviewing PR {pr_id} ({i}/{len(pr_id_list)})...", total=None)
            
            try:
                # Fetch PR info
                console.print(f"\n[bold]PR {pr_id}[/bold]")
                pr_info = fetch_pr_info(repo_url, pr_id, settings.github_token)
                
                # Checkout PR branch
                merge_base, _ = checkout_pr_branch(repo_path, pr_id)
                
                # Create PR metadata
                pr_metadata = PRMetadata(
                    pr_id=pr_id,
                    repository=repo_path.name,
                    branch_source=pr_info["head"]["ref"],
                    branch_target=pr_info["base"]["ref"],
                    title=pr_info["title"],
                    description=pr_info.get("body", "") or "",
                    author=pr_info["user"]["login"],
                    language=language_enum,
                )
                
                # Run review with optimized multi-agent system
                console.print(f"[cyan]Running optimized multi-agent review...[/cyan]")
                result = flow.run_multi_agent_review(pr_metadata, repo_path, base_branch=merge_base)
                
                console.print(f"[green]OK[/green] Review completed: {len(result.findings)} findings")
                
            except Exception as e:
                console.print(f"[red]Error processing PR {pr_id}: {e}[/red]")
                continue
            finally:
                progress.remove_task(task)
    
    console.print(f"\n[bold green]All reviews completed![/bold green]")

if __name__ == "__main__":
    app()

