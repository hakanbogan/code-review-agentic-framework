"""GitHub API client for collecting PR data."""

import time
from typing import Any, Dict, List, Optional

import requests

from app.logging import get_logger

logger = get_logger(__name__)


class GitHubPRCollector:
    """Collects PR data from GitHub API."""

    def __init__(self, token: str):
        """Initialize collector.

        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository data
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = self._make_request(url)
        return response.json()

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        per_page: int = 100,
        max_pages: int = 3,
    ) -> List[Dict[str, Any]]:
        """List pull requests from repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            per_page: Results per page
            max_pages: Maximum pages to fetch

        Returns:
            List of PR data
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "per_page": per_page,
        }

        all_prs = []
        for page in range(1, max_pages + 1):
            params["page"] = page
            response = self._make_request(url, params=params)
            prs = response.json()

            if not prs:
                break

            all_prs.extend(prs)
            logger.info(f"Fetched page {page}: {len(prs)} PRs from {owner}/{repo}")

            # Respect rate limits
            time.sleep(1)

        return all_prs

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get detailed PR information.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Detailed PR data
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = self._make_request(url)
        return response.json()

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Get PR diff content.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Diff content as string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        response = self._make_request(url, headers=headers)
        return response.text

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get files changed in PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of changed files
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = self._make_request(url)
        return response.json()

    def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get commits in PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of commits
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        response = self._make_request(url)
        return response.json()

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get reviews for PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of reviews
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        response = self._make_request(url)
        return response.json()

    def get_pr_review_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> List[Dict[str, Any]]:
        """Get review comments for PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of review comments
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        response = self._make_request(url)
        return response.json()

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Rate limit information
        """
        url = f"{self.base_url}/rate_limit"
        response = self._make_request(url)
        return response.json()

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Make HTTP request with error handling.

        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails
        """
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.get(url, params=params, headers=request_headers)
            response.raise_for_status()

            # Log rate limit info
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining:
                logger.debug(f"Rate limit remaining: {remaining}")

            return response

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                # Rate limit exceeded
                reset_time = e.response.headers.get("X-RateLimit-Reset")
                logger.error(f"Rate limit exceeded. Resets at: {reset_time}")
            raise
