"""Run evaluation for all dataset PRs."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    print("=" * 70)
    print("ALL DATASET EVALUATION")
    print("=" * 70)
    
    # Check ground truth coverage
    from eval.run_eval import DatasetLoader
    dataset_loader = DatasetLoader(settings.eval_dataset_path)
    ground_truth = dataset_loader.load_ground_truth()
    
    print(f"Ground truth entries: {len(ground_truth)}")
    missing_gt = []
    
    # Load all reviews
    from app.review_storage import ReviewStorage
    storage = ReviewStorage(settings)
    all_reviews = storage.list_reviews()
    reviewed_prs = {r["pr_id"] for r in all_reviews if r.get("system_type") == "multi_agent"}
    
    print(f"Multi-agent reviews: {len(reviewed_prs)}")
    
    for pr_id in reviewed_prs:
        if pr_id not in ground_truth:
            missing_gt.append(pr_id)
    
    if missing_gt:
        print(f"  Missing GT for: {sorted(missing_gt)}")
        print(f"  Run extract_ground_truth_from_reviews.py to add them")
    
    # Run evaluation for multi-agent
    print(f"\n{'=' * 70}")
    print("Running Multi-Agent Evaluation...")
    print(f"{'=' * 70}")
    
    try:
        result = runner.run_evaluation(
            system_type=SystemType.MULTI_AGENT,
            use_stored_reviews=True,
            aggregate=True
        )
        
        # Display results
        print(f"\n{'=' * 70}")
        print("EVALUATION RESULTS - MULTI-AGENT SYSTEM")
        print(f"{'=' * 70}")
        print(f"\nSystem: {result.system_type.value}")
        print(f"Dataset size: {result.dataset_size}")
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
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

