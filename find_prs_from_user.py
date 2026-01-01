"""Find PRs from a specific GitHub user."""

import typer
from typing import Optional
from app.config import get_settings

app = typer.Typer()

@app.command()
def main(
    username: str = typer.Option(..., "--username", help="GitHub username"),
    repo: str = typer.Option(..., "--repo", help="Repository (owner/repo)"),
    state: str = typer.Option("open", "--state", help="PR state (open, closed, all)"),
    limit: int = typer.Option(10, "--limit", help="Maximum number of PRs to return"),
):
    """Find PRs from a specific GitHub user."""
    settings = get_settings()
    
    import requests
    
    if not settings.github_token:
        print("ERROR: GitHub token not found. Set GITHUB_TOKEN environment variable.")
        return
    
    headers = {"Authorization": f"token {settings.github_token}"}
    url = f"https://api.github.com/repos/{repo}/pulls"
    
    params = {
        "state": state,
        "per_page": min(limit, 100),
        "page": 1
    }
    
    print(f"Searching for PRs from {username} in {repo}...")
    
    prs = []
    page = 1
    
    while len(prs) < limit:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"ERROR: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        if not data:
            break
        
        for pr in data:
            if pr["user"]["login"] == username:
                prs.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "url": pr["html_url"]
                })
                if len(prs) >= limit:
                    break
        
        page += 1
        if len(data) < 100:
            break
    
    print(f"\nFound {len(prs)} PRs:")
    for pr in prs:
        print(f"  #{pr['number']}: {pr['title']} ({pr['state']})")
        print(f"    {pr['url']}")

if __name__ == "__main__":
    app()

