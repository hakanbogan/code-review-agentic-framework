"""Evaluation runner and dataset management."""

import json
from pathlib import Path
from typing import Dict, List

from domain import EvaluationResult, GroundTruthLabel, PRMetadata, PRReviewResult, SystemType
from eval.metrics import (
    ActionabilityMetric,
    CoverageMetric,
    MetricsAggregator,
    NoiseMetric,
    PerformanceMetric,
    ThesisMetrics,
)
from flows import ReviewFlow
from app.config import Settings
from app.logging import get_logger

logger = get_logger(__name__)


class DatasetLoader:
    """Loads evaluation dataset."""

    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path

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
        """Load ground truth labels."""
        gt_file = self.dataset_path / "ground_truth.json"
        
        if not gt_file.exists():
            logger.warning(f"Ground truth not found: {gt_file}")
            return {}
        
        with open(gt_file) as f:
            data = json.load(f)
        
        return {
            label["pr_id"]: GroundTruthLabel(**label)
            for label in data
        }


class EvaluationRunner:
    """Runs evaluation experiments."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.review_flow = ReviewFlow(settings)
        self.dataset_loader = DatasetLoader(settings.eval_dataset_path)

    def run_evaluation(
        self,
        system_type: SystemType,
        repo_path: Path,
    ) -> EvaluationResult:
        """Run evaluation for a system type.
        
        Args:
            system_type: Type of system to evaluate
            repo_path: Path to repository
            
        Returns:
            EvaluationResult with metrics
        """
        logger.info(f"Starting evaluation for {system_type.value}")
        
        # Load dataset
        pr_list = self.dataset_loader.load_pr_list()
        ground_truth = self.dataset_loader.load_ground_truth()
        
        if not pr_list:
            raise ValueError("No PRs in dataset")
        
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
            system_type
        )
        
        # Save evaluation result
        self._save_evaluation(evaluation_result)
        
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
    ) -> EvaluationResult:
        """Calculate all metrics."""
        aggregator = MetricsAggregator()
        
        # Register metrics
        aggregator.register(ActionabilityMetric())
        aggregator.register(NoiseMetric())
        aggregator.register(CoverageMetric())
        aggregator.register(PerformanceMetric())
        aggregator.register(ThesisMetrics())
        
        return aggregator.evaluate(results, ground_truth, system_type)

    def _save_result(self, result: PRReviewResult) -> None:
        """Save individual review result."""
        results_dir = self.settings.eval_results_path / result.system_type.value
        results_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = results_dir / f"{result.pr_id}.json"
        
        with open(result_file, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2)

    def _save_evaluation(self, evaluation: EvaluationResult) -> None:
        """Save evaluation result."""
        eval_file = self.settings.eval_results_path / f"evaluation_{evaluation.system_type.value}.json"
        
        with open(eval_file, "w") as f:
            json.dump(evaluation.model_dump(mode="json"), f, indent=2)


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
        from eval.metrics.statistical import effect_size_cohens_d
        
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

