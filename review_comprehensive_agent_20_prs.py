"""Review 20 PRs using comprehensive agent."""

import typer
from pathlib import Path
from typing import Optional
from app.config import get_settings
from flows.review_flow import ReviewFlow
from domain import PRMetadata, Language

app = typer.Typer()

@app.command()
def main(
    repo_path: Path = typer.Option(..., "--repo-path", help="Repository path"),
    pr_ids: str = typer.Option(..., "--pr-ids", help="Comma-separated PR IDs"),
    language: str = typer.Option("python", "--language", help="Primary language"),
):
    """Review 20 PRs using comprehensive agent."""
    settings = get_settings()
    
    pr_id_list = [pid.strip() for pid in pr_ids.split(",")]
    
    print(f"Reviewing {len(pr_id_list)} PRs with comprehensive agent...")
    
    language_enum = Language.PYTHON if language == "python" else Language.JAVASCRIPT
    flow = ReviewFlow(settings, language=language_enum)
    
    for pr_id in pr_id_list:
        print(f"\nProcessing PR {pr_id}...")
        # Note: Comprehensive agent was removed, this is a placeholder
        print(f"  WARNING: Comprehensive agent is no longer available")

if __name__ == "__main__":
    app()

