"""Review storage and management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.config import Settings
from app.logging import get_logger
from domain import PRReviewResult, Severity

logger = get_logger(__name__)


class ReviewStorage:
    """Manages storage and retrieval of review results."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.reviews_path = settings.reviews_path
        self.reviews_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.reviews_path / "index.json"

    def save_review(self, result: PRReviewResult) -> Dict[str, Path]:
        """Save review result in multiple formats.

        Returns:
            Dict with paths to saved files (markdown, json, summary)
        """
        pr_id = result.pr_id

        # Create PR-specific directory
        pr_dir = self.reviews_path / pr_id
        pr_dir.mkdir(exist_ok=True)

        # Save markdown comment
        md_path = pr_dir / "review.md"
        md_path.write_text(result.final_comment_md)

        # Save full JSON result
        json_path = pr_dir / "review.json"
        json_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2))

        # Update index
        self._update_index(result)

        logger.info(f"Review saved: {pr_id} -> {pr_dir}")

        return {
            "markdown": md_path,
            "json": json_path,
            "directory": pr_dir,
        }

    def _update_index(self, result: PRReviewResult) -> None:
        """Update review index with new review."""
        index = self._load_index()

        # Create summary entry
        summary = {
            "pr_id": result.pr_id,
            "repository": result.metadata.get("repository", "unknown"),
            "title": result.metadata.get("title", ""),
            "system_type": result.system_type.value,
            "review_time_s": result.review_time_s,
            "token_cost": result.token_cost_estimate,
            "findings_count": len(result.findings),
            "findings_by_severity": {
                severity.value: len(findings)
                for severity, findings in result.findings_by_severity.items()
            },
            "created_at": result.created_at.isoformat(),
            "reviewed_at": datetime.utcnow().isoformat(),
        }

        # Update or add entry
        index[result.pr_id] = summary

        # Save index
        self.index_file.write_text(json.dumps(index, indent=2, sort_keys=True))

    def _load_index(self) -> Dict[str, Dict]:
        """Load review index."""
        if not self.index_file.exists():
            return {}

        try:
            return json.loads(self.index_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def get_review(self, pr_id: str) -> Optional[PRReviewResult]:
        """Load a review by PR ID."""
        json_path = self.reviews_path / pr_id / "review.json"

        if not json_path.exists():
            return None

        try:
            data = json.loads(json_path.read_text())
            return PRReviewResult(**data)
        except Exception as e:
            logger.error(f"Failed to load review {pr_id}: {e}")
            return None

    def list_reviews(self, limit: Optional[int] = None) -> List[Dict]:
        """List all reviews from index."""
        index = self._load_index()
        reviews = list(index.values())

        # Sort by reviewed_at (newest first)
        reviews.sort(key=lambda x: x.get("reviewed_at", ""), reverse=True)

        if limit:
            reviews = reviews[:limit]

        return reviews

    def get_summary(self) -> Dict:
        """Get summary statistics of all reviews."""
        index = self._load_index()
        reviews = list(index.values())

        if not reviews:
            return {
                "total_reviews": 0,
                "total_findings": 0,
                "avg_review_time": 0.0,
                "total_cost": 0.0,
            }

        total_findings = sum(r.get("findings_count", 0) for r in reviews)
        total_time = sum(r.get("review_time_s", 0.0) for r in reviews)
        total_cost = sum(r.get("token_cost", 0.0) for r in reviews)

        # Count by severity
        severity_counts = {
            severity.value: sum(
                r.get("findings_by_severity", {}).get(severity.value, 0)
                for r in reviews
            )
            for severity in Severity
        }

        return {
            "total_reviews": len(reviews),
            "total_findings": total_findings,
            "avg_findings_per_review": total_findings / len(reviews) if reviews else 0,
            "avg_review_time": total_time / len(reviews) if reviews else 0.0,
            "total_cost": total_cost,
            "avg_cost": total_cost / len(reviews) if reviews else 0.0,
            "findings_by_severity": severity_counts,
            "last_reviewed": max((r.get("reviewed_at", "") for r in reviews), default=""),
        }
