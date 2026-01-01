"""Run evaluation for FastAPI PRs."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    # FastAPI PR IDs
    fastapi_prs = ["14584", "14585", "14586", "14587", "14588", 
                   "14589", "14591", "14592", "14593", "14594"]
    
    print("=" * 70)
    print("FASTAPI PR EVALUATION")
    print("=" * 70)
    print(f"Evaluating {len(fastapi_prs)} FastAPI PRs...")
    
    result = runner.run_evaluation(
        system_type=SystemType.MULTI_AGENT,
        use_stored_reviews=True,
        pr_ids=fastapi_prs,
        aggregate=True
    )
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Actionability Rate: {result.actionability_rate:.2%}")
    print(f"Noise Rate: {result.noise_rate:.2%}")
    print(f"Important Issue Coverage: {result.important_issue_coverage:.2%}")
    print(f"Precision: {result.metadata.get('precision', 0):.2%}")
    print(f"Recall: {result.metadata.get('recall', 0):.2%}")
    print(f"F1-Score: {result.metadata.get('f1_score', 0):.2%}")

if __name__ == "__main__":
    main()

