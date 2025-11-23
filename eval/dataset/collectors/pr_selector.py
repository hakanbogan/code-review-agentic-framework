"""PR selection logic for dataset curation."""

from typing import Any, Dict, List

from app.logging import get_logger

logger = get_logger(__name__)


class PRSelector:
    """Selects appropriate PRs for evaluation dataset."""

    def __init__(
        self,
        min_lines: int = 50,
        max_lines: int = 500,
        min_files: int = 1,
        max_files: int = 15,
        require_review: bool = True,
    ):
        """Initialize selector.

        Args:
            min_lines: Minimum total lines changed
            max_lines: Maximum total lines changed
            min_files: Minimum files changed
            max_files: Maximum files changed
            require_review: Require at least one review comment
        """
        self.min_lines = min_lines
        self.max_lines = max_lines
        self.min_files = min_files
        self.max_files = max_files
        self.require_review = require_review

    def filter_prs(
        self,
        prs: List[Dict[str, Any]],
        files_data: Dict[int, List[Dict[str, Any]]],
        reviews_data: Dict[int, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Filter PRs based on criteria.

        Args:
            prs: List of PR data
            files_data: Mapping of PR number to files changed
            reviews_data: Mapping of PR number to reviews

        Returns:
            Filtered list of PRs
        """
        filtered = []

        for pr in prs:
            pr_number = pr["number"]

            # Must be merged
            if not pr.get("merged_at"):
                continue

            # Check file count
            files = files_data.get(pr_number, [])
            if len(files) < self.min_files or len(files) > self.max_files:
                continue

            # Check if Python files present
            python_files = [f for f in files if f.get("filename", "").endswith(".py")]
            if not python_files:
                continue

            # Check lines changed
            additions = pr.get("additions", 0)
            deletions = pr.get("deletions", 0)
            total_lines = additions + deletions

            if total_lines < self.min_lines or total_lines > self.max_lines:
                continue

            # Check for reviews if required
            if self.require_review:
                reviews = reviews_data.get(pr_number, [])
                if not reviews or len(reviews) == 0:
                    continue

            filtered.append(pr)

        logger.info(f"Filtered {len(filtered)} PRs from {len(prs)} total")
        return filtered

    def categorize_pr(self, pr: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        """Categorize PR by type.

        Args:
            pr: PR data
            files: Files changed in PR

        Returns:
            Category string (feature, bugfix, refactor, security, test, other)
        """
        title = pr.get("title", "").lower()
        body = pr.get("body", "").lower()
        labels = [label.get("name", "").lower() for label in pr.get("labels", [])]

        # Security
        if any(word in title for word in ["security", "vulnerability", "cve"]):
            return "security"
        if any(word in labels for word in ["security", "vulnerability"]):
            return "security"

        # Bug fix
        if any(word in title for word in ["fix", "bug", "issue", "error"]):
            return "bugfix"
        if any(word in labels for word in ["bug", "bugfix"]):
            return "bugfix"

        # Test
        test_files = [f for f in files if "test" in f.get("filename", "").lower()]
        if len(test_files) == len(files):  # Only test files
            return "test"

        # Refactor
        if any(word in title for word in ["refactor", "cleanup", "reorganize"]):
            return "refactor"
        if any(word in labels for word in ["refactor", "cleanup"]):
            return "refactor"

        # Feature
        if any(word in title for word in ["add", "implement", "feature", "new"]):
            return "feature"
        if any(word in labels for word in ["feature", "enhancement"]):
            return "feature"

        return "other"

    def select_balanced_dataset(
        self,
        prs: List[Dict[str, Any]],
        files_data: Dict[int, List[Dict[str, Any]]],
        target_per_category: int = 5,
    ) -> List[Dict[str, Any]]:
        """Select balanced dataset across categories.

        Args:
            prs: Filtered PRs
            files_data: Files data for categorization
            target_per_category: Target PRs per category

        Returns:
            Balanced selection of PRs
        """
        categorized: Dict[str, List[Dict[str, Any]]] = {
            "feature": [],
            "bugfix": [],
            "refactor": [],
            "security": [],
            "test": [],
            "other": [],
        }

        # Categorize all PRs
        for pr in prs:
            pr_number = pr["number"]
            files = files_data.get(pr_number, [])
            category = self.categorize_pr(pr, files)
            categorized[category].append(pr)

        # Log distribution
        for category, category_prs in categorized.items():
            logger.info(f"Category '{category}': {len(category_prs)} PRs")

        # Select balanced subset
        selected = []
        for category in ["security", "bugfix", "feature", "refactor"]:
            category_prs = categorized[category]
            count = min(len(category_prs), target_per_category)
            selected.extend(category_prs[:count])

        logger.info(f"Selected {len(selected)} PRs across categories")
        return selected

    def calculate_complexity_score(
        self,
        pr: Dict[str, Any],
        files: List[Dict[str, Any]],
    ) -> int:
        """Calculate PR complexity score.

        Args:
            pr: PR data
            files: Files changed

        Returns:
            Complexity score (0-100)
        """
        score = 0

        # Lines changed (max 40 points)
        total_lines = pr.get("additions", 0) + pr.get("deletions", 0)
        score += min(40, total_lines // 10)

        # Files changed (max 30 points)
        score += min(30, len(files) * 5)

        # Commits (max 20 points)
        score += min(20, pr.get("commits", 0) * 2)

        # Python percentage (max 10 points)
        python_files = [f for f in files if f.get("filename", "").endswith(".py")]
        python_pct = len(python_files) / len(files) if files else 0
        score += int(python_pct * 10)

        return min(100, score)
