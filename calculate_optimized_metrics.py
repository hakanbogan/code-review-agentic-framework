"""Calculate detailed metrics for optimized system."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def load_optimized_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load optimized evaluation result from JSON file."""
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    settings = get_settings()
    
    print("=" * 70)
    print("OPTIMIZED SYSTEM METRICS CALCULATION")
    print("=" * 70)
    
    # Try to load from existing optimized evaluation (comprehensive agent was mapped to multi_agent)
    # First try comprehensive agent file (which has the actual optimized results)
    optimized_file = settings.eval_results_path / "evaluation_comprehensive_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
    optimized_data = load_optimized_result(optimized_file)
    
    if not optimized_data:
        # Fallback: try multi-agent file
        optimized_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
        optimized_data = load_optimized_result(optimized_file)
    
    if not optimized_data:
        # If no existing file, run evaluation
        runner = EvaluationRunner(settings)
        optimized_prs = ["20446", "20447", "20448", "20449", "20450", 
                         "20451", "20452", "20453", "20454", "20455",
                         "14584", "14585", "14586", "14587", "14588", 
                         "14589", "14591", "14592", "14593", "14594"]
        result = runner.run_evaluation(
            system_type=SystemType.MULTI_AGENT,
            use_stored_reviews=True,
            pr_ids=optimized_prs,
            aggregate=True
        )
        metadata = result.metadata
        actionability = result.actionability_rate
        noise = result.noise_rate
        coverage = result.important_issue_coverage
    else:
        # Use loaded data
        metadata = optimized_data.get("metadata", {})
        actionability = optimized_data.get("actionability_rate", 0)
        noise = optimized_data.get("noise_rate", 0)
        coverage = optimized_data.get("important_issue_coverage", 0)
        result = None
    
    print("\n" + "=" * 70)
    print("DETAILED METRICS")
    print("=" * 70)
    
    print("\nCore Metrics:")
    print(f"  Actionability Rate: {actionability:.4f} ({actionability:.2%})")
    print(f"    - Total Findings: {metadata.get('total_findings', 0)}")
    print(f"    - Actionable Findings: {metadata.get('actionable_findings', 0)}")
    print(f"    - CI 95%: {metadata.get('actionability_ci_95', [0, 0])}")
    
    print(f"\n  Noise Rate: {noise:.4f} ({noise:.2%})")
    print(f"    - Total Noise Findings: {metadata.get('total_noise_findings', 0)}")
    print(f"    - CI 95%: {metadata.get('noise_ci_95', [0, 0])}")
    
    print(f"\n  Important Issue Coverage: {coverage:.4f} ({coverage:.2%})")
    print(f"    - Total Important Issues: {metadata.get('total_important_issues', 0)}")
    print(f"    - Detected Important Issues: {metadata.get('detected_important_issues', 0)}")
    print(f"    - Coverage Method: {metadata.get('coverage_method', 'unknown')}")
    print(f"    - CI 95%: {metadata.get('coverage_ci_95', [0, 0])}")
    
    print("\nAdvanced Metrics:")
    precision = metadata.get('precision', 0)
    recall = metadata.get('recall', 0)
    f1_score = metadata.get('f1_score', 0)
    
    print(f"  Precision: {precision:.4f} ({precision:.2%})")
    print(f"    - Avg Precision per PR: {metadata.get('avg_precision_per_pr', 0):.4f}")
    
    print(f"  Recall: {recall:.4f} ({recall:.2%})")
    print(f"    - Avg Recall per PR: {metadata.get('avg_recall_per_pr', 0):.4f}")
    
    print(f"  F1-Score: {f1_score:.4f} ({f1_score:.2%})")
    print(f"    - Avg F1 per PR: {metadata.get('avg_f1_per_pr', 0):.4f}")
    
    print("\nPerformance Metrics:")
    if result:
        print(f"  Avg Findings per PR: {result.avg_findings_per_pr:.2f}")
        print(f"  Avg Review Time: {result.avg_review_time_s:.2f}s")
        print(f"  Avg Token Cost: ${result.avg_token_cost:.4f}")
    else:
        print(f"  Avg Findings per PR: {optimized_data.get('avg_findings_per_pr', 0):.2f}")
        print(f"  Avg Review Time: {optimized_data.get('avg_review_time_s', 0):.2f}s")
        print(f"  Avg Token Cost: ${optimized_data.get('avg_token_cost', 0):.4f}")
    
    print("\nBenchmark Comparison:")
    benchmark_ratio = metadata.get('benchmark_normalized_ratio', 0)
    benchmark_deviation = metadata.get('benchmark_deviation', 0)
    benchmark_quality = metadata.get('benchmark_quality_score', 0)
    
    print(f"  Benchmark Normalized Ratio: {benchmark_ratio:.4f}")
    print(f"  Benchmark Deviation: {benchmark_deviation:.4f}")
    print(f"  Benchmark Quality Score: {benchmark_quality:.4f}")
    
    print("\nAnomaly Detection:")
    anomaly_rate = metadata.get('anomaly_rate', 0)
    total_anomalies = metadata.get('total_anomalies', 0)
    print(f"  Anomaly Rate: {anomaly_rate:.4f} ({anomaly_rate:.2%})")
    print(f"  Total Anomalies: {total_anomalies}")
    print(f"  Over-detection: {metadata.get('over_detection_count', 0)}")
    print(f"  Under-detection: {metadata.get('under_detection_count', 0)}")
    print(f"  Extreme Deviation: {metadata.get('extreme_deviation_count', 0)}")
    
    # Save detailed metrics to file
    output_file = settings.eval_results_path / "optimized_system_detailed_metrics.json"
    if result:
        dataset_size = result.dataset_size
        system_type = result.system_type.value
        avg_findings = result.avg_findings_per_pr
        avg_time = result.avg_review_time_s
        avg_cost = result.avg_token_cost
    else:
        dataset_size = optimized_data.get("dataset_size", 20)
        system_type = optimized_data.get("system_type", "multi_agent")
        avg_findings = optimized_data.get("avg_findings_per_pr", 0)
        avg_time = optimized_data.get("avg_review_time_s", 0)
        avg_cost = optimized_data.get("avg_token_cost", 0)
    
    with open(output_file, 'w') as f:
        json.dump({
            "system_type": system_type,
            "dataset_size": dataset_size,
            "core_metrics": {
                "actionability_rate": actionability,
                "noise_rate": noise,
                "important_issue_coverage": coverage,
            },
            "advanced_metrics": {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
            },
            "performance_metrics": {
                "avg_findings_per_pr": avg_findings,
                "avg_review_time_s": avg_time,
                "avg_token_cost": avg_cost,
            },
            "detailed_metadata": metadata,
        }, f, indent=2)
    
    print(f"\nDetailed metrics saved to: {output_file}")

if __name__ == "__main__":
    main()

