"""Base classes for evaluation metrics."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from domain import EvaluationResult, GroundTruthLabel, PRReviewResult, SystemType


class BaseMetric(ABC):
    """Abstract base class for evaluation metrics."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate metric value.

        Args:
            results: List of review results
            ground_truth: Ground truth labels by PR ID

        Returns:
            Dictionary of metric values
        """
        pass


class MetricsAggregator:
    """Aggregates metrics from multiple calculators."""

    def __init__(self):
        self.metrics: List[BaseMetric] = []

    def register(self, metric: BaseMetric) -> None:
        """Register a metric calculator."""
        self.metrics.append(metric)

    def evaluate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
        system_type: SystemType,
    ) -> EvaluationResult:
        """Run all metrics and aggregate results.

        Args:
            results: Review results to evaluate
            ground_truth: Ground truth labels
            system_type: System being evaluated

        Returns:
            Complete EvaluationResult
        """
        all_metrics: Dict[str, Any] = {}

        for metric in self.metrics:
            metric_values = metric.calculate(results, ground_truth)
            all_metrics.update(metric_values)

        # Calculate core metrics
        actionability_rate = all_metrics.get("actionability_rate", 0.0)
        noise_rate = all_metrics.get("noise_rate", 0.0)
        coverage = all_metrics.get("important_issue_coverage", 0.0)

        # Extract other metrics
        avg_findings = all_metrics.get("avg_findings_per_pr", 0.0)
        avg_time = all_metrics.get("avg_review_time_s", 0.0)
        avg_cost = all_metrics.get("avg_token_cost", 0.0)

        ctr_score = all_metrics.get("change_type_recognition_score", 0.0)
        cl_score = all_metrics.get("change_location_score", 0.0)
        sl_score = all_metrics.get("solution_logic_score", 0.0)

        confidence_intervals = all_metrics.get("confidence_intervals", {})

        return EvaluationResult(
            system_type=system_type,
            dataset_size=len(results),
            actionability_rate=actionability_rate,
            noise_rate=noise_rate,
            important_issue_coverage=coverage,
            avg_findings_per_pr=avg_findings,
            avg_review_time_s=avg_time,
            avg_token_cost=avg_cost,
            change_type_recognition_score=ctr_score,
            change_location_score=cl_score,
            solution_logic_score=sl_score,
            confidence_interval_95=confidence_intervals,
            metadata=all_metrics,
        )
