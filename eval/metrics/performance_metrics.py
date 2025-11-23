"""Performance and cost metrics."""

from typing import Dict, List

from domain import GroundTruthLabel, PRReviewResult
from eval.metrics.base import BaseMetric


class PerformanceMetric(BaseMetric):
    """Calculates performance metrics (time, cost)."""

    def __init__(self):
        super().__init__("performance")

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate performance metrics."""
        if not results:
            return {
                "avg_review_time_s": 0.0,
                "avg_token_cost": 0.0,
                "avg_findings_per_pr": 0.0,
            }

        total_time = sum(r.review_time_s for r in results)
        total_cost = sum(r.token_cost_estimate for r in results)
        total_findings = sum(len(r.findings) for r in results)

        return {
            "avg_review_time_s": total_time / len(results),
            "avg_token_cost": total_cost / len(results),
            "avg_findings_per_pr": total_findings / len(results),
            "total_review_time_s": total_time,
            "total_cost": total_cost,
        }


class ThesisMetrics(BaseMetric):
    """Calculates thesis-specific CTR/CL/SI scores."""

    def __init__(self):
        super().__init__("thesis_metrics")

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate CTR, CL, SI scores.

        These require manual evaluation, so we provide placeholders
        for the evaluation framework to fill in.
        """
        # These would be calculated from manual evaluation data
        # For now, return placeholders
        return {
            "change_type_recognition_score": 0.0,
            "change_location_score": 0.0,
            "solution_logic_score": 0.0,
        }
