"""Evaluation metrics package."""

from eval.metrics.base import BaseMetric, MetricsAggregator
from eval.metrics.core_metrics import ActionabilityMetric, CoverageMetric, NoiseMetric
from eval.metrics.performance_metrics import PerformanceMetric
from eval.metrics.benchmark_metrics import BenchmarkComparisonMetric
from eval.metrics.advanced_metrics import (
    PrecisionRecallMetric,
    AnomalyDetectionMetric,
    CategoryThresholdMetric,
)
from eval.metrics.statistical import (
    calculate_confidence_interval,
    cohens_kappa,
    effect_size_cohens_d,
    mann_whitney_test,
    proportion_test,
    wilcoxon_test,
)

__all__ = [
    "BaseMetric",
    "MetricsAggregator",
    "ActionabilityMetric",
    "NoiseMetric",
    "CoverageMetric",
    "PerformanceMetric",
    "BenchmarkComparisonMetric",
    "PrecisionRecallMetric",
    "AnomalyDetectionMetric",
    "CategoryThresholdMetric",
    "calculate_confidence_interval",
    "proportion_test",
    "wilcoxon_test",
    "mann_whitney_test",
    "cohens_kappa",
    "effect_size_cohens_d",
]
