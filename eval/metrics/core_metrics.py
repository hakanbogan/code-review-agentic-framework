"""Core metrics: actionability, noise, coverage."""

from typing import Any, Callable, Dict, List, Optional

from domain import GroundTruthLabel, PRMetadata, PRReviewResult, Severity
from eval.metrics.base import BaseMetric
from eval.metrics.statistical import calculate_confidence_interval

# Category-based tolerance for noise detection (when no GT available)
CATEGORY_TOLERANCE = {
    "bugfix": 2,    # Lower tolerance - bugfixes should have fewer noise findings
    "feature": 4,   # Higher tolerance - new features may have more exploratory findings
    "refactor": 3,  # Medium tolerance - refactors should be relatively clean
    "other": 3,     # Default medium tolerance
}


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
        actionability_per_pr = []

        for result in results:
            pr_total = 0
            pr_actionable = 0

            for finding in result.findings:
                total_findings += 1
                pr_total += 1

                if finding.has_patch:
                    actionable_findings += 1
                    pr_actionable += 1
                elif finding.severity in [Severity.MAJOR, Severity.CRITICAL]:
                    if finding.location and finding.evidence.reference:
                        actionable_findings += 1
                        pr_actionable += 1

            # Track per-PR actionability for CI calculation
            if pr_total > 0:
                actionability_per_pr.append(pr_actionable / pr_total)

        rate = actionable_findings / total_findings if total_findings > 0 else 0.0

        # Calculate confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(
            actionability_per_pr) if len(actionability_per_pr) >= 2 else (0.0, 0.0)

        return {
            "actionability_rate": rate,
            "total_findings": total_findings,
            "actionable_findings": actionable_findings,
            "actionability_ci_95": (ci_lower, ci_upper),
        }


