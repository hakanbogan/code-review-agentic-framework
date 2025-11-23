"""Transform GitHub API data to our domain models."""

from typing import Any, Dict, List

from domain import GroundTruthLabel, PRMetadata
from app.logging import get_logger

logger = get_logger(__name__)


class DataTransformer:
    """Transforms GitHub API responses to our data models."""

    @staticmethod
    def pr_to_metadata(
        pr: Dict[str, Any],
        files: List[Dict[str, Any]],
        commits: List[Dict[str, Any]],
    ) -> PRMetadata:
        """Transform GitHub PR to PRMetadata.

        Args:
            pr: GitHub PR data
            files: Files changed
            commits: Commit data

        Returns:
            PRMetadata object
        """
        # Extract commit messages
        commit_messages = [
            c.get("commit", {}).get("message", "").split("\n")[0]
            for c in commits
        ]

        # Count Python files
        python_files = [f for f in files if f.get("filename", "").endswith(".py")]

        return PRMetadata(
            pr_id=str(pr["number"]),
            repository=pr["base"]["repo"]["full_name"],
            branch_source=pr["head"]["ref"],
            branch_target=pr["base"]["ref"],
            title=pr["title"],
            description=pr.get("body", ""),
            author=pr["user"]["login"],
            commit_messages=commit_messages,
            files_changed=len(files),
            lines_added=pr.get("additions", 0),
            lines_deleted=pr.get("deletions", 0),
            language="python",
        )

    @staticmethod
    def extract_ground_truth_from_reviews(
        pr: Dict[str, Any],
        review_comments: List[Dict[str, Any]],
    ) -> GroundTruthLabel:
        """Extract ground truth from review comments.

        Args:
            pr: GitHub PR data
            review_comments: Review comments

        Returns:
            GroundTruthLabel object
        """
        important_issues = []

        # Extract issues from review comments
        for comment in review_comments:
            body = comment.get("body", "")

            # Heuristics for important issues
            if any(keyword in body.lower() for keyword in [
                "security", "vulnerability", "injection", "xss", "sql",
                "bug", "error", "crash", "fail",
                "breaking", "critical", "must fix",
            ]):
                # Create issue description with location
                path = comment.get("path", "")
                line = comment.get("original_line") or comment.get("line")
                issue = f"{body[:100]}... @ {path}:{line}" if line else body[:100]
                important_issues.append(issue)

        return GroundTruthLabel(
            pr_id=str(pr["number"]),
            important_issues=important_issues,
            false_positive_tolerance=min(5, len(review_comments) // 3),
            labeler_id="github_reviewers",
            notes=f"Extracted from {len(review_comments)} review comments",
        )

    @staticmethod
    def filter_python_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter to only Python files.

        Args:
            files: List of file changes

        Returns:
            Filtered list
        """
        return [
            f for f in files
            if f.get("filename", "").endswith(".py")
            and not f.get("filename", "").startswith("test")
            and f.get("status") != "removed"
        ]

    @staticmethod
    def calculate_file_stats(files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate statistics from files.

        Args:
            files: List of file changes

        Returns:
            Statistics dictionary
        """
        python_files = DataTransformer.filter_python_files(files)

        return {
            "total_files": len(files),
            "python_files": len(python_files),
            "additions": sum(f.get("additions", 0) for f in files),
            "deletions": sum(f.get("deletions", 0) for f in files),
            "changes": sum(f.get("changes", 0) for f in files),
        }
