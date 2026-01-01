"""Calculate detailed metrics for baseline system."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def load_baseline_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load baseline evaluation result."""
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    settings = get_settings()
    
    print("=" * 70)
    print("BASELINE SYSTEM METRICS CALCULATION")
    print("=" * 70)
    
    # Try to load from existing baseline evaluation (45 PR baseline)
    baseline_file = settings.eval_results_path / "evaluation_multi_agent_aggregated_12000_14_143_14468_14595_and_40_more.json"
    baseline_data = load_baseline_result(baseline_file)
    
    if baseline_data:
        metadata = baseline_data.get("metadata", {})
        
        print("\n" + "=" * 70)
        print("BASELINE SYSTEM METRICS (FROM STORED EVALUATION)")
        print("=" * 70)
        
        print("\nCore Metrics:")
        actionability = baseline_data.get("actionability_rate", 0)
        print(f"  Actionability Rate: {actionability:.4f} ({actionability:.2%})")
        print(f"    - Total Findings: {metadata.get('total_findings', 0)}")
        print(f"    - Actionable Findings: {metadata.get('actionable_findings', 0)}")
        
        noise = baseline_data.get("noise_rate", 0)
        print(f"\n  Noise Rate: {noise:.4f} ({noise:.2%})")
        print(f"    - Total Noise Findings: {metadata.get('total_noise_findings', 0)}")
        
        coverage = baseline_data.get("important_issue_coverage", 0)
        print(f"\n  Important Issue Coverage: {coverage:.4f} ({coverage:.2%})")
        print(f"    - Total Important Issues: {metadata.get('total_important_issues', 0)}")
        print(f"    - Detected Important Issues: {metadata.get('detected_important_issues', 0)}")
        
        print("\nAdvanced Metrics:")
        precision = metadata.get('precision', 0)
        recall = metadata.get('recall', 0)
        f1_score = metadata.get('f1_score', 0)
        
        print(f"  Precision: {precision:.4f} ({precision:.2%})")
        print(f"  Recall: {recall:.4f} ({recall:.2%})")
        print(f"  F1-Score: {f1_score:.4f} ({f1_score:.2%})")
        
        print("\nPerformance Metrics:")
        print(f"  Avg Findings per PR: {baseline_data.get('avg_findings_per_pr', 0):.2f}")
        print(f"  Avg Review Time: {baseline_data.get('avg_review_time_s', 0):.2f}s")
        print(f"  Avg Token Cost: ${baseline_data.get('avg_token_cost', 0):.4f}")
        
        # Save detailed metrics
        output_file = settings.eval_results_path / "baseline_system_detailed_metrics.json"
        with open(output_file, 'w') as f:
            json.dump({
                "system_type": baseline_data.get("system_type", "multi_agent"),
                "dataset_size": baseline_data.get("dataset_size", 0),
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
                    "avg_findings_per_pr": baseline_data.get('avg_findings_per_pr', 0),
                    "avg_review_time_s": baseline_data.get('avg_review_time_s', 0),
                    "avg_token_cost": baseline_data.get('avg_token_cost', 0),
                },
                "detailed_metadata": metadata,
            }, f, indent=2)
        
        print(f"\nBaseline metrics saved to: {output_file}")
    else:
        print("\nBaseline evaluation file not found.")
        print("Expected file: evaluation_multi_agent_aggregated_12000_14_143_14468_14595_and_40_more.json")
        print("\nTo calculate baseline metrics, run evaluation on baseline PRs first.")

if __name__ == "__main__":
    main()

