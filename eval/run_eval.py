"""Evaluation runner and dataset management."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain import EvaluationResult, GroundTruthLabel, PRMetadata, PRReviewResult, SystemType
from eval.metrics import (
    ActionabilityMetric,
    CoverageMetric,
    MetricsAggregator,
    NoiseMetric,
    PerformanceMetric,
)
from flows import ReviewFlow
from app.config import Settings
from app.logging import get_logger
from app.review_storage import ReviewStorage

logger = get_logger(__name__)


def categorize_pr(pr_metadata: PRMetadata) -> str:
    """Categorize PR by analyzing title and metadata.

    Args:
        pr_metadata: PR metadata

    Returns:
        Category string (bugfix, feature, refactor, other)
    """
    title = pr_metadata.title.lower()
    description = pr_metadata.description.lower()

    # Bug fix
    if any(word in title for word in ["fix", "bug", "issue", "error", "bugfix"]):
        return "bugfix"

    # Refactor
    if any(word in title for word in ["refactor", "cleanup", "reorganize", "simplify"]):
        return "refactor"

    # Feature
    if any(word in title for word in ["add", "implement", "feature", "new", "support"]):
        return "feature"

    # Fallback to description
    if any(word in description for word in ["fix", "bug", "error"]):
        return "bugfix"
    if any(word in description for word in ["refactor", "cleanup"]):
        return "refactor"
    if any(word in description for word in ["feature", "new"]):
        return "feature"

    return "other"


class DatasetLoader:
    """Loads evaluation dataset."""

    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path
        self._category_benchmarks = None

    def load_category_benchmarks(self) -> Dict[str, Dict]:
        """Load benchmark statistics for each category."""
        if self._category_benchmarks is not None:
            return self._category_benchmarks

        index_file = self.dataset_path / "categorized" / "index.json"
        if not index_file.exists():
            return {}

        with open(index_file) as f:
            data = json.load(f)

        self._category_benchmarks = data.get("categories", {})
        return self._category_benchmarks

    def load_pr_list(self) -> List[PRMetadata]:
        """Load list of PRs to evaluate."""
        pr_list_file = self.dataset_path / "pr_list.json"

        if not pr_list_file.exists():
            logger.warning(f"PR list not found: {pr_list_file}")
            return []

        with open(pr_list_file) as f:
            data = json.load(f)

        return [PRMetadata(**pr) for pr in data]

    def load_ground_truth(self) -> Dict[str, GroundTruthLabel]:
        """Load ground truth labels.

        NOTE: For new reviewed PRs, ground truth should NOT exist.
        Dataset ground truth is only for benchmarking purposes and should
        not be used for evaluation of new reviews.

        Returns empty dict to ensure new reviews don't have ground truth.
        """
        # Return empty dict - new reviews should not have ground truth
        # Dataset is only for benchmarking (category statistics)
        logger.info("Ground truth: Using empty dict (new reviews have no ground truth)")
        return {}


class EvaluationRunner:
    """Runs evaluation experiments."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.review_flow = ReviewFlow(settings)
        self.dataset_loader = DatasetLoader(settings.eval_dataset_path)
        self.review_storage = ReviewStorage(settings)

    def load_stored_reviews(self, pr_ids: Optional[List[str]] = None) -> List[PRReviewResult]:
        """Load stored review results.

        Args:
            pr_ids: List of PR IDs to load. If None, loads all from reviews/

        Returns:
            List of review results
        """
        if pr_ids:
            results = []
            for pr_id in pr_ids:
                review = self.review_storage.get_review(pr_id)
                if review:
                    results.append(review)
                else:
                    logger.warning(f"Review not found for PR {pr_id}")
            return results
        else:
            # Load all reviews from index
            index_entries = self.review_storage.list_reviews()
            results = []
            for entry in index_entries:
                pr_id = entry["pr_id"]
                review = self.review_storage.get_review(pr_id)
                if review:
                    results.append(review)
            return results

    def run_evaluation(
        self,
        system_type: SystemType,
        repo_path: Optional[Path] = None,
        use_stored_reviews: bool = True,
        pr_ids: Optional[List[str]] = None,
        aggregate: bool = False,
    ) -> EvaluationResult:
        """Run evaluation for a system type.

        Args:
            system_type: Type of system to evaluate
            repo_path: Path to repository (required if use_stored_reviews=False)
            use_stored_reviews: If True, load from reviews/ directory. If False, run reviews.
            pr_ids: Optional list of PR IDs to filter evaluation
            aggregate: Save results in aggregated file

        Returns:
            EvaluationResult with metrics
        """
        logger.info(f"Starting evaluation for {system_type.value}")

        # Load ground truth
        ground_truth = self.dataset_loader.load_ground_truth()

        # Load category benchmarks for comparison
        category_benchmarks = self.dataset_loader.load_category_benchmarks()

        # Get review results
        if use_stored_reviews:
            logger.info("Loading stored review results...")
            results = self.load_stored_reviews(pr_ids)

            if not results:
                raise ValueError("No stored reviews found")

            # Filter by system type
            results = [r for r in results if r.system_type == system_type]

            if not results:
                raise ValueError(f"No stored reviews found for system type: {system_type.value}")

            logger.info(f"Loaded {len(results)} stored reviews")
        else:
            # Original behavior: run reviews
            if not repo_path:
                raise ValueError("repo_path required when use_stored_reviews=False")

            # Load dataset
            pr_list = self.dataset_loader.load_pr_list()

            if not pr_list:
                raise ValueError("No PRs in dataset")

            # Filter by PR IDs if specified
            if pr_ids:
                pr_list = [pr for pr in pr_list if pr.pr_id in pr_ids]

            # Run reviews
            results: List[PRReviewResult] = []

            for pr_metadata in pr_list:
                logger.info(f"Reviewing PR {pr_metadata.pr_id}")

                try:
                    if system_type == SystemType.SINGLE_AGENT:
                        result = self.review_flow.run_single_agent_review(
                            pr_metadata,
                            repo_path
                        )
                    elif system_type == SystemType.MULTI_AGENT:
                        result = self.review_flow.run_multi_agent_review(
                            pr_metadata,
                            repo_path
                        )
                    else:
                        raise ValueError(f"Unsupported system type: {system_type}")

                    results.append(result)

                    # Save individual result
                    self._save_result(result)

                except Exception as e:
                    logger.error(f"Failed to review PR {pr_metadata.pr_id}: {e}")
                    continue

        # Calculate metrics
        evaluation_result = self._calculate_metrics(
            results,
            ground_truth,
            system_type,
            category_benchmarks
        )

        # Add benchmark comparison to metadata
        if category_benchmarks:
            evaluation_result.metadata["category_benchmarks"] = category_benchmarks

        # Save evaluation result with PR IDs
        pr_ids_evaluated = [r.pr_id for r in results]
        self._save_evaluation(evaluation_result, pr_ids_evaluated, aggregate)

        logger.info(
            f"Evaluation completed: {len(results)} PRs, "
            f"actionability={evaluation_result.actionability_rate:.2%}"
        )

        return evaluation_result

    def _calculate_metrics(
        self,
        results: List[PRReviewResult],
        ground_truth: Dict[str, GroundTruthLabel],
        system_type: SystemType,
        category_benchmarks: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Calculate all metrics."""
        aggregator = MetricsAggregator()

        # Register core metrics (pass categorizer for NoiseMetric)
        aggregator.register(ActionabilityMetric())
        aggregator.register(NoiseMetric(categorizer_fn=categorize_pr))
        aggregator.register(CoverageMetric())
        aggregator.register(PerformanceMetric())

        # Register benchmark and advanced metrics if available
        if category_benchmarks:
            from eval.metrics import (
                BenchmarkComparisonMetric,
                PrecisionRecallMetric,
                AnomalyDetectionMetric,
                CategoryThresholdMetric,
            )

            aggregator.register(BenchmarkComparisonMetric(category_benchmarks, categorize_pr))
            aggregator.register(PrecisionRecallMetric(categorize_pr))
            aggregator.register(AnomalyDetectionMetric(category_benchmarks, categorize_pr))
            aggregator.register(CategoryThresholdMetric(category_benchmarks, categorize_pr))

        return aggregator.evaluate(results, ground_truth, system_type)

    def _save_result(self, result: PRReviewResult) -> None:
        """Save individual review result."""
        results_dir = self.settings.eval_results_path / result.system_type.value
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = results_dir / f"{result.pr_id}.json"

        with open(result_file, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2)

    def _save_evaluation(self, evaluation: EvaluationResult, pr_ids: List[str], aggregate: bool = False) -> None:
        """Save evaluation result with PR IDs.

        Args:
            evaluation: Evaluation result
            pr_ids: List of PR IDs evaluated
            aggregate: If True, save in single file. If False, save per-PR in separate directories.
        """
        eval_data = evaluation.model_dump(mode="json")
        eval_data["pr_ids"] = pr_ids

        if aggregate:
            # Save in single aggregated file
            pr_ids_str = "_".join(sorted(pr_ids)[:5])
            if len(pr_ids) > 5:
                pr_ids_str += f"_and_{len(pr_ids)-5}_more"
            eval_file = self.settings.eval_results_path / \
                f"evaluation_{evaluation.system_type.value}_aggregated_{pr_ids_str}.json"
            with open(eval_file, "w") as f:
                json.dump(eval_data, f, indent=2)
        else:
            # Save aggregated result (general)
            eval_file = self.settings.eval_results_path / f"evaluation_{evaluation.system_type.value}.json"
            with open(eval_file, "w") as f:
                json.dump(eval_data, f, indent=2)

            # Save per-PR result in PR-specific directories
            for pr_id in pr_ids:
                pr_dir = self.settings.eval_results_path / pr_id
                pr_dir.mkdir(parents=True, exist_ok=True)

                pr_eval_file = pr_dir / f"evaluation_{evaluation.system_type.value}.json"
                with open(pr_eval_file, "w") as f:
                    json.dump(eval_data, f, indent=2)


class ComparisonAnalyzer:
    """Analyzes and compares evaluation results."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def compare_systems(
        self,
        baseline: EvaluationResult,
        proposed: EvaluationResult,
    ) -> Dict[str, any]:
        """Compare two systems statistically.

        Args:
            baseline: Baseline system results
            proposed: Proposed system results

        Returns:
            Comparison statistics
        """

        comparison = {
            "baseline": baseline.system_type.value,
            "proposed": proposed.system_type.value,
            "metrics": {
                "actionability": {
                    "baseline": baseline.actionability_rate,
                    "proposed": proposed.actionability_rate,
                    "improvement": proposed.actionability_rate - baseline.actionability_rate,
                },
                "noise": {
                    "baseline": baseline.noise_rate,
                    "proposed": proposed.noise_rate,
                    "improvement": baseline.noise_rate - proposed.noise_rate,  # Lower is better
                },
                "coverage": {
                    "baseline": baseline.important_issue_coverage,
                    "proposed": proposed.important_issue_coverage,
                    "improvement": proposed.important_issue_coverage - baseline.important_issue_coverage,
                },
            },
        }

        return comparison

    def export_latex_table(
        self,
        evaluations: List[EvaluationResult],
        output_file: Path,
    ) -> None:
        """Export results as LaTeX table for thesis.

        Args:
            evaluations: List of evaluation results
            output_file: Output LaTeX file
        """
        lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Evaluation Results}",
            "\\begin{tabular}{lcccc}",
            "\\hline",
            "System & Actionability & Noise Rate & Coverage & Avg Time (s) \\\\",
            "\\hline",
        ]

        for eval_result in evaluations:
            lines.append(
                f"{eval_result.system_type.value} & "
                f"{eval_result.actionability_rate:.2%} & "
                f"{eval_result.noise_rate:.2%} & "
                f"{eval_result.important_issue_coverage:.2%} & "
                f"{eval_result.avg_review_time_s:.1f} \\\\"
            )

        lines.extend([
            "\\hline",
            "\\end{tabular}",
            "\\end{table}",
        ])

        output_file.write_text("\n".join(lines))
        logger.info(f"Exported LaTeX table to {output_file}")
