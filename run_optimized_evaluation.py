"""Run evaluation for optimized system reviews."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    # 20 PR IDs reviewed with optimized system (10 Django + 10 FastAPI)
    optimized_prs = ["20446", "20447", "20448", "20449", "20450", 
                     "20451", "20452", "20453", "20454", "20455",
                     "14584", "14585", "14586", "14587", "14588", 
                     "14589", "14591", "14592", "14593", "14594"]
    
    print("=" * 70)
    print("OPTIMIZED SYSTEM EVALUATION")
    print("=" * 70)
    print(f"Evaluating {len(optimized_prs)} PRs reviewed with optimized system...")
    print("\nOptimizations applied:")
    print("  - Supervisor: Quality filtering (score < 0.6 filtered)")
    print("  - Supervisor: Minor issue limit (max 3)")
    print("  - Revision Proposer: MINOR severity patches enabled")
    print("  - Revision Proposer: Patch limit increased to 10")
    print("  - Config: max_nits_per_review = 2 (was 5)")
    print("  - Config: max_patch_lines = 15 (was 10)")
    
    result = runner.run_evaluation(
        system_type=SystemType.MULTI_AGENT,
        use_stored_reviews=True,
        pr_ids=optimized_prs,
        aggregate=True
    )
    
    print("\n" + "=" * 70)
    print("OPTIMIZED SYSTEM RESULTS")
    print("=" * 70)
    print(f"Dataset Size: {result.dataset_size} PRs")
    print(f"\nCore Metrics:")
    print(f"  Actionability Rate: {result.actionability_rate:.2%}")
    print(f"  Noise Rate: {result.noise_rate:.2%}")
    print(f"  Important Issue Coverage: {result.important_issue_coverage:.2%}")
    print(f"\nAdvanced Metrics:")
    print(f"  Precision: {result.metadata.get('precision', 0):.2%}")
    print(f"  Recall: {result.metadata.get('recall', 0):.2%}")
    print(f"  F1-Score: {result.metadata.get('f1_score', 0):.2%}")
    print(f"\nPerformance Metrics:")
    print(f"  Avg Findings per PR: {result.avg_findings_per_pr:.2f}")
    print(f"  Avg Review Time: {result.avg_review_time_s:.2f}s")
    print(f"  Avg Token Cost: ${result.avg_token_cost:.4f}")
    
    # Compare with baseline if available
    print("\n" + "=" * 70)
    print("COMPARISON WITH BASELINE")
    print("=" * 70)
    print("Baseline metrics (from previous evaluation):")
    print("  Actionability Rate: ~31.5%")
    print("  Noise Rate: ~1.3%")
    print("  Avg Findings per PR: ~11.6")
    print("\nOptimized system improvements:")
    actionability_improvement = result.actionability_rate - 0.315
    noise_improvement = 0.013 - result.noise_rate
    findings_improvement = 11.6 - result.avg_findings_per_pr
    print(f"  Actionability: +{actionability_improvement:.2%}")
    print(f"  Noise Reduction: {noise_improvement:.2%}")
    print(f"  Findings Reduction: {findings_improvement:.2f} per PR")

if __name__ == "__main__":
    main()

