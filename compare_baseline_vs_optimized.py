"""Compare baseline vs optimized system."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from eval.metrics.statistical import proportion_test
from domain import SystemType

def load_evaluation_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load evaluation result from JSON file."""
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    print("=" * 70)
    print("BASELINE vs OPTIMIZED SYSTEM COMPARISON")
    print("=" * 70)
    
    # PR IDs
    pr_ids = ["20446", "20447", "20448", "20449", "20450", 
              "20451", "20452", "20453", "20454", "20455",
              "14584", "14585", "14586", "14587", "14588", 
              "14589", "14591", "14592", "14593", "14594"]
    
    # Try to load baseline from old evaluation (45 PR baseline)
    baseline_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_12000_14_143_14468_14595_and_40_more.json"
    baseline_data = load_evaluation_result(baseline_file)
    
    # Try to load optimized from existing file first
    # Check 10 Django PR file (has good results: 95.24%)
    django_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_20446_20447_20448_20449_20450_and_5_more.json"
    django_data = load_evaluation_result(django_file)
    
    # Try 20 PR file
    optimized_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
    optimized_data = load_evaluation_result(optimized_file)
    
    if optimized_data and optimized_data.get("actionability_rate", 0) > 0.5:
        # Use existing optimized data
        print("\nUsing existing optimized evaluation results...")
        optimized_result = None
        optimized_actionability = optimized_data.get("actionability_rate", 0)
        optimized_noise = optimized_data.get("noise_rate", 0)
        optimized_findings = optimized_data.get("avg_findings_per_pr", 0)
        optimized_precision = optimized_data.get("metadata", {}).get("precision", 0)
        optimized_metadata = optimized_data.get("metadata", {})
    else:
        # Run optimized evaluation
        print("\nRunning optimized system evaluation...")
        optimized_result = runner.run_evaluation(
            system_type=SystemType.MULTI_AGENT,
            use_stored_reviews=True,
            pr_ids=pr_ids,
            aggregate=True
        )
        optimized_actionability = optimized_result.actionability_rate
        optimized_noise = optimized_result.noise_rate
        optimized_findings = optimized_result.avg_findings_per_pr
        optimized_precision = optimized_result.metadata.get("precision", 0)
        optimized_metadata = optimized_result.metadata
    
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    if baseline_data:
        baseline_actionability = baseline_data.get("actionability_rate", 0)
        baseline_noise = baseline_data.get("noise_rate", 0)
        baseline_findings = baseline_data.get("avg_findings_per_pr", 0)
        baseline_precision = baseline_data.get("metadata", {}).get("precision", 0)
        
        print(f"\n{'Metric':<30} {'Baseline':<20} {'Optimized':<20} {'Improvement':<20}")
        print("-" * 90)
        
        # Actionability
        act_improvement = optimized_actionability - baseline_actionability
        print(f"{'Actionability Rate':<30} {baseline_actionability:.2%}          {optimized_actionability:.2%}          {act_improvement:+.2%}")
        
        # Noise
        noise_improvement = baseline_noise - optimized_noise
        print(f"{'Noise Rate':<30} {baseline_noise:.2%}          {optimized_noise:.2%}          {noise_improvement:+.2%}")
        
        # Findings
        findings_improvement = baseline_findings - optimized_findings
        print(f"{'Avg Findings per PR':<30} {baseline_findings:.2f}          {optimized_findings:.2f}          {findings_improvement:+.2f}")
        
        # Precision
        prec_improvement = optimized_precision - baseline_precision
        print(f"{'Precision':<30} {baseline_precision:.2%}          {optimized_precision:.2%}          {prec_improvement:+.2%}")
        
        # Statistical test
        print("\n" + "=" * 70)
        print("STATISTICAL TEST (Chi-Square)")
        print("=" * 70)
        
        baseline_actionable = baseline_data.get("metadata", {}).get("actionable_findings", 0)
        baseline_total = baseline_data.get("metadata", {}).get("total_findings", 0)
        optimized_actionable = optimized_metadata.get("actionable_findings", 0)
        optimized_total = optimized_metadata.get("total_findings", 0)
        
        if baseline_total > 0 and optimized_total > 0:
            test_result = proportion_test(
                successes_a=optimized_actionable,
                total_a=optimized_total,
                successes_b=baseline_actionable,
                total_b=baseline_total,
            )
            
            print(f"Chi-square: {test_result['chi2']:.4f}")
            print(f"p-value: {test_result['p_value']:.4f}")
            print(f"Significant: {test_result['significant']}")
    else:
        print("\nBaseline data not found. Showing optimized results only:")
        if optimized_result:
            print(f"  Actionability Rate: {optimized_result.actionability_rate:.2%}")
            print(f"  Noise Rate: {optimized_result.noise_rate:.2%}")
            print(f"  Important Issue Coverage: {optimized_result.important_issue_coverage:.2%}")
            print(f"  Precision: {optimized_result.metadata.get('precision', 0):.2%}")
            print(f"  Recall: {optimized_result.metadata.get('recall', 0):.2%}")
            print(f"  F1-Score: {optimized_result.metadata.get('f1_score', 0):.2%}")
            print(f"  Avg Findings per PR: {optimized_result.avg_findings_per_pr:.2f}")
        elif optimized_data:
            print(f"  Actionability Rate: {optimized_actionability:.2%}")
            print(f"  Noise Rate: {optimized_noise:.2%}")
            print(f"  Important Issue Coverage: {optimized_data.get('important_issue_coverage', 0):.2%}")
            print(f"  Precision: {optimized_precision:.2%}")
            print(f"  Recall: {optimized_metadata.get('recall', 0):.2%}")
            print(f"  F1-Score: {optimized_metadata.get('f1_score', 0):.2%}")
            print(f"  Avg Findings per PR: {optimized_findings:.2f}")

if __name__ == "__main__":
    main()

