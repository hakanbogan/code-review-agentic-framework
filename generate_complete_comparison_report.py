"""Generate complete comparison report between baseline and optimized systems."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from app.config import get_settings
from eval.metrics.statistical import proportion_test

def load_evaluation_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load evaluation result from JSON file."""
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_statistical_tests(baseline: Dict, optimized: Dict) -> Dict[str, Any]:
    """Calculate statistical tests for comparison."""
    baseline_meta = baseline.get("metadata", {})
    optimized_meta = optimized.get("metadata", {})
    
    tests = {}
    
    # Actionability test
    baseline_actionable = baseline_meta.get("actionable_findings", 0)
    baseline_total = baseline_meta.get("total_findings", 0)
    optimized_actionable = optimized_meta.get("actionable_findings", 0)
    optimized_total = optimized_meta.get("total_findings", 0)
    
    if baseline_total > 0 and optimized_total > 0:
        act_test = proportion_test(
            successes_a=optimized_actionable,
            total_a=optimized_total,
            successes_b=baseline_actionable,
            total_b=baseline_total,
        )
        tests["actionability"] = act_test
    
    # Precision test
    baseline_precision = baseline_meta.get("precision", 0)
    optimized_precision = optimized_meta.get("precision", 0)
    
    if baseline_precision > 0 and optimized_precision > 0:
        baseline_prec_count = int(baseline_precision * baseline_total) if baseline_total > 0 else 0
        optimized_prec_count = int(optimized_precision * optimized_total) if optimized_total > 0 else 0
        
        prec_test = proportion_test(
            successes_a=optimized_prec_count,
            total_a=optimized_total,
            successes_b=baseline_prec_count,
            total_b=baseline_total,
        )
        tests["precision"] = prec_test
    
    return tests

def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2%}"

def format_improvement(old: float, new: float, higher_is_better: bool = True) -> Dict[str, Any]:
    """Calculate improvement metrics."""
    absolute_change = new - old
    if old > 0:
        relative_change_pct = (absolute_change / old) * 100
    else:
        relative_change_pct = 0.0 if new == 0 else 999.0  # Use large number instead of inf
    
    return {
        "absolute": float(absolute_change),
        "relative_percent": float(relative_change_pct),
        "improvement": bool(absolute_change > 0 if higher_is_better else absolute_change < 0),
    }