class NoiseMetric(BaseMetric):
    """Calculates noise/false positive rate."""

    def __init__(self, categorizer_fn: Optional[Callable[[PRMetadata], str]] = None):
        super().__init__("noise")
        self.categorizer_fn = categorizer_fn

    def calculate(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate noise rate.

        Uses ground truth false_positive_tolerance as baseline.
        Falls back to category-based tolerance when GT unavailable.
        """
        total_findings = 0
        noise_findings = 0
        noise_per_pr = []

        for result in results:
            gt = ground_truth.get(result.pr_id)
            pr_total = 0
            pr_noise = 0

            # Determine tolerance threshold
            if gt and gt.false_positive_tolerance is not None:
                # Use ground truth tolerance
                tolerance = gt.false_positive_tolerance
            else:
                # Fallback: Category-based tolerance
                category = self._categorize_pr(result)
                tolerance = CATEGORY_TOLERANCE.get(category, 3)

            for finding in result.findings:
                total_findings += 1
                pr_total += 1

                # Heuristic scoring for potential false positives
                noise_score = 0

                # Nit without patch is likely noise
                if finding.severity == Severity.NIT and not finding.has_patch:
                    noise_score += 1

                # Missing evidence reference
                if not finding.evidence.reference or finding.evidence.reference.strip() == "":
                    noise_score += 1

                # Missing or very short description
                if not finding.description or len(finding.description.strip()) < 20:
                    noise_score += 1

                # If noise score exceeds tolerance, count as noise
                if noise_score >= tolerance:
                    noise_findings += 1
                    pr_noise += 1

            # Track per-PR noise for CI calculation
            if pr_total > 0:
                noise_per_pr.append(pr_noise / pr_total)

        rate = noise_findings / total_findings if total_findings > 0 else 0.0

        # Calculate confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(noise_per_pr) if len(noise_per_pr) >= 2 else (0.0, 0.0)

        return {
            "noise_rate": rate,
            "total_noise_findings": noise_findings,
            "noise_ci_95": (ci_lower, ci_upper),
        }

    def _categorize_pr(self, result: PRReviewResult) -> str:
        """Categorize PR based on metadata (title, description)."""
        if self.categorizer_fn:
            try:
                # Extract PR info from result metadata
                title = result.metadata.get("title", "").lower()
                description = result.metadata.get("description", "").lower()

                # Simple categorization based on title/description
                if any(word in title for word in ["fix", "bug", "issue", "error", "bugfix"]):
                    return "bugfix"
                if any(word in title for word in ["refactor", "cleanup", "reorganize", "simplify"]):
                    return "refactor"
                if any(word in title for word in ["add", "implement", "feature", "new", "support"]):
                    return "feature"

                # Fallback to description
                if any(word in description for word in ["fix", "bug", "error"]):
                    return "bugfix"
                if any(word in description for word in ["refactor", "cleanup"]):
                    return "refactor"
                if any(word in description for word in ["feature", "new"]):
                    return "feature"
            except Exception:
                pass
        return "other"


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

        Primary: Uses ground truth labels if available.
        Fallback: Uses severity-based important issues (CRITICAL + MAJOR).
        """
        # Try GT-based coverage first
        if ground_truth:
            return self.r43_calculate_gt_coverage(results, ground_truth)

        # Fallback: Severity-based coverage
        return self._calculate_severity_coverage(results)

    def r43_calculate_gt_coverage(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
    ) -> Dict[str, float]:
        """Calculate coverage using ground truth labels."""
        total_important = 0
        detected_important = 0
        coverage_per_pr = []

        for result in results:
            gt = ground_truth.get(result.pr_id)
            if not gt:
                continue

            important_issues = gt.important_issues
            total_important += len(important_issues)
            pr_detected = 0

            # Extract finding information
            finding_texts = []
            for f in result.findings:
                # Combine title and description for better matching
                text = f"{f.title.lower()} {f.description.lower()}"
                finding_texts.append(text)

            # Check if each important issue is detected
            for issue in important_issues:
                issue_lower = issue.lower()
                issue_keywords = self._extract_keywords(issue_lower)

                detected = False
                for finding_text in finding_texts:
                    # Multi-strategy matching
                    if self._match_issue(issue_lower, issue_keywords, finding_text):
                        detected = True
                        break

                if detected:
                    detected_important += 1
                    pr_detected += 1

            # Track per-PR coverage for CI calculation
            if len(important_issues) > 0:
                coverage_per_pr.append(pr_detected / len(important_issues))

        coverage = detected_important / total_important if total_important > 0 else 0.0

        # Calculate confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(coverage_per_pr) if len(coverage_per_pr) >= 2 else (0.0, 0.0)

        return {
            "important_issue_coverage": coverage,
            "total_important_issues": total_important,
            "detected_important_issues": detected_important,
            "coverage_ci_95": (ci_lower, ci_upper),
            "coverage_method": "ground_truth",
        }

    def _calculate_severity_coverage(
        self,
        results: List[PRReviewResult],
    ) -> Dict[str, float]:
        """Calculate coverage using severity-based important issues.

        Important issues = CRITICAL + MAJOR severity findings.
        This is a proxy metric when ground truth is unavailable.
        """
        total_findings = 0
        important_findings = 0
        severity_per_pr = []

        for result in results:
            pr_total = len(result.findings)
            pr_important = 0

            for finding in result.findings:
                total_findings += 1

                # Important issues = CRITICAL or MAJOR severity
                if finding.severity in [Severity.CRITICAL, Severity.MAJOR]:
                    important_findings += 1
                    pr_important += 1

            # Track per-PR important issue ratio for CI calculation
            if pr_total > 0:
                severity_per_pr.append(pr_important / pr_total)

        # Calculate ratio of important findings to total findings
        important_ratio = important_findings / total_findings if total_findings > 0 else 0.0

        # Calculate confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(severity_per_pr) if len(severity_per_pr) >= 2 else (0.0, 0.0)

        return {
            "important_issue_coverage": important_ratio,
            "total_important_issues": important_findings,
            "detected_important_issues": important_findings,
            "coverage_ci_95": (ci_lower, ci_upper),
            "coverage_method": "severity_proxy",
            "severity_proxy_note": "Important issues identified by CRITICAL+MAJOR severity (no ground truth available)",
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from issue text."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were',
                      'in', 'on', 'at', 'to', 'for', 'of', 'with', 'without'}
        words = text.split()
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return keywords

    def _match_issue(self, issue: str, keywords: List[str], finding_text: str) -> bool:
        """Match issue with finding using multiple strategies."""
        # Strategy 1: Direct substring match
        if issue in finding_text:
            return True

        # Strategy 2: Keyword overlap (at least 50% of keywords present)
        if keywords:
            matches = sum(1 for kw in keywords if kw in finding_text)
            if matches / len(keywords) >= 0.5:
                return True

        # Strategy 3: Reverse match (finding mentions issue)
        issue_words = set(issue.split())
        finding_words = set(finding_text.split())
        overlap = len(issue_words & finding_words)
        if len(issue_words) > 0 and overlap / len(issue_words) >= 0.6:
            return True

        return False
