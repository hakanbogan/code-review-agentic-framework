"""Calculate optimization improvements and statistics."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import get_settings
from eval.metrics.statistical import proportion_test

def load_evaluation_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load evaluation result from JSON file."""
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_improvements(baseline: Dict, optimized: Dict) -> Dict[str, Any]:
    """Calculate improvement percentages and statistics."""
    baseline_meta = baseline.get("metadata", {})
    optimized_meta = optimized.get("metadata", {})
    
    improvements = {}
    
    # Actionability
    baseline_act = baseline.get("actionability_rate", 0)
    optimized_act = optimized.get("actionability_rate", 0)
    act_improvement = optimized_act - baseline_act
    act_improvement_pct = (act_improvement / baseline_act * 100) if baseline_act > 0 else 0
    
    improvements["actionability"] = {
        "baseline": baseline_act,
        "optimized": optimized_act,
        "absolute_improvement": act_improvement,
        "relative_improvement_pct": act_improvement_pct,
    }
    
    # Precision
    baseline_prec = baseline_meta.get("precision", 0)
    optimized_prec = optimized_meta.get("precision", 0)
    prec_improvement = optimized_prec - baseline_prec
    prec_improvement_pct = (prec_improvement / baseline_prec * 100) if baseline_prec > 0 else 0
    
    improvements["precision"] = {
        "baseline": baseline_prec,
        "optimized": optimized_prec,
        "absolute_improvement": prec_improvement,
        "relative_improvement_pct": prec_improvement_pct,
    }
    
    # Noise (lower is better)
    baseline_noise = baseline.get("noise_rate", 0)
    optimized_noise = optimized.get("noise_rate", 0)
    noise_reduction = baseline_noise - optimized_noise
    noise_reduction_pct = (noise_reduction / baseline_noise * 100) if baseline_noise > 0 else 0
    
    improvements["noise"] = {
        "baseline": baseline_noise,
        "optimized": optimized_noise,
        "reduction": noise_reduction,
        "reduction_pct": noise_reduction_pct,
    }
    
    # Findings per PR (lower is better for efficiency)
    baseline_findings = baseline.get("avg_findings_per_pr", 0)
    optimized_findings = optimized.get("avg_findings_per_pr", 0)
    findings_reduction = baseline_findings - optimized_findings
    findings_reduction_pct = (findings_reduction / baseline_findings * 100) if baseline_findings > 0 else 0
    
    improvements["findings_per_pr"] = {
        "baseline": baseline_findings,
        "optimized": optimized_findings,
        "reduction": findings_reduction,
        "reduction_pct": findings_reduction_pct,
    }
    
    # Statistical tests
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
        improvements["statistical_tests"] = {
            "actionability": act_test,
        }
    
    return improvements

def main():
    settings = get_settings()
    
    print("=" * 70)
    print("OPTIMIZATION IMPROVEMENTS CALCULATION")
    print("=" * 70)
    
    # Load baseline (45 PR baseline)
    baseline_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_12000_14_143_14468_14595_and_40_more.json"
    baseline = load_evaluation_result(baseline_file)
    
    # Load optimized (try comprehensive agent file first - has actual optimized results)
    optimized_file = settings.eval_results_path / "evaluation_comprehensive_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
    optimized = load_evaluation_result(optimized_file)
    
    if not optimized:
        # Fallback to multi-agent file
        optimized_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_14584_14585_14586_14587_14588_and_15_more.json"
        optimized = load_evaluation_result(optimized_file)
    
    if not baseline or not optimized:
        print("\nERROR: Missing evaluation files.")
        if not baseline:
            print("  Baseline file not found")
        if not optimized:
            print("  Optimized file not found")
        return
    
    improvements = calculate_improvements(baseline, optimized)
    
    print("\n" + "=" * 70)
    print("IMPROVEMENTS SUMMARY")
    print("=" * 70)
    
    print("\n1. Actionability Rate:")
    act = improvements["actionability"]
    print(f"   Baseline: {act['baseline']:.2%}")
    print(f"   Optimized: {act['optimized']:.2%}")
    print(f"   Improvement: {act['absolute_improvement']:+.2%} ({act['relative_improvement_pct']:+.1f}%)")
    
    print("\n2. Precision:")
    prec = improvements["precision"]
    print(f"   Baseline: {prec['baseline']:.2%}")
    print(f"   Optimized: {prec['optimized']:.2%}")
    print(f"   Improvement: {prec['absolute_improvement']:+.2%} ({prec['relative_improvement_pct']:+.1f}%)")
    
    print("\n3. Noise Rate:")
    noise = improvements["noise"]
    print(f"   Baseline: {noise['baseline']:.2%}")
    print(f"   Optimized: {noise['optimized']:.2%}")
    print(f"   Reduction: {noise['reduction']:+.2%} ({noise['reduction_pct']:+.1f}%)")
    
    print("\n4. Avg Findings per PR:")
    findings = improvements["findings_per_pr"]
    print(f"   Baseline: {findings['baseline']:.2f}")
    print(f"   Optimized: {findings['optimized']:.2f}")
    print(f"   Reduction: {findings['reduction']:+.2f} ({findings['reduction_pct']:+.1f}%)")
    
    if "statistical_tests" in improvements:
        print("\n" + "=" * 70)
        print("STATISTICAL VALIDATION")
        print("=" * 70)
        act_test = improvements["statistical_tests"]["actionability"]
        print(f"\nActionability Chi-Square Test:")
        print(f"  Chi-square: {act_test['chi2']:.4f}")
        print(f"  p-value: {act_test['p_value']:.4f}")
        print(f"  Significant: {act_test['significant']}")
    
    # Save improvements
    output_file = settings.eval_results_path / "optimization_improvements.json"
    with open(output_file, 'w') as f:
        json.dump(improvements, f, indent=2)
    
    print(f"\nImprovements saved to: {output_file}")

if __name__ == "__main__":
    main()

