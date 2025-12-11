"""Benchmark comparison metrics using dataset statistics."""

from typing import Any, Dict, List

from domain import GroundTruthLabel, PRReviewResult
from eval.metrics.base import BaseMetric


class BenchmarkComparisonMetric(BaseMetric):
    """Compare review results against category benchmarks from dataset."""

    def __init__(self, category_benchmarks: Dict[str, Any], categorizer_fn):
        super().__init__("benchmark_comparison")
        self.benchmarks = category_benchmarks
        self.categorizer_fn = categorizer_fn

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate benchmark-based metrics.

        Compares review results against dataset category benchmarks:
        - Normalized findings ratio (actual / expected)
        - Deviation score (how far from expected)
        - Quality score (combination of metrics)
        """
        if not self.benchmarks:
            return {}

        total_normalized_ratio = 0.0
        total_deviation = 0.0
        total_quality_score = 0.0
        count = 0

        category_stats = {
            "bugfix": {"count": 0, "avg_ratio": 0.0, "avg_deviation": 0.0},
            "feature": {"count": 0, "avg_ratio": 0.0, "avg_deviation": 0.0},
            "refactor": {"count": 0, "avg_ratio": 0.0, "avg_deviation": 0.0},
        }

        for result in results:
            # Categorize PR
            category = self._categorize_from_result(result)
            if category not in self.benchmarks:
                continue

            benchmark = self.benchmarks[category]
            stats = benchmark.get("statistics", {})
            expected_issues = stats.get("avg_issues_per_pr", 0)

            if expected_issues == 0:
                continue

            actual_issues = len(result.findings)

            # Normalized ratio (1.0 = perfect match)
            normalized_ratio = actual_issues / expected_issues

            # Deviation score (0 = perfect match, negative = under, positive = over)
            deviation = (actual_issues - expected_issues) / expected_issues

            # Quality score: penalize both under and over detection
            quality_score = 1.0 - min(abs(deviation), 1.0)

            total_normalized_ratio += normalized_ratio
            total_deviation += deviation
            total_quality_score += quality_score
            count += 1

            # Track per-category
            if category in category_stats:
                cat_stat = category_stats[category]
                cat_stat["count"] += 1
                cat_stat["avg_ratio"] += normalized_ratio
                cat_stat["avg_deviation"] += deviation

        if count == 0:
            return {}

        # Calculate averages
        avg_normalized_ratio = total_normalized_ratio / count
        avg_deviation = total_deviation / count
        avg_quality_score = total_quality_score / count

        # Calculate per-category averages
        for category, stat in category_stats.items():
            if stat["count"] > 0:
                stat["avg_ratio"] /= stat["count"]
                stat["avg_deviation"] /= stat["count"]

        return {
            "benchmark_normalized_ratio": avg_normalized_ratio,
            "benchmark_deviation": avg_deviation,
            "benchmark_quality_score": avg_quality_score,
            "benchmark_category_stats": category_stats,
            "benchmark_evaluated_prs": count,
        }

    def _categorize_from_result(self, result: PRReviewResult) -> str:
        """Extract or infer category from review result."""
        # Check if category is already in metadata
        if "category" in result.metadata:
            return result.metadata["category"]

        # Use categorizer function if available
        if self.categorizer_fn and "pr_metadata" in result.metadata:
            return self.categorizer_fn(result.metadata["pr_metadata"])

        # Fallback: analyze change summary
        summary_lower = result.change_summary.lower()
        if any(word in summary_lower for word in ["fix", "bug", "error"]):
            return "bugfix"
        if any(word in summary_lower for word in ["refactor", "cleanup"]):
            return "refactor"
        if any(word in summary_lower for word in ["add", "new", "feature"]):
            return "feature"

        return "other"