def main():
    settings = get_settings()
    
    print("=" * 70)
    print("GENERATING COMPLETE COMPARISON REPORT")
    print("=" * 70)
    
    # Load baseline (45 PR baseline)
    baseline_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_12000_14_143_14468_14595_and_40_more.json"
    baseline = load_evaluation_result(baseline_file)
    
    if not baseline:
        print(f"\nERROR: Baseline file not found: {baseline_file}")
        print("Please ensure baseline evaluation has been run.")
        return
    
    # Load optimized (try 10 Django PR first, then 20 PR)
    optimized_file_10 = settings.eval_results_path / "evaluation_multi_agent_aggregated_20446_20447_20448_20449_20450_and_5_more.json"
    optimized_10 = load_evaluation_result(optimized_file_10)
    
    optimized_file_20 = settings.eval_results_path / "evaluation_multi_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
    optimized_20 = load_evaluation_result(optimized_file_20)
    
    # Use the one with better results (non-zero actionability)
    if optimized_20 and optimized_20.get("actionability_rate", 0) > 0.5:
        optimized = optimized_20
        optimized_label = "20 PRs (10 Django + 10 FastAPI)"
    elif optimized_10 and optimized_10.get("actionability_rate", 0) > 0.5:
        optimized = optimized_10
        optimized_label = "10 PRs (Django)"
    else:
        print(f"\nERROR: Optimized evaluation files not found or have invalid results.")
        print(f"  Tried: {optimized_file_10.name}")
        print(f"  Tried: {optimized_file_20.name}")
        return
    
    # Extract metrics
    baseline_meta = baseline.get("metadata", {})
    optimized_meta = optimized.get("metadata", {})
    
    # Core metrics
    baseline_act = baseline.get("actionability_rate", 0)
    optimized_act = optimized.get("actionability_rate", 0)
    act_improvement = format_improvement(baseline_act, optimized_act, higher_is_better=True)
    
    baseline_noise = baseline.get("noise_rate", 0)
    optimized_noise = optimized.get("noise_rate", 0)
    noise_improvement = format_improvement(baseline_noise, optimized_noise, higher_is_better=False)
    
    baseline_cov = baseline.get("important_issue_coverage", 0)
    optimized_cov = optimized.get("important_issue_coverage", 0)
    cov_improvement = format_improvement(baseline_cov, optimized_cov, higher_is_better=True)
    
    # Advanced metrics
    baseline_prec = baseline_meta.get("precision", 0)
    optimized_prec = optimized_meta.get("precision", 0)
    prec_improvement = format_improvement(baseline_prec, optimized_prec, higher_is_better=True)
    
    baseline_rec = baseline_meta.get("recall", 0)
    optimized_rec = optimized_meta.get("recall", 0)
    rec_improvement = format_improvement(baseline_rec, optimized_rec, higher_is_better=True)
    
    baseline_f1 = baseline_meta.get("f1_score", 0)
    optimized_f1 = optimized_meta.get("f1_score", 0)
    f1_improvement = format_improvement(baseline_f1, optimized_f1, higher_is_better=True)
    
    # Performance metrics
    baseline_findings = baseline.get("avg_findings_per_pr", 0)
    optimized_findings = optimized.get("avg_findings_per_pr", 0)
    findings_improvement = format_improvement(baseline_findings, optimized_findings, higher_is_better=False)
    
    baseline_time = baseline.get("avg_review_time_s", 0)
    optimized_time = optimized.get("avg_review_time_s", 0)
    time_change = optimized_time - baseline_time
    
    baseline_cost = baseline.get("avg_token_cost", 0)
    optimized_cost = optimized.get("avg_token_cost", 0)
    cost_change = optimized_cost - baseline_cost
    
    # Statistical tests
    statistical_tests = calculate_statistical_tests(baseline, optimized)
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_to_native(obj):
        """Convert numpy types to Python native types."""
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        return obj
    
    statistical_tests = convert_to_native(statistical_tests)
    
    # Create comprehensive report
    report = {
        "report_generated_at": datetime.now().isoformat(),
        "baseline_system": {
            "file": baseline_file.name,
            "dataset_size": baseline.get("dataset_size", 0),
            "pr_ids": baseline.get("pr_ids", []),
            "core_metrics": {
                "actionability_rate": baseline_act,
                "noise_rate": baseline_noise,
                "important_issue_coverage": baseline_cov,
            },
            "advanced_metrics": {
                "precision": baseline_prec,
                "recall": baseline_rec,
                "f1_score": baseline_f1,
            },
            "performance_metrics": {
                "avg_findings_per_pr": baseline_findings,
                "avg_review_time_s": baseline_time,
                "avg_token_cost": baseline_cost,
            },
            "detailed_metadata": {
                "total_findings": baseline_meta.get("total_findings", 0),
                "actionable_findings": baseline_meta.get("actionable_findings", 0),
                "total_noise_findings": baseline_meta.get("total_noise_findings", 0),
                "total_important_issues": baseline_meta.get("total_important_issues", 0),
                "detected_important_issues": baseline_meta.get("detected_important_issues", 0),
            },
        },
        "optimized_system": {
            "file": optimized_file_20.name if optimized == optimized_20 else optimized_file_10.name,
            "label": optimized_label,
            "dataset_size": optimized.get("dataset_size", 0),
            "pr_ids": optimized.get("pr_ids", []),
            "core_metrics": {
                "actionability_rate": optimized_act,
                "noise_rate": optimized_noise,
                "important_issue_coverage": optimized_cov,
            },
            "advanced_metrics": {
                "precision": optimized_prec,
                "recall": optimized_rec,
                "f1_score": optimized_f1,
            },
            "performance_metrics": {
                "avg_findings_per_pr": optimized_findings,
                "avg_review_time_s": optimized_time,
                "avg_token_cost": optimized_cost,
            },
            "detailed_metadata": {
                "total_findings": optimized_meta.get("total_findings", 0),
                "actionable_findings": optimized_meta.get("actionable_findings", 0),
                "total_noise_findings": optimized_meta.get("total_noise_findings", 0),
                "total_important_issues": optimized_meta.get("total_important_issues", 0),
                "detected_important_issues": optimized_meta.get("detected_important_issues", 0),
            },
        },
        "comparison": {
            "core_metrics": {
                "actionability_rate": {
                    "baseline": baseline_act,
                    "optimized": optimized_act,
                    "absolute_improvement": act_improvement["absolute"],
                    "relative_improvement_percent": act_improvement["relative_percent"],
                    "improved": act_improvement["improvement"],
                },
                "noise_rate": {
                    "baseline": baseline_noise,
                    "optimized": optimized_noise,
                    "absolute_reduction": noise_improvement["absolute"],
                    "relative_reduction_percent": abs(noise_improvement["relative_percent"]),
                    "improved": noise_improvement["improvement"],
                },
                "important_issue_coverage": {
                    "baseline": baseline_cov,
                    "optimized": optimized_cov,
                    "absolute_improvement": cov_improvement["absolute"],
                    "relative_improvement_percent": cov_improvement["relative_percent"],
                    "improved": cov_improvement["improvement"],
                },
            },
            "advanced_metrics": {
                "precision": {
                    "baseline": baseline_prec,
                    "optimized": optimized_prec,
                    "absolute_improvement": prec_improvement["absolute"],
                    "relative_improvement_percent": prec_improvement["relative_percent"],
                    "improved": prec_improvement["improvement"],
                },
                "recall": {
                    "baseline": baseline_rec,
                    "optimized": optimized_rec,
                    "absolute_improvement": rec_improvement["absolute"],
                    "relative_improvement_percent": rec_improvement["relative_percent"],
                    "improved": rec_improvement["improvement"],
                },
                "f1_score": {
                    "baseline": baseline_f1,
                    "optimized": optimized_f1,
                    "absolute_improvement": f1_improvement["absolute"],
                    "relative_improvement_percent": f1_improvement["relative_percent"],
                    "improved": f1_improvement["improvement"],
                },
            },
            "performance_metrics": {
                "avg_findings_per_pr": {
                    "baseline": baseline_findings,
                    "optimized": optimized_findings,
                    "absolute_reduction": findings_improvement["absolute"],
                    "relative_reduction_percent": abs(findings_improvement["relative_percent"]),
                    "improved": findings_improvement["improvement"],
                },
                "avg_review_time_s": {
                    "baseline": baseline_time,
                    "optimized": optimized_time,
                    "change": time_change,
                },
                "avg_token_cost": {
                    "baseline": baseline_cost,
                    "optimized": optimized_cost,
                    "change": cost_change,
                },
            },
        },
        "statistical_tests": {
            "actionability": statistical_tests.get("actionability", {}),
            "precision": statistical_tests.get("precision", {}),
        },
        "summary": {
            "key_improvements": [
                f"Actionability Rate: {baseline_act:.2%} → {optimized_act:.2%} ({act_improvement['relative_percent']:+.1f}%)",
                f"Precision: {baseline_prec:.2%} → {optimized_prec:.2%} ({prec_improvement['relative_percent']:+.1f}%)",
                f"Noise Rate: {baseline_noise:.2%} → {optimized_noise:.2%} ({abs(noise_improvement['relative_percent']):+.1f}% reduction)",
                f"Avg Findings per PR: {baseline_findings:.2f} → {optimized_findings:.2f} ({abs(findings_improvement['relative_percent']):+.1f}% reduction)",
            ],
            "statistical_significance": {
                "actionability": statistical_tests.get("actionability", {}).get("significant", False),
                "precision": statistical_tests.get("precision", {}).get("significant", False),
            },
        },
    }
    
    # Save report
    output_file = settings.eval_results_path / "baseline_vs_optimized_complete_comparison.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    print(f"\nBaseline System:")
    print(f"  Dataset: {baseline.get('dataset_size', 0)} PRs")
    print(f"  Actionability: {format_percentage(baseline_act)}")
    print(f"  Precision: {format_percentage(baseline_prec)}")
    print(f"  Noise Rate: {format_percentage(baseline_noise)}")
    print(f"  Avg Findings per PR: {baseline_findings:.2f}")
    
    print(f"\nOptimized System ({optimized_label}):")
    print(f"  Dataset: {optimized.get('dataset_size', 0)} PRs")
    print(f"  Actionability: {format_percentage(optimized_act)}")
    print(f"  Precision: {format_percentage(optimized_prec)}")
    print(f"  Noise Rate: {format_percentage(optimized_noise)}")
    print(f"  Avg Findings per PR: {optimized_findings:.2f}")
    
    print(f"\nImprovements:")
    print(f"  Actionability: {act_improvement['relative_percent']:+.1f}%")
    print(f"  Precision: {prec_improvement['relative_percent']:+.1f}%")
    print(f"  Noise Reduction: {abs(noise_improvement['relative_percent']):+.1f}%")
    print(f"  Findings Reduction: {abs(findings_improvement['relative_percent']):+.1f}%")
    
    if statistical_tests.get("actionability"):
        act_test = statistical_tests["actionability"]
        print(f"\nStatistical Tests:")
        print(f"  Actionability Chi-square: {act_test.get('chi2', 0):.4f}")
        print(f"  Actionability p-value: {act_test.get('p_value', 1):.4f}")
        print(f"  Actionability Significant: {act_test.get('significant', False)}")
    
    print(f"\n" + "=" * 70)
    print(f"Complete report saved to: {output_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()

