"""Core metrics: actionability, noise, coverage."""

from typing import Dict, List

from domain import GroundTruthLabel, PRReviewResult, Severity
from eval.metrics.base import BaseMetric


class ActionabilityMetric(BaseMetric):
    """Calculates actionability rate of findings."""

    def __init__(self):
        super().__init__("actionability")

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate actionability rate.

        Actionable findings are those with:
        - Patches (has_patch=True), or
        - Major/Critical severity with clear location
        """
        total_findings = 0
        actionable_findings = 0

        for result in results:
            for finding in result.findings:
                total_findings += 1

                if finding.has_patch:
                    actionable_findings += 1
                elif finding.severity in [Severity.MAJOR, Severity.CRITICAL]:
                    if finding.location and finding.evidence.reference:
                        actionable_findings += 1

        rate = actionable_findings / total_findings if total_findings > 0 else 0.0

        return {
            "actionability_rate": rate,
            "total_findings": total_findings,
            "actionable_findings": actionable_findings,
        }


class NoiseMetric(BaseMetric):
    """Calculates noise/false positive rate."""

    def __init__(self):
        super().__init__("noise")

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate noise rate.

        This requires manual labeling in ground truth.
        For now, use heuristics:
        - Nits without fixes are often noise
        - Findings without evidence are noise
        """
        total_findings = 0
        noise_findings = 0

        for result in results:
            gt = ground_truth.get(result.pr_id)
            if not gt:
                continue

            for finding in result.findings:
                total_findings += 1

                # Heuristic: nit without patch is likely noise
                if finding.severity == Severity.NIT and not finding.has_patch:
                    noise_findings += 1
                # Findings without proper evidence
                elif not finding.evidence.reference:
                    noise_findings += 1

        rate = noise_findings / total_findings if total_findings > 0 else 0.0

        return {
            "noise_rate": rate,
            "total_noise_findings": noise_findings,
        }


class CoverageMetric(BaseMetric):
    """Calculates important issue coverage."""

    def __init__(self):
        super().__init__("coverage")

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate coverage of important issues.

        Important issues are defined in ground truth labels.
        """
        total_important = 0
        detected_important = 0

        for result in results:
            gt = ground_truth.get(result.pr_id)
            if not gt:
                continue

            important_issues = gt.important_issues
            total_important += len(important_issues)

            # Check if each important issue is detected
            finding_descriptions = [f.description.lower() for f in result.findings]

            for issue in important_issues:
                issue_lower = issue.lower()
                # Simple keyword matching (could be improved)
                if any(issue_lower in desc for desc in finding_descriptions):
                    detected_important += 1

        coverage = detected_important / total_important if total_important > 0 else 0.0

        return {
            "important_issue_coverage": coverage,
            "total_important_issues": total_important,
            "detected_important_issues": detected_important,
        }
