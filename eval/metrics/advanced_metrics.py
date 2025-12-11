"""Advanced evaluation metrics: Precision, Recall, F1-Score, Anomaly Detection."""

from typing import Any, Callable, Dict, List, Optional

from domain import GroundTruthLabel, PRMetadata, PRReviewResult, Severity
from eval.metrics.base import BaseMetric


class PrecisionRecallMetric(BaseMetric):
    """Calculate Precision, Recall, and F1-Score.

    Uses proxy metrics when full ground truth is unavailable:
    - Precision proxy: Actionable findings / Total findings
    - Recall: Coverage metric (important issues detected)
    - F1-Score: Harmonic mean of Precision and Recall
    """

    def __init__(self, categorizer_fn: Optional[Callable[[PRMetadata], str]] = None):
        super().__init__("precision_recall")
        self.categorizer_fn = categorizer_fn

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate precision, recall, and F1-score metrics."""
        total_findings = 0
        total_actionable = 0
        total_important_issues = 0
        total_detected_important = 0

        precision_per_pr = []
        recall_per_pr = []
        f1_per_pr = []

        for result in results:
            findings = result.findings
            pr_findings = len(findings)
            total_findings += pr_findings

            # Precision proxy: actionable findings
            actionable = sum(1 for f in findings
                             if f.has_patch or (f.severity in [Severity.MAJOR, Severity.CRITICAL]
                                                and f.location and f.evidence.reference))
            total_actionable += actionable

            # Calculate per-PR precision
            pr_precision = actionable / pr_findings if pr_findings > 0 else 0.0
            precision_per_pr.append(pr_precision)

            # Recall: from ground truth (if available)
            gt = ground_truth.get(result.pr_id)
            if gt and gt.important_issues:
                important_count = len(gt.important_issues)
                total_important_issues += important_count

                # Simple matching: check if finding mentions important issue
                detected = 0
                finding_texts = [f"{f.title.lower()} {f.description.lower()}" for f in findings]

                for issue in gt.important_issues:
                    issue_lower = issue.lower()
                    issue_keywords = [w for w in issue_lower.split() if len(w) > 3]

                    for text in finding_texts:
                        # Match if issue substring or 50%+ keywords found
                        if issue_lower in text or (issue_keywords and
                                                   sum(1 for kw in issue_keywords if kw in text) / len(issue_keywords) >= 0.5):
                            detected += 1
                            break

                total_detected_important += detected
                pr_recall = detected / important_count if important_count > 0 else 0.0
                recall_per_pr.append(pr_recall)

                # F1-Score per PR
                if pr_precision + pr_recall > 0:
                    pr_f1 = 2 * (pr_precision * pr_recall) / (pr_precision + pr_recall)
                    f1_per_pr.append(pr_f1)

        # Overall metrics
        precision = total_actionable / total_findings if total_findings > 0 else 0.0
        recall = total_detected_important / total_important_issues if total_important_issues > 0 else 0.0

        # F1-Score
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Average per-PR metrics
        avg_precision = sum(precision_per_pr) / len(precision_per_pr) if precision_per_pr else 0.0
        avg_recall = sum(recall_per_pr) / len(recall_per_pr) if recall_per_pr else 0.0
        avg_f1 = sum(f1_per_pr) / len(f1_per_pr) if f1_per_pr else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "avg_precision_per_pr": avg_precision,
            "avg_recall_per_pr": avg_recall,
            "avg_f1_per_pr": avg_f1,
            "total_actionable_findings": total_actionable,
            "total_important_issues": total_important_issues,
            "total_detected_important": total_detected_important,
        }


class AnomalyDetectionMetric(BaseMetric):
    """Detect anomalies in review results based on category benchmarks.

    Identifies PRs with:
    - Too many findings (over-detection)
    - Too few findings (under-detection)
    - Unusual patterns compared to category norms
    """

    def __init__(self, category_benchmarks: Dict[str, Any], categorizer_fn):
        super().__init__("anomaly_detection")
        self.benchmarks = category_benchmarks
        self.categorizer_fn = categorizer_fn

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, Any]:
        """Detect anomalies in review results."""
        if not self.benchmarks:
            return {}

        anomalies = []
        over_detection_count = 0
        under_detection_count = 0
        extreme_deviation_count = 0

        # Thresholds for anomaly detection
        OVER_THRESHOLD = 2.5  # 250% more than expected
        UNDER_THRESHOLD = 0.4  # 60% less than expected
        EXTREME_THRESHOLD = 4.0  # 400% deviation

        for result in results:
            category = self._categorize_from_result(result)
            if category not in self.benchmarks:
                continue

            benchmark = self.benchmarks[category]
            stats = benchmark.get("statistics", {})
            expected_issues = stats.get("avg_issues_per_pr", 0)

            if expected_issues == 0:
                continue

            actual_issues = len(result.findings)
            ratio = actual_issues / expected_issues

            anomaly_type = None
            severity = "normal"

            # Detect over-detection
            if ratio > EXTREME_THRESHOLD:
                anomaly_type = "extreme_over_detection"
                severity = "critical"
                extreme_deviation_count += 1
                over_detection_count += 1
            elif ratio > OVER_THRESHOLD:
                anomaly_type = "over_detection"
                severity = "warning"
                over_detection_count += 1

            # Detect under-detection
            elif ratio < UNDER_THRESHOLD:
                anomaly_type = "under_detection"
                severity = "warning"
                under_detection_count += 1

            # Record anomaly
            if anomaly_type:
                anomalies.append({
                    "pr_id": result.pr_id,
                    "category": category,
                    "type": anomaly_type,
                    "severity": severity,
                    "expected_issues": expected_issues,
                    "actual_issues": actual_issues,
                    "ratio": round(ratio, 2),
                    "deviation_pct": round((ratio - 1.0) * 100, 1),
                })

        anomaly_rate = len(anomalies) / len(results) if results else 0.0

        return {
            "anomaly_rate": anomaly_rate,
            "total_anomalies": len(anomalies),
            "over_detection_count": over_detection_count,
            "under_detection_count": under_detection_count,
            "extreme_deviation_count": extreme_deviation_count,
            "anomalies": anomalies[:10],  # Top 10 for brevity
            "has_critical_anomalies": extreme_deviation_count > 0,
        }

    def _categorize_from_result(self, result: PRReviewResult) -> str:
        """Extract or infer category from review result."""
        if "category" in result.metadata:
            return result.metadata["category"]

        if self.categorizer_fn and "pr_metadata" in result.metadata:
            return self.categorizer_fn(result.metadata["pr_metadata"])

        summary_lower = result.change_summary.lower()
        if any(word in summary_lower for word in ["fix", "bug", "error"]):
            return "bugfix"
        if any(word in summary_lower for word in ["refactor", "cleanup"]):
            return "refactor"
        if any(word in summary_lower for word in ["add", "new", "feature"]):
            return "feature"

        return "other"


class CategoryThresholdMetric(BaseMetric):
    """Calculate category-specific quality thresholds.

    Each category has different expectations:
    - Bugfix: Lower findings count, higher precision expected
    - Feature: Higher findings count, more coverage expected
    - Refactor: Moderate findings, focus on code quality
    """

    def __init__(self, category_benchmarks: Dict[str, Any], categorizer_fn):
        super().__init__("category_threshold")
        self.benchmarks = category_benchmarks
        self.categorizer_fn = categorizer_fn

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, Any]:
        """Calculate category-specific threshold compliance."""
        if not self.benchmarks:
            return {}

        category_performance = {
            "bugfix": {"count": 0, "within_threshold": 0, "avg_score": 0.0},
            "feature": {"count": 0, "within_threshold": 0, "avg_score": 0.0},
            "refactor": {"count": 0, "within_threshold": 0, "avg_score": 0.0},
        }

        # Define acceptable ranges per category
        thresholds = {
            "bugfix": {"min_ratio": 0.5, "max_ratio": 2.0},  # 50%-200% of expected
            "feature": {"min_ratio": 0.7, "max_ratio": 2.5},  # 70%-250% of expected
            "refactor": {"min_ratio": 0.5, "max_ratio": 1.8},  # 50%-180% of expected
        }

        for result in results:
            category = self._categorize_from_result(result)
            if category not in self.benchmarks or category not in thresholds:
                continue

            benchmark = self.benchmarks[category]
            stats = benchmark.get("statistics", {})
            expected_issues = stats.get("avg_issues_per_pr", 0)

            if expected_issues == 0:
                continue

            actual_issues = len(result.findings)
            ratio = actual_issues / expected_issues

            threshold = thresholds[category]
            within_threshold = threshold["min_ratio"] <= ratio <= threshold["max_ratio"]

            # Quality score: how close to ideal (1.0)
            ideal_ratio = 1.0
            deviation = abs(ratio - ideal_ratio)
            quality_score = max(0.0, 1.0 - deviation / 2.0)  # Normalize to 0-1

            cat_perf = category_performance[category]
            cat_perf["count"] += 1
            if within_threshold:
                cat_perf["within_threshold"] += 1
            cat_perf["avg_score"] += quality_score

        # Calculate averages
        for category, perf in category_performance.items():
            if perf["count"] > 0:
                perf["threshold_compliance_rate"] = perf["within_threshold"] / perf["count"]
                perf["avg_score"] /= perf["count"]
            else:
                perf["threshold_compliance_rate"] = 0.0

        overall_compliance = sum(p["within_threshold"] for p in category_performance.values())
        total_evaluated = sum(p["count"] for p in category_performance.values())
        overall_compliance_rate = overall_compliance / total_evaluated if total_evaluated > 0 else 0.0

        return {
            "overall_threshold_compliance": overall_compliance_rate,
            "category_performance": category_performance,
            "total_evaluated": total_evaluated,
        }

    def _categorize_from_result(self, result: PRReviewResult) -> str:
        """Extract or infer category from review result."""
        if "category" in result.metadata:
            return result.metadata["category"]

        if self.categorizer_fn and "pr_metadata" in result.metadata:
            return self.categorizer_fn(result.metadata["pr_metadata"])

        summary_lower = result.change_summary.lower()
        if any(word in summary_lower for word in ["fix", "bug", "error"]):
            return "bugfix"
        if any(word in summary_lower for word in ["refactor", "cleanup"]):
            return "refactor"
        if any(word in summary_lower for word in ["add", "new", "feature"]):
            return "feature"

        return "other"
