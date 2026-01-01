"""Run full evaluation on all stored reviews."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    print("=" * 70)
    print("FULL EVALUATION")
    print("=" * 70)
    print("Evaluating all stored reviews...")
    
    result = runner.run_evaluation(
        system_type=SystemType.MULTI_AGENT,
        use_stored_reviews=True,
        pr_ids=None,  # All reviews
        aggregate=True
    )
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Dataset Size: {result.dataset_size}")
    print(f"Actionability Rate: {result.actionability_rate:.2%}")
    print(f"Noise Rate: {result.noise_rate:.2%}")
    print(f"Important Issue Coverage: {result.important_issue_coverage:.2%}")
    print(f"Precision: {result.metadata.get('precision', 0):.2%}")
    print(f"Recall: {result.metadata.get('recall', 0):.2%}")
    print(f"F1-Score: {result.metadata.get('f1_score', 0):.2%}")

if __name__ == "__main__":
    main()

