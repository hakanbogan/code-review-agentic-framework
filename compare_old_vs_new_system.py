"""Compare old (baseline) vs new (optimized) system metrics."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import get_settings
from eval.metrics.statistical import proportion_test

def load_metrics(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load metrics from JSON file."""
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    settings = get_settings()
    
    print("=" * 70)
    print("OLD (BASELINE) vs NEW (OPTIMIZED) SYSTEM COMPARISON")
    print("=" * 70)
    
    # Load baseline metrics (try detailed first, then fallback to aggregated)
    baseline_file = settings.eval_results_path / "baseline_system_detailed_metrics.json"
    baseline_metrics = load_metrics(baseline_file)
    
    if not baseline_metrics:
        # Fallback to aggregated baseline file
        baseline_agg_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_12000_14_143_14468_14595_and_40_more.json"
        baseline_agg = load_metrics(baseline_agg_file)
        if baseline_agg:
            baseline_metrics = {
                "core_metrics": {
                    "actionability_rate": baseline_agg.get("actionability_rate", 0),
                    "noise_rate": baseline_agg.get("noise_rate", 0),
                    "important_issue_coverage": baseline_agg.get("important_issue_coverage", 0),
                },
                "advanced_metrics": baseline_agg.get("metadata", {}),
                "performance_metrics": {
                    "avg_findings_per_pr": baseline_agg.get("avg_findings_per_pr", 0),
                    "avg_review_time_s": baseline_agg.get("avg_review_time_s", 0),
                    "avg_token_cost": baseline_agg.get("avg_token_cost", 0),
                },
                "detailed_metadata": baseline_agg.get("metadata", {}),
            }
    
    # Load optimized metrics (try comprehensive agent file first, then detailed, then aggregated)
    optimized_file = settings.eval_results_path / "optimized_system_detailed_metrics.json"
    optimized_metrics = load_metrics(optimized_file)
    
    if not optimized_metrics:
        # Try comprehensive agent file (has actual optimized results)
        comp_file = settings.eval_results_path / "evaluation_comprehensive_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
        comp_data = load_metrics(comp_file)
        if comp_data:
            optimized_metrics = {
                "core_metrics": {
                    "actionability_rate": comp_data.get("actionability_rate", 0),
                    "noise_rate": comp_data.get("noise_rate", 0),
                    "important_issue_coverage": comp_data.get("important_issue_coverage", 0),
                },
                "advanced_metrics": comp_data.get("metadata", {}),
                "performance_metrics": {
                    "avg_findings_per_pr": comp_data.get("avg_findings_per_pr", 0),
                    "avg_review_time_s": comp_data.get("avg_review_time_s", 0),
                    "avg_token_cost": comp_data.get("avg_token_cost", 0),
                },
                "detailed_metadata": comp_data.get("metadata", {}),
            }
    
    if not optimized_metrics:
        # Fallback to aggregated multi-agent file
        opt_agg_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
        opt_agg = load_metrics(opt_agg_file)
        if opt_agg:
            optimized_metrics = {
                "core_metrics": {
                    "actionability_rate": opt_agg.get("actionability_rate", 0),
                    "noise_rate": opt_agg.get("noise_rate", 0),
                    "important_issue_coverage": opt_agg.get("important_issue_coverage", 0),
                },
                "advanced_metrics": opt_agg.get("metadata", {}),
                "performance_metrics": {
                    "avg_findings_per_pr": opt_agg.get("avg_findings_per_pr", 0),
                    "avg_review_time_s": opt_agg.get("avg_review_time_s", 0),
                    "avg_token_cost": opt_agg.get("avg_token_cost", 0),
                },
                "detailed_metadata": opt_agg.get("metadata", {}),
            }
    
    if not baseline_metrics or not optimized_metrics:
        print("\nERROR: Missing metrics files.")
        if not baseline_metrics:
            print("  - Run calculate_baseline_metrics.py first")
        if not optimized_metrics:
            print("  - Run calculate_optimized_metrics.py first")
        return
    
    baseline_core = baseline_metrics.get("core_metrics", {})
    optimized_core = optimized_metrics.get("core_metrics", {})
    baseline_advanced = baseline_metrics.get("advanced_metrics", {})
    optimized_advanced = optimized_metrics.get("advanced_metrics", {})
    baseline_perf = baseline_metrics.get("performance_metrics", {})
    optimized_perf = optimized_metrics.get("performance_metrics", {})
    
    print("\n" + "=" * 70)
    print("METRIC COMPARISON")
    print("=" * 70)
    
    print(f"\n{'Metric':<35} {'Old (Baseline)':<20} {'New (Optimized)':<20} {'Change':<20}")
    print("-" * 95)
    
    # Core Metrics
    print("\nCore Metrics:")
    old_act = baseline_core.get("actionability_rate", 0)
    new_act = optimized_core.get("actionability_rate", 0)
    act_change = new_act - old_act
    print(f"{'Actionability Rate':<35} {old_act:.2%}          {new_act:.2%}          {act_change:+.2%}")
    
    old_noise = baseline_core.get("noise_rate", 0)
    new_noise = optimized_core.get("noise_rate", 0)
    noise_change = old_noise - new_noise  # Lower is better
    print(f"{'Noise Rate':<35} {old_noise:.2%}          {new_noise:.2%}          {noise_change:+.2%}")
    
    old_cov = baseline_core.get("important_issue_coverage", 0)
    new_cov = optimized_core.get("important_issue_coverage", 0)
    cov_change = new_cov - old_cov
    print(f"{'Important Issue Coverage':<35} {old_cov:.2%}          {new_cov:.2%}          {cov_change:+.2%}")
    
    # Advanced Metrics
    print("\nAdvanced Metrics:")
    old_prec = baseline_advanced.get("precision", 0)
    new_prec = optimized_advanced.get("precision", 0)
    prec_change = new_prec - old_prec
    print(f"{'Precision':<35} {old_prec:.2%}          {new_prec:.2%}          {prec_change:+.2%}")
    
    old_rec = baseline_advanced.get("recall", 0)
    new_rec = optimized_advanced.get("recall", 0)
    rec_change = new_rec - old_rec
    print(f"{'Recall':<35} {old_rec:.2%}          {new_rec:.2%}          {rec_change:+.2%}")
    
    old_f1 = baseline_advanced.get("f1_score", 0)
    new_f1 = optimized_advanced.get("f1_score", 0)
    f1_change = new_f1 - old_f1
    print(f"{'F1-Score':<35} {old_f1:.2%}          {new_f1:.2%}          {f1_change:+.2%}")
    
    # Performance Metrics
    print("\nPerformance Metrics:")
    old_findings = baseline_perf.get("avg_findings_per_pr", 0)
    new_findings = optimized_perf.get("avg_findings_per_pr", 0)
    findings_change = new_findings - old_findings
    print(f"{'Avg Findings per PR':<35} {old_findings:.2f}          {new_findings:.2f}          {findings_change:+.2f}")
    
    old_time = baseline_perf.get("avg_review_time_s", 0)
    new_time = optimized_perf.get("avg_review_time_s", 0)
    time_change = new_time - old_time
    print(f"{'Avg Review Time (s)':<35} {old_time:.2f}          {new_time:.2f}          {time_change:+.2f}")
    
    # Statistical Tests
    print("\n" + "=" * 70)
    print("STATISTICAL TESTS (Chi-Square)")
    print("=" * 70)
    
    baseline_meta = baseline_metrics.get("detailed_metadata", {})
    optimized_meta = optimized_metrics.get("detailed_metadata", {})
    
    baseline_actionable = baseline_meta.get("actionable_findings", 0)
    baseline_total = baseline_meta.get("total_findings", 0)
    optimized_actionable = optimized_meta.get("actionable_findings", 0)
    optimized_total = optimized_meta.get("total_findings", 0)
    
    if baseline_total > 0 and optimized_total > 0:
        # Actionability test
        act_test = proportion_test(
            successes_a=optimized_actionable,
            total_a=optimized_total,
            successes_b=baseline_actionable,
            total_b=baseline_total,
        )
        
        print("\n1. Actionability Rate Test:")
        print(f"   Chi-square: {act_test['chi2']:.4f}")
        print(f"   p-value: {act_test['p_value']:.4f}")
        print(f"   Significant (p < 0.05): {act_test['significant']}")
        
        # Precision test
        baseline_prec_count = int(old_prec * baseline_total) if baseline_total > 0 else 0
        optimized_prec_count = int(new_prec * optimized_total) if optimized_total > 0 else 0
        
        prec_test = proportion_test(
            successes_a=optimized_prec_count,
            total_a=optimized_total,
            successes_b=baseline_prec_count,
            total_b=baseline_total,
        )
        
        print("\n2. Precision Test:")
        print(f"   Chi-square: {prec_test['chi2']:.4f}")
        print(f"   p-value: {prec_test['p_value']:.4f}")
        print(f"   Significant (p < 0.05): {prec_test['significant']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Actionability Improvement: {act_change:+.2%}")
    print(f"Noise Reduction: {noise_change:+.2%}")
    print(f"Precision Improvement: {prec_change:+.2%}")
    print(f"F1-Score Improvement: {f1_change:+.2%}")
    print(f"Findings Reduction: {findings_change:+.2f} per PR ({((old_findings - new_findings) / old_findings * 100) if old_findings > 0 else 0:.1f}%)")

if __name__ == "__main__":
    main()

